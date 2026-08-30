"""Test whether an endpoint honours a minimum-token floor.

Stage 1's first full-size probe found that block fill collapses from 1.000 to
~0.11 the moment the window is full: conditioned on 8192 tokens of its own
output, the model emits a stop token after ~82 tokens. That is interesting as a
finding and ruinous as an operating point, because under protocol P1 the input
cost is `(T/S)·W` and a stride of 82 instead of 1024 multiplies the bill by an
order of magnitude.

A provider-side `min_tokens` floor would restore a constant stride. It is also an
*intervention on the sampling process* -- we would be studying the model
conditioned on not stopping -- so this script only establishes whether the option
exists. Whether to use it is a decision for the human, and would need an ADR.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import replace
from typing import Any

import pandas as pd

from semantic_afterlife.audits import PROBE_TEXT
from semantic_afterlife.config import SamplingConfig, get_settings, load_experiment_config
from semantic_afterlife.generation.trajectory import build_request
from semantic_afterlife.providers import build_client, close_clients

#: Provider conventions differ and none of them is documented by the routers.
CANDIDATES: tuple[tuple[str, dict[str, Any]], ...] = (
    ("baseline", {}),
    ("min_tokens", {"min_tokens": 512}),
    ("min_new_tokens", {"min_new_tokens": 512}),
    ("provider.min_tokens", {"provider": {"min_tokens": 512}}),
    ("ignore_eos", {"ignore_eos": True}),
    ("skip_special_tokens=false", {"skip_special_tokens": False}),
)


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", help="generator slug from the config")
    parser.add_argument("--config", default="configs/stages/stage0_audit_openrouter.yaml")
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument(
        "--context-repeats",
        type=int,
        default=60,
        help="repeat the probe text to build a long prompt; the early-stop "
        "behaviour only appears once the window is substantially full",
    )
    args = parser.parse_args()

    settings = get_settings()
    experiment, _resolved, _sha = load_experiment_config(args.config)
    generator = experiment.generator(args.model)
    client = build_client(generator.api, settings)
    sampling = SamplingConfig(temperature=1.0, top_p=1.0)
    prompt = (PROBE_TEXT + " ") * args.context_repeats

    rows: list[dict[str, Any]] = []
    try:
        for label, extra in CANDIDATES:
            request = build_request(
                generator, sampling, prompt=prompt, max_tokens=args.max_tokens, seed=31337
            )
            request = replace(request, extra={**request.extra, **extra})
            row: dict[str, Any] = {"switch": label, "requested_min": extra and 512 or None}
            try:
                response = await client.complete(request)
            except Exception as exc:
                row |= {"accepted": False, "error": f"{type(exc).__name__}: {str(exc)[:140]}"}
            else:
                row |= {
                    "accepted": True,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "finish_reason": response.finish_reason,
                    "floor_honoured": response.usage.completion_tokens >= 512,
                    "error": None,
                }
            rows.append(row)
    finally:
        await close_clients()

    frame = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(f"\n{generator.slug} via {generator.api}/{generator.provider_slug}")
    print(f"prompt length: ~{len(prompt)} chars, max_tokens={args.max_tokens}\n")
    print(frame.to_string(index=False))
    if "floor_honoured" in frame.columns and frame["floor_honoured"].fillna(False).any():
        working = frame[frame["floor_honoured"].fillna(False)]["switch"].tolist()
        print(f"\nfloor honoured by: {', '.join(working)}")
    else:
        print("\nno switch produced a token floor; the early stop cannot be suppressed here")


if __name__ == "__main__":
    asyncio.run(main())
