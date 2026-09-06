"""Stage 5 lock-occupancy sample splits.

F4 (domain last-band gap) uses the ten domain seeds. F6 (twins) uses the
two one-fact pairs. Pooling a twin member into domain ``D_between`` is a
confound: the pair is designed to be close, so it would shrink the domain
gap. This module is the guard that keeps those samples apart.

Not a new dynamical estimator. The quantities are still
``compute_separation`` and ``compute_twin_contrast``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..errors import AnalysisError
from .rates import parse_trajectory_id
from .separation import Trajectory, pairwise_distances

DOMAIN_SEED_ORDER: tuple[str, ...] = (
    "physics",
    "surreal",
    "finance",
    "biology",
    "war",
    "love",
    "recipe",
    "programming",
    "philosophy",
    "noise",
)
TWIN_SEED_ORDER: tuple[str, ...] = (
    "waterloo-won",
    "waterloo-lost",
    "reactor-stable",
    "reactor-unstable",
)
TWIN_PAIRS: tuple[tuple[str, str], ...] = (
    ("waterloo-won", "waterloo-lost"),
    ("reactor-stable", "reactor-unstable"),
)

DOMAIN_SEEDS = frozenset(DOMAIN_SEED_ORDER)
TWIN_SEEDS = frozenset(TWIN_SEED_ORDER)
RAW_PREFIX = "or-qwen3-8b__"
LOCK_W = 4096
LOCK_TEMPERATURE = 0.3

TWO_SPACE_S51_EMBED = "s5-embed-lock-occupancy-20260906T030125Z-eab6e484"
TWO_SPACE_S22_EMBED = "s2-embed-mechanism-20260901T131051Z-55761049"
GEMINI_S51_EMBED = "s6-embed-third-space-20260906T082301Z-588eff8f"
GEMINI_S22_EMBED = "s6-embed-third-space-20260906T082628Z-9077d587"
OCCUPANCY_SPACE_ORDER: tuple[str, ...] = ("bge-m3", "qwen3-embed-8b", "gemini-embed-001")


def occupancy_embed_runs(slug: str) -> tuple[str, str]:
    """``(s5.1_embed_run_id, s2.2_embed_run_id)`` for one representation.

    Gemini lives on the Stage 6 embed runs. Reusing the S5 two-space
    embed id for ``gemini-embed-001`` would silently drop the third space.
    """
    if slug == "gemini-embed-001":
        return GEMINI_S51_EMBED, GEMINI_S22_EMBED
    if slug in ("bge-m3", "qwen3-embed-8b"):
        return TWO_SPACE_S51_EMBED, TWO_SPACE_S22_EMBED
    raise AnalysisError(f"no occupancy embed runs for {slug!r}")


def is_raw_lock_trajectory(trajectory_id: str) -> bool:
    """True for P1 raw ``or-qwen3-8b`` cells at the S5 lock ``(W=4096, T=0.3)``."""
    if not str(trajectory_id).startswith(RAW_PREFIX):
        return False
    parsed = parse_trajectory_id(str(trajectory_id))
    window = parsed["W"]
    temperature = parsed["temperature"]
    if not isinstance(window, int) or not isinstance(temperature, (int, float)):
        return False
    return window == LOCK_W and float(temperature) == LOCK_TEMPERATURE


def filter_raw_lock(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep raw lock cells; drop prefill rows and other ``(W, T)``."""
    if "trajectory_id" not in frame.columns:
        raise AnalysisError("frame has no trajectory_id")
    mask = frame["trajectory_id"].astype(str).map(is_raw_lock_trajectory)
    return frame.loc[mask].copy()


