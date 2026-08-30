"""OpenRouter client — used only for Stage 6 cross-provider replication.

The wire format is the same OpenAI-compatible shape as RouterAI, including the
``provider`` routing block and the per-model ``/endpoints`` catalogue, so the
implementation is inherited. The one substantive difference is currency:
OpenRouter prices in USD, so no rouble conversion is applied.
"""

from __future__ import annotations

from typing import Any

from ..config import Settings
from ..logging_utils import EventLogger
from .cache import ResponseCache
from .routerai import RouterAIClient


class OpenRouterClient(RouterAIClient):
    provider_name = "openrouter"

    def __init__(
        self,
        settings: Settings,
        *,
        events: EventLogger | None = None,
        cache: ResponseCache | None = None,
        price_table: dict[str, dict[str, float]] | None = None,
    ) -> None:
        super().__init__(
            settings,
            events=events,
            cache=cache,
            price_table=price_table,
            extra_headers={
                "HTTP-Referer": "https://github.com/AdamCage/llm-semantic-afterlife",
                "X-Title": "llm-semantic-afterlife",
            },
        )
        # Reported costs are already USD.
        self._usd_per_rub = 1.0


def parse_price_table_usd(models: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """``model_id -> per-token USD`` from an OpenRouter ``/models`` payload."""
    table: dict[str, dict[str, float]] = {}
    for entry in models:
        model_id = entry.get("id")
        pricing = entry.get("pricing") or {}
        if not model_id or not isinstance(pricing, dict):
            continue
        try:
            table[str(model_id)] = {
                "input_usd_per_token": float(pricing.get("prompt", 0.0)),
                "output_usd_per_token": float(pricing.get("completion", 0.0)),
            }
        except (TypeError, ValueError):
            continue
    return table
