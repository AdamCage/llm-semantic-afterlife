"""Stage 0 capability audits.

Every function here answers a question that documentation cannot: what this
provider actually does, today, for these models. Their outputs are Stage 0's
scientific deliverable — not because the facts are interesting in themselves,
but because the design of every later stage depends on them, and guessing would
propagate silently into the paper.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, replace
from typing import Any

import pandas as pd

from .config import EmbeddingConfig, GeneratorConfig, Settings
from .errors import AfterlifeError, TokenizerError
from .generation.trajectory import build_request
from .ledger import Ledger
from .logging_utils import EventLogger, get_logger
from .providers import EmbeddingRequest, InferenceClient
from .tokenization import describe, load_tokenizer

logger = get_logger("audits")

#: Short, continuation-shaped probe. Deliberately not a question: a question
#: measures instruction-following, which is a different behaviour from free
#: continuation.
PROBE_TEXT = (
    "The measurement had been repeated four times before anyone noticed that the "
    "calibration drift was not random but followed the ambient temperature almost "
    "exactly, which meant that"
)


# ---------------------------------------------------------------------------
# S0.2 — provider capability audit
# ---------------------------------------------------------------------------


async def audit_providers(
    client: InferenceClient,
    generators: list[GeneratorConfig],
    *,
    usd_per_rub: float,
    events: EventLogger,
) -> pd.DataFrame:
    """Per-endpoint capabilities and prices for every candidate generator.

    A model absent from the router yields a row with ``available=False`` rather
    than an exception: "not available" is a normal audit finding that the stage
    report has to state.
    """
    rows: list[dict[str, Any]] = []
    for generator in generators:
        try:
            endpoints = await client.list_endpoints(generator.model_id)
        except AfterlifeError as exc:
            events.event(
                "audit.providers.error",
                level="WARNING",
                generator=generator.slug,
                model_id=generator.model_id,
                error=str(exc),
            )
            rows.append(
                {
                    "generator": generator.slug,
                    "model_id": generator.model_id,
                    "available": False,
                    "error": str(exc),
                }
            )
            continue

        if not endpoints:
            rows.append(
                {
                    "generator": generator.slug,
                    "model_id": generator.model_id,
                    "available": False,
                    "error": "no endpoints returned",
                }
            )
            events.event(
                "audit.providers.unavailable",
                level="WARNING",
                generator=generator.slug,
                model_id=generator.model_id,
                mirror=f"{generator.model_id}: not available on {client.name}",
            )
            continue

        for endpoint in endpoints:
            pricing = endpoint.get("pricing") or {}
            input_rub = _as_float(pricing.get("prompt") or pricing.get("input"))
            output_rub = _as_float(pricing.get("completion") or pricing.get("output"))
            supported_apis = endpoint.get("supported_apis") or []
            supported_params = endpoint.get("supported_parameters") or []
            rows.append(
                {
                    "generator": generator.slug,
                    "model_id": generator.model_id,
                    "available": True,
                    "provider_tag": endpoint.get("tag"),
                    "provider_name": endpoint.get("provider_name") or endpoint.get("name"),
                    "country": endpoint.get("country"),
                    "quantization": endpoint.get("quantization"),
                    "context_length": endpoint.get("context_length"),
                    "max_completion_tokens": endpoint.get("max_completion_tokens"),
                    "max_prompt_tokens": endpoint.get("max_prompt_tokens"),
                    "status": endpoint.get("status"),
                    "supports_completions": "completions" in supported_apis,
                    "supports_chat": "chat" in supported_apis,
                    "supports_seed": "seed" in supported_params,
                    "supports_logprobs": "logprobs" in supported_params,
                    "supported_apis": ",".join(map(str, supported_apis)),
                    "supported_parameters": ",".join(map(str, supported_params)),
                    "price_rub_per_m_input": None if input_rub is None else input_rub * 1e6,
                    "price_rub_per_m_output": None if output_rub is None else output_rub * 1e6,
                    "price_usd_per_m_input": None
                    if input_rub is None
                    else input_rub * 1e6 * usd_per_rub,
                    "price_usd_per_m_output": None
                    if output_rub is None
                    else output_rub * 1e6 * usd_per_rub,
                    "error": None,
                }
            )
        events.event(
            "audit.providers.model",
            generator=generator.slug,
            model_id=generator.model_id,
            n_endpoints=len(endpoints),
            mirror=f"{generator.model_id}: {len(endpoints)} endpoint(s)",
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# S0.3 — continuation-mechanism audit
# ---------------------------------------------------------------------------

_MECHANISMS: tuple[str, ...] = ("raw_completion", "assistant_prefill", "chat_instructed")


@dataclass(slots=True)
class ContinuationProbe:
    generator: str
    mechanism: str
    ok: bool
    n_chars: int
    finish_reason: str | None
    completion_tokens: int
    prompt_tokens_api: int
    prompt_tokens_local: int | None
    served_provider: str | None
    latency_s: float
    cost_usd: float
    looks_like_meta: bool
    sample: str
    error: str | None


#: Openings that mean the model is talking *about* the text rather than continuing it.
_META_MARKERS = (
    "as an ai",
    "i cannot",
    "i can't",
    "sure!",
    "certainly",
    "here is",
    "here's",
    "this text",
    "the passage",
    "the text describes",
    "it seems",
    "summary:",
    "continuation:",
)


async def audit_continuation(
    client: InferenceClient,
    generators: list[GeneratorConfig],
    *,
    settings: Settings,
    events: EventLogger,
    ledger: Ledger,
    max_tokens: int = 160,
) -> pd.DataFrame:
    """Which continuation mechanisms actually work, per model.

    All three mechanisms are attempted for every model regardless of its
    configured default, because the point is to discover what is possible rather
    than to confirm what we assumed.
    """
    from .config import SamplingConfig

    sampling = SamplingConfig(temperature=0.7, top_p=1.0)
    probes: list[ContinuationProbe] = []

    for generator in generators:
        local_tokens: int | None = None
        try:
            tokenizer = load_tokenizer(
                generator.tokenizer_repo,
                generator.tokenizer_revision,
                str(settings.paths.tokenizer_cache),
            )
            local_tokens = tokenizer.count(PROBE_TEXT)
        except TokenizerError as exc:
            events.event(
                "audit.continuation.tokenizer_unavailable",
                level="WARNING",
                generator=generator.slug,
                error=str(exc),
            )

        for mechanism in _MECHANISMS:
            variant = generator.model_copy(
                update={
                    "continuation": mechanism,
                    "continuation_instruction": generator.continuation_instruction
                    or "Continue the following text directly. Output only the continuation.",
                }
            )
            request = build_request(
                variant, sampling, prompt=PROBE_TEXT, max_tokens=max_tokens, seed=12345
            )
            try:
                ledger.reserve(0.01, what=f"continuation probe {generator.slug}/{mechanism}")
                response = await client.complete(request)
            except AfterlifeError as exc:
                probes.append(
                    ContinuationProbe(
                        generator=generator.slug,
                        mechanism=mechanism,
                        ok=False,
                        n_chars=0,
                        finish_reason=None,
                        completion_tokens=0,
                        prompt_tokens_api=0,
                        prompt_tokens_local=local_tokens,
                        served_provider=None,
                        latency_s=0.0,
                        cost_usd=0.0,
                        looks_like_meta=False,
                        sample="",
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                events.event(
                    "audit.continuation.failed",
                    level="WARNING",
                    generator=generator.slug,
                    mechanism=mechanism,
                    error=str(exc),
                    mirror=f"{generator.slug}/{mechanism}: {type(exc).__name__}",
                )
                continue

            ledger.record(
                response.usage,
                kind="audit.continuation",
                generator=generator.slug,
                mechanism=mechanism,
            )
            text = response.text
            head = text.strip().lower()[:120]
            probes.append(
                ContinuationProbe(
                    generator=generator.slug,
                    mechanism=mechanism,
                    ok=bool(text.strip()),
                    n_chars=len(text),
                    finish_reason=response.finish_reason,
                    completion_tokens=response.usage.completion_tokens,
                    prompt_tokens_api=response.usage.prompt_tokens,
                    prompt_tokens_local=local_tokens,
                    served_provider=response.served_provider,
                    latency_s=response.latency_s,
                    cost_usd=response.usage.cost_usd,
                    looks_like_meta=any(marker in head for marker in _META_MARKERS),
                    sample=text[:600],
                    error=None,
                )
            )
            events.event(
                "audit.continuation.ok",
                generator=generator.slug,
                mechanism=mechanism,
                completion_tokens=response.usage.completion_tokens,
                finish_reason=response.finish_reason,
                prompt_tokens_api=response.usage.prompt_tokens,
                prompt_tokens_local=local_tokens,
                served_provider=response.served_provider,
                mirror=f"{generator.slug}/{mechanism}: {response.usage.completion_tokens} tokens, "
                f"finish={response.finish_reason}",
            )

    frame = pd.DataFrame([p.__dict__ for p in probes])
    if not frame.empty:
        # A large gap between our token count and the provider's is the signature
        # of a chat template being added server-side; it is a protocol fact, not noise.
        frame["prompt_token_delta"] = frame["prompt_tokens_api"] - frame["prompt_tokens_local"]
    return frame


# ---------------------------------------------------------------------------
# S0.4 — determinism audit
# ---------------------------------------------------------------------------


async def audit_determinism(
    client: InferenceClient,
    generators: list[GeneratorConfig],
    *,
    events: EventLogger,
    ledger: Ledger,
    n_repeats: int = 5,
    max_tokens: int = 128,
    temperature: float = 0.7,
) -> pd.DataFrame:
    """Measured reproducibility of identical seeded requests.

    We never assert that an LLM API is deterministic. We measure the rate and
    report it, because the reproducibility level the paper may claim depends on
    this number and on nothing else.
    """
    from .config import SamplingConfig

    sampling = SamplingConfig(temperature=temperature, top_p=1.0)
    rows: list[dict[str, Any]] = []

    for generator in generators:
        request = build_request(
            generator, sampling, prompt=PROBE_TEXT, max_tokens=max_tokens, seed=987_654
        )
        outputs: list[str] = []
        providers: set[str] = set()
        errors: list[str] = []
        for repeat in range(n_repeats):
            try:
                ledger.reserve(0.01, what=f"determinism probe {generator.slug}")
                # `cache_bust` gives each repeat its own cache entry without
                # changing the payload: a cache hit would report perfect
                # determinism, which is exactly the thing under test.
                response = await client.complete(replace(request, cache_bust=repeat))
            except AfterlifeError as exc:
                errors.append(f"{type(exc).__name__}: {exc}")
                continue
            ledger.record(response.usage, kind="audit.determinism", generator=generator.slug)
            outputs.append(response.text)
            if response.served_provider:
                providers.add(response.served_provider)

        if not outputs:
            rows.append(
                {
                    "generator": generator.slug,
                    "n_attempts": n_repeats,
                    "n_responses": 0,
                    "exact_match_rate": float("nan"),
                    "mean_similarity": float("nan"),
                    "errors": "; ".join(errors[:3]),
                }
            )
            continue

        reference = outputs[0]
        exact = sum(1 for text in outputs if text == reference) / len(outputs)
        # autojunk=False is essential: difflib's default heuristic treats characters
        # appearing in more than 1% of a sequence longer than 200 elements as junk,
        # which on natural-language text collapses the similarity of two nearly
        # identical outputs to near zero.
        similarities = [
            difflib.SequenceMatcher(None, reference, text, autojunk=False).ratio()
            for text in outputs[1:]
        ]
        rows.append(
            {
                "generator": generator.slug,
                "n_attempts": n_repeats,
                "n_responses": len(outputs),
                "exact_match_rate": exact,
                "mean_similarity": float(sum(similarities) / len(similarities))
                if similarities
                else 1.0,
                "min_similarity": float(min(similarities)) if similarities else 1.0,
                "distinct_outputs": len(set(outputs)),
                "served_providers": ",".join(sorted(providers)),
                "errors": "; ".join(errors[:3]) or None,
            }
        )
        events.event(
            "audit.determinism.completed",
            generator=generator.slug,
            exact_match_rate=exact,
            distinct_outputs=len(set(outputs)),
            mirror=f"{generator.slug}: exact-match {exact:.0%} over {len(outputs)} repeats, "
            f"{len(set(outputs))} distinct outputs",
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# S0.5 — embedding audit
# ---------------------------------------------------------------------------

_EMBED_PROBES = (
    "Lattice gauge configurations are generated with a Markov chain whose autocorrelation time matters.",
    "The repo rate printed above the corridor twice, so financing the position stopped being an arbitrage.",
    "She left the letter unopened on the windowsill for two days, which he took as an answer.",
)


async def audit_embeddings(
    client: InferenceClient,
    embeddings: list[EmbeddingConfig],
    *,
    events: EventLogger,
    ledger: Ledger,
) -> pd.DataFrame:
    """Dimension, normalisation, latency and cost per representation space.

    Also records whether the three probe texts — drawn from three different
    domains — are actually separated in the space, which is the minimum a
    representation must do for anything downstream to be meaningful.
    """
    import numpy as np

    rows: list[dict[str, Any]] = []
    for config in embeddings:
        try:
            ledger.reserve(0.02, what=f"embedding probe {config.slug}")
            response = await client.embed(
                EmbeddingRequest(model_id=config.model_id, inputs=_EMBED_PROBES)
            )
        except AfterlifeError as exc:
            rows.append(
                {
                    "embedding": config.slug,
                    "model_id": config.model_id,
                    "available": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            events.event(
                "audit.embeddings.failed",
                level="WARNING",
                embedding=config.slug,
                error=str(exc),
                mirror=f"{config.slug}: {type(exc).__name__}",
            )
            continue

        ledger.record(response.usage, kind="audit.embedding", embedding=config.slug)
        matrix = np.asarray(response.vectors, dtype=np.float64)
        norms = np.linalg.norm(matrix, axis=1)
        normalised = matrix / np.where(norms > 0, norms, 1.0)[:, None]
        cross = normalised @ normalised.T
        off_diagonal = cross[~np.eye(cross.shape[0], dtype=bool)]

        rows.append(
            {
                "embedding": config.slug,
                "model_id": config.model_id,
                "architecture": config.architecture,
                "available": True,
                "dim": int(matrix.shape[1]),
                "expected_dim": config.expected_dim,
                "dim_matches_expected": config.expected_dim is None
                or int(matrix.shape[1]) == config.expected_dim,
                "provider_normalised": bool(abs(float(norms.mean()) - 1.0) < 1e-3),
                "mean_norm": float(norms.mean()),
                "max_cross_domain_cosine": float(off_diagonal.max()),
                "mean_cross_domain_cosine": float(off_diagonal.mean()),
                "prompt_tokens": response.usage.prompt_tokens,
                "latency_s": round(response.latency_s, 3),
                "cost_usd": round(response.usage.cost_usd, 8),
                "error": None,
            }
        )
        events.event(
            "audit.embeddings.ok",
            embedding=config.slug,
            dim=int(matrix.shape[1]),
            provider_normalised=bool(abs(float(norms.mean()) - 1.0) < 1e-3),
            mean_cross_domain_cosine=float(off_diagonal.mean()),
            mirror=f"{config.slug}: dim={matrix.shape[1]}, mean |z|={norms.mean():.4f}, "
            f"cross-domain cos={off_diagonal.mean():.3f}",
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# S0.6 — tokenizer audit
# ---------------------------------------------------------------------------

_ROUNDTRIP_PROBES = (
    PROBE_TEXT,
    "Ünïcödé — “quotes”, emoji 🜁, math ∫₀^∞ e^{-x²}dx, CJK 漢字, Cyrillic текст.",
    "   leading and trailing whitespace   \n\ttabs\tand\nnewlines\n\n",
    "a" * 4096,
)


def audit_tokenizers(
    generators: list[GeneratorConfig], *, settings: Settings, events: EventLogger
) -> pd.DataFrame:
    """Round-trip integrity and vocabulary identity for every generator tokenizer.

    A failed round trip means the window boundary is not where the manifest
    claims, which invalidates ``W`` for that model — so this is a gate, not a
    diagnostic.
    """
    rows: list[dict[str, Any]] = []
    for generator in generators:
        try:
            tokenizer = load_tokenizer(
                generator.tokenizer_repo,
                generator.tokenizer_revision,
                str(settings.paths.tokenizer_cache),
            )
        except TokenizerError as exc:
            rows.append(
                {
                    "generator": generator.slug,
                    "tokenizer_repo": generator.tokenizer_repo,
                    "loaded": False,
                    "error": str(exc),
                }
            )
            events.event(
                "audit.tokenizer.failed",
                level="WARNING",
                generator=generator.slug,
                repo=generator.tokenizer_repo,
                error=str(exc),
                mirror=f"{generator.slug}: tokenizer unavailable ({exc})",
            )
            continue

        results = {probe: tokenizer.roundtrip_ok(probe) for probe in _ROUNDTRIP_PROBES}
        # The tail operation is what the window actually uses, so it is checked
        # separately from a plain encode/decode round trip.
        tail_text, tail_tokens = tokenizer.tail(PROBE_TEXT * 20, 128)
        info = describe(tokenizer)
        rows.append(
            {
                "generator": generator.slug,
                "tokenizer_repo": generator.tokenizer_repo,
                "loaded": True,
                "type": info["type"],
                "vocab_size": info["vocab_size"],
                "fingerprint": info["fingerprint"],
                "roundtrip_all_ok": all(results.values()),
                "n_roundtrip_probes": len(results),
                "n_roundtrip_failures": sum(1 for ok in results.values() if not ok),
                "tail_exact": tail_tokens == 128,
                "probe_tokens": tokenizer.count(PROBE_TEXT),
                "tail_chars": len(tail_text),
                "error": None,
            }
        )
        events.event(
            "audit.tokenizer.ok",
            generator=generator.slug,
            repo=generator.tokenizer_repo,
            vocab_size=info["vocab_size"],
            roundtrip_all_ok=all(results.values()),
            mirror=f"{generator.slug}: vocab={info['vocab_size']}, "
            f"roundtrip={'ok' if all(results.values()) else 'FAILED'}",
        )
    return pd.DataFrame(rows)


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
