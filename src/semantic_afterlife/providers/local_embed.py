"""Local embedding backends for Paper B (BGE-M3, Qwen3-Embedding).

CI stays torch-free: tests inject a ``LocalEmbedBackend``. Production loads
sentence-transformers / transformers only inside ``_load``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np

from ..errors import ProviderError
from ..ledger import Usage
from ..logging_utils import get_logger
from .base import EmbeddingRequest, EmbeddingResponse, InferenceClient

logger = get_logger("providers.local_embed")


class LocalEmbedBackend(Protocol):
    def embed(self, texts: list[str]) -> np.ndarray: ...


@dataclass
class ScriptedEmbedBackend:
    """Deterministic vectors for tests (hashing bag-of-words style)."""

    dim: int = 32

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            rng = np.random.default_rng(abs(hash(text)) % (2**32))
            vec = rng.normal(size=self.dim).astype(np.float32)
            n = float(np.linalg.norm(vec))
            out[i] = vec / n if n > 0 else vec
        return out


class SentenceTransformersBackend:
    """Lazy sentence-transformers wrapper (BGE-M3 and friends)."""

    def __init__(self, model_id: str, *, device: str = "cpu", trust_remote_code: bool = False) -> None:
        self.model_id = model_id
        self.device = device
        self.trust_remote_code = trust_remote_code
        self._model: Any = None

    def _load(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ProviderError(
                "local embeddings require sentence-transformers "
                "(uv sync --extra local)"
            ) from exc
        logger.info("loading local embedder %s device=%s", self.model_id, self.device)
        self._model = SentenceTransformer(
            self.model_id,
            device=self.device,
            trust_remote_code=self.trust_remote_code or "qwen" in self.model_id.lower(),
        )
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        model = self._load()
        vectors = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return np.asarray(vectors, dtype=np.float32)

    def unload(self) -> None:
        self._model = None


class LocalEmbedClient(InferenceClient):
    """Local-only embedding client; completions are refused."""

    name = "local_embed"

    def __init__(
        self,
        *,
        backend: LocalEmbedBackend | None = None,
        model_id: str | None = None,
        device: str = "cpu",
    ) -> None:
        self._backend = backend
        self._model_id = model_id
        self._device = device
        self._resolved: dict[str, LocalEmbedBackend] = {}

    async def complete(self, _request: Any) -> Any:
        raise ProviderError("local_embed client does not serve completions")

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        backend = self._resolve(request.model_id)
        matrix = backend.embed(list(request.inputs))
        as_tuples = tuple(tuple(float(x) for x in row) for row in matrix)
        return EmbeddingResponse(
            vectors=as_tuples,
            usage=Usage(
                prompt_tokens=0,
                completion_tokens=0,
                cost_usd=0.0,
                from_cache=False,
            ),
            model_returned=request.model_id,
            latency_s=0.0,
            from_cache=False,
            raw={"n": len(as_tuples), "dim": int(matrix.shape[1]) if len(matrix) else 0},
        )

    def _resolve(self, model_id: str) -> LocalEmbedBackend:
        if self._backend is not None:
            return self._backend
        cached = self._resolved.get(model_id)
        if cached is not None:
            return cached
        # ADR-0024: one local CUDA model at a time.
        for mid, previous in list(self._resolved.items()):
            unload = getattr(previous, "unload", None)
            if callable(unload):
                unload()
            del self._resolved[mid]
        backend: LocalEmbedBackend = SentenceTransformersBackend(
            model_id,
            device=self._device,
            trust_remote_code="qwen" in model_id.lower(),
        )
        self._resolved[model_id] = backend
        return backend

    async def unload(self, model_id: str | None = None) -> None:
        targets = list(self._resolved) if model_id is None else [model_id]
        for mid in targets:
            backend = self._resolved.pop(mid, None)
            unload = getattr(backend, "unload", None)
            if callable(unload):
                unload()
        try:
            import torch
        except ImportError:
            return
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    async def aclose(self) -> None:
        await self.unload(None)

    async def list_models(self) -> list[dict[str, Any]]:
        return [
            {"id": "BAAI/bge-m3", "name": "BGE-M3 (local)"},
            {"id": "Qwen/Qwen3-Embedding-8B", "name": "Qwen3-Embedding-8B (local)"},
        ]
