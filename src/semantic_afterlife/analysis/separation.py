"""Does seed identity survive the context horizon?

This is the measurement Stage 1 exists to make. The naive version -- "trajectories
started from different seeds are far apart in embedding space" -- says nothing,
because two trajectories from the *same* seed are also far apart: they diverge
through sampling noise alone. The quantity that means something is the contrast:

    D_within(t)   distance between trajectories sharing a semantic seed,
                  differing only in their stochastic seed
    D_between(t)  distance between trajectories from different semantic seeds
    gap(t)        D_between(t) - D_within(t)

``D_within`` is the control. A positive gap past the context horizon means the
seed still shapes the trajectory after it has physically left the model's input;
a gap indistinguishable from zero means it does not. Everything else in this
module exists to put an honest confidence interval on that number.

Two methodological constraints are enforced rather than left to the caller:

* **The replicate unit is the trajectory.** Pairs are not independent -- one
  trajectory appears in many of them -- so bootstrapping over pairs would shrink
  the interval by a factor related to the number of pairs rather than the number
  of trajectories. Resampling is over trajectories, and pairs are recomputed
  from each resample.
* **Comparisons are at matched positions.** Trajectories are compared chunk index
  by chunk index, never pooled across time, because both distances drift.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from ..embeddings.client import l2_normalise
from ..errors import AnalysisError


class SeparationParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    n_boot: int = Field(default=2000, ge=100)
    alpha: float = Field(default=0.05, gt=0.0, lt=0.5)
    seed: int = Field(default=0)
    turnover_bin: float = Field(
        default=2.0,
        gt=0.0,
        description="width of the turnover bands the contrast is reported in; chunk-level "
        "resolution is noisy and the question is about trend, not individual chunks",
    )
    min_pairs: int = Field(
        default=3,
        ge=1,
        description="a band with fewer pairs than this is reported as missing rather than "
        "as an estimate",
    )


@dataclass(slots=True)
class Trajectory:
    """One trajectory's embeddings plus the labels that define the contrast."""

    trajectory_id: str
    semantic_seed: str
    stochastic_seed: int
    embeddings: np.ndarray  # (n_chunks, d)
    turnovers: np.ndarray  # (n_chunks,)

    def __post_init__(self) -> None:
        if self.embeddings.ndim != 2:
            raise AnalysisError(f"{self.trajectory_id}: expected a 2-D embedding matrix")
        if self.embeddings.shape[0] != self.turnovers.size:
            raise AnalysisError(
                f"{self.trajectory_id}: {self.embeddings.shape[0]} embeddings but "
                f"{self.turnovers.size} turnover positions"
            )


@dataclass(slots=True)
class SeparationResult:
    per_band: pd.DataFrame
    pairs: pd.DataFrame
    scalars: dict[str, float]


