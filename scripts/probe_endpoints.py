"""Probe every healthy endpoint of one model and report which actually serve.

Stage 0 found that the cheapest healthy endpoint is not always the usable one:
a provider can be listed with ``status: 0`` and still refuse traffic because its
shared rate-limit pool is exhausted, or return malformed error bodies. Endpoint
choice is therefore an empirical question, and it has to be re-answered whenever
a stage locks its matrix.

Costs a few tokens per endpoint.
"""

from __future__ import annotations

import argparse
import asyncio

import pandas as pd

from semantic_afterlife.audits import PROBE_TEXT
from semantic_afterlife.config import SamplingConfig, get_settings, load_experiment_config
from semantic_afterlife.generation.trajectory import build_request
from semantic_afterlife.providers import build_client, close_clients


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", help="generator slug from the stage config")
    parser.add_argument("--config", default="configs/stages/stage0_audit.yaml")
    parser.add_argument("--max-tokens", type=int, default=48)
    parser.add_argument(
        "--include-degraded",
        action="store_true",
        help="also probe endpoints the router reports as deprioritised (status < 0)",
    )
    args = parser.parse_args()

    settings = get_settings()
    experiment, _resolved, _sha = load_experiment_config(args.config)
    generator = experiment.generator(args.model)
    client = build_client(generator.api, settings)
    sampling = SamplingConfig(temperature=0.7, top_p=1.0)

    rows: list[dict[str, object]] = []
    try:
        endpoints = await client.list_endpoints(generator.model_id)
        for endpoint in endpoints:
            status = endpoint.get("status") or 0
            tag = endpoint.get("tag")
            if not tag or (status < 0 and not args.include_degraded):
                continue
            variant = generator.model_copy(update={"provider_slug": tag, "allow_fallbacks": False})
            request = build_request(
                variant, sampling, prompt=PROBE_TEXT, max_tokens=args.max_tokens, seed=777
            )
            row: dict[str, object] = {
                "provider_tag": tag,
                "quantization": endpoint.get("quantization"),
                "router_status": status,
                "context_length": endpoint.get("context_length"),
            }
            try:
                response = await client.complete(request)
            except Exception as exc:
                row |= {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:160]}"}
            else:
                usage = response.usage
                row |= {
                    "ok": bool(response.text.strip()),
                    "completion_tokens": usage.completion_tokens,
                    "reasoning_tokens": response.reasoning_tokens,
                    "visible_chars": len(response.text),
                    "latency_s": round(response.latency_s, 2),
                    "cost_usd": round(usage.cost_usd, 8),
                    "served_provider": response.served_provider,
                    "error": None,
                }
            rows.append(row)
    finally:
        await close_clients()

    frame = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 60)
    print(f"\n{generator.slug} ({generator.model_id}) -- {len(frame)} endpoint(s) probed\n")
    print(frame.to_string(index=False))
    if "ok" in frame.columns:
        usable = frame[frame["ok"].fillna(False).astype(bool)]
        print(f"\nusable: {len(usable)} of {len(frame)}")
        if not usable.empty:
            cheapest = usable.sort_values("cost_usd").iloc[0]
            print(f"cheapest usable: {cheapest['provider_tag']} ({cheapest['quantization']})")


if __name__ == "__main__":
    asyncio.run(main())
