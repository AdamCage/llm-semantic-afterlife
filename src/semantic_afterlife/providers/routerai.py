"""RouterAI client (https://routerai.ru/api/v1) — the primary provider.

RouterAI is OpenAI-compatible and prices in roubles. Two of its behaviours are
load-bearing for this project and are implemented deliberately:

* ``provider.only`` / ``order`` / ``ignore`` are documented as routing
  *preferences*: a fallback attempt after an upstream failure may be served
  outside the list. Only ``allow_fallbacks: false`` turns a preference into a
  constraint, returning ``404`` instead of silently substituting an endpoint.
  We always send both, and we verify the served provider afterwards (ADR-0003).
* ``GET /models/{author}/{slug}/endpoints`` exposes per-endpoint ``quantization``,
  ``context_length``, ``supported_parameters`` and ``supported_apis``. That is
  the only reliable way to learn what a model can actually do, so Stage 0 audits
  it rather than trusting prose documentation.
"""

from __future__ import annotations

from typing import Any

from ..config import ExecutionMode, Settings
from ..errors import ProviderError, ProviderPinningError
from ..hashing import canonical_json
from ..ledger import Usage
from ..logging_utils import EventLogger
from .base import (
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    HTTPInferenceClient,
)
from .cache import ResponseCache, cache_key

# Header names seen in the wild for "which upstream actually served this".
_PROVIDER_HEADERS = ("x-routerai-provider", "x-provider", "x-upstream-provider")


