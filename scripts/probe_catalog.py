"""Search the provider catalogue for candidate generators.

Stage 0 discovered that our first-choice base model is absent from the router
and that no endpoint advertises the raw text-completion API. Both facts change
the experiment design, so this script exists to answer the follow-up question
the audit raised: what *is* available, and at what price?

Read-only and free -- it only calls ``GET /models``.
"""

from __future__ import annotations

import argparse
import asyncio
from typing import Any

import pandas as pd

from semantic_afterlife.config import get_settings
from semantic_afterlife.providers import build_client, close_clients


def flatten(entry: dict[str, Any], to_usd: float) -> dict[str, Any]:
    """Normalise one catalogue entry.

    ``to_usd`` converts the provider's native per-token price into USD: RouterAI
    quotes roubles, OpenRouter already quotes USD.
    """
    pricing = entry.get("pricing") or {}

    def price(*keys: str) -> float | None:
        for key in keys:
            if key in pricing:
                try:
                    return float(pricing[key]) * 1e6 * to_usd
                except (TypeError, ValueError):
                    continue
        return None

    return {
        "id": entry.get("id") or entry.get("slug"),
        "name": entry.get("name"),
        "context_length": entry.get("context_length"),
        "usd_per_m_input": price("prompt", "input"),
        "usd_per_m_output": price("completion", "output"),
        "supported_apis": ",".join(map(str, entry.get("supported_apis") or [])),
        "supported_parameters": ",".join(map(str, entry.get("supported_parameters") or [])),
        "modalities": ",".join(map(str, entry.get("output_modalities") or [])),
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "patterns",
        nargs="*",
        default=["llama", "base", "qwen3", "mistral", "glimmer", "embedding", "bge"],
        help="case-insensitive regexes matched against the model id and name",
    )
    parser.add_argument("--api", default="routerai")
    parser.add_argument("--sort", default="usd_per_m_input")
    args = parser.parse_args()

    settings = get_settings()
    client = build_client(args.api, settings)
    try:
        models = await client.list_models()
    finally:
        await close_clients()

    to_usd = 1.0 if args.api == "openrouter" else settings.afterlife_usd_per_rub
    frame = pd.DataFrame([flatten(m, to_usd) for m in models])
    print(f"catalogue: {len(frame)} models on {args.api}")
    print(
        f"models advertising a completions API: {frame['supported_apis'].str.contains('completion').sum()}"
    )
    print()

    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 46)
    for pattern in args.patterns:
        mask = frame["id"].fillna("").str.contains(pattern, case=False, regex=True) | frame[
            "name"
        ].fillna("").str.contains(pattern, case=False, regex=True)
        subset = frame[mask].sort_values(args.sort, na_position="last")
        print(f"--- /{pattern}/ : {len(subset)} match(es) ---")
        if subset.empty:
            print("  none")
        else:
            print(
                subset[
                    [
                        "id",
                        "context_length",
                        "usd_per_m_input",
                        "usd_per_m_output",
                        "supported_apis",
                    ]
                ].to_string(index=False)
            )
        print()


if __name__ == "__main__":
    asyncio.run(main())
