"""Deterministic offline generator and embedder.

This is not a stub. It is a *known-ground-truth* fixture: text is produced by a
hidden Markov chain over topics whose transition matrix is deliberately
non-reversible, so the full pipeline — sliding window, chunking, embedding,
geometry, MSM estimation, probability currents — can be validated end to end
against an answer we already know, with no network and no cost.

Two properties make it a useful test of the real thing:

* the next topic depends on the *tail of the prompt*, so a sliding window
  genuinely changes the dynamics rather than being decorative;
* the topic chain has non-zero probability currents by construction, so an
  analysis that reports ``J = 0`` on mock data is broken.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from ..ledger import Usage
from .base import (
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    InferenceClient,
)

TOPICS: dict[str, tuple[str, ...]] = {
    "physics": (
        "quantum",
        "entropy",
        "momentum",
        "lattice",
        "photon",
        "gauge",
        "boson",
        "renormalisation",
        "hamiltonian",
        "spin",
        "vacuum",
        "symmetry",
    ),
    "finance": (
        "liquidity",
        "arbitrage",
        "yield",
        "collateral",
        "hedge",
        "spread",
        "volatility",
        "settlement",
        "notional",
        "counterparty",
        "coupon",
        "basis",
    ),
    "biology": (
        "ribosome",
        "allele",
        "mitochondrion",
        "phenotype",
        "enzyme",
        "cortex",
        "synapse",
        "genome",
        "membrane",
        "protein",
        "lineage",
        "vesicle",
    ),
    "narrative": (
        "morning",
        "harbour",
        "letter",
        "stranger",
        "footsteps",
        "window",
        "silence",
        "remembered",
        "candle",
        "corridor",
        "promise",
        "departure",
    ),
    "meta": (
        "however",
        "therefore",
        "arguably",
        "conclusion",
        "framework",
        "notion",
        "discussion",
        "consider",
        "premise",
        "accordingly",
        "namely",
        "insofar",
    ),
}

TOPIC_NAMES: tuple[str, ...] = tuple(TOPICS)

#: Row-stochastic, deliberately asymmetric: physics -> meta -> narrative -> ...
#: The forward cycle is much likelier than the reverse, so `J_ij != 0` is the
#: ground truth an irreversibility estimator must recover.
TRANSITION_MATRIX: np.ndarray = np.array(
    [
        [0.82, 0.04, 0.02, 0.02, 0.10],
        [0.02, 0.84, 0.04, 0.02, 0.08],
        [0.02, 0.02, 0.85, 0.05, 0.06],
        [0.03, 0.02, 0.02, 0.86, 0.07],
        [0.09, 0.06, 0.05, 0.06, 0.74],
    ],
    dtype=np.float64,
)

_MOCK_EMBED_DIM = 96
_TAIL_WORDS = 400
_PRICE_USD_PER_TOKEN = 0.0


def _stable_seed(*parts: Any) -> int:
    digest = hashlib.sha256("\u241f".join(str(p) for p in parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _infer_topic(text: str) -> int:
    """Read the current topic off the tail of the prompt.

    Ties (including an empty prompt) resolve to index 0 deterministically, which
    keeps the fixture reproducible.
    """
    words = text.lower().split()[-_TAIL_WORDS:]
    if not words:
        return 0
    counts = np.zeros(len(TOPIC_NAMES), dtype=np.int64)
    lookup = {word: idx for idx, name in enumerate(TOPIC_NAMES) for word in TOPICS[name]}
    for word in words:
        stripped = word.strip(".,;:!?()[]\"'")
        if (idx := lookup.get(stripped)) is not None:
            counts[idx] += 1
    return int(counts.argmax())


@dataclass(frozen=True, slots=True)
class MockConfig:
    words_per_token: float = 1.0
    noise_fraction: float = 0.12
    sentence_length: int = 14


class MockClient(InferenceClient):
    """Offline generator/embedder used by CI, tests and ``--dry-run`` workflows."""

    name = "mock"

    def __init__(self, config: MockConfig | None = None) -> None:
        self.config = config or MockConfig()

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        source = (
            request.prompt if request.prompt is not None else _messages_to_text(request.messages)
        )
        rng = np.random.default_rng(
            _stable_seed(request.model_id, request.seed, request.temperature, source[-2000:])
        )
        topic = _infer_topic(source)
        # Temperature widens the transition distribution: at T=0 the chain sticks,
        # at high T it mixes. Mirrors the effect we expect to measure for real.
        row = _tempered(TRANSITION_MATRIX[topic], request.temperature)
        topic = int(rng.choice(len(TOPIC_NAMES), p=row))

        n_words = max(1, int(request.max_tokens * self.config.words_per_token))
        words: list[str] = []
        vocabulary = TOPICS[TOPIC_NAMES[topic]]
        others = [w for name in TOPIC_NAMES if name != TOPIC_NAMES[topic] for w in TOPICS[name]]
        for index in range(n_words):
            pool = others if rng.random() < self.config.noise_fraction else vocabulary
            word = str(pool[int(rng.integers(len(pool)))])
            if index % self.config.sentence_length == 0:
                word = word.capitalize()
            words.append(word)
            if index % self.config.sentence_length == self.config.sentence_length - 1:
                words[-1] = words[-1] + "."
        text = " " + " ".join(words)

        prompt_tokens = max(1, len(source.split()))
        return CompletionResponse(
            text=text,
            finish_reason="length",
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=n_words,
                cost_usd=_PRICE_USD_PER_TOKEN,
                from_cache=False,
            ),
            served_provider=request.provider_slug or "mock",
            model_returned=request.model_id,
            latency_s=0.0,
            attempts=1,
            from_cache=False,
            raw={"mock": True, "topic": TOPIC_NAMES[topic], "topic_index": topic},
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        vectors = tuple(tuple(float(x) for x in _hash_embed(text)) for text in request.inputs)
        return EmbeddingResponse(
            vectors=vectors,
            usage=Usage(
                prompt_tokens=sum(len(t.split()) for t in request.inputs),
                completion_tokens=0,
                cost_usd=0.0,
                from_cache=False,
            ),
            model_returned=request.model_id,
            latency_s=0.0,
            from_cache=False,
            raw={"mock": True},
        )

    async def list_models(self) -> list[dict[str, Any]]:
        return [{"id": "mock/hmm-5topic", "pricing": {"prompt": 0.0, "completion": 0.0}}]

    async def list_endpoints(self, model_id: str) -> list[dict[str, Any]]:
        return [
            {
                "model_id": model_id,
                "tag": "mock",
                "provider_name": "Mock",
                "country": "zz",
                "context_length": 1_000_000,
                "quantization": "none",
                "max_completion_tokens": 8192,
                "supported_parameters": ["max_tokens", "temperature", "top_p", "seed", "logprobs"],
                "supported_apis": ["chat", "completions", "embeddings"],
                "status": 0,
                "pricing": {"prompt": 0.0, "completion": 0.0},
            }
        ]


def _messages_to_text(messages: tuple[dict[str, str], ...] | None) -> str:
    return "\n".join(m.get("content", "") for m in (messages or ()))


def _tempered(row: np.ndarray, temperature: float) -> np.ndarray:
    """Flatten a transition row as temperature rises; sharpen it as T -> 0."""
    if temperature <= 1e-6:
        out = np.zeros_like(row)
        out[int(row.argmax())] = 1.0
        return out
    logits = np.log(np.clip(row, 1e-12, None)) / max(temperature, 1e-6)
    logits -= logits.max()
    weights = np.exp(logits)
    return weights / weights.sum()


def _hash_embed(text: str, dim: int = _MOCK_EMBED_DIM) -> np.ndarray:
    """Hashing bag-of-words embedding, L2-normalised.

    Topic-specific vocabularies therefore land in topic-specific directions, so
    downstream clustering has real structure to find rather than noise.
    """
    vector = np.zeros(dim, dtype=np.float64)
    for word in text.lower().split():
        stripped = word.strip(".,;:!?()[]\"'")
        if not stripped:
            continue
        digest = hashlib.blake2b(stripped.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(float(vector @ vector))
    return vector / norm if norm > 0 else vector