def ensure_semantic_seed(frame: pd.DataFrame) -> pd.DataFrame:
    """Fill ``semantic_seed`` / ``stochastic_seed`` from ``trajectory_id`` if needed."""
    if "trajectory_id" not in frame.columns:
        raise AnalysisError("frame has no trajectory_id")
    out = frame.copy()
    parsed = pd.DataFrame(out["trajectory_id"].astype(str).map(parse_trajectory_id).tolist())
    if "semantic_seed" not in out.columns or out["semantic_seed"].isna().any():
        out["semantic_seed"] = parsed["semantic_seed"].to_numpy()
    if "stochastic_seed" not in out.columns or out["stochastic_seed"].isna().any():
        out["stochastic_seed"] = parsed["stochastic_seed"].to_numpy()
    if "W" not in out.columns or out["W"].isna().any():
        out["W"] = parsed["W"].to_numpy()
    if "temperature" not in out.columns or out["temperature"].isna().any():
        out["temperature"] = parsed["temperature"].to_numpy()
    return out


def split_domain_twin(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Partition into F4 (domains) and F6 (twins).

    Raises if a twin seed appears among domains, or if any seed is neither.
    Does not require the full 10+4 grid — callers that need the scientific
    sample call ``require_occupancy_grid``.
    """
    out = ensure_semantic_seed(frame)
    seeds = set(out["semantic_seed"].astype(str))
    unknown = seeds - DOMAIN_SEEDS - TWIN_SEEDS
    if unknown:
        raise AnalysisError(f"unrecognised semantic seeds: {sorted(unknown)}")
    domain = out[out["semantic_seed"].isin(DOMAIN_SEEDS)].copy()
    twin = out[out["semantic_seed"].isin(TWIN_SEEDS)].copy()
    leaked = set(domain["semantic_seed"].astype(str)) & TWIN_SEEDS
    if leaked:
        raise AnalysisError(f"twin seeds leaked into the domain partition: {sorted(leaked)}")
    return domain, twin


def require_occupancy_grid(domain: pd.DataFrame, twin: pd.DataFrame) -> None:
    """The scientific S5 sample: 10 domains × 2 + 2 twin pairs × 2 = 28."""
    domain_ids = set(domain["trajectory_id"].astype(str))
    twin_ids = set(twin["trajectory_id"].astype(str))
    if domain_ids & twin_ids:
        raise AnalysisError("domain and twin partitions share trajectory_ids")
    domain_seeds = set(domain["semantic_seed"].astype(str))
    twin_seeds = set(twin["semantic_seed"].astype(str))
    if domain_seeds != DOMAIN_SEEDS:
        raise AnalysisError(
            f"domain partition has seeds {sorted(domain_seeds)}, expected {list(DOMAIN_SEED_ORDER)}"
        )
    if twin_seeds != TWIN_SEEDS:
        raise AnalysisError(
            f"twin partition has seeds {sorted(twin_seeds)}, expected {list(TWIN_SEED_ORDER)}"
        )
    if len(domain_ids) != 20:
        raise AnalysisError(f"expected 20 domain trajectories, got {len(domain_ids)}")
    if len(twin_ids) != 8:
        raise AnalysisError(f"expected 8 twin trajectories, got {len(twin_ids)}")


def last_band_seed_matrix(
    trajectories: list[Trajectory],
    *,
    turnover_bin: float = 2.0,
) -> pd.DataFrame:
    """Tidy last-band mean cosine distance for every seed pair, including diagonal.

    Diagonal cells are ``D_within`` (same seed, different stochastic seed).
    Off-diagonal cells are the mean last-band between-seed distance. The
    matrix is an occupancy map, not a cluster count, and is computed in the
    original embedding space.
    """
    if len(trajectories) < 2:
        raise AnalysisError("last-band matrix needs at least two trajectories")
    pairs = pairwise_distances(trajectories)
    pairs = pairs.copy()
    pairs["band"] = (pairs["turnover"].to_numpy() // turnover_bin) * turnover_bin
    last_band = float(pairs["band"].max())
    last = pairs.loc[pairs["band"] == last_band]
    present = {t.semantic_seed for t in trajectories}
    seeds = [s for s in (*DOMAIN_SEED_ORDER, *TWIN_SEED_ORDER) if s in present]
    seeds.extend(sorted(present - set(seeds)))
    rows: list[dict[str, object]] = []
    for row_seed in seeds:
        for col_seed in seeds:
            if row_seed == col_seed:
                block = last[(last["kind"] == "within") & (last["semantic_left"] == row_seed)]
                kind = "within"
            else:
                block = last[
                    ((last["semantic_left"] == row_seed) & (last["semantic_right"] == col_seed))
                    | ((last["semantic_left"] == col_seed) & (last["semantic_right"] == row_seed))
                ]
                kind = "between"
            distance = float(block["distance"].mean()) if len(block) else float("nan")
            rows.append(
                {
                    "seed_row": row_seed,
                    "seed_col": col_seed,
                    "kind": kind,
                    "distance": distance,
                    "n_chunk_pairs": len(block),
                    "last_band": last_band,
                }
            )
    return pd.DataFrame(rows)


def lock_rate_by_seed(verdicts: pd.DataFrame) -> pd.DataFrame:
    """Degenerate count per seed as ``k/n``. n=2 CIs are not the headline."""
    frame = ensure_semantic_seed(verdicts)
    if "degenerate" not in frame.columns:
        raise AnalysisError("verdicts have no degenerate column")
    rows: list[dict[str, object]] = []
    for seed, block in frame.groupby("semantic_seed", sort=True):
        n = len(block)
        n_deg = int(block["degenerate"].astype(bool).sum())
        role = "domain" if seed in DOMAIN_SEEDS else "twin" if seed in TWIN_SEEDS else "other"
        rows.append(
            {
                "semantic_seed": str(seed),
                "role": role,
                "n": n,
                "n_degenerate": n_deg,
                "k_over_n": f"{n_deg}/{n}",
                "fraction": (n_deg / n) if n else float("nan"),
            }
        )
    domain = frame[frame["semantic_seed"].isin(DOMAIN_SEEDS)]
    if not domain.empty:
        n = len(domain)
        n_deg = int(domain["degenerate"].astype(bool).sum())
        n_seeds_hit = int(domain.groupby("semantic_seed")["degenerate"].any().astype(bool).sum())
        n_domain_seeds = int(domain["semantic_seed"].nunique())
        rows.append(
            {
                "semantic_seed": "_domain_all",
                "role": "domain_overall",
                "n": n,
                "n_degenerate": n_deg,
                "k_over_n": f"{n_deg}/{n}",
                "fraction": n_deg / n,
            }
        )
        rows.append(
            {
                "semantic_seed": "_domain_seeds_with_a_lock",
                "role": "domain_seed_hit",
                "n": n_domain_seeds,
                "n_degenerate": n_seeds_hit,
                "k_over_n": f"{n_seeds_hit}/{n_domain_seeds}",
                "fraction": n_seeds_hit / n_domain_seeds,
            }
        )
    return pd.DataFrame(rows)


def last_chunk_2d_illustration(frame: pd.DataFrame) -> pd.DataFrame:
    """PCA of last-chunk embeddings. Illustration only — not a cluster count."""
    columns = [c for c in frame.columns if c.startswith("e") and c[1:].isdigit()]
    if not columns:
        raise AnalysisError("no embedding columns found")
    last = (
        ensure_semantic_seed(frame)
        .sort_values(["trajectory_id", "chunk_index"])
        .groupby("trajectory_id", as_index=False)
        .tail(1)
        .copy()
    )
    matrix = last[columns].to_numpy(dtype=np.float64)
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    coords = centered @ vt[:2].T
    last["pc1"] = coords[:, 0]
    last["pc2"] = coords[:, 1]
    keep = [
        c
        for c in (
            "trajectory_id",
            "semantic_seed",
            "stochastic_seed",
            "chunk_index",
            "turnover",
            "pc1",
            "pc2",
        )
        if c in last.columns
    ]
    return last[keep].reset_index(drop=True)
