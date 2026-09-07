"""ADR-0020 P0 tables: per-T Stage 2 rates, F4 seed-pair tests, F6 quarantine."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from semantic_afterlife.analysis.occupancy import F6_INVALID_CI_COLUMNS
from semantic_afterlife.analysis.rates import clopper_pearson_ci

ROOT = Path(__file__).resolve().parents[1]
S2 = ROOT / "artifacts/stage-2/model-axis/rates"
TMLR = ROOT / "artifacts/tmlr-correctness"


def test_stage2_per_temperature_is_n4_not_pooled_t03() -> None:
    frame = pd.read_csv(S2 / "fixed_point_rates_by_temperature.csv")
    qwen_03 = frame.loc[
        (frame["generator"] == "or-qwen3-8b") & (frame["temperature"] == 0.3)
    ].iloc[0]
    qwen_1 = frame.loc[
        (frame["generator"] == "or-qwen3-8b") & (frame["temperature"] == 1.0)
    ].iloc[0]
    gemma_03 = frame.loc[
        (frame["generator"] == "or-gemma-4-31b") & (frame["temperature"] == 0.3)
    ].iloc[0]
    oss_03 = frame.loc[
        (frame["generator"] == "or-gpt-oss-120b") & (frame["temperature"] == 0.3)
    ].iloc[0]
    assert int(qwen_03["n"]) == 4
    assert int(qwen_03["n_positive"]) == 3
    assert int(qwen_1["n_positive"]) == 4
    assert int(gemma_03["n_positive"]) == 0
    assert int(oss_03["n_positive"]) == 4
    low, high = clopper_pearson_ci(3, 4)
    assert float(qwen_03["ci_low"]) == pytest.approx(low, abs=1e-5)
    assert float(qwen_03["ci_high"]) == pytest.approx(high, abs=1e-5)
    pooled = pd.read_csv(S2 / "fixed_point_rates.csv")
    qwen_pooled = pooled.loc[pooled["generator"] == "or-qwen3-8b"].iloc[0]
    assert int(qwen_pooled["n"]) == 8
    assert int(qwen_pooled["n_positive"]) == 7


def test_f4_randomization_and_loo_are_seed_texts_not_umap() -> None:
    rand = pd.read_csv(TMLR / "occupancy_within_pair_randomization.csv")
    loo = pd.read_csv(TMLR / "occupancy_leave_one_seed_out.csv")
    gaps = pd.read_csv(TMLR / "occupancy_seed_pair_gap.csv")
    assert set(rand["embedding"]) == {"bge-m3", "qwen3-embed-8b", "gemini-embed-001"}
    assert (rand["n_perm"] == 9999).all()
    assert (rand["p_value"] <= 0.001).all()
    assert (rand["n_extreme"] == 0).all()
    assert (loo["gap"] > 0.12).all()
    by_space = {row.embedding: row.gap for row in gaps.itertuples(index=False)}
    assert by_space["bge-m3"] == pytest.approx(0.201, abs=0.002)
    assert by_space["qwen3-embed-8b"] == pytest.approx(0.390, abs=0.002)
    assert by_space["gemini-embed-001"] == pytest.approx(0.150, abs=0.002)
    meta = (TMLR / "occupancy_within_pair_randomization.meta.json").read_text(encoding="utf-8")
    assert "Do not read a cluster count off UMAP" in meta


def test_f6_canonical_has_no_ci_columns() -> None:
    for folder in (
        ROOT / "artifacts/stage-5/occupancy",
        ROOT / "artifacts/stage-6/occupancy",
    ):
        for stem in ("twin_last_band", "twin_per_band"):
            canonical = pd.read_csv(folder / f"{stem}.csv")
            legacy = pd.read_csv(folder / f"{stem}.legacy_invalid.csv")
            for column in F6_INVALID_CI_COLUMNS:
                assert column not in canonical.columns
            assert "delta" in canonical.columns
            assert "divergent" in canonical.columns
            assert "delta_ci_low" in legacy.columns
            assert "delta_ci_high" in legacy.columns
            assert "delta" in legacy.columns