class RouterAIClient(HTTPInferenceClient):
    """RouterAI inference client with strict endpoint pinning and cost accounting."""

    CHAT_PATH = "/chat/completions"
    COMPLETIONS_PATH = "/completions"
    EMBEDDINGS_PATH = "/embeddings"

    #: Multiplier turning provider-reported cost into USD. RouterAI reports
    #: roubles; an override of 1.0 makes the same implementation serve any
    #: OpenAI-compatible router that already reports USD.
    provider_name = "routerai"

    def __init__(
        self,
        settings: Settings,
        *,
        events: EventLogger | None = None,
        cache: ResponseCache | None = None,
        price_table: dict[str, dict[str, float]] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            name=self.provider_name,
            base_url=settings.base_url(self.provider_name),
            api_key=settings.api_key(self.provider_name),
            timeout_s=settings.afterlife_request_timeout_s,
            max_retries=settings.afterlife_max_retries,
            events=events,
            extra_headers=extra_headers,
        )
        self._settings = settings
        self._cache = cache
        self._mode = settings.afterlife_execution_mode
        self._usd_per_rub = settings.afterlife_usd_per_rub
        # model_id -> {"input_usd_per_token", "output_usd_per_token"}
        self._price_table = price_table or {}

    # -- payload construction ------------------------------------------------

    def _provider_block(self, request: CompletionRequest) -> dict[str, Any] | None:
        """Routing preferences, or ``None`` when there is nothing to constrain.

        ``allow_fallbacks`` is only meaningful alongside a preference list: on its
        own it would ask the router to fail rather than route, which is not what
        an unpinned audit request wants. So it is sent only when a provider is
        actually pinned -- and then it is what turns the pin from a preference
        into a constraint (ADR-0003).
        """
        block: dict[str, Any] = {}
        if request.provider_slug:
            block["only"] = [request.provider_slug]
            block["allow_fallbacks"] = request.allow_fallbacks
        if request.country:
            block["country"] = request.country
        return block or None

    def build_payload(self, request: CompletionRequest) -> tuple[str, dict[str, Any]]:
        payload: dict[str, Any] = {
            "model": request.model_id,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stream": False,
        }
        if request.is_chat:
            path = self.CHAT_PATH
            payload["messages"] = [dict(message) for message in request.messages or ()]
        else:
            path = self.COMPLETIONS_PATH
            payload["prompt"] = request.prompt

        if request.seed is not None:
            payload["seed"] = request.seed
        if request.top_k is not None:
            payload["top_k"] = request.top_k
        if request.repetition_penalty is not None:
            payload["repetition_penalty"] = request.repetition_penalty
        if request.stop:
            payload["stop"] = list(request.stop)
        if request.logprobs:
            payload["logprobs"] = True
            if request.top_logprobs is not None:
                payload["top_logprobs"] = request.top_logprobs
        if request.service_tier:
            payload["service_tier"] = request.service_tier
        if (provider := self._provider_block(request)) is not None:
            payload["provider"] = provider
        payload.update(request.extra)
        return path, payload

    # -- pricing -------------------------------------------------------------

    @property
    def native_price_to_usd(self) -> float:
        """RouterAI quotes roubles per token."""
        return self._usd_per_rub

    def set_price_table(self, table: dict[str, dict[str, float]]) -> None:
        self._price_table = table

    def _cost(self, model_id: str, body: dict[str, Any]) -> tuple[float, float | None]:
        """Cost in USD, and the raw rouble figure when the API reports one.

        Provider-reported cost is preferred over our own multiplication whenever
        available, because it accounts for tier discounts and cached-token
        pricing that a static table cannot.
        """
        usage = body.get("usage") or {}
        reported = usage.get("cost")
        if reported is not None:
            try:
                cost_rub = float(reported)
            except (TypeError, ValueError):
                cost_rub = None
            if cost_rub is not None:
                return cost_rub * self._usd_per_rub, cost_rub

        prices = self._price_table.get(model_id)
        if not prices:
            return 0.0, None
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        usd = prompt_tokens * prices.get(
            "input_usd_per_token", 0.0
        ) + completion_tokens * prices.get("output_usd_per_token", 0.0)
        return usd, None

    # -- served-provider verification ---------------------------------------

    @staticmethod
    def _served_provider(body: dict[str, Any], headers: dict[str, str]) -> str | None:
        for key in ("provider", "served_provider", "provider_name"):
            value = body.get(key)
            if isinstance(value, str) and value:
                return value
            if isinstance(value, dict):
                for inner in ("tag", "slug", "name"):
                    if isinstance(value.get(inner), str):
                        return str(value[inner])
        lowered = {k.lower(): v for k, v in headers.items()}
        for header in _PROVIDER_HEADERS:
            if lowered.get(header):
                return lowered[header]
        return None

    # -- completion ----------------------------------------------------------

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        path, payload = self.build_payload(request)
        key = cache_key(
            self.name,
            path,
            payload if request.cache_bust is None else {**payload, "__probe": request.cache_bust},
        )

        if self._mode is ExecutionMode.REPLAY:
            entry = (
                self._cache.require(key, context=f"{path} {request.model_id}")
                if self._cache
                else None
            )
            if entry is None:
                raise ProviderError("replay mode requires a response cache")
            return self._parse_completion(
                request,
                entry["body"],
                entry.get("headers", {}),
                latency_s=0.0,
                attempts=0,
                from_cache=True,
            )

        if self._cache is not None and (entry := self._cache.get(key)) is not None:
            return self._parse_completion(
                request,
                entry["body"],
                entry.get("headers", {}),
                latency_s=0.0,
                attempts=0,
                from_cache=True,
            )

        body, headers, latency, attempts = await self._post(path, payload)
        if self._cache is not None:
            self._cache.put(key, provider=self.name, path=path, payload=payload, body=body)
        return self._parse_completion(
            request, body, headers, latency_s=latency, attempts=attempts, from_cache=False
        )

    def _parse_completion(
        self,
        request: CompletionRequest,
        body: dict[str, Any],
        headers: dict[str, str],
        *,
        latency_s: float,
        attempts: int,
        from_cache: bool,
    ) -> CompletionResponse:
        choices = body.get("choices")
        if not choices:
            raise ProviderError(
                f"routerai returned no choices for {request.model_id}: {canonical_json(body)[:500]}"
            )
        choice = choices[0]
        if request.is_chat:
            message = choice.get("message") or {}
            text = message.get("content") or ""
        else:
            text = choice.get("text") or ""

        usage_block = body.get("usage") or {}
        cost_usd, cost_rub = self._cost(request.model_id, body)
        usage = Usage(
            prompt_tokens=int(usage_block.get("prompt_tokens") or 0),
            completion_tokens=int(usage_block.get("completion_tokens") or 0),
            cost_usd=0.0 if from_cache else cost_usd,
            cost_rub=None if from_cache else cost_rub,
            cached_tokens=(usage_block.get("prompt_tokens_details") or {}).get("cached_tokens"),
            from_cache=from_cache,
        )
        served = self._served_provider(body, headers)
        if request.provider_slug and served and not _same_provider(served, request.provider_slug):
            raise ProviderPinningError(
                f"pinned provider {request.provider_slug!r} but request was served by {served!r}; "
                "this changes the generator mid-experiment (ADR-0003)"
            )
        return CompletionResponse(
            text=text,
            finish_reason=choice.get("finish_reason") or choice.get("native_finish_reason"),
            usage=usage,
            served_provider=served,
            model_returned=body.get("model"),
            latency_s=latency_s,
            attempts=attempts,
            from_cache=from_cache,
            raw=body,
        )

    # -- embeddings ----------------------------------------------------------

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        payload: dict[str, Any] = {
            "model": request.model_id,
            "input": list(request.inputs),
            **request.extra,
        }
        key = cache_key(self.name, self.EMBEDDINGS_PATH, payload)

        if self._mode is ExecutionMode.REPLAY:
            if self._cache is None:
                raise ProviderError("replay mode requires a response cache")
            entry = self._cache.require(key, context=f"embeddings {request.model_id}")
            return self._parse_embedding(request, entry["body"], latency_s=0.0, from_cache=True)

        if self._cache is not None and (cached := self._cache.get(key)) is not None:
            return self._parse_embedding(request, cached["body"], latency_s=0.0, from_cache=True)

        body, _headers, latency, _attempts = await self._post(self.EMBEDDINGS_PATH, payload)
        if self._cache is not None:
            self._cache.put(
                key, provider=self.name, path=self.EMBEDDINGS_PATH, payload=payload, body=body
            )
        return self._parse_embedding(request, body, latency_s=latency, from_cache=False)

    def _parse_embedding(
        self,
        request: EmbeddingRequest,
        body: dict[str, Any],
        *,
        latency_s: float,
        from_cache: bool,
    ) -> EmbeddingResponse:
        data = body.get("data")
        if not data:
            raise ProviderError(
                f"routerai embeddings returned no data for {request.model_id}: "
                f"{canonical_json(body)[:500]}"
            )
        ordered = sorted(data, key=lambda item: item.get("index", 0))
        vectors = tuple(tuple(float(x) for x in item["embedding"]) for item in ordered)
        usage_block = body.get("usage") or {}
        cost_usd, cost_rub = self._cost(request.model_id, body)
        return EmbeddingResponse(
            vectors=vectors,
            usage=Usage(
                prompt_tokens=int(usage_block.get("prompt_tokens") or 0),
                completion_tokens=0,
                cost_usd=0.0 if from_cache else cost_usd,
                cost_rub=None if from_cache else cost_rub,
                from_cache=from_cache,
            ),
            model_returned=body.get("model"),
            latency_s=latency_s,
            from_cache=from_cache,
            raw=body,
        )

    # -- catalogue -----------------------------------------------------------

    async def list_models(self) -> list[dict[str, Any]]:
        body = await self._get("/models")
        if isinstance(body, dict):
            data = body.get("data", body.get("models", []))
            return list(data) if isinstance(data, list) else []
        return list(body) if isinstance(body, list) else []

    async def list_endpoints(self, model_id: str) -> list[dict[str, Any]]:
        """Per-endpoint capabilities for ``author/slug``.

        Returns ``[]`` rather than raising when the model is absent, because
        "not available on this router" is a normal audit outcome that the report
        needs to record, not an exception.
        """
        if "/" not in model_id:
            raise ProviderError(f"model_id {model_id!r} must be 'author/slug'")
        try:
            body = await self._get(f"/models/{model_id}/endpoints")
        except ProviderError as exc:
            if exc.status_code == 404:
                return []
            raise
        if isinstance(body, dict):
            data = body.get("data") or body
            if isinstance(data, dict):
                endpoints = data.get("endpoints", [])
                return list(endpoints) if isinstance(endpoints, list) else []
            if isinstance(data, list):
                return data
        return []


