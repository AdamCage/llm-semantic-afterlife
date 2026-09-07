#!/usr/bin/env python3
"""TMLR P0 artifacts from committed tables. No generate, no embed.

ADR-0020. Per-temperature Stage 2 rates, F4 seed-pair leave-one-out and
within-pair randomisation, and quarantine of invalid F6 CI columns.
Spend is $0. Occupancy embedding parquet is not required.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from semantic_afterlife.analysis.occupancy import (
    OCCUPANCY_SPACE_ORDER,
    last_band_gap_from_matrix,
    leave_one_seed_out_gaps,
    quarantine_f6_ci_columns,
    within_pair_randomization,
)
from semantic_afterlife.analysis.rates import grouped_rates
from semantic_afterlife.provenance import git_state
from semantic_afterlife.reporting.tables import save_table
from semantic_afterlife.viz.export import FigureMeta

ROOT = Path(__file__).resolve().parents[1]
S2_AXIS = ROOT / "artifacts/stage-2/model-axis/rates"
S2_SCALARS = ROOT / "artifacts/stage-2/model-axis/geometry-bge-m3/geometry_scalars.csv"
S6_MATRIX = ROOT / "artifacts/stage-6/occupancy/last_band_distance_matrix.csv"
TMLR = ROOT / "artifacts/tmlr-correctness"
S6_OCC = ROOT / "artifacts/stage-6/occupancy"

S2_RUN_IDS = [
    "s2-model-axis-20260901T015457Z-ab59afc8",
    "s2-rates-20260901T125506Z-41d2e88e",
]
F4_RUN_IDS = [
    "s5-lock-occupancy-20260905T164327Z-6780902f",
    "s5-embed-lock-occupancy-20260906T030125Z-eab6e484",
    "s6-embed-third-space-20260906T082301Z-588eff8f",
]
F6_TABLES = (
    ROOT / "artifacts/stage-5/occupancy/twin_last_band.csv",
    ROOT / "artifacts/stage-5/occupancy/twin_per_band.csv",
    ROOT / "artifacts/stage-6/occupancy/twin_last_band.csv",
    ROOT / "artifacts/stage-6/occupancy/twin_per_band.csv",
)
F6_QUARANTINE_NOTE = (
    "ADR-0020: invalid CI columns used set(chosen) and are not bootstrap "
    "intervals; they live in the sibling *.legacy_invalid.csv sidecar. "
    "Canonical table keeps point Δ. Do not treat the sidecar as a CI."
)


def _git_sha() -> str | None:
    return git_state(ROOT).get("sha")


def _stage2_per_temperature() -> pd.DataFrame:
    scalars = pd.read_csv(S2_SCALARS)
    rates = grouped_rates(
        scalars,
        flag_column="at_fixed_point",
        group_columns=["generator", "temperature"],
    )
    rates["k_over_n"] = [
        f"{int(row.n_positive)}/{int(row.n)}" for row in rates.itertuples(index=False)
    ]
    rates["temperature"] = rates["temperature"].astype(float)
    return rates.sort_values(["generator", "temperature"]).reset_index(drop=True)


def _write_stage2(rates: pd.DataFrame, git_sha: str | None) -> None:
    save_table(
        rates,
        S2_AXIS,
        FigureMeta(
            name="fixed_point_rates_by_temperature",
            caption=(
                "Stage 2 model-axis repetition-lock rates split by temperature. "
                "Each cell is n=4 except or-gpt-oss-20b, which did not complete "
                "the design T. 95% Clopper–Pearson. The pooled n=8 table "
                "fixed_point_rates.csv remains; it is not a T=0.3 table."
            ),
            run_ids=S2_RUN_IDS,
            git_sha=git_sha,
            limitations=(
                "Pooled 0/8, 7/8, 8/8 mix T=0.3 with T=1.0. Direction (F2) is "
                "still gemma versus 120B. Qwen is 3/4 at T=0.3 and 4/4 at T=1.0; "
                "the pooled 7/8 interval that includes 0.5 is not a T=0.3 claim. "
                "Lock flag is at_fixed_point on geometry_scalars.csv, the same "
                "column as the pooled table."
            ),
        ),
    )


def _space_blocks(matrix: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    blocks: list[tuple[str, pd.DataFrame]] = []
    for space in OCCUPANCY_SPACE_ORDER:
        block = matrix.loc[matrix["embedding"].astype(str) == space].copy()
        if block.empty:
            raise SystemExit(f"missing embedding {space} in {S6_MATRIX}")
        blocks.append((space, block))
    return blocks


def _write_f4(git_sha: str | None) -> None:
    matrix = pd.read_csv(S6_MATRIX)
    loo_parts: list[pd.DataFrame] = []
    rand_rows: list[dict[str, object]] = []
    gap_rows: list[dict[str, object]] = []
    for space, block in _space_blocks(matrix):
        stats = last_band_gap_from_matrix(block)
        gap_rows.append({"embedding": space, **stats, "method": "unique_finite_seed_pairs"})
        loo = leave_one_seed_out_gaps(block)
        loo.insert(0, "embedding", space)
        loo_parts.append(loo)
        rand = within_pair_randomization(block, n_perm=9999, seed=0)
        rand_rows.append({"embedding": space, **rand})
    gaps = pd.DataFrame(gap_rows)
    loo_frame = pd.concat(loo_parts, ignore_index=True)
    rand_frame = pd.DataFrame(rand_rows)
    caption_gap = (
        "F4 last-band gap from the committed seed-pair matrix: unweighted mean "
        "of finite within-seed diagonals versus unordered between-seed pairs. "
        "Inferential target is ten fixed seed texts, not a domain population. "
        "Trajectory-bootstrap CIs are not recomputed here (embeddings absent)."
    )
    limitations = (
        "physics s1 has no last-band within diagonal (n_within_pairs=9). "
        "Leave-one-seed-out and within-pair randomisation are tests on these "
        "ten texts. They do not replace trajectory-bootstrap CIs. Do not read "
        "a cluster count off UMAP. Domain ≡ seed instance (ADR-0020)."
    )
    for out_dir in (TMLR, S6_OCC):
        save_table(
            gaps,
            out_dir,
            FigureMeta(
                name="occupancy_seed_pair_gap",
                caption=caption_gap,
                run_ids=F4_RUN_IDS,
                git_sha=git_sha,
                limitations=limitations,
            ),
        )
        save_table(
            loo_frame,
            out_dir,
            FigureMeta(
                name="occupancy_leave_one_seed_out",
                caption=(
                    "Leave-one-seed-out F4 gaps on the committed last-band "
                    "seed-pair matrix. Each row drops one of the ten seed texts "
                    "and recomputes mean(between) − mean(within) on the rest."
                ),
                run_ids=F4_RUN_IDS,
                git_sha=git_sha,
                limitations=limitations,
            ),
        )
        save_table(
            rand_frame,
            out_dir,
            FigureMeta(
                name="occupancy_within_pair_randomization",
                caption=(
                    "Within-pair randomisation on unique finite seed pairs. "
                    "Each permutation assigns the observed number of within-pairs "
                    "at random. p = (1+n_extreme)/(1+n_perm), n_perm=9999, seed=0. "
                    "One-sided on gap. Not a trajectory bootstrap."
                ),
                run_ids=F4_RUN_IDS,
                git_sha=git_sha,
                limitations=limitations,
            ),
        )


def _quarantine_one(path: Path, git_sha: str | None) -> None:
    frame = pd.read_csv(path)
    canonical, legacy = quarantine_f6_ci_columns(frame)
    meta_path = path.with_suffix(".meta.json")
    previous = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
    limitations = str(previous.get("limitations") or "")
    if "ADR-0020" not in limitations:
        limitations = (limitations + " " + F6_QUARANTINE_NOTE).strip()
    caption = str(previous.get("caption") or path.stem)
    if "legacy_invalid" not in caption:
        caption = caption.rstrip(".") + ". Invalid CI columns: sibling *.legacy_invalid.csv."
    run_ids = [str(item) for item in previous.get("run_ids") or []]
    save_table(
        canonical,
        path.parent,
        FigureMeta(
            name=path.stem,
            caption=caption,
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=limitations,
        ),
    )
    legacy_name = f"{path.stem}.legacy_invalid"
    save_table(
        legacy,
        path.parent,
        FigureMeta(
            name=legacy_name,
            caption=(
                f"Quarantined F6 CI columns from {path.stem}. Not bootstrap "
                "intervals (ADR-0019 set(chosen)). Kept so the withdrawn numbers "
                "remain inspectable. Do not cite as CIs."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=F6_QUARANTINE_NOTE,
        ),
    )


def main() -> None:
    git_sha = _git_sha()
    TMLR.mkdir(parents=True, exist_ok=True)
    rates = _stage2_per_temperature()
    _write_stage2(rates, git_sha)
    _write_f4(git_sha)
    for path in F6_TABLES:
        if not path.is_file():
            raise SystemExit(f"missing {path}")
        _quarantine_one(path, git_sha)
    index = TMLR / "INDEX.md"
    extra = (
        "\n\n## ADR-0020 P0 tables\n\n"
        "- [`fixed_point_rates_by_temperature.csv`](../stage-2/model-axis/rates/fixed_point_rates_by_temperature.csv) "
        "— Stage 2 lock rates per temperature (`n=4`).\n"
        "- [`occupancy_seed_pair_gap.csv`](occupancy_seed_pair_gap.csv) — matrix F4 points.\n"
        "- [`occupancy_leave_one_seed_out.csv`](occupancy_leave_one_seed_out.csv) — leave-one-seed-out.\n"
        "- [`occupancy_within_pair_randomization.csv`](occupancy_within_pair_randomization.csv) "
        "— within-pair randomisation.\n"
        "- F6 canonical CSVs no longer carry `delta_ci_*`; sidecars are "
        "`*.legacy_invalid.csv` under `artifacts/stage-5/occupancy/` and "
        "`artifacts/stage-6/occupancy/`.\n"
        "- Trajectory-bootstrap F4 CIs are **not** recomputed (occupancy embeddings absent).\n"
    )
    text = index.read_text(encoding="utf-8") if index.is_file() else "# TMLR correctness\n"
    if "ADR-0020 P0 tables" not in text:
        index.write_text(text.rstrip() + extra, encoding="utf-8")


if __name__ == "__main__":
    main()
