"""The S12 escape clock is L0 plus the continuation, censored at T_min."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from semantic_afterlife.analysis.persistence import prefix_lock_escape

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from s12_tau import concatenate_clock, confirmed_through_tmin


def test_escape_on_the_continuation_uses_the_l0_clock() -> None:
    l0_t = np.arange(1, 49, dtype=np.float64) * 0.25  # 0.25 .. 12.0
    l0_loop = np.ones_like(l0_t, dtype=bool)
    cont_t = np.arange(1, 5, dtype=np.float64) * 0.25  # 0.25 .. 1.0
    cont_loop = np.array([False, False, False, True])
    turnovers, flags = concatenate_clock(l0_t, l0_loop, cont_t, cont_loop)
    result = prefix_lock_escape(flags, turnovers, n_confirm=3)
    assert result.tau_lock == 0.75
    # Third non-looping continuation chunk ends at absolute turnover 12.75.
    assert result.confirmed_escape
    assert result.tau_escape == 12.75


def test_escape_after_tmin_is_censored() -> None:
    assert confirmed_through_tmin(12.75, 12.5) is False
    assert confirmed_through_tmin(12.75, 12.75) is True
    assert confirmed_through_tmin(None, 20.0) is False
