#!/usr/bin/env python3
"""Independent recompute of headline numbers from committed tidy tables.

Does **not** import ``compute_separation`` or ``compute_twin_contrast``.
F4 bootstrap CIs cannot be re-derived without embedding parquet (the
2026-09-01 snapshot predates occupancy). The gap *point* estimate is
checked against the last-band seed-pair matrix. Bernoulli intervals are
re-derived from k/n via Clopper–Pearson. F6 published bootstrap CIs are
flagged as invalid under ADR-0019.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from semantic_afterlife.analysis.rates import clopper_pearson_ci
from semantic_afterlife.provenance import git_state

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/tmlr-correctness"


def _gap_from_matrix(matrix: pd.DataFrame) -> dict[str, float]:
    """Seed-pair means, unique unordered pairs, finite distances only."""
    within = matrix.loc[
        (matrix["kind"] == "within")
        & (matrix["seed_row"] == matrix["seed_col"])
        & matrix["distance"].notna()
    ]
    between = matrix.loc[(matrix["kind"] == "between") & (matrix["seed_row"] < matrix["seed_col"])]
    between = between.loc[between["distance"].notna()]
    d_within = float(within["distance"].mean()) if not within.empty else float("nan")
    d_between = float(between["distance"].mean()) if not between.empty else float("nan")
    return {
        "d_within": d_within,
        "d_between": d_between,
        "gap": d_between - d_within,
        "n_within_pairs": len(within),
        "n_between_pairs": len(between),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "git_sha": git_state(ROOT).get("sha"),
        "snapshot": (
            "state-latest is 2026-09-01T01:35Z and does not contain S5/S6 "
            "embedding parquet. F4 CIs and F6 CIs were not re-bootstrapped "
            "from raw embeddings in this pass."
        ),
        "f4_points": [],
        "bernoulli": [],
        "lock": {},
        "f6": {
            "status": "bootstrap_invalid_until_embeddings",
            "reason": (
                "twins.py used set(chosen), dropping resample multiplicities. "
                "Point Δ values in twin_last_band.csv are still the observed "
                "means; published CI columns are not bootstrap intervals."
            ),
        },
    }

    locks = pd.read_csv(ROOT / "artifacts/stage-5/occupancy/lock_rate_by_seed.csv")
    domain_all = locks.loc[locks["semantic_seed"] == "_domain_all"].iloc[0]
    seed_hit = locks.loc[locks["semantic_seed"] == "_domain_seeds_with_a_lock"].iloc[0]
    lock_k, lock_n = int(domain_all["n_degenerate"]), int(domain_all["n"])
    lock_low, lock_high = clopper_pearson_ci(lock_k, lock_n)
    report["lock"] = {
        "k": lock_k,
        "n": lock_n,
        "k_over_n": f"{lock_k}/{lock_n}",
        "seeds_with_a_lock": (f"{int(seed_hit['n_degenerate'])}/{int(seed_hit['n'])}"),
        "clopper_pearson": [lock_low, lock_high],
        "matches_committed": lock_k == 19 and lock_n == 20 and int(seed_hit["n_degenerate"]) == 10,
    }

    last = pd.read_csv(ROOT / "artifacts/stage-6/occupancy/domain_separation_last_band.csv")
    matrix = pd.read_csv(ROOT / "artifacts/stage-6/occupancy/last_band_distance_matrix.csv")
    for _, row in last.iterrows():
        slug = str(row["embedding"])
        piece = matrix.loc[matrix["embedding"] == slug]
        derived = _gap_from_matrix(piece)
        published = float(row["gap"])
        report["f4_points"].append(
            {
                "embedding": slug,
                "published_gap": published,
                "published_d_within": float(row["d_within"]),
                "published_d_between": float(row["d_between"]),
                "matrix_gap": derived["gap"],
                "matrix_d_within": derived["d_within"],
                "matrix_d_between": derived["d_between"],
                "sign_agrees": bool(derived["gap"] > 0 and published > 0),
                "point_abs_diff": abs(derived["gap"] - published),
            }
        )

    s2 = pd.read_csv(ROOT / "artifacts/stage-2/model-axis/rates/fixed_point_rates.csv")
    for _, row in s2.iterrows():
        k, n = int(row["n_positive"]), int(row["n"])
        low, high = clopper_pearson_ci(k, n)
        report["bernoulli"].append(
            {
                "table": "stage-2/model-axis",
                "generator": row["generator"],
                "k": k,
                "n": n,
                "csv_ci": [float(row["ci_low"]), float(row["ci_high"])],
                "clopper_pearson": [low, high],
                "csv_matches": abs(float(row["ci_low"]) - low) < 1e-6
                and abs(float(row["ci_high"]) - high) < 1e-6,
            }
        )

    s4 = pd.read_csv(ROOT / "artifacts/stage-4/grid/looping_rate_by_cell.csv")
    for _, row in s4.iterrows():
        k, n = int(row["n_degenerate"]), int(row["n"])
        low, high = clopper_pearson_ci(k, n)
        report["bernoulli"].append(
            {
                "table": "stage-4/grid",
                "W": int(row["W"]),
                "temperature": float(row["temperature"]),
                "k": k,
                "n": n,
                "csv_ci": [float(row["ci_low"]), float(row["ci_high"])],
                "clopper_pearson": [low, high],
                "csv_matches": abs(float(row["ci_low"]) - low) < 1e-6
                and abs(float(row["ci_high"]) - high) < 1e-6,
            }
        )

    out = OUT / "headline_audit.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
