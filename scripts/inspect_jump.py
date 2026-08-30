"""Classify an abrupt transition in a trajectory: metastable or degenerate?

A sudden jump in distance-from-origin can mean two very different things. If it
comes with rising n-gram repetition and falling entropy, the model has collapsed
into a loop and the "new state" is an artifact. If those are flat across the
jump, the trajectory has genuinely changed semantic regime -- which is the
metastability the project is looking for.

Prints the diagnostics either side of the split and a sample of the text, so the
verdict rests on the numbers *and* on reading what the model actually wrote.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from semantic_afterlife.analysis.degeneracy import (
    DegeneracyParams,
    compare_segments,
    compute_degeneracy,
)
from semantic_afterlife.config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id", help="generation run holding chunks.parquet")
    parser.add_argument("--split-token", type=int, required=True)
    parser.add_argument("--sample-chars", type=int, default=420)
    args = parser.parse_args()

    settings = get_settings()
    run = settings.paths.find_run(args.run_id)
    chunks = pd.read_parquet(run.chunks()).sort_values("chunk_index").reset_index(drop=True)

    trajectory_id = str(chunks["trajectory_id"].iloc[0])
    W = int(chunks["W"].iloc[0])
    result = compute_degeneracy(
        chunks["text"].tolist(),
        trajectory_id=trajectory_id,
        token_ends=chunks["token_end"].to_numpy(),
        W=W,
        params=DegeneracyParams(),
    )

    pd.set_option("display.width", 160)
    print(f"\n{trajectory_id}   W={W}   chunks={len(chunks)}\n")
    print("trajectory-level:")
    for key, value in result.scalars.items():
        print(f"  {key:32s} {value:.4f}")

    print(
        f"\nacross the split at t = {args.split_token:,} tokens "
        f"({args.split_token / W:.1f} turnovers):"
    )
    print(compare_segments(result, split_token=args.split_token).to_string(index=False))

    before = chunks[chunks["token_end"] < args.split_token]
    after = chunks[chunks["token_end"] >= args.split_token]
    for label, block in (("BEFORE", before.tail(1)), ("AFTER", after.head(1))):
        if block.empty:
            continue
        row = block.iloc[0]
        text = " ".join(str(row["text"]).split())
        print(f"\n--- {label} (chunk {int(row['chunk_index'])}, t={int(row['token_end']):,}) ---")
        print(text[: args.sample_chars])

    verdict = compare_segments(result, split_token=args.split_token).set_index("metric")
    repetition_rose = verdict.loc["ngram_repetition", "delta"] > 0.1
    entropy_fell = verdict.loc["unigram_entropy_bits", "delta"] < -0.5
    print()
    if repetition_rose or entropy_fell:
        print("VERDICT: consistent with degeneracy -- repetition rose and/or entropy fell.")
    elif np.isclose(verdict.loc["ngram_repetition", "delta"], 0.0, atol=0.1):
        print(
            "VERDICT: consistent with a metastable transition -- surface statistics are "
            "unchanged across the jump, so the move is not a collapse."
        )
    else:
        print("VERDICT: ambiguous; read the samples above.")


if __name__ == "__main__":
    main()
