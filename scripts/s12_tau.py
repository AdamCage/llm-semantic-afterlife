"""Clock for the S12 escape table.

The continuation is not a new trajectory. L0 already reached 12 turnovers
with a confirmed lock at 0.75, so continuation turnovers are shifted by that
horizon before ``prefix_lock_escape`` sees them. An escape later than the
common ``T_min`` is censored.
"""

from __future__ import annotations

import numpy as np

L0_TOKENS = 49152
W = 4096
HORIZON_TURNOVERS = L0_TOKENS / W  # 12.0
LOCK_TURNOVER = 0.75


def concatenate_clock(
    l0_turnovers: np.ndarray,
    l0_looping: np.ndarray,
    cont_turnovers: np.ndarray,
    cont_looping: np.ndarray,
    *,
    horizon: float = HORIZON_TURNOVERS,
) -> tuple[np.ndarray, np.ndarray]:
    """Absolute turnovers from the start of L0, L0 rows then the continuation."""
    if l0_turnovers.shape != l0_looping.shape:
        raise ValueError("L0 flags and turnovers must align")
    if cont_turnovers.shape != cont_looping.shape:
        raise ValueError("continuation flags and turnovers must align")
    if l0_turnovers.size == 0:
        raise ValueError("L0 series is empty")
    turnovers = np.concatenate(
        [np.asarray(l0_turnovers, dtype=np.float64), np.asarray(cont_turnovers, dtype=np.float64) + horizon]
    )
    flags = np.concatenate(
        [np.asarray(l0_looping, dtype=bool), np.asarray(cont_looping, dtype=bool)]
    )
    order = np.argsort(turnovers, kind="mergesort")
    return turnovers[order], flags[order]


def confirmed_through_tmin(tau_escape: float | None, t_min: float) -> bool:
    """True only when the escape is at or before the common horizon."""
    if tau_escape is None:
        return False
    return float(tau_escape) <= float(t_min) + 1e-9
