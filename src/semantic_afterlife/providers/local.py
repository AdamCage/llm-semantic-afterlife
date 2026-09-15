"""Local Hugging Face transformers client (ADR-0011).

Routers still host no true base models (re-measured 2026-09-01). This client
runs a local checkpoint through the same ``InferenceClient`` surface as
RouterAI / OpenRouter so the sliding-window engine, cache, ledger and replay
path do not fork.

Weights live on disk; generation costs $0. Embeddings go through a lazily
created :class:`LocalEmbedClient` so ``api: local`` representation slugs
do not fall back to a hosted provider (ADR-0024).
"""

from __future__ import annotations

import asyncio
import gc
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Protocol

from ..config import ExecutionMode, Settings
from ..errors import ProviderError, ReasoningLeakError
from ..ledger import Usage
from ..logging_utils import EventLogger, get_logger
from ..tokenization import Tokenizer, load_tokenizer
from .base import (
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    InferenceClient,
)
from .cache import ResponseCache, cache_key

logger = get_logger("providers.local")

#: Keys in ``request.extra`` that configure the loader, not the sampler.
_LOAD_KEYS = frozenset(
    {
        "device",
        "dtype",
        "attn_implementation",
        "local_files_only",
        "trust_remote_code",
        "low_cpu_mem_usage",
        "tokenizer_repo",
        "tokenizer_revision",
        "revision",
        "model_revision",
        "device_map",
        "quantization",
        "load_in_4bit",
        "load_in_8bit",
        "bnb_4bit_quant_type",
        "bnb_4bit_use_double_quant",
        "bnb_4bit_compute_dtype",
        "bnb_4bit_quant_storage",
        "llm_int8_threshold",
        "llm_int8_skip_modules",
        "llm_int8_enable_fp32_cpu_offload",
        "llm_int8_has_fp16_weight",
        # Protocol knobs recorded in extra_body; never sampler kwargs.
        "serialization",
        "text_only",
        "enable_thinking",
        "notes",
    }
)

_PATH = "/local/completions"

_THINK_MARKERS = (
    "<think>",
    "</think>",
)


def _wants_cuda(extra: dict[str, Any]) -> bool:
    device = str(extra.get("device") or "cpu")
    device_map = extra.get("device_map")
    if device.startswith("cuda"):
        return True
    if device_map in {0, "cuda", "auto"}:
        return True
    if isinstance(device_map, str) and device_map.startswith("cuda"):
        return True
    return bool(extra.get("load_in_4bit") or extra.get("load_in_8bit"))


def _default_embed_device() -> str:
    """Prefer CUDA after the generator is unloaded; stay CPU when torch is absent."""
    try:
        import torch
    except ImportError:
        return "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


def assert_no_thinking(text: str, *, model_id: str) -> None:
    """Fail the step if a thinking block leaked into visible text."""
    lowered = text.lower()
    for marker in _THINK_MARKERS:
        if marker.lower() in lowered:
            raise ReasoningLeakError(
                f"thinking tokens leaked into visible completion for {model_id!r}; "
                "Paper B requires thinking disabled (ADR-0023)"
            )


@dataclass(frozen=True, slots=True)
class LocalGeneration:
    """Token ids produced by a backend, already stripped of a trailing EOS."""

    token_ids: list[int]
    finish_reason: str
    extras: dict[str, Any] = field(default_factory=dict)


class LocalBackend(Protocol):
    """Swap-in for tests. Production uses :class:`TransformersBackend`."""

    def generate(
        self,
        input_ids: list[int],
        *,
        max_tokens: int,
        temperature: float,
        top_p: float,
        top_k: int | None,
        repetition_penalty: float | None,
        seed: int | None,
        extra: dict[str, Any],
    ) -> LocalGeneration: ...


