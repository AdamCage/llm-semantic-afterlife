"""What exactly does a reasoning-mandatory endpoint return, and what bounds it?

Two claims decide whether reasoning models can enter this project at all, and
both are testable rather than arguable:

1. **Is the trace returned?** If the provider hands back the reasoning text, the
   request/response record is complete and the project's logging rule is
   satisfiable. If only a token count comes back, we cannot reconstruct what the
   model produced and the run is unattributable.

2. **What does ``max_tokens`` bound?** If it caps *visible* output with reasoning
   billed on top, the window still advances by a stride we chose and the only
   cost is money. If reasoning is charged against the same budget, the stride
   becomes a function of how much the model decided to think — which is the
   objection that actually matters, since Stage 1 failed E7 on stride drift with
   no reasoning at all.

Run against one endpoint at a time. Costs fractions of a cent.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import httpx

PROMPT = (
    "The lattice spacing sets the ultraviolet cutoff, and everything else in the "
    "calculation follows from that single choice. When the coupling is tuned towards "
    "the critical surface the correlation length grows without bound in units of the "
    "spacing, and"
)


def load_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no OPENROUTER_API_KEY")


def describe(payload: dict[str, Any], label: str, max_tokens: int) -> None:
    choice = (payload.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    usage = payload.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}

    visible = message.get("content") or choice.get("text") or ""
    # OpenRouter exposes the trace under either key depending on the provider.
    trace = message.get("reasoning") or ""
    trace_details = message.get("reasoning_details")

    reasoning_tokens = details.get("reasoning_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    print(f"--- {label} (max_tokens={max_tokens}) ---")
    print(f"  finish_reason        {choice.get('finish_reason')}")
    print(f"  completion_tokens    {completion_tokens}")
    print(f"  reasoning_tokens     {reasoning_tokens}")
    print(f"  visible chars        {len(visible)}")
    print(f"  trace returned       {bool(trace) or bool(trace_details)}")
    if trace:
        print(f"  trace chars          {len(trace)}")
        print(f"  trace head           {trace[:160]!r}")
    if trace_details:
        print(f"  reasoning_details    {json.dumps(trace_details)[:200]}")
    if visible:
        print(f"  visible head         {visible[:160]!r}")

    # The decisive arithmetic. If completion_tokens already includes reasoning
    # and is capped at max_tokens, then thinking eats the block.
    if completion_tokens and reasoning_tokens:
        share = reasoning_tokens / completion_tokens
        print(f"  reasoning share of completion_tokens  {share:.1%}")
        print(
            "  VERDICT: reasoning is charged against the block"
            if completion_tokens <= max_tokens * 1.05
            else "  VERDICT: visible output is bounded separately; reasoning is on top"
        )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", help="e.g. openai/gpt-oss-120b")
    parser.add_argument("--provider", default=None, help="pin one endpoint tag")
    parser.add_argument("--max-tokens", type=int, default=200)
    args = parser.parse_args()

    key = load_key()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    base: dict[str, Any] = {
        "model": args.model,
        "max_tokens": args.max_tokens,
        "temperature": 1.0,
        "seed": 4242,
    }
    if args.provider:
        base["provider"] = {"only": [args.provider], "allow_fallbacks": False}

    with httpx.Client(timeout=180) as client:
        # 1. Chat, reasoning left at its default — the way the router UI calls it.
        payload = {**base, "messages": [{"role": "user", "content": PROMPT}]}
        response = client.post(
            "https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload
        )
        if response.status_code == 200:
            describe(response.json(), "chat, reasoning default", args.max_tokens)
        else:
            print(f"--- chat, reasoning default --- HTTP {response.status_code}")
            print(f"  {response.text[:300]}\n")

        # 2. Chat, asking explicitly for the trace to be included.
        payload = {
            **base,
            "messages": [{"role": "user", "content": PROMPT}],
            "reasoning": {"effort": "low", "exclude": False},
        }
        response = client.post(
            "https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload
        )
        if response.status_code == 200:
            describe(response.json(), "chat, reasoning effort=low, exclude=false", args.max_tokens)
        else:
            print(f"--- chat, effort=low --- HTTP {response.status_code}")
            print(f"  {response.text[:300]}\n")

        # 3. Raw completion with reasoning *allowed* rather than disabled. The
        #    earlier capability probe only tried to switch it off, which every
        #    endpoint refused; whether the endpoint serves /completions at all is
        #    a separate question and this is what answers it.
        payload = {**base, "prompt": PROMPT, "reasoning": {"effort": "low", "exclude": False}}
        response = client.post(
            "https://openrouter.ai/api/v1/completions", headers=headers, json=payload
        )
        if response.status_code == 200:
            describe(response.json(), "raw completion, reasoning allowed", args.max_tokens)
        else:
            print(f"--- raw completion, reasoning allowed --- HTTP {response.status_code}")
            print(f"  {response.text[:300]}\n")


if __name__ == "__main__":
    main()
