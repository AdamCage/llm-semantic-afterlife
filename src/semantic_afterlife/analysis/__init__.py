"""Analysis passes: pure functions over trajectory embeddings.

No module here performs network I/O or writes files. Runners and exporters do
that. The split is what lets every estimator be tested against a synthetic
process with a known answer before it touches real data.
"""

from __future__ import annotations

from .degeneracy import DegeneracyParams, DegeneracyResult, compute_degeneracy
from .geometry import (
    GeometryParams,
    GeometryResult,
    aggregate_msd,
    compute_geometry,
    fit_msd_exponent,
    mean_squared_displacement,
    recurrence_matrix,
    recurrence_quantification,
)
from .rates import (
    grouped_rates,
    parse_trajectory_id,
    quarter_diagnostics,
    rate_ci,
    rate_difference_ci,
)
from .separation import (
    SeparationParams,
    SeparationResult,
    Trajectory,
    compute_separation,
    trajectories_from_frame,
)

__all__ = [
    "DegeneracyParams",
    "DegeneracyResult",
    "GeometryParams",
    "GeometryResult",
    "SeparationParams",
    "SeparationResult",
    "Trajectory",
    "aggregate_msd",
    "compute_degeneracy",
    "compute_geometry",
    "compute_separation",
    "fit_msd_exponent",
    "grouped_rates",
    "mean_squared_displacement",
    "parse_trajectory_id",
    "quarter_diagnostics",
    "rate_ci",
    "rate_difference_ci",
    "recurrence_matrix",
    "recurrence_quantification",
    "trajectories_from_frame",
]
