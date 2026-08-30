"""Analysis passes: pure functions over trajectory embeddings.

No module here performs network I/O or writes files. Runners and exporters do
that. The split is what lets every estimator be tested against a synthetic
process with a known answer before it touches real data.
"""

from __future__ import annotations

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

__all__ = [
    "GeometryParams",
    "GeometryResult",
    "aggregate_msd",
    "compute_geometry",
    "fit_msd_exponent",
    "mean_squared_displacement",
    "recurrence_matrix",
    "recurrence_quantification",
]
