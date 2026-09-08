"""Rate estimators recover known Bernoulli answers.

Stage 2 reports repetition-lock rates with Clopper–Pearson CIs over
trajectories. An interval that collapses to ``[0, 0]`` or ``[1, 1]`` at
small ``n`` cannot be trusted as a population probability (ADR-0019).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from semantic_afterlife.analysis.rates import (
    assign_quarter,
    clopper_pearson_ci,
    grouped_rates,
    marker_register_flag,
    parse_trajectory_id,
    quarter_diagnostics,
    rate_ci,
    rate_difference_ci,
)


def test_parse_trajectory_id_round_trip() -> None:
    parsed = parse_trajectory_id("or-qwen3-8b-prefill__W4096__T1__surreal__s2")
    assert parsed["generator"] == "or-qwen3-8b-prefill"
    assert parsed["W"] == 4096
    assert parsed["temperature"] == 1.0
    assert parsed["semantic_seed"] == "surreal"
    assert parsed["stochastic_seed"] == 2


def test_parse_trajectory_id_rejects_malformed() -> None:
    with pytest.raises(ValueError, match="unrecognised"):
        parse_trajectory_id("not-a-trajectory")


def test_rate_ci_recovers_known_proportion() -> None:
    rng = np.random.default_rng(7)
    flags = rng.binomial(1, 0.25, size=400)
    stats = rate_ci(flags, seed=1)
    assert abs(stats["rate"] - flags.mean()) < 1e-12
    assert stats["ci_low"] < 0.25 < stats["ci_high"]
    assert stats["n"] == 400
    assert stats["n_positive"] == int(flags.sum())
    assert stats["method"] == "clopper_pearson"


def test_rate_ci_all_ones_is_not_a_point_mass() -> None:
    stats = rate_ci(np.ones(8), seed=0)
    assert stats["rate"] == 1.0
    assert stats["ci_low"] == pytest.approx(0.6305833524471808)
    assert stats["ci_high"] == 1.0
    assert stats["ci_low"] < 1.0


def test_rate_ci_all_zeros_is_not_a_point_mass() -> None:
    stats = rate_ci(np.zeros(8), seed=0)
    assert stats["rate"] == 0.0
    assert stats["ci_low"] == 0.0
    assert stats["ci_high"] == pytest.approx(0.3694166475528192)
    assert stats["ci_high"] > 0.0


def test_clopper_pearson_matches_named_tables() -> None:
    low, high = clopper_pearson_ci(4, 4)
    assert low == pytest.approx(0.3976353643835254)
    assert high == 1.0
    low0, high0 = clopper_pearson_ci(0, 4)
    assert low0 == 0.0
    assert high0 == pytest.approx(0.6023646356164746)
    low19, high19 = clopper_pearson_ci(19, 20)
    assert low19 == pytest.approx(0.7512672372279723)
    assert high19 == pytest.approx(0.9987349105020502)


def test_rate_difference_ci_recovers_known_gap() -> None:
    rng = np.random.default_rng(3)
    a = rng.binomial(1, 0.8, size=300)
    b = rng.binomial(1, 0.2, size=300)
    stats = rate_difference_ci(a, b, seed=2)
    assert stats["diff"] == pytest.approx(a.mean() - b.mean())
    assert stats["ci_low"] < 0.6 < stats["ci_high"]
    assert stats["ci_low"] > 0.0
    assert stats["fisher_p"] < 1e-20


def test_rate_difference_four_vs_zero_is_not_certainty() -> None:
    stats = rate_difference_ci(np.ones(4), np.zeros(4), seed=0)
    assert stats["diff"] == 1.0
    assert stats["ci_low"] == pytest.approx(0.30718973500360847)
    assert stats["ci_high"] == 1.0
    assert stats["fisher_p"] == pytest.approx(0.028571428571428567)
    weak = rate_difference_ci(np.ones(4), np.array([1, 1, 0, 0], dtype=float), seed=0)
    assert weak["fisher_p"] == pytest.approx(0.42857142857142855)


def test_grouped_rates_one_row_per_cell() -> None:
    frame = pd.DataFrame(
        {
            "generator": ["g"] * 4 + ["h"] * 4,
            "at_fixed_point": [1, 1, 1, 0, 0, 0, 0, 1],
        }
    )
    rates = grouped_rates(frame, flag_column="at_fixed_point", group_columns=["generator"])
    assert set(rates["generator"]) == {"g", "h"}
    g = rates.set_index("generator").loc["g"]
    assert g["rate"] == 0.75
    assert g["n_positive"] == 3


def test_assign_quarter_covers_the_unit_interval() -> None:
    progress = np.array([0.0, 0.24, 0.25, 0.49, 0.5, 0.74, 0.75, 1.0])
    assert assign_quarter(progress).tolist() == [1, 1, 2, 2, 3, 3, 4, 4]


def test_quarter_diagnostics_does_not_emit_a_run_mean() -> None:
    steps = pd.DataFrame(
        {
            "trajectory_id": ["or-qwen3-8b__W4096__T0p3__physics__s1"] * 8,
            "generated_tokens": [1024 * (i + 1) for i in range(8)],
            "block_fill_ratio": [1.0, 1.0, 0.8, 0.8, 0.5, 0.5, 0.2, 0.2],
            "finish_reason": ["length"] * 6 + ["stop", "stop"],
        }
    )
    out = quarter_diagnostics(steps)
    assert set(out["quarter"]) == {1, 2, 3, 4}
    by_q = out.set_index("quarter")["block_fill"]
    assert by_q.loc[1] == pytest.approx(1.0)
    assert by_q.loc[4] == pytest.approx(0.2)
    assert "block_fill_mean" not in out.columns


def test_marker_register_flag_hits_known_openings() -> None:
    assert marker_register_flag(
        "Your passage is a deep and insightful discussion of lattice field theory."
    )
    assert not marker_register_flag(
        "the Polyakov loop expectation value remains finite in the deconfined phase."
    )
