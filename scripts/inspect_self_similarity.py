"""Inter-chunk self-similarity of a running trajectory, measured on raw text.

Written because the degeneracy diagnostic missed a trajectory that had converged
to a near-exact textual fixed point. That diagnostic measures repetition *inside*
a chunk, so a trajectory whose every chunk is varied prose scores clean even when
chunk 40, chunk 80 and chunk 129 are almost the same page. Intra-chunk variety and
inter-chunk novelty are different quantities, and only the second one distinguishes
"bounded semantic exploration" from "printing the same page forever".

Text-only and dependency-free on purpose: it must be usable on a live run before
any embedding exists, and its verdict must not depend on the representation space
whose behaviour is under study.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path

WORD = re.compile(r"[\w']+", re.UNICODE)


def tokens(text: str) -> list[str]:
    return WORD.findall(text.lower())


def shingles(text: str, n: int) -> set[tuple[str, ...]]:
    t = tokens(text)
    return {tuple(t[i : i + n]) for i in range(len(t) - n + 1)}


def jaccard(a: set[tuple[str, ...]], b: set[tuple[str, ...]]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_chunks(path: Path) -> list[str]:
    rows = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    return [row["text"] for row in rows if row.get("text")]


def report(path: Path, *, n: int, W: int, block: int) -> None:
    texts = load_chunks(path)
    if len(texts) < 8:
        print(f"{path.stem}: {len(texts)} chunks, too few to profile")
        return
    grams = [shingles(t, n) for t in texts]
    per_turnover = W / block

    print(f"\n=== {path.stem} — {len(texts)} chunks, {len(texts) / per_turnover:.1f} turnovers ===")
    print(f"  {n}-gram Jaccard between chunks separated by a given lag:")
    for lag in (1, 2, 5, 10, 20, 40, 80):
        if lag >= len(grams):
            continue
        vals = [jaccard(grams[i], grams[i + lag]) for i in range(len(grams) - lag)]
        print(
            f"    lag {lag:3d} chunks ({lag / per_turnover:5.2f} turnovers): "
            f"mean {statistics.mean(vals):.3f}  max {max(vals):.3f}"
        )

    half = len(grams) // 2
    late = range(half, len(grams))
    pairs = [jaccard(grams[a], grams[b]) for a in late for b in late if b > a]
    if pairs:
        print(
            f"  second half, all {len(pairs)} pairs: mean {statistics.mean(pairs):.3f}  "
            f"median {statistics.median(pairs):.3f}  max {max(pairs):.3f}"
        )
    # A trajectory that keeps producing new material has a low ceiling here. A
    # near-fixed point has a high floor, and the floor is the diagnostic quantity:
    # a single repeated page pushes every late pair up at once.
    if pairs and statistics.median(pairs) > 0.30:
        print(
            "  VERDICT: converged to a near-textual fixed point. Intra-chunk metrics will "
            "not show this; any confinement measured here is textual, not semantic."
        )
    elif pairs and statistics.median(pairs) > 0.15:
        print("  VERDICT: strong inter-chunk recurrence; treat confinement claims with care.")
    else:
        print("  VERDICT: chunks keep introducing new material.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="*.steps.jsonl checkpoints, or a run directory")
    parser.add_argument("-n", type=int, default=5, help="shingle length in words")
    parser.add_argument("--window", type=int, default=4096, help="W, for turnover labels")
    parser.add_argument("--block", type=int, default=1024, help="block size, for turnover labels")
    args = parser.parse_args()

    targets: list[Path] = []
    for raw in args.paths:
        path = Path(raw)
        if path.is_dir():
            targets.extend(sorted(path.rglob("*.steps.jsonl")))
        else:
            targets.append(path)
    for target in targets:
        report(target, n=args.n, W=args.window, block=args.block)


if __name__ == "__main__":
    main()
