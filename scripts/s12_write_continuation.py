"""Write the S12 continuation seed bank from L0 trajectory tails.

The tail is the initial condition of the waiting-time run. The window
truncates it to the last W tokens. Does not edit seed_bank_v1.
"""

from __future__ import annotations

from pathlib import Path

import yaml

TAIL_CHARS = 40000
OUT = Path("configs/seeds/seed_bank_s12_continuation.yaml")

SOURCES = [
    (
        "mb-physics-s1",
        "physics",
        "runs/s11/s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b/data/trajectories/pb-ministral-8b-base__W4096__T0p3__physics__s1.text",
    ),
    (
        "mb-physics-s2",
        "physics",
        "runs/s11/s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b/data/trajectories/pb-ministral-8b-base__W4096__T0p3__physics__s2.text",
    ),
    (
        "mb-love-s1",
        "love",
        "runs/s11/s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b/data/trajectories/pb-ministral-8b-base__W4096__T0p3__love__s1.text",
    ),
    (
        "mb-love-s2",
        "love",
        "runs/s11/s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b/data/trajectories/pb-ministral-8b-base__W4096__T0p3__love__s2.text",
    ),
    (
        "qi-physics-s1",
        "physics",
        "runs/s9/s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6/data/trajectories/pb-qwen3-8b-instruct__W4096__T0p3__physics__s1.text",
    ),
    (
        "qi-physics-s2",
        "physics",
        "runs/s9/s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6/data/trajectories/pb-qwen3-8b-instruct__W4096__T0p3__physics__s2.text",
    ),
    (
        "qi-love-s1",
        "love",
        "runs/s9/s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6/data/trajectories/pb-qwen3-8b-instruct__W4096__T0p3__love__s1.text",
    ),
    (
        "qi-love-s2",
        "love",
        "runs/s9/s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6/data/trajectories/pb-qwen3-8b-instruct__W4096__T0p3__love__s2.text",
    ),
]


def main() -> None:
    seeds = []
    for seed_id, domain, rel in SOURCES:
        path = Path(rel)
        if not path.is_file():
            raise SystemExit(f"missing {path}")
        text = path.read_text(encoding="utf-8", errors="replace")
        tail = text[-TAIL_CHARS:]
        seeds.append(
            {
                "id": seed_id,
                "domain": domain,
                "language": "en",
                "text": tail,
            }
        )
        print(f"{seed_id} chars={len(tail)} source={rel}")
    doc = {
        "version": "s12-continuation",
        "description": (
            "Tails of eight L0 trajectories selected by the still-locked "
            "checkpoint rule and ADR-0023 F3. Not an edit of seed_bank_v1. "
            "The sliding window keeps the last W tokens of each tail."
        ),
        "seeds": seeds,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
