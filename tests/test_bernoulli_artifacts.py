"""Committed Stage 2/4 rate tables use Clopper–Pearson, not [0, 0] / [1, 1]."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from semantic_afterlife.analysis.rates import clopper_pearson_ci

ROOT = Path(__file__).resolve().parents[1]


def test_stage2_zero_and_all_success_are_not_point_masses() -> None:
    frame = pd.read_csv(ROOT / "artifacts/stage-2/model-axis/rates/fixed_point_rates.csv")
    gemma = frame.loc[frame["generator"] == "or-gemma-4-31b"].iloc[0]
    oss = frame.loc[frame["generator"] == "or-gpt-oss-120b"].iloc[0]
    assert int(gemma["n_positive"]) == 0
    assert int(gemma["n"]) == 8
    assert float(gemma["ci_low"]) == 0.0
    assert float(gemma["ci_high"]) == pytest.approx(0.3694166475528192)
    assert float(gemma["ci_high"]) > 0.0
    assert int(oss["n_positive"]) == 8
    assert float(oss["ci_low"]) == pytest.approx(0.6305833524471808)
    assert float(oss["ci_high"]) == 1.0
    assert float(oss["ci_low"]) < 1.0


def test_stage4_four_of_four_is_not_one_one() -> None:
    frame = pd.read_csv(ROOT / "artifacts/stage-4/grid/looping_rate_by_cell.csv")
    locked = frame.loc[(frame["W"] == 4096) & (frame["temperature"] == 0.3)].iloc[0]
    open_cell = frame.loc[(frame["W"] == 4096) & (frame["temperature"] == 1.5)].iloc[0]
    assert int(locked["n_degenerate"]) == 4
    low, high = clopper_pearson_ci(4, 4)
    assert float(locked["ci_low"]) == pytest.approx(low)
    assert float(locked["ci_high"]) == pytest.approx(high)
    assert not (float(locked["ci_low"]) == 1.0 and float(locked["ci_high"]) == 1.0)
    assert int(open_cell["n_degenerate"]) == 0
    low0, high0 = clopper_pearson_ci(0, 4)
    assert float(open_cell["ci_low"]) == pytest.approx(low0)
    assert float(open_cell["ci_high"]) == pytest.approx(high0)
    assert float(open_cell["ci_high"]) > 0.0


def test_stage4_contrasts_name_fisher() -> None:
    path = ROOT / "artifacts/stage-4/grid/looping_rate_contrasts.csv"
    frame = pd.read_csv(path)
    w4096 = frame.loc[frame["W"] == 4096].iloc[0]
    assert float(w4096["fisher_p"]) == pytest.approx(0.028571428571428567)
    assert "fisher" in str(w4096["method"])


def test_headline_audit_signs_and_lock() -> None:
    report = json.loads(
        (ROOT / "artifacts/tmlr-correctness/headline_audit.json").read_text(encoding="utf-8")
    )
    assert all(row["sign_agrees"] for row in report["f4_points"])
    by_space = {row["embedding"]: row for row in report["f4_points"]}
    assert by_space["bge-m3"]["published_gap"] == pytest.approx(0.201, abs=5e-4)
    assert by_space["qwen3-embed-8b"]["published_gap"] == pytest.approx(0.390, abs=5e-4)
    assert by_space["gemini-embed-001"]["published_gap"] == pytest.approx(0.150, abs=5e-4)
    assert all(row["csv_matches"] for row in report["bernoulli"])
    assert report["lock"]["k_over_n"] == "19/20"
    assert report["lock"]["seeds_with_a_lock"] == "10/10"
    assert report["f6"]["status"] == "bootstrap_invalid_until_embeddings"