class LocalClient(InferenceClient):
    """CPU (or local GPU) completions from a Hugging Face causal LM."""

    name = "local"

    def __init__(
        self,
        settings: Settings,
        *,
        events: EventLogger | None = None,
        cache: ResponseCache | None = None,
        tokenizer: Tokenizer | None = None,
        backend: LocalBackend | None = None,
    ) -> None:
        self._settings = settings
        self._events = events
        self._cache = cache
        self._mode = settings.afterlife_execution_mode
        self._injected_tokenizer = tokenizer
        self._injected_backend = backend
        self._lock = asyncio.Lock()
        self._resolved: dict[str, tuple[Tokenizer, LocalBackend]] = {}
        self._embed_client: Any | None = None

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        path, payload = self.build_payload(request)
        key = cache_key(
            self.name,
            path,
            payload if request.cache_bust is None else {**payload, "__probe": request.cache_bust},
        )

        if self._mode is ExecutionMode.REPLAY:
            if self._cache is None:
                raise ProviderError("replay mode requires a response cache")
            entry = self._cache.require(key, context=f"{path} {request.model_id}")
            return self._parse(
                request, _cached_body(entry), latency_s=0.0, attempts=0, from_cache=True
            )

        cached = self._cache.get(key) if self._cache is not None else None
        if cached is not None:
            return self._parse(
                request, _cached_body(cached), latency_s=0.0, attempts=0, from_cache=True
            )

        body, latency, attempts = await self._generate(request)
        if self._cache is not None:
            self._cache.put(key, provider=self.name, path=path, payload=payload, body=body)
        return self._parse(request, body, latency_s=latency, attempts=attempts, from_cache=False)

    def build_payload(self, request: CompletionRequest) -> tuple[str, dict[str, Any]]:
        """Canonical payload used as the cache key.

        Includes loader knobs (device, dtype) so a replay cannot silently mix
        a CPU float32 body with a later bfloat16 request.
        """
        payload: dict[str, Any] = {
            "model": request.model_id,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "seed": request.seed,
            "extra": dict(request.extra),
        }
        if request.is_chat:
            payload["messages"] = [dict(message) for message in request.messages or ()]
        else:
            payload["prompt"] = request.prompt
        if request.top_k is not None:
            payload["top_k"] = request.top_k
        if request.repetition_penalty is not None:
            payload["repetition_penalty"] = request.repetition_penalty
        if request.stop:
            payload["stop"] = list(request.stop)
        return _PATH, payload

    async def _generate(self, request: CompletionRequest) -> tuple[dict[str, Any], float, int]:
        tokenizer, backend = self._resolve(request)
        source = (
            request.prompt if request.prompt is not None else _messages_to_text(request.messages)
        )
        input_ids = tokenizer.encode(source)
        start = perf_counter()
        async with self._lock:
            generation = await asyncio.to_thread(
                backend.generate,
                input_ids,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k,
                repetition_penalty=request.repetition_penalty,
                seed=request.seed,
                extra={k: v for k, v in request.extra.items() if k not in _LOAD_KEYS},
            )
        latency = perf_counter() - start
        token_ids = list(generation.token_ids[: request.max_tokens])
        text = tokenizer.decode(token_ids)
        if request.stop:
            text = _truncate_at_stop(text, request.stop)
        assert_no_thinking(text, model_id=request.model_id)
        local_meta: dict[str, Any] = {
            "device": request.extra.get("device", "cpu"),
            "dtype": request.extra.get("dtype"),
            "n_input_ids": len(input_ids),
            "n_output_ids": len(token_ids),
        }
        local_meta.update(generation.extras)
        if self._events is not None:
            self._events.event(
                "local.generate.completed",
                model_id=request.model_id,
                n_input_ids=len(input_ids),
                n_output_ids=len(token_ids),
                finish_reason=generation.finish_reason,
                tok_s=generation.extras.get("tok_s"),
                decode_s=generation.extras.get("decode_s"),
                peak_vram_mib=generation.extras.get("peak_vram_mib"),
                hf_revision=generation.extras.get("hf_revision"),
                architecture=generation.extras.get("architecture"),
                loader_class=generation.extras.get("loader_class"),
                quant_config=generation.extras.get("quant_config"),
            )
        body: dict[str, Any] = {
            "id": f"local-{request.model_id}",
            "model": request.model_id,
            "provider": "local",
            "object": "text_completion",
            "choices": [
                {
                    "index": 0,
                    "text": text,
                    "finish_reason": generation.finish_reason,
                }
            ],
            "usage": {
                "prompt_tokens": len(input_ids),
                "completion_tokens": len(token_ids),
            },
            "local": local_meta,
        }
        return body, latency, 1

    def _resolve(self, request: CompletionRequest) -> tuple[Tokenizer, LocalBackend]:
        if self._injected_tokenizer is not None and self._injected_backend is not None:
            return self._injected_tokenizer, self._injected_backend
        cached = self._resolved.get(request.model_id)
        if cached is not None:
            return cached
        extra = request.extra
        repo = str(extra.get("tokenizer_repo") or request.model_id)
        revision = extra.get("tokenizer_revision")
        revision_s = str(revision) if revision else None
        tokenizer = self._injected_tokenizer or load_tokenizer(
            repo, revision_s, str(self._settings.paths.tokenizer_cache)
        )
        if _wants_cuda(dict(extra)) and self._resolved:
            others = [mid for mid in self._resolved if mid != request.model_id]
            if others:
                raise ProviderError(
                    "refusing to load a second CUDA local model while "
                    f"{others[0]!r} is still resident; call unload() first (ADR-0024)"
                )
        backend = TransformersBackend(
            model_id=request.model_id,
            token=self._settings.hf_token,
            extra=extra,
            events=self._events,
        )
        resolved = (tokenizer, backend)
        self._resolved[request.model_id] = resolved
        return resolved

    def _parse(
        self,
        request: CompletionRequest,
        body: dict[str, Any],
        *,
        latency_s: float,
        attempts: int,
        from_cache: bool,
    ) -> CompletionResponse:
        choices = body.get("choices")
        if not choices:
            raise ProviderError(f"local backend returned no choices for {request.model_id}")
        choice = choices[0]
        usage_block = body.get("usage") or {}
        return CompletionResponse(
            text=choice.get("text") or "",
            finish_reason=choice.get("finish_reason"),
            usage=Usage(
                prompt_tokens=int(usage_block.get("prompt_tokens") or 0),
                completion_tokens=int(usage_block.get("completion_tokens") or 0),
                cost_usd=0.0,
                from_cache=from_cache,
            ),
            served_provider="local",
            model_returned=body.get("model") or request.model_id,
            latency_s=latency_s,
            attempts=attempts,
            from_cache=from_cache,
            raw=body,
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        if self._embed_client is None:
            from .local_embed import LocalEmbedClient

            self._embed_client = LocalEmbedClient(device=_default_embed_device())
        return await self._embed_client.embed(request)

    async def list_models(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "google/gemma-3-270m",
                "name": "Gemma 3 270M (local, pretrained)",
                "supported_apis": ["completions"],
            },
            {
                "id": "google/gemma-3-1b-pt",
                "name": "Gemma 3 1B PT (local, pretrained)",
                "supported_apis": ["completions"],
            },
            {
                "id": "google/gemma-4-E2B",
                "name": "Gemma 4 E2B (local, pretrained; multimodal, ~10 GB)",
                "supported_apis": ["completions"],
            },
        ]

    async def unload(self, model_id: str | None = None) -> None:
        """Drop one (or every) loaded backend and free CUDA cache (ADR-0024)."""
        if self._injected_backend is not None:
            self._resolved.clear()
            return
        targets = list(self._resolved) if model_id is None else [model_id]
        for mid in targets:
            resolved = self._resolved.pop(mid, None)
            if resolved is None:
                continue
            _tokenizer, backend = resolved
            unload = getattr(backend, "unload", None)
            if callable(unload):
                unload()
        if self._embed_client is not None:
            await self._embed_client.unload(model_id)
            if model_id is None:
                self._embed_client = None
        self._clear_cuda_cache()
        from .registry import forget_client

        forget_client("local")

    async def aclose(self) -> None:
        await self.unload(None)

    @staticmethod
    def _clear_cuda_cache() -> None:
        try:
            import torch
        except ImportError:
            return
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()


