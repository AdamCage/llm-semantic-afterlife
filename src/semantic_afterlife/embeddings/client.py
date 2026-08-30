"""Embedding computation with a content-addressed cache.

Embeddings are pure functions of ``(model_id, text)``, so they are cached by
``sha256(model_id ‖ text)`` and never recomputed. That matters practically:
re-analysing a 200-trajectory stage under a different chunk size or a different
estimator would otherwise re-pay the entire embedding bill each time.

Vectors are stored as ``float32`` (storage) and used as ``float64`` for
statistics. An explicitly L2-normalised copy is always produced, regardless of
whether the provider normalises, so that cosine and Euclidean geometry are
unambiguous downstream (methodology.md §2).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..config import EmbeddingConfig
from ..costs import estimate_embedding_usd
from ..errors import ProviderError
from ..hashing import sha256_text
from ..ledger import Ledger
from ..logging_utils import EventLogger, get_logger
from ..providers import EmbeddingRequest, InferenceClient

logger = get_logger("embeddings")


def l2_normalise(matrix: np.ndarray) -> np.ndarray:
    """Row-wise L2 normalisation. Zero rows are left untouched rather than NaN."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    safe = np.where(norms > 0, norms, 1.0)
    return (matrix / safe).astype(matrix.dtype, copy=False)


class EmbeddingCache:
    """Sharded ``.npy`` store keyed by content hash."""

    def __init__(self, root: Path, model_id: str) -> None:
        self.root = root / sha256_text(model_id)[:16]
        self.root.mkdir(parents=True, exist_ok=True)
        self.model_id = model_id
        self.hits = 0
        self.misses = 0

    def _path(self, text: str) -> Path:
        key = sha256_text(f"{self.model_id}\n{text}")
        return self.root / key[:2] / f"{key}.npy"

    def get(self, text: str) -> np.ndarray | None:
        path = self._path(text)
        if not path.is_file():
            self.misses += 1
            return None
        self.hits += 1
        return np.load(path)

    def put(self, text: str, vector: np.ndarray) -> None:
        path = self._path(text)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, vector.astype(np.float32, copy=False))

    def stats(self) -> dict[str, int]:
        return {"hits": self.hits, "misses": self.misses}


class Embedder:
    """Batched, cached embedding for one representation space."""

    def __init__(
        self,
        config: EmbeddingConfig,
        *,
        client: InferenceClient,
        cache_root: Path,
        events: EventLogger,
        ledger: Ledger,
        tokens_per_text_estimate: int = 1024,
    ) -> None:
        self.config = config
        self.client = client
        self.events = events
        self.ledger = ledger
        self.cache = EmbeddingCache(cache_root, config.model_id)
        self._tokens_per_text = tokens_per_text_estimate
        self.dim: int | None = config.expected_dim
        self.provider_normalised: bool | None = None

    async def embed(self, texts: list[str]) -> np.ndarray:
        """Return an ``(n, d)`` float32 matrix, in the order given."""
        if not texts:
            return np.zeros((0, self.dim or 0), dtype=np.float32)

        vectors: list[np.ndarray | None] = [self.cache.get(text) for text in texts]
        pending = [index for index, vector in enumerate(vectors) if vector is None]

        for start in range(0, len(pending), self.config.max_batch):
            batch_indices = pending[start : start + self.config.max_batch]
            batch = [texts[i] for i in batch_indices]
            reserve = estimate_embedding_usd(
                self.config.price_usd_per_m_input,
                n_tokens=self._tokens_per_text * len(batch),
            )
            self.ledger.reserve(reserve, what=f"embed {self.config.slug} x{len(batch)}")
            response = await self.client.embed(
                EmbeddingRequest(model_id=self.config.model_id, inputs=tuple(batch))
            )
            if len(response.vectors) != len(batch):
                raise ProviderError(
                    f"{self.config.slug} returned {len(response.vectors)} vectors for "
                    f"{len(batch)} inputs"
                )
            self.ledger.record(
                response.usage,
                kind="embedding",
                embedding=self.config.slug,
                model_id=self.config.model_id,
                n_inputs=len(batch),
            )
            for offset, index in enumerate(batch_indices):
                vector = np.asarray(response.vectors[offset], dtype=np.float32)
                self._observe(vector)
                self.cache.put(texts[index], vector)
                vectors[index] = vector

        matrix = np.vstack([np.asarray(v, dtype=np.float32) for v in vectors])
        self.events.event(
            "embeddings.batch.completed",
            embedding=self.config.slug,
            model_id=self.config.model_id,
            n_texts=len(texts),
            n_computed=len(pending),
            n_cached=len(texts) - len(pending),
            dim=int(matrix.shape[1]),
            provider_normalised=self.provider_normalised,
        )
        return matrix

    def _observe(self, vector: np.ndarray) -> None:
        """Record dimension and whether the provider already normalises.

        Both are audit facts (S0.5). A dimension mismatch against the config is
        an error rather than a warning: it means we are embedding with a
        different model than the one the manifest claims.
        """
        if self.dim is None:
            self.dim = int(vector.shape[0])
        elif int(vector.shape[0]) != self.dim:
            raise ProviderError(
                f"{self.config.slug}: expected dim {self.dim}, provider returned {vector.shape[0]}"
            )
        if self.provider_normalised is None:
            norm = float(np.linalg.norm(vector))
            self.provider_normalised = abs(norm - 1.0) < 1e-3

    def stats(self) -> dict[str, object]:
        return {
            "slug": self.config.slug,
            "model_id": self.config.model_id,
            "architecture": self.config.architecture,
            "dim": self.dim,
            "provider_normalised": self.provider_normalised,
            "cache": self.cache.stats(),
        }
