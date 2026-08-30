"""Provider-agnostic request/response types and the shared HTTP client.

Everything a run needs to know about a request lives in
:class:`CompletionRequest`; everything it needs to record about the outcome lives
in :class:`CompletionResponse`, including the *served* provider, which is what
lets us detect the silent endpoint substitution described in ADR-0003.
"""

from __future__ import annotations

import abc
import asyncio
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from ..errors import ProviderError
from ..ledger import Usage
from ..logging_utils import EventLogger, get_logger

logger = get_logger("providers")

RETRYABLE_STATUS = frozenset({408, 409, 425, 429, 500, 502, 503, 504, 522, 524})


class RetryableProviderError(ProviderError):
    """A transient provider failure worth retrying."""


@dataclass(frozen=True, slots=True)
class CompletionRequest:
    """One generation step.

    Exactly one of ``prompt`` (raw completion) or ``messages`` (chat) is set;
    which one is a protocol fact recorded per run (methodology.md 1.3).
    """

    model_id: str
    max_tokens: int
    temperature: float
    prompt: str | None = None
    messages: tuple[dict[str, str], ...] | None = None
    top_p: float = 1.0
    top_k: int | None = None
    repetition_penalty: float | None = None
    seed: int | None = None
    stop: tuple[str, ...] | None = None
    logprobs: bool = False
    top_logprobs: int | None = None

    provider_slug: str | None = None
    allow_fallbacks: bool = False
    service_tier: str | None = None
    country: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
    cache_bust: int | None = field(
        default=None,
        compare=False,
        metadata={
            "why": "Distinguishes cache entries for otherwise identical requests, without "
            "altering the payload sent to the provider. Required by the determinism audit, "
            "where a cache hit would report perfect reproducibility — the very thing under test."
        },
    )

    @property
    def is_chat(self) -> bool:
        return self.messages is not None

    def __post_init__(self) -> None:
        if (self.prompt is None) == (self.messages is None):
            raise ProviderError("exactly one of prompt / messages must be set")


@dataclass(frozen=True, slots=True)
class CompletionResponse:
    text: str
    finish_reason: str | None
    usage: Usage
    served_provider: str | None
    model_returned: str | None
    latency_s: float
    attempts: int
    from_cache: bool
    raw: dict[str, Any]

    @property
    def logprobs(self) -> Any:
        choices = self.raw.get("choices") or [{}]
        return choices[0].get("logprobs")


@dataclass(frozen=True, slots=True)
class EmbeddingRequest:
    model_id: str
    inputs: tuple[str, ...]
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EmbeddingResponse:
    vectors: tuple[tuple[float, ...], ...]
    usage: Usage
    model_returned: str | None
    latency_s: float
    from_cache: bool
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def dim(self) -> int:
        return len(self.vectors[0]) if self.vectors else 0


class InferenceClient(abc.ABC):
    """Common surface for every provider."""

    name: str

    @abc.abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse: ...

    @abc.abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse: ...

    async def list_models(self) -> list[dict[str, Any]]:
        raise NotImplementedError(f"{self.name} does not expose a model catalogue")

    async def list_endpoints(self, model_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError(f"{self.name} does not expose per-model endpoints")

    async def aclose(self) -> None:
        return None


class HTTPInferenceClient(InferenceClient):
    """Shared HTTP plumbing: auth, retries, timeouts, structured retry logging."""

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        api_key: str,
        timeout_s: float,
        max_retries: int,
        events: EventLogger | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self._events = events
        self._max_retries = max_retries
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            **(extra_headers or {}),
        }
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(timeout_s, connect=30.0),
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _post(
        self, path: str, payload: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, str], float, int]:
        """POST with bounded retries. Returns ``(body, headers, latency_s, attempts)``.

        Headers are returned because some routers report the upstream provider
        that actually served the request only in a response header, and ADR-0003
        requires us to compare it against the pinned one.
        """
        attempts = 0
        start = perf_counter()
        retrying = AsyncRetrying(
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential_jitter(initial=2.0, max=120.0, jitter=3.0),
            retry=retry_if_exception_type(
                (RetryableProviderError, httpx.TransportError, asyncio.TimeoutError)
            ),
            reraise=True,
        )
        async for attempt in retrying:
            with attempt:
                attempts += 1
                try:
                    response = await self._client.post(path, json=payload)
                except httpx.TransportError as exc:
                    self._log_retry(path, attempts, reason=f"transport: {exc}")
                    raise
                if response.status_code in RETRYABLE_STATUS:
                    self._log_retry(
                        path,
                        attempts,
                        reason=f"http {response.status_code}",
                        body=response.text[:2000],
                    )
                    raise RetryableProviderError(
                        f"{self.name} {path} -> {response.status_code}",
                        status_code=response.status_code,
                        body=response.text[:4000],
                    )
                if response.status_code >= 400:
                    # 4xx other than 429: a client error. Retrying cannot help and
                    # would burn budget; surface it immediately.
                    raise ProviderError(
                        f"{self.name} {path} -> {response.status_code}: {response.text[:1000]}",
                        status_code=response.status_code,
                        body=response.text[:4000],
                    )
                return (
                    response.json(),
                    dict(response.headers),
                    perf_counter() - start,
                    attempts,
                )
        raise ProviderError(f"{self.name} {path}: retries exhausted")

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        retrying = AsyncRetrying(
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential_jitter(initial=2.0, max=60.0, jitter=2.0),
            retry=retry_if_exception_type((RetryableProviderError, httpx.TransportError)),
            reraise=True,
        )
        async for attempt in retrying:
            with attempt:
                response = await self._client.get(path, params=params)
                if response.status_code in RETRYABLE_STATUS:
                    raise RetryableProviderError(
                        f"{self.name} GET {path} -> {response.status_code}",
                        status_code=response.status_code,
                    )
                if response.status_code >= 400:
                    raise ProviderError(
                        f"{self.name} GET {path} -> {response.status_code}: {response.text[:500]}",
                        status_code=response.status_code,
                    )
                return response.json()
        raise ProviderError(f"{self.name} GET {path}: retries exhausted")

    def _log_retry(self, path: str, attempt: int, *, reason: str, body: str | None = None) -> None:
        if self._events is not None:
            self._events.event(
                "provider.retry",
                level="WARNING",
                provider=self.name,
                path=path,
                attempt=attempt,
                reason=reason,
                body=body,
            )
        logger.warning("%s %s retry %d: %s", self.name, path, attempt, reason)
