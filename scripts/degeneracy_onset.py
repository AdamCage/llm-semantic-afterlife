"""When does a trajectory collapse, and is there a usable window before it?

If degeneracy sets in immediately, the protocol produces nothing measurable about
semantic dynamics. If it sets in after several turnovers, the pre-collapse
segment is still a valid observation window and the collapse itself becomes a
measurable endpoint -- a "time to degeneracy" that is a legitimate quantity in
its own right.

Prints a turnover-binned profile of the degeneracy indicators and locates the
onset as the first turnover after which repetition stays above threshold.
"""

from __future__ import annotations

import argparse

import pandas as pd

from semantic_afterlife.analysis.degeneracy import DegeneracyParams, compute_degeneracy
from semantic_afterlife.config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("--bin-turnovers", type=float, default=2.0)
    args = parser.parse_args()

    settings = get_settings()
    run = settings.paths.find_run(args.run_id)
    chunks = pd.read_parquet(run.chunks()).sort_values("chunk_index").reset_index(drop=True)
    params = DegeneracyParams()

    pd.set_option("display.width", 170)
    for trajectory_id, block in chunks.groupby("trajectory_id", sort=True):
        block = block.sort_values("chunk_index")
        W = int(block["W"].iloc[0])
        result = compute_degeneracy(
            block["text"].tolist(),
            trajectory_id=str(trajectory_id),
            token_ends=block["token_end"].to_numpy(),
            W=W,
            params=params,
        )
        frame = result.per_chunk.copy()
        frame["bin"] = (frame["turnover"] // args.bin_turnovers) * args.bin_turnovers
        profile = (
            frame.groupby("bin")
            .agg(
                chunks=("chunk_index", "size"),
                repetition=("ngram_repetition", "mean"),
                type_token=("type_token_ratio", "mean"),
                entropy=("unigram_entropy_bits", "mean"),
                compression=("compression_ratio", "mean"),
                looping=("looping", "mean"),
            )
            .reset_index()
        )

        # Onset: the first bin from which looping never again drops below half.
        onset = None
        for index in range(len(profile)):
            if (profile["looping"].iloc[index:] >= 0.5).all():
                onset = float(profile["bin"].iloc[index])
                break

        print(f"\n=== {trajectory_id}  (W={W}, {len(block)} chunks) ===")
        print(profile.to_string(index=False))
        if onset is None:
            print("\nno sustained collapse detected")
        else:
            usable = frame[frame["turnover"] < onset]
            post_horizon_usable = usable[usable["turnover"] > 1.0]
            print(
                f"\ncollapse onset: turnover {onset:.0f}"
                f"  |  usable post-horizon window: turnovers 1 to {onset:.0f}"
                f"  ({len(post_horizon_usable)} chunks)"
            )


if __name__ == "__main__":
    main()