def parse_price_table(
    models: list[dict[str, Any]], usd_per_rub: float
) -> dict[str, dict[str, float]]:
    """Build a ``model_id -> per-token USD`` table from a ``/models`` payload.

    RouterAI prices in roubles per token. Field names vary between routers and
    over time, so we probe a few shapes and skip anything unparseable rather
    than guessing — a missing price shows up as a zero-cost estimate in the
    audit, which is visible, instead of a wrong one, which is not.
    """
    table: dict[str, dict[str, float]] = {}
    for entry in models:
        model_id = entry.get("id") or entry.get("slug") or entry.get("model")
        pricing = entry.get("pricing") or entry.get("price") or {}
        if not model_id or not isinstance(pricing, dict):
            continue
        input_rub = _first_float(pricing, ("prompt", "input", "input_tokens", "prompt_tokens"))
        output_rub = _first_float(
            pricing, ("completion", "output", "output_tokens", "completion_tokens")
        )
        if input_rub is None and output_rub is None:
            continue
        table[str(model_id)] = {
            "input_usd_per_token": (input_rub or 0.0) * usd_per_rub,
            "output_usd_per_token": (output_rub or 0.0) * usd_per_rub,
            "input_rub_per_token": input_rub or 0.0,
            "output_rub_per_token": output_rub or 0.0,
        }
    return table


def _normalise_provider(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


def _same_provider(served: str, pinned: str) -> bool:
    """Compare a served provider against a pinned slug.

    The response reports a human-readable name (``"Io Net"``, ``"DeepInfra"``)
    while the pin is a slug (``"io-net"``, ``"deepinfra"``), so a literal
    comparison raises a false pinning violation and would discard perfectly valid
    trajectories -- measured in S0. Names are also sometimes suffixed
    (``"Mancer 2"`` for ``"mancer"``), hence the prefix allowance.
    """
    left, right = _normalise_provider(served), _normalise_provider(pinned)
    if not left or not right:
        return True
    return left == right or left.startswith(right) or right.startswith(left)


def _first_float(mapping: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key in mapping:
            try:
                return float(mapping[key])
            except (TypeError, ValueError):
                continue
    return None
