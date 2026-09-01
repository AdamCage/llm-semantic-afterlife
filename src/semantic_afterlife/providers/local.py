"""Local Hugging Face transformers client (ADR-0011).

Routers still host no true base models (re-measured 2026-09-01). This client
runs a local checkpoint through the same ``InferenceClient`` surface as
RouterAI / OpenRouter so the sliding-window engine, cache, ledger and replay
path do not fork.

Weights live on disk; generation costs $0. Embeddings are *not* implemented
here — representation models stay on the existing embedding providers so a
local generator can still be read in BGE-M3 / Qwen3-Embedding.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Protocol

from ..config import ExecutionMode, Settings
from ..errors import ProviderError
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
    }
)

_PATH = "/local/completions"


@dataclass(frozen=True, slots=True)
class LocalGeneration:
    """Token ids produced by a backend, already stripped of a trailing EOS."""

    token_ids: list[int]
    finish_reason: str


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
                extra=dict(request.extra),
            )
        latency = perf_counter() - start
        token_ids = list(generation.token_ids[: request.max_tokens])
        text = tokenizer.decode(token_ids)
        if request.stop:
            text = _truncate_at_stop(text, request.stop)
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
            "local": {
                "device": request.extra.get("device", "cpu"),
                "dtype": request.extra.get("dtype"),
                "n_input_ids": len(input_ids),
                "n_output_ids": len(token_ids),
            },
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
        backend = TransformersBackend(
            model_id=request.model_id,
            token=self._settings.hf_token,
            extra=extra,
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
        raise ProviderError(
            f"local embeddings are not implemented ({request.model_id}). "
            "A local *generator* still uses the existing embedding providers "
            "(BGE-M3 / Qwen3-Embedding) so representation space stays comparable."
        )

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

    async def aclose(self) -> None:
        self._resolved.clear()


class TransformersBackend:
    """Lazy ``AutoModelForCausalLM`` wrapper. Imports torch only on first use."""

    def __init__(self, *, model_id: str, token: str | None, extra: dict[str, Any]) -> None:
        self.model_id = model_id
        self._token = token
        self._extra = dict(extra)
        self._model: Any = None
        self._eos_ids: set[int] = set()

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

        device = str(self._extra.get("device") or "cpu")
        dtype_name = str(self._extra.get("dtype") or "float32")
        dtype = getattr(torch, dtype_name, None)
        if dtype is None:
            raise ProviderError(f"unknown local dtype {dtype_name!r}")
        attn = self._extra.get("attn_implementation") or "eager"
        local_only = bool(self._extra.get("local_files_only", False))
        trust = bool(self._extra.get("trust_remote_code", False))
        low_mem = bool(self._extra.get("low_cpu_mem_usage", True))

        config = AutoConfig.from_pretrained(
            self.model_id, token=self._token, local_files_only=local_only, trust_remote_code=trust
        )
        architecture = ""
        if getattr(config, "architectures", None):
            architecture = str(config.architectures[0])
        if "ConditionalGeneration" in architecture or getattr(config, "model_type", "") == "gemma4":
            # Gemma 4 E2B ships as a multimodal conditional-generation checkpoint.
            # Try the causal-LM auto class first (text weights); fall through
            # with a precise error if this transformers build cannot load it.
            logger.warning(
                "loading %s (architecture %s) via AutoModelForCausalLM; "
                "multimodal Gemma 4 may need a newer transformers",
                self.model_id,
                architecture,
            )

        logger.info(
            "loading local model %s device=%s dtype=%s attn=%s",
            self.model_id,
            device,
            dtype_name,
            attn,
        )
        load_kwargs: dict[str, Any] = {
            "token": self._token,
            "attn_implementation": str(attn),
            "low_cpu_mem_usage": low_mem,
            "local_files_only": local_only,
            "trust_remote_code": trust,
        }
        # transformers 5 renamed torch_dtype -> dtype. The public signature is
        # **kwargs, so we cannot inspect the name; branch on the package version.
        major = int(str(transformers.__version__).split(".", 1)[0])
        if major >= 5:
            load_kwargs["dtype"] = dtype
        else:
            load_kwargs["torch_dtype"] = dtype
        try:
            model = AutoModelForCausalLM.from_pretrained(self.model_id, **load_kwargs)
        except Exception as exc:
            raise ProviderError(
                f"could not load local model {self.model_id!r} ({architecture or 'unknown'}): {exc}"
            ) from exc
        placed: Any = model
        if device != "cpu":
            placed = placed.to(device)
        placed.eval()
        self._eos_ids = _eos_token_ids(placed.config)
        self._model = placed
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
        do_sample = temperature > 1e-6
        eos_ids = self._eos_ids or _eos_token_ids(model.config)
        pad_id = _first_int(
            getattr(model.config, "pad_token_id", None),
            getattr(getattr(model.config, "text_config", None), "pad_token_id", None),
            next(iter(eos_ids), None),
        )
        kwargs: dict[str, Any] = {
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

        with torch.inference_mode():
            output = model.generate(tensor, **kwargs)
        new_ids, finish = strip_eos(output[0, tensor.shape[1] :].tolist(), eos_ids)
        return LocalGeneration(token_ids=new_ids, finish_reason=finish)


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