def _cuda_mem() -> dict[str, float]:
    """Allocated / reserved / peak CUDA memory in MiB. Empty on CPU."""
    try:
        import torch
    except ImportError:
        return {}
    if not torch.cuda.is_available():
        return {}
    return {
        "allocated_mib": round(torch.cuda.memory_allocated() / 1024**2, 1),
        "reserved_mib": round(torch.cuda.memory_reserved() / 1024**2, 1),
        "peak_vram_mib": round(torch.cuda.max_memory_allocated() / 1024**2, 1),
    }


_MULTIMODAL_AUTO = (
    "AutoModelForImageTextToText",
    "AutoModelForMultimodalLM",
)
_CAUSAL_FALLBACK_MARKERS = ("Gemma4", "Unified")
_ARCH_SUFFIXES = (
    "ForConditionalGeneration",
    "ForCausalLM",
    "ForImageTextToText",
)


def _is_multimodal_architecture(architecture: str) -> bool:
    return "ConditionalGeneration" in architecture or "Unified" in architecture


def _architecture_module_guesses(architecture: str, model_type: str = "") -> tuple[str, ...]:
    """Hub ``architectures[0]`` / ``model_type`` → ``transformers.models.<leaf>`` guesses."""
    guesses: list[str] = []
    if model_type:
        leaf = model_type.replace("-", "_")
        guesses.append(leaf)
        if "_" in leaf:
            guesses.append(leaf.split("_", 1)[0])
    stem = architecture
    for suffix in _ARCH_SUFFIXES:
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    stem = stem.replace("Unified", "")
    if stem:
        guesses.append(stem.lower())
    seen: list[str] = []
    for guess in guesses:
        if guess and guess not in seen:
            seen.append(guess)
    return tuple(seen)