def _cosine_distance_rows(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Row-wise ``1 - cos`` between two aligned matrices."""
    an, bn = l2_normalise(a.astype(np.float64)), l2_normalise(b.astype(np.float64))
    return 1.0 - np.einsum("ij,ij->i", an, bn)


def pairwise_distances(trajectories: list[Trajectory]) -> pd.DataFrame:
    """Chunk-aligned distance for every trajectory pair, labelled within/between.

    Pairs are truncated to their shorter member: a trajectory that stopped early
    must not silently extend a comparison past where it has data.
    """
    if len(trajectories) < 2:
        raise AnalysisError("the contrast needs at least two trajectories")

    rows: list[pd.DataFrame] = []
    for left, right in itertools.combinations(trajectories, 2):
        n = min(left.embeddings.shape[0], right.embeddings.shape[0])
        if n == 0:
            continue
        same_seed = left.semantic_seed == right.semantic_seed
        rows.append(
            pd.DataFrame(
                {
                    "left": left.trajectory_id,
                    "right": right.trajectory_id,
                    "kind": "within" if same_seed else "between",
                    "semantic_left": left.semantic_seed,
                    "semantic_right": right.semantic_seed,
                    "chunk_index": np.arange(n, dtype=np.int64),
                    "turnover": left.turnovers[:n],
                    "distance": _cosine_distance_rows(left.embeddings[:n], right.embeddings[:n]),
                }
            )
        )
    if not rows:
        raise AnalysisError("no comparable chunks across trajectories")
    return pd.concat(rows, ignore_index=True)


def _band_gap(pairs: pd.DataFrame) -> tuple[float, float, float, int, int]:
    within = pairs.loc[pairs["kind"] == "within", "distance"]
    between = pairs.loc[pairs["kind"] == "between", "distance"]
    if within.empty or between.empty:
        return (np.nan, np.nan, np.nan, len(within), len(between))
    return (
        float(between.mean() - within.mean()),
        float(within.mean()),
        float(between.mean()),
        len(within),
        len(between),
    )


def compute_separation(
    trajectories: list[Trajectory], *, params: SeparationParams
) -> SeparationResult:
    """The ``D_between`` versus ``D_within`` contrast, with a trajectory bootstrap.

    Requires at least two semantic seeds and at least one semantic seed carrying
    two stochastic repetitions -- without the latter there is no ``D_within``, and
    without a control the contrast is not interpretable.
    """
    semantic_seeds = {t.semantic_seed for t in trajectories}
    if len(semantic_seeds) < 2:
        raise AnalysisError("need at least two distinct semantic seeds")
    repeats = pd.Series([t.semantic_seed for t in trajectories]).value_counts()
    if int(repeats.max()) < 2:
        raise AnalysisError(
            "no semantic seed has two stochastic repetitions, so D_within cannot be formed; "
            "the contrast would have no control"
        )

    pairs = pairwise_distances(trajectories)
    pairs["band"] = (pairs["turnover"] // params.turnover_bin) * params.turnover_bin

    rng = np.random.default_rng(params.seed)
    index = {t.trajectory_id: i for i, t in enumerate(trajectories)}
    n_traj = len(trajectories)

    records: list[dict[str, float | int | bool]] = []
    for band, block in pairs.groupby("band", sort=True):
        gap, within, between, n_within, n_between = _band_gap(block)
        if n_within < params.min_pairs or n_between < params.min_pairs:
            continue

        # Resample trajectories, then keep the pairs both of whose members were
        # drawn. This preserves the dependency structure that makes a pair-level
        # bootstrap wrong.
        boots = np.empty(params.n_boot, dtype=np.float64)
        left_idx = block["left"].map(index).to_numpy()
        right_idx = block["right"].map(index).to_numpy()
        is_within = (block["kind"] == "within").to_numpy()
        distances = block["distance"].to_numpy()
        for b in range(params.n_boot):
            drawn = rng.integers(0, n_traj, size=n_traj)
            counts = np.bincount(drawn, minlength=n_traj)
            weight = counts[left_idx] * counts[right_idx]
            w_within, w_between = weight * is_within, weight * ~is_within
            if w_within.sum() == 0 or w_between.sum() == 0:
                boots[b] = np.nan
                continue
            boots[b] = (distances * w_between).sum() / w_between.sum() - (
                distances * w_within
            ).sum() / w_within.sum()
        finite = boots[np.isfinite(boots)]
        low, high = (
            (
                float(np.quantile(finite, params.alpha / 2)),
                float(np.quantile(finite, 1 - params.alpha / 2)),
            )
            if finite.size >= 20
            else (np.nan, np.nan)
        )
        records.append(
            {
                "band": float(band),
                "d_within": within,
                "d_between": between,
                "gap": gap,
                "gap_ci_low": low,
                "gap_ci_high": high,
                "separated": bool(np.isfinite(low) and low > 0.0),
                "n_within_pairs": n_within,
                "n_between_pairs": n_between,
                "n_boot_valid": int(finite.size),
            }
        )

    if not records:
        raise AnalysisError(
            "no turnover band had enough pairs of both kinds; more trajectories or a wider "
            "turnover_bin are needed"
        )
    per_band = pd.DataFrame(records)

    post = per_band[per_band["band"] >= 1.0]
    reference = post if not post.empty else per_band
    scalars = {
        "n_trajectories": float(n_traj),
        "n_semantic_seeds": float(len(semantic_seeds)),
        "gap_post_horizon_mean": float(reference["gap"].mean()),
        "gap_first_post_horizon_band": float(reference["gap"].iloc[0]),
        "gap_last_band": float(reference["gap"].iloc[-1]),
        "bands_separated_fraction": float(reference["separated"].mean()),
        "separated_at_last_band": float(bool(reference["separated"].iloc[-1])),
        # A negative trend means the seed's influence is decaying; the rate is
        # what Stage 2 turns into a half-life.
        "gap_trend_per_turnover": _slope(reference["band"].to_numpy(), reference["gap"].to_numpy()),
    }
    return SeparationResult(per_band=per_band, pairs=pairs, scalars=scalars)


def _slope(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 3:
        return 0.0
    x, y = x[mask], y[mask]
    xc = x - x.mean()
    denominator = float(xc @ xc)
    return float((xc @ (y - y.mean())) / denominator) if denominator else 0.0


def trajectories_from_frame(
    frame: pd.DataFrame, *, embedding_columns: list[str] | None = None
) -> list[Trajectory]:
    """Build trajectories from an ``embeddings_*.parquet`` table."""
    columns = embedding_columns or [
        c for c in frame.columns if c.startswith("e") and c[1:].isdigit()
    ]
    if not columns:
        raise AnalysisError("no embedding columns found")
    out: list[Trajectory] = []
    for trajectory_id, block in frame.groupby("trajectory_id", sort=True):
        block = block.sort_values("chunk_index")
        out.append(
            Trajectory(
                trajectory_id=str(trajectory_id),
                semantic_seed=str(block["semantic_seed"].iloc[0]),
                stochastic_seed=int(block["stochastic_seed"].iloc[0]),
                embeddings=block[columns].to_numpy(dtype=np.float64),
                turnovers=block["turnover"].to_numpy(dtype=np.float64),
            )
        )
    return out
