"""Twin-seed contrast against the same-seed stochastic control.

Methodology §3.2. A twin pair differs in one factual proposition. The
quantity is the last-band difference

    Δ = D_twin_matched − D_control

where ``D_twin_matched`` is the mean cosine distance between the two
members of a twin pair at the *same* stochastic seed, and ``D_control``
is ``D_within`` among those members (same seed, different stochastic
seed). Bootstrap is over trajectories.

Classification at the last band:

- ``divergent`` if the 95% CI of Δ excludes 0 from above
- ``collapsed`` otherwise (CI includes 0, or Δ is negative)

``metastable`` is reserved for validated MSM macrostates and is not a
label this pass may emit.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from ..config import SeedBank
from ..errors import AnalysisError
from .separation import Trajectory, _cosine_distance_rows, _matched_regime


class TwinParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    n_boot: int = Field(default=2000, ge=100)
    alpha: float = Field(default=0.05, gt=0.0, lt=0.5)
    seed: int = Field(default=0)
    turnover_bin: float = Field(default=2.0, gt=0.0)


@dataclass(slots=True)
class TwinResult:
    per_band: pd.DataFrame
    pairs: pd.DataFrame
    scalars: dict[str, float]


def twin_pairs_from_bank(bank: SeedBank) -> list[tuple[str, str]]:
    """Return ``(canonical, variant)`` pairs from ``twin_of`` links."""
    by_id = {seed.id: seed for seed in bank.seeds}
    pairs: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    for seed in bank.seeds:
        if not seed.twin_of:
            continue
        if seed.twin_of not in by_id:
            raise AnalysisError(f"{seed.id} names unknown twin_of {seed.twin_of!r}")
        key = frozenset({seed.id, seed.twin_of})
        if key in seen:
            continue
        seen.add(key)
        pairs.append((seed.twin_of, seed.id))
    return pairs


def _pair_kind(
    left: Trajectory,
    right: Trajectory,
    twins: set[frozenset[str]],
) -> str | None:
    if left.semantic_seed == right.semantic_seed:
        return "control"
    if frozenset({left.semantic_seed, right.semantic_seed}) in twins:
        if left.stochastic_seed == right.stochastic_seed:
            return "twin_matched"
        return "twin_crossed"
    return None


def twin_pairwise_distances(
    trajectories: list[Trajectory],
    *,
    twin_pairs: list[tuple[str, str]],
) -> pd.DataFrame:
    """Chunk-aligned distances for twin-matched and same-seed control pairs."""
    if len(trajectories) < 2:
        raise AnalysisError("the twin contrast needs at least two trajectories")
    twins = {frozenset(pair) for pair in twin_pairs}
    if not twins:
        raise AnalysisError("no twin pairs supplied")

    rows: list[pd.DataFrame] = []
    for left, right in ((a, b) for i, a in enumerate(trajectories) for b in trajectories[i + 1 :]):
        if not _matched_regime(left, right):
            continue
        kind = _pair_kind(left, right, twins)
        if kind not in {"control", "twin_matched"}:
            continue
        n = min(left.embeddings.shape[0], right.embeddings.shape[0])
        if n == 0:
            continue
        family = (
            left.semantic_seed
            if kind == "control"
            else "+".join(sorted({left.semantic_seed, right.semantic_seed}))
        )
        rows.append(
            pd.DataFrame(
                {
                    "left": left.trajectory_id,
                    "right": right.trajectory_id,
                    "kind": kind,
                    "family": family,
                    "chunk_index": np.arange(n, dtype=np.int64),
                    "turnover": left.turnovers[:n],
                    "distance": _cosine_distance_rows(left.embeddings[:n], right.embeddings[:n]),
                }
            )
        )
    if not rows:
        raise AnalysisError("no twin-matched or control pairs in this sample")
    return pd.concat(rows, ignore_index=True)


def _band_delta(pairs: pd.DataFrame) -> tuple[float, float, float, int, int]:
    twin = pairs.loc[pairs["kind"] == "twin_matched", "distance"]
    control = pairs.loc[pairs["kind"] == "control", "distance"]
    if twin.empty or control.empty:
        return (np.nan, np.nan, np.nan, len(twin), len(control))
    d_twin = float(twin.mean())
    d_control = float(control.mean())
    return (d_twin - d_control, d_twin, d_control, len(twin), len(control))


def compute_twin_contrast(
    trajectories: list[Trajectory],
    *,
    twin_pairs: list[tuple[str, str]],
    params: TwinParams,
) -> TwinResult:
    """Last-band and per-band Δ = D_twin_matched − D_control."""
    ids = {t.semantic_seed for t in trajectories}
    needed = {name for pair in twin_pairs for name in pair}
    missing = needed - ids
    if missing:
        raise AnalysisError(f"twin contrast missing seeds: {sorted(missing)}")

    pairs = twin_pairwise_distances(trajectories, twin_pairs=twin_pairs)
    pairs["band"] = (pairs["turnover"] // params.turnover_bin) * params.turnover_bin

    rng = np.random.default_rng(params.seed)
    index = {t.trajectory_id: i for i, t in enumerate(trajectories)}
    n_traj = len(trajectories)
    records: list[dict[str, float | int | bool | str]] = []

    for band, block in pairs.groupby("band", sort=True):
        families = sorted(block["family"].unique())
        scopes: list[tuple[str, pd.DataFrame]] = [("all", block)]
        scopes.extend((str(family), block[block["family"] == family]) for family in families)

        for scope, scoped in scopes:
            point, d_twin, d_control, n_twin, n_control = _band_delta(scoped)
            boot = np.empty(params.n_boot, dtype=np.float64)
            boot[:] = np.nan
            for draw in range(params.n_boot):
                chosen = rng.integers(0, n_traj, size=n_traj)
                keep = {tid for tid, pos in index.items() if pos in set(chosen.tolist())}
                resampled = scoped[scoped["left"].isin(keep) & scoped["right"].isin(keep)]
                boot[draw] = _band_delta(resampled)[0]
            finite = boot[np.isfinite(boot)]
            if finite.size == 0:
                low = high = float("nan")
            else:
                tail = 100.0 * params.alpha / 2.0
                low, high = np.percentile(finite, [tail, 100.0 - tail])
            records.append(
                {
                    "band": float(band),
                    "scope": scope,
                    "delta": point,
                    "d_twin": d_twin,
                    "d_control": d_control,
                    "delta_ci_low": float(low),
                    "delta_ci_high": float(high),
                    "divergent": bool(np.isfinite(low) and low > 0.0),
                    "n_twin_pairs": int(n_twin),
                    "n_control_pairs": int(n_control),
                }
            )

    per_band = pd.DataFrame.from_records(records)
    last = per_band.loc[per_band["scope"] == "all"]
    if last.empty:
        raise AnalysisError("twin contrast produced no all-scope bands")
    last_row = last.loc[last["band"].idxmax()]
    scalars = {
        "last_band": float(last_row["band"]),
        "delta_last": float(last_row["delta"]),
        "delta_ci_low": float(last_row["delta_ci_low"]),
        "delta_ci_high": float(last_row["delta_ci_high"]),
        "divergent_at_last_band": float(last_row["divergent"]),
        "d_twin_last": float(last_row["d_twin"]),
        "d_control_last": float(last_row["d_control"]),
    }
    return TwinResult(per_band=per_band, pairs=pairs, scalars=scalars)
