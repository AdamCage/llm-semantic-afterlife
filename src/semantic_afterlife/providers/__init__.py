"""Inference providers behind one interface.

``routerai`` is primary (ADR-0003), ``openrouter`` exists for cross-provider
replication in Stage 6, and ``mock`` is a deterministic offline generator used by
CI and by tests so that the whole pipeline can be exercised without cost.
"""

from __future__ import annotations

from .base import (
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    InferenceClient,
)
from .registry import build_client, close_clients

__all__ = [
    "CompletionRequest",
    "CompletionResponse",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "InferenceClient",
    "build_client",
    "close_clients",
]
