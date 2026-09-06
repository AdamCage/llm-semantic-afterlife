"""Stage 6 occupancy artifacts: three spaces, F4/F6 split held."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from semantic_afterlife.analysis.occupancy import DOMAIN_SEED_ORDER, TWIN_SEED_ORDER

ROOT = Path("artifacts/stage-6/occupancy")


def test_gemini_grid_is_20_domain_plus_8_twin() -> None:
    grid = pd.read_csv(ROOT / "gemini_grid_counts.csv")
    assert int(grid["gemini_domain_trajectories"].iloc[0]) == 20
    assert int(grid["gemini_twin_trajectories"].iloc[0]) == 8


def test_last_band_has_three_spaces_and_gemini_separated() -> None:
    last = pd.read_csv(ROOT / "domain_separation_last_band.csv")
    assert set(last["embedding"]) == {"bge-m3", "qwen3-embed-8b", "gemini-embed-001"}
    gemini = last.loc[last["embedding"] == "gemini-embed-001"].iloc[0]
    assert int(gemini["n_trajectories"]) == 20
    assert bool(gemini["separated"])
    assert float(gemini["gap_ci_low"]) > 0.0


def test_twins_not_in_domain_matrix() -> None:
    matrix = pd.read_csv(ROOT / "last_band_distance_matrix.csv")
    gemini = matrix.loc[matrix["embedding"] == "gemini-embed-001"]
    seeds = set(gemini["seed_row"].astype(str)) | set(gemini["seed_col"].astype(str))
    assert seeds <= set(DOMAIN_SEED_ORDER)
    assert seeds.isdisjoint(set(TWIN_SEED_ORDER))


def test_gemini_twin_last_band_operational_collapsed() -> None:
    twin = pd.read_csv(ROOT / "twin_last_band.csv")
    gemini = twin.loc[twin["embedding"] == "gemini-embed-001"]
    assert not gemini.empty
    assert not gemini["divergent"].astype(bool).any()
    meta = json.loads((ROOT / "twin_last_band.meta.json").read_text(encoding="utf-8"))
    assert "not occupancy of one lock" in str(meta["limitations"])