def _bind_architecture_class(
    transformers: Any, architecture: str, model_type: str = ""
) -> None:
    """Export ``architecture`` onto the transformers module if it only lives in models.*."""
    if not architecture or getattr(transformers, architecture, None) is not None:
        return
    import importlib

    for leaf in _architecture_module_guesses(architecture, model_type):
        for mod_name in (
            f"transformers.models.{leaf}.modeling_{leaf}",
            f"transformers.models.{leaf}",
        ):
            try:
                module = importlib.import_module(mod_name)
            except ImportError:
                continue
            found = getattr(module, architecture, None)
            if found is not None:
                setattr(transformers, architecture, found)
                return


def _resolve_model_class(transformers: Any, causal_cls: Any, architecture: str) -> tuple[Any, str]:
    """Pick the HF class from ``config.architectures``.

    Transformers 5 dropped ``AutoModelForConditionalGeneration``. Ministral 3 is
    ``Mistral3ForConditionalGeneration`` and is *not* in the CausalLM auto map
    (Wave 2 smoke failed on that fallback). Gemma 4 Unified can load through
    CausalLM as a last resort. Quant/map keys stay in ``_LOAD_KEYS``.
    """
    if architecture:
        named = getattr(transformers, architecture, None)
        if named is not None:
            return named, architecture
    if _is_multimodal_architecture(architecture):
        for candidate in _MULTIMODAL_AUTO:
            found = getattr(transformers, candidate, None)
            if found is not None:
                return found, candidate
        if any(marker in architecture for marker in _CAUSAL_FALLBACK_MARKERS):
            return causal_cls, "AutoModelForCausalLM"
        version = getattr(transformers, "__version__", "unknown")
        raise ProviderError(
            f"transformers {version} cannot load {architecture!r} "
            "(no named class, no ImageTextToText/MultimodalLM auto). "
            "Upgrade the WSL env used by wave2_run_one.sh; do not swap model ids."
        )
    return causal_cls, "AutoModelForCausalLM"


def _multimodal_generate_failed(exc: BaseException) -> bool:
    message = str(exc).lower()
    return any(
        needle in message
        for needle in (
            "pixel_values",
            "pixel values",
            "image_grid",
            "vision",
            "audio_values",
        )
    )


