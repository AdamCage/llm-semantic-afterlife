"""Rates over trajectories, with uncertainty over the replicate unit.

Stage 2's headline quantities are Bernoulli rates — repetition-lock
incidence per generator, reviewer-register incidence per mechanism — not
continuous means. The replicate unit is still the trajectory.

A percentile bootstrap of 0/1 flags yields ``[0, 0]`` at ``0/n`` and
``[1, 1]`` at ``n/n``. Those intervals are not a statement about a population
probability (ADR-0019). Rates therefore use Clopper–Pearson exact
intervals. Two-sample contrasts report a Newcombe difference CI and a
Fisher exact *p*-value.

A rate whose interval includes 0.5 does not decide a direction.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import binomtest, fisher_exact
from statsmodels.stats.proportion import confint_proportions_2indep

TRAJECTORY_ID_PARTS = ("generator", "W", "temperature", "semantic_seed", "stochastic_seed")


def parse_trajectory_id(trajectory_id: str) -> dict[str, object]:
    """Split ``generator__W4096__T0p3__physics__s1`` into typed fields."""
    parts = trajectory_id.split("__")
    if len(parts) != 5:
        raise ValueError(f"unrecognised trajectory_id {trajectory_id!r}")
    generator, window, temp, seed, replicate = parts
    if not window.startswith("W") or not temp.startswith("T") or not replicate.startswith("s"):
        raise ValueError(f"unrecognised trajectory_id {trajectory_id!r}")
    return {
        "trajectory_id": trajectory_id,
        "generator": generator,
        "W": int(window[1:]),
        "temperature": float(temp[1:].replace("p", ".")),
        "semantic_seed": seed,
        "stochastic_seed": int(replicate[1:]),
    }


def clopper_pearson_ci(k: int, n: int, *, alpha: float = 0.05) -> tuple[float, float]:
    """Exact binomial interval for a Bernoulli rate. ``k`` successes in ``n`` trials."""
    if n <= 0:
        return (float("nan"), float("nan"))
    if k < 0 or k > n:
        raise ValueError(f"need 0 ≤ k ≤ n, got k={k}, n={n}")
    interval = binomtest(k, n).proportion_ci(confidence_level=1.0 - alpha, method="exact")
    return (float(interval.low), float(interval.high))


def rate_ci(flags: np.ndarray, *, seed: int = 0, n_boot: int = 2000) -> dict[str, float]:
    """Clopper–Pearson CI for a Bernoulli rate. ``flags`` is one 0/1 per trajectory.

    ``seed`` and ``n_boot`` are accepted for call-site compatibility and ignored:
    the interval is exact, not a resample.
    """
    del seed, n_boot
    x = np.asarray(flags, dtype=np.float64)
    x = x[np.isfinite(x)]
    n = int(x.size)
    if n == 0:
        return {
            "rate": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
            "n": 0,
            "n_positive": 0,
            "method": "clopper_pearson",
        }
    k = int(np.round(x.sum()))
    k = min(max(k, 0), n)
    low, high = clopper_pearson_ci(k, n)
    return {
        "rate": k / n,
        "ci_low": low,
        "ci_high": high,
        "n": n,
        "n_positive": k,
        "method": "clopper_pearson",
    }


def rate_difference_ci(
    flags_a: np.ndarray,
    flags_b: np.ndarray,
    *,
    seed: int = 0,
    n_boot: int = 2000,
) -> dict[str, float]:
    """Unpaired Newcombe CI for ``rate(a) - rate(b)``, plus Fisher exact *p*.

    The two arms are different generators or mechanisms, so the trajectories
    are not paired. A percentile bootstrap of the two means is the wrong
    interval at ``0/n`` and ``n/n`` (ADR-0019). ``seed`` and ``n_boot`` are
    ignored.
    """
    del seed, n_boot
    a = np.asarray(flags_a, dtype=np.float64)
    b = np.asarray(flags_b, dtype=np.float64)
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    n_a, n_b = int(a.size), int(b.size)
    if n_a == 0 or n_b == 0:
        return {
            "diff": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
            "n_a": n_a,
            "n_b": n_b,
            "fisher_p": float("nan"),
            "method": "newcomb",
        }
    k_a = int(np.round(a.sum()))
    k_b = int(np.round(b.sum()))
    k_a, k_b = min(max(k_a, 0), n_a), min(max(k_b, 0), n_b)
    low, high = confint_proportions_2indep(
        k_a, n_a, k_b, n_b, method="newcomb", compare="diff", alpha=0.05
    )
    table = np.array([[k_a, n_a - k_a], [k_b, n_b - k_b]], dtype=np.int64)
    fisher = fisher_exact(table, alternative="two-sided")
    fisher_p = float(fisher.pvalue)
    return {
        "diff": float(k_a / n_a - k_b / n_b),
        "ci_low": float(low),
        "ci_high": float(high),
        "n_a": n_a,
        "n_b": n_b,
        "rate_a": float(k_a / n_a),
        "rate_b": float(k_b / n_b),
        "fisher_p": fisher_p,
        "method": "newcomb",
    }


def grouped_rates(
    frame: pd.DataFrame,
    *,
    flag_column: str,
    group_columns: list[str],
    seed: int = 0,
) -> pd.DataFrame:
    """One rate + CI row per group. Groups with no finite flags are omitted."""
    rows: list[dict[str, object]] = []
    for keys, block in frame.groupby(group_columns, sort=True, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        flags = block[flag_column].to_numpy(dtype=np.float64)
        stats = rate_ci(flags, seed=seed)
        row = dict(zip(group_columns, keys, strict=True))
        row.update(stats)
        rows.append(row)
    return pd.DataFrame(rows)


def assign_quarter(progress: np.ndarray) -> np.ndarray:
    """Map a 0–1 progress series onto quarters 1–4, last point included in 4."""
    p = np.asarray(progress, dtype=np.float64)
    quarter = np.floor(np.clip(p, 0.0, 0.999999) * 4.0).astype(np.int64) + 1
    return quarter


def quarter_diagnostics(steps: pd.DataFrame) -> pd.DataFrame:
    """Block fill and stop rate per trajectory-quarter, then per generator-quarter.

    Progress is ``generated_tokens / max(generated_tokens)`` *within* a
    trajectory, so a run that ends early still has four quarters of itself.
    A run-level mean of fill is not computed here on purpose.
    """
    required = {"trajectory_id", "generated_tokens", "block_fill_ratio", "finish_reason"}
    missing = required - set(steps.columns)
    if missing:
        raise ValueError(f"steps frame missing {sorted(missing)}")

    per = steps.sort_values(["trajectory_id", "generated_tokens"]).copy()
    per["step_index"] = per.groupby("trajectory_id").cumcount()
    counts = per.groupby("trajectory_id")["step_index"].transform("max") + 1
    # Even bins over steps, not over tokens: fill and stop are per-request
    # properties, and late steps are systematically shorter when the model
    # starts hitting stop, so token-progress quarters would overweight the
    # collapse.
    per["quarter"] = np.floor(per["step_index"] / counts * 4.0).astype(np.int64) + 1
    per["stopped"] = per["finish_reason"].astype(str) != "length"
    if "generator" not in per.columns:
        parsed = per["trajectory_id"].map(parse_trajectory_id)
        per["generator"] = parsed.map(lambda row: row["generator"])

    per_traj = (
        per.groupby(["generator", "trajectory_id", "quarter"], sort=True)
        .agg(
            n_steps=("block_fill_ratio", "size"),
            block_fill=("block_fill_ratio", "mean"),
            stop_rate=("stopped", "mean"),
        )
        .reset_index()
    )
    return per_traj


@dataclass(slots=True)
class RegisterCriterion:
    """Stated rule for the F4 hand count. Applied to step-1 completion text."""

    name: str = "reviewer_register_v1"
    description: str = (
        "Step-1 is in the reviewer register if it addresses the seed as a document "
        "to evaluate or explain (second-person reference to the reader's text, or "
        "an opening evaluative/meta frame such as praise-plus-restatement or "
        "'let me break this down'), rather than continuing the seed's last clause "
        "in the same grammatical person and tense."
    )


REVIEWER_MARKERS = (
    "your passage",
    "your text",
    "you've provided",
    "you have provided",
    "you provided",
    "you're discussing",
    "you are discussing",
    "let me break",
    "let's break",
    "let us break",
    "excellent and comprehensive",
    "comprehensive overview",
    "well-structured",
    "insightful discussion",
    "thank you for",
    "you've written",
    "you have written",
)


def marker_register_flag(text: str) -> bool:
    """Cheap pre-filter for the hand count; not a substitute for F4.

    A hit is evidence the opening *may* be in register. A miss is not evidence
    it is not — the hand count still reads the text. Reported separately so the
    two cannot be confused.
    """
    lowered = " ".join(text.lower().split())
    return any(marker in lowered for marker in REVIEWER_MARKERS)
