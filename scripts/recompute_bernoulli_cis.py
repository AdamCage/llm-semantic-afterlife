#!/usr/bin/env python3
"""Recompute Bernoulli CIs from committed k/n without generation runs.

ADR-0019. Clopper–Pearson replaces the percentile bootstrap that published
``[0, 0]`` and ``[1, 1]``. Point counts are unchanged; only the intervals
and figure whiskers move. Spend is $0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from semantic_afterlife.analysis.rates import clopper_pearson_ci, rate_difference_ci
from semantic_afterlife.provenance import git_state
from semantic_afterlife.reporting.tables import save_table
from semantic_afterlife.viz.export import FigureMeta, save_matplotlib_figure, save_plotly_figure
from semantic_afterlife.viz.figures import rate_bar_figure

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

from assemble_stage4_grid import _plotly_rate, looping_figure  # noqa: E402

ROOT = _ROOT
S2_AXIS = ROOT / "artifacts/stage-2/model-axis/rates"
S2_MECH = ROOT / "artifacts/stage-2/mechanism/rates"
S4_GRID = ROOT / "artifacts/stage-4/grid"

F6_META_PATHS = (
    ROOT / "artifacts/stage-5/occupancy/twin_last_band.meta.json",
    ROOT / "artifacts/stage-5/occupancy/twin_per_band.meta.json",
    ROOT / "artifacts/stage-5/occupancy/twin_delta_vs_turnover.meta.json",
    ROOT / "artifacts/stage-6/occupancy/twin_last_band.meta.json",
    ROOT / "artifacts/stage-6/occupancy/twin_per_band.meta.json",
    ROOT / "artifacts/stage-6/occupancy/twin_delta_vs_turnover.meta.json",
)

F6_CI_NOTE = (
    "ADR-0019: published twin CI columns used set(chosen) and are not "
    "bootstrap intervals. Point Δ is the observed mean. Occupancy embeddings "
    "were absent from the 2026-09-01 snapshot, so CIs were not re-derived. "
    "n=2; no detected divergence is not semantic collapse."
)


def _git_sha() -> str | None:
    return git_state(ROOT).get("sha")


def _rewrite_rate_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    lows: list[float] = []
    highs: list[float] = []
    methods: list[str] = []
    for _, row in frame.iterrows():
        k = int(row["n_positive"])
        n = int(row["n"])
        low, high = clopper_pearson_ci(k, n)
        lows.append(low)
        highs.append(high)
        methods.append("clopper_pearson")
    frame["ci_low"] = lows
    frame["ci_high"] = highs
    frame["method"] = methods
    frame["rate"] = frame["n_positive"] / frame["n"]
    return frame


def _s2_axis() -> None:
    rates = _rewrite_rate_frame(S2_AXIS / "fixed_point_rates.csv")
    git_sha = _git_sha()
    run_ids = [
        "s2-model-axis-20260901T015457Z-ab59afc8",
        "s2-rates-20260901T125506Z-41d2e88e",
    ]
    caption = (
        "Fraction of trajectories labelled a textual repetition lock, with a 95% "
        "Clopper–Pearson CI. The dashed line is 0.5, the Stage 2 direction "
        "threshold (F2). 0/8 is [0, 0.369], not [0, 0]; 8/8 is [0.631, 1], not [1, 1]."
    )
    limitations = (
        "The verdict is the calibrated late-phase shingle Jaccard, not a semantic "
        "state and not an exact period-1 recurrence. Eight trajectories per generator "
        "make the interval wide on purpose. Incidence is not reproducible across seed "
        "derivations (S1.2); only the rate is. 7/8 on or-qwen3-8b now includes 0.5."
    )
    save_table(
        rates,
        S2_AXIS,
        FigureMeta(
            name="fixed_point_rates",
            caption=caption,
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=limitations,
        ),
    )
    figure, tidy, meta = rate_bar_figure(
        rates,
        group_column="generator",
        run_ids=run_ids,
        caption=caption,
        limitations=limitations,
    )
    meta.git_sha = git_sha
    save_plotly_figure(figure, S2_AXIS, meta, data=tidy)


def _s2_mech() -> None:
    rates = _rewrite_rate_frame(S2_MECH / "fixed_point_rates.csv")
    git_sha = _git_sha()
    run_ids = [
        "s2-mechanism-20260901T071519Z-dfbb173a",
        "s2-rates-20260901T125506Z-41d2e88e",
    ]
    caption = (
        "Repetition-lock rate on the Stage 2 mechanism arm, 95% Clopper–Pearson CI. "
        "raw_completion versus assistant_prefill on or-qwen3-8b."
    )
    save_table(
        rates,
        S2_MECH,
        FigureMeta(
            name="fixed_point_rates",
            caption=caption,
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=("n = 8 per mechanism. Clopper–Pearson; 8/8 is not a point mass at 1."),
        ),
    )


def _s4_grid() -> None:
    rates = pd.read_csv(S4_GRID / "looping_rate_by_cell.csv")
    lows: list[float] = []
    highs: list[float] = []
    for _, row in rates.iterrows():
        k = int(row["n_degenerate"])
        n = int(row["n"])
        low, high = clopper_pearson_ci(k, n)
        lows.append(low)
        highs.append(high)
    rates["ci_low"] = lows
    rates["ci_high"] = highs
    rates["method"] = "clopper_pearson"
    git_sha = _git_sha()
    run_ids = [
        "s2-mechanism-20260901T071519Z-dfbb173a",
        "s4-w4096-new-temps-20260904T103121Z-589c8eb1",
        "s4-w8192-20260904T120057Z-ce82ce55",
    ]
    figure, tidy, meta = looping_figure(rates, run_ids=run_ids, git_sha=git_sha)
    save_matplotlib_figure(figure, S4_GRID, meta, data=tidy)
    interactive, interactive_tidy, interactive_meta = _plotly_rate(
        rates, run_ids=run_ids, git_sha=git_sha
    )
    save_plotly_figure(interactive, S4_GRID, interactive_meta, data=interactive_tidy)
    save_table(
        rates,
        S4_GRID,
        FigureMeta(
            name="looping_rate_by_cell",
            caption=meta.caption,
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=meta.limitations,
        ),
    )

    contrasts: list[dict[str, object]] = []
    for window, block in rates.groupby("W", sort=True):
        cell_lock = block.loc[block["temperature"] == 0.3].iloc[0]
        cell_open = block.loc[block["temperature"] == 1.5].iloc[0]
        a = np.concatenate(
            [
                np.ones(int(cell_lock.n_degenerate)),
                np.zeros(int(cell_lock.n - cell_lock.n_degenerate)),
            ]
        )
        b = np.concatenate(
            [
                np.ones(int(cell_open.n_degenerate)),
                np.zeros(int(cell_open.n - cell_open.n_degenerate)),
            ]
        )
        stats = rate_difference_ci(a, b)
        contrasts.append(
            {
                "W": int(window),
                "cell_a": "T=0.3",
                "cell_b": "T=1.5",
                "k_a": int(cell_lock.n_degenerate),
                "n_a": int(cell_lock.n),
                "k_b": int(cell_open.n_degenerate),
                "n_b": int(cell_open.n),
                "diff": stats["diff"],
                "ci_low": stats["ci_low"],
                "ci_high": stats["ci_high"],
                "fisher_p": stats["fisher_p"],
                "method": "newcomb+fisher_exact",
            }
        )
    save_table(
        pd.DataFrame(contrasts),
        S4_GRID,
        FigureMeta(
            name="looping_rate_contrasts",
            caption=(
                "Newcombe 95% CI and two-sided Fisher exact p for the 4/4 lock cell "
                "(T=0.3) versus the T=1.5 cell at each W. Not a temperature law: n=4."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=(
                "4/4 vs 0/4 at W=4096 is p≈0.029; 4/4 vs 2/4 at W=8192 T=1.5 is not "
                "the same contrast. Do not read a phase diagram from n=4."
            ),
        ),
    )


def _relabel_f6_meta() -> None:
    """Captions on committed twin tables: no_detected_divergence; CIs invalid."""
    for path in F6_META_PATHS:
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        caption = str(data.get("caption") or "")
        caption = caption.replace("otherwise collapsed", "otherwise no detected divergence")
        caption = caption.replace("operational collapsed", "no detected divergence")
        data["caption"] = caption
        if data.get("alt_text"):
            data["alt_text"] = caption
        limitations = str(data.get("limitations") or "")
        limitations = limitations.replace(
            "the operational collapsed verdict",
            "no detected divergence",
        )
        if "ADR-0019" not in limitations:
            limitations = limitations.rstrip() + " " + F6_CI_NOTE
        data["limitations"] = limitations
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    _s2_axis()
    _s2_mech()
    _s4_grid()
    _relabel_f6_meta()
    print("rewrote Stage 2 and Stage 4 Bernoulli CIs (Clopper–Pearson)")
    print("relabelled F6 meta (CIs not re-bootstrapped)")


if __name__ == "__main__":
    main()