def _quant_label(extra: dict[str, Any]) -> str:
    if extra.get("load_in_4bit") or str(extra.get("quantization", "")).lower() in {"nf4", "4bit"}:
        return "nf4"
    if extra.get("load_in_8bit") or str(extra.get("quantization", "")).lower() in {"int8", "8bit"}:
        return "int8"
    return "none"


class TransformersBackend:
    """Lazy HF wrapper. Causal-LM or ConditionalGeneration; torch imported on first use."""

    def __init__(
        self,
        *,
        model_id: str,
        token: str | None,
        extra: dict[str, Any],
        events: EventLogger | None = None,
    ) -> None:
        self.model_id = model_id
        self._token = token
        self._extra = dict(extra)
        self._events = events
        self._model: Any = None
        self._eos_ids: set[int] = set()
        self.load_stats: dict[str, Any] = {}

    def _emit(self, name: str, *, mirror: str | None = None, **fields: Any) -> None:
        if self._events is not None:
            self._events.event(name, mirror=mirror, **fields)
        elif mirror:
            logger.info(mirror)

    def unload(self) -> None:
        mem = _cuda_mem()
        if self._model is not None:
            self._emit(
                "local.model.unloaded",
                model_id=self.model_id,
                architecture=self.load_stats.get("architecture"),
                **mem,
                mirror=f"unloaded {self.model_id} peak_vram_mib={mem.get('peak_vram_mib')}",
            )
        self._model = None
        self._eos_ids = set()
        gc.collect()

    def _load(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            import torch
            import transformers
            from transformers import AutoConfig, AutoModelForCausalLM
        except ImportError as exc:
            raise ProviderError(
                "local inference requires the optional extra `local` "
                "(torch + transformers). Install with "
                "`uv sync --extra local` or "
                "`uv pip install torch --index-url https://download.pytorch.org/whl/cpu "
                "&& uv pip install 'transformers>=4.51' accelerate`."
            ) from exc

        wants_quant = bool(
            self._extra.get("load_in_4bit")
            or self._extra.get("load_in_8bit")
            or self._extra.get("quantization")
        )
        device = str(self._extra.get("device") or ("cuda" if wants_quant else "cpu"))
        dtype_name = str(self._extra.get("dtype") or ("bfloat16" if wants_quant else "float32"))
        dtype = getattr(torch, dtype_name, None)
        if dtype is None:
            raise ProviderError(f"unknown local dtype {dtype_name!r}")
        attn = self._extra.get("attn_implementation") or "eager"
        local_only = bool(self._extra.get("local_files_only", False))
        trust = bool(self._extra.get("trust_remote_code", False))
        low_mem = bool(self._extra.get("low_cpu_mem_usage", True))
        revision = self._extra.get("revision") or self._extra.get("model_revision")

        config_kwargs: dict[str, Any] = {
            "token": self._token,
            "local_files_only": local_only,
            "trust_remote_code": trust,
        }
        if revision:
            config_kwargs["revision"] = str(revision)
        config = AutoConfig.from_pretrained(self.model_id, **config_kwargs)
        architecture = ""
        if getattr(config, "architectures", None):
            architecture = str(config.architectures[0])
        model_type = str(getattr(config, "model_type", "") or "")
        _bind_architecture_class(transformers, architecture, model_type)
        model_cls, loader_class = _resolve_model_class(
            transformers, AutoModelForCausalLM, architecture
        )

        logger.info(
            "loading local model %s device=%s dtype=%s attn=%s loader=%s",
            self.model_id,
            device,
            dtype_name,
            attn,
            loader_class,
        )
        load_kwargs: dict[str, Any] = {
            "token": self._token,
            "attn_implementation": str(attn),
            "low_cpu_mem_usage": low_mem,
            "local_files_only": local_only,
            "trust_remote_code": trust,
        }
        if revision:
            load_kwargs["revision"] = str(revision)
        quant = _bitsandbytes_config(self._extra)
        device_map = self._extra.get("device_map")
        if quant is not None:
            load_kwargs["quantization_config"] = quant
            load_kwargs["device_map"] = device_map if device_map is not None else "cuda"
        elif device_map is not None:
            load_kwargs["device_map"] = device_map
        # transformers 5 renamed torch_dtype -> dtype. The public signature is
        # **kwargs, so we cannot inspect the name; branch on the package version.
        major = int(str(transformers.__version__).split(".", 1)[0])
        if major >= 5:
            load_kwargs["dtype"] = dtype
        else:
            load_kwargs["torch_dtype"] = dtype
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
        started = perf_counter()
        try:
            model = model_cls.from_pretrained(self.model_id, **load_kwargs)
        except Exception as exc:
            raise ProviderError(
                f"could not load local model {self.model_id!r} "
                f"({architecture or 'unknown'} via {loader_class}): {exc}"
            ) from exc
        load_s = round(perf_counter() - started, 3)
        placed: Any = model
        if quant is None and device_map is None and device != "cpu":
            placed = placed.to(device)
        placed.eval()
        self._eos_ids = _eos_token_ids(placed.config)
        hf_revision = getattr(config, "_commit_hash", None) or (
            str(revision) if revision else None
        )
        mem = _cuda_mem()
        self.load_stats = {
            "architecture": architecture or model_type or "unknown",
            "loader_class": loader_class,
            "hf_revision": hf_revision,
            "quant_config": _quant_label(self._extra),
            "load_s": load_s,
            **mem,
        }
        self._model = placed
        self._emit(
            "local.model.loaded",
            model_id=self.model_id,
            mirror=(
                f"loaded {self.model_id} {architecture} via {loader_class} "
                f"rev={hf_revision} peak_vram_mib={mem.get('peak_vram_mib')} "
                f"in {load_s}s"
            ),
            **self.load_stats,
        )
        return placed

    def generate(
        self,
        input_ids: list[int],
        *,
        max_tokens: int,
        temperature: float,
        top_p: float,
        top_k: int | None,
        repetition_penalty: float | None,
        seed: int | None,
        extra: dict[str, Any],
    ) -> LocalGeneration:
        import torch

        model = self._load()
        device = next(model.parameters()).device
        if seed is not None:
            torch.manual_seed(int(seed))
        tensor = torch.tensor([input_ids], dtype=torch.long, device=device)
        attention_mask = torch.ones_like(tensor)
        do_sample = temperature > 1e-6
        eos_ids = self._eos_ids or _eos_token_ids(model.config)
        pad_id = _first_int(
            getattr(model.config, "pad_token_id", None),
            getattr(getattr(model.config, "text_config", None), "pad_token_id", None),
            next(iter(eos_ids), None),
        )
        kwargs: dict[str, Any] = {
            "input_ids": tensor,
            "attention_mask": attention_mask,
            "max_new_tokens": max_tokens,
            "do_sample": do_sample,
            "pad_token_id": pad_id,
            "eos_token_id": next(iter(eos_ids), None) if eos_ids else None,
            "use_cache": True,
        }
        if do_sample:
            kwargs["temperature"] = max(float(temperature), 1e-5)
            kwargs["top_p"] = float(top_p)
            if top_k is not None:
                kwargs["top_k"] = int(top_k)
        if repetition_penalty is not None:
            kwargs["repetition_penalty"] = float(repetition_penalty)
        # Loader knobs must not reach generate().
        extra_gen = {k: v for k, v in extra.items() if k not in _LOAD_KEYS}
        extra_gen.pop("stop", None)
        kwargs.update(extra_gen)

        started = perf_counter()
        with torch.inference_mode():
            output = self._generate_text_only(model, kwargs)
        decode_s = perf_counter() - started
        new_ids, finish = strip_eos(output[0, tensor.shape[1] :].tolist(), eos_ids)
        tok_s = round(len(new_ids) / decode_s, 3) if decode_s > 0 else 0.0
        extras = {
            **self.load_stats,
            "decode_s": round(decode_s, 4),
            "tok_s": tok_s,
            **_cuda_mem(),
        }
        return LocalGeneration(token_ids=new_ids, finish_reason=finish, extras=extras)

    def _generate_text_only(self, model: Any, kwargs: dict[str, Any]) -> Any:
        """Text-only ``generate``: never pass vision/audio tensors (ADR-0024).

        Wrapper ``generate`` is preferred so multimodal special-token handling
        stays intact. If the wrapper refuses a text-only call, retry on
        ``language_model`` when that submodule exists.
        """
        try:
            return model.generate(**kwargs)
        except Exception as exc:
            language = getattr(model, "language_model", None)
            if language is None or not _multimodal_generate_failed(exc):
                raise
            self._emit(
                "local.generate.text_only_fallback",
                model_id=self.model_id,
                architecture=self.load_stats.get("architecture"),
                error_type=type(exc).__name__,
                mirror=(
                    f"wrapper generate refused text-only inputs for {self.model_id}; "
                    "retrying on language_model"
                ),
            )
            return language.generate(**kwargs)


def _first_int(*values: Any) -> int | None:
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple)) and value:
            return int(value[0])
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _eos_token_ids(config: Any) -> set[int]:
    """Collect EOS ids from a causal or multimodal (text_config) HF config."""
    ids: set[int] = set()
    for value in (
        getattr(config, "eos_token_id", None),
        getattr(getattr(config, "text_config", None), "eos_token_id", None),
    ):
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            ids.update(int(x) for x in value if x is not None)
        else:
            ids.add(int(value))
    return ids


