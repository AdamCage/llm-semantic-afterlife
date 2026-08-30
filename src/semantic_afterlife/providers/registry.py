"""Client construction and lifecycle.

Clients are cached per (provider, run) so that one HTTP connection pool serves
every trajectory, and so that the response cache is shared rather than
duplicated.
"""

from __future__ import annotations

from ..config import ExecutionMode, Settings
from ..errors import ConfigError
from ..logging_utils import EventLogger
from .base import InferenceClient
from .cache import ResponseCache
from .mock import MockClient
from .openrouter import OpenRouterClient
from .routerai import RouterAIClient

_CLIENTS: dict[str, InferenceClient] = {}


def build_client(
    api: str,
    settings: Settings,
    *,
    events: EventLogger | None = None,
    price_table: dict[str, dict[str, float]] | None = None,
    reuse: bool = True,
) -> InferenceClient:
    """Return a client for ``api``, honouring the execution mode.

    In ``mock`` mode every provider resolves to :class:`MockClient`, so the same
    configs run offline without a parallel code path — which is the only way the
    offline path stays trustworthy.
    """
    if settings.afterlife_execution_mode is ExecutionMode.MOCK or api == "mock":
        key = "mock"
        if reuse and key in _CLIENTS:
            return _CLIENTS[key]
        client: InferenceClient = MockClient()
        if reuse:
            _CLIENTS[key] = client
        return client

    key = f"{api}:{id(settings)}"
    if reuse and key in _CLIENTS:
        return _CLIENTS[key]

    cache = ResponseCache(settings.paths.response_cache)
    if api == "routerai":
        client = RouterAIClient(settings, events=events, cache=cache, price_table=price_table)
    elif api == "openrouter":
        client = OpenRouterClient(settings, events=events, cache=cache, price_table=price_table)
    else:
        raise ConfigError(f"unknown api {api!r}; expected 'routerai', 'openrouter' or 'mock'")

    if reuse:
        _CLIENTS[key] = client
    return client


async def close_clients() -> None:
    for client in list(_CLIENTS.values()):
        await client.aclose()
    _CLIENTS.clear()