def strip_eos(token_ids: list[int], eos_ids: set[int]) -> tuple[list[int], str]:
    """Drop a leading-to-first EOS so decoded text does not contain ``<eos>``."""
    if not eos_ids or not token_ids:
        return token_ids, "length"
    for index, token in enumerate(token_ids):
        if token in eos_ids:
            return token_ids[:index], "stop"
    return token_ids, "length"


def _cached_body(entry: dict[str, Any]) -> dict[str, Any]:
    body = entry.get("body")
    if not isinstance(body, dict):
        raise ProviderError("cached local response is missing a JSON object body")
    return body


def _messages_to_text(messages: tuple[dict[str, str], ...] | None) -> str:
    """Flatten a chat into raw text. Base models do not get a chat template.

    Applying an instruct template here would re-introduce the confound this
    client exists to remove. Chat-mechanism arms still send ``messages``; we
    concatenate contents so the request is defined, and record that fact.
    """
    return "\n".join(m.get("content", "") for m in (messages or ()))


def _truncate_at_stop(text: str, stops: tuple[str, ...]) -> str:
    cut = len(text)
    for stop in stops:
        if not stop:
            continue
        index = text.find(stop)
        if index != -1:
            cut = min(cut, index)
    return text[:cut]


def _bitsandbytes_config(extra: dict[str, Any]) -> Any | None:
    """Build a BitsAndBytesConfig from loader extras, or None for full precision."""
    load_4 = bool(extra.get("load_in_4bit")) or str(extra.get("quantization", "")).lower() in {
        "nf4",
        "4bit",
    }
    load_8 = bool(extra.get("load_in_8bit")) or str(extra.get("quantization", "")).lower() in {
        "int8",
        "8bit",
    }
    if not load_4 and not load_8:
        return None
    try:
        import torch
        from transformers import BitsAndBytesConfig
    except ImportError as exc:
        raise ProviderError(
            "NF4/INT8 local load requires transformers + bitsandbytes "
            "(uv sync --extra local)"
        ) from exc
    if load_4 and load_8:
        raise ProviderError("load_in_4bit and load_in_8bit are mutually exclusive")
    if load_8:
        return BitsAndBytesConfig(load_in_8bit=True)
    compute_name = str(extra.get("bnb_4bit_compute_dtype") or "bfloat16")
    compute_dtype = getattr(torch, compute_name, None)
    if compute_dtype is None:
        raise ProviderError(f"unknown bnb_4bit_compute_dtype {compute_name!r}")
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=str(extra.get("bnb_4bit_quant_type") or "nf4"),
        bnb_4bit_use_double_quant=bool(extra.get("bnb_4bit_use_double_quant", True)),
        bnb_4bit_compute_dtype=compute_dtype,
    )
