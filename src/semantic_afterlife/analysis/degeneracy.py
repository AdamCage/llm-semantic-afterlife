"""Degeneracy diagnostics for a generated trajectory.

Free-running generation can collapse: into verbatim repetition, into a short
cycle, or into vocabulary exhaustion. This matters twice over.

First, it qualifies every other measurement. A trajectory that has fallen into a
loop occupies one point in representation space, so it will look maximally
"confined" and maximally "metastable" for reasons that have nothing to do with
semantics. Confinement measured on a degenerate trajectory is an artifact.

Second, degeneracy is itself a dynamical state and a reportable finding. It is
counted and characterised, never filtered out of the sample (methodology §3.7,
risks.md R3).

All functions are pure: arrays and frames in, arrays and frames out.
"""

from __future__ import annotations

import re
import zlib
from collections import Counter
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from ..errors import AnalysisError

# Letters and digits, no underscores. Digits are kept deliberately: a trajectory
# that degenerates into enumeration ("1. 2. 3. ...") is degenerate, and a
# letters-only tokenizer would score it as maximally varied by seeing almost no
# tokens at all.
_WORD = re.compile(r"[^\W_]+", re.UNICODE)


class DegeneracyParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ngram: int = Field(default=3, ge=1, description="n-gram order for the repetition rate")
    loop_repetition_threshold: float = Field(
        default=0.5,
        gt=0.0,
        lt=1.0,
        description="n-gram repetition rate above which a chunk counts as looping. 0.5 means "
        "half the n-grams in the chunk are repeats of an earlier one *within the same chunk*",
    )
    loop_chunk_fraction: float = Field(
        default=0.2,
        gt=0.0,
        le=1.0,
        description="fraction of post-horizon chunks that must be looping for the trajectory "
        "to be labelled degenerate",
    )
    self_similarity_threshold: float = Field(
        default=0.98,
        gt=0.0,
        le=1.0,
        description="cosine between consecutive chunk embeddings above which the trajectory has "
        "effectively stopped moving",
    )


def tokenize_words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def ngram_repetition_rate(words: list[str], n: int = 3) -> float:
    """Share of n-grams that are not the first occurrence of their type.

    0.0 means every n-gram is new; values near 1.0 mean the text is cycling.
    """
    if len(words) < n + 1:
        return 0.0
    grams = [tuple(words[i : i + n]) for i in range(len(words) - n + 1)]
    return 1.0 - len(set(grams)) / len(grams)


def type_token_ratio(words: list[str]) -> float:
    return len(set(words)) / len(words) if words else 0.0


def unigram_entropy(words: list[str]) -> float:
    """Shannon entropy of the word distribution, in bits.

    Falls as the trajectory's vocabulary narrows, so it detects the slow variety
    of collapse that n-gram repetition misses.
    """
    if not words:
        return 0.0
    counts = np.array(list(Counter(words).values()), dtype=np.float64)
    p = counts / counts.sum()
    return float(-(p * np.log2(p)).sum())


def compression_ratio(text: str) -> float:
    """Compressed size over raw size. A cheap, tokenizer-free redundancy proxy."""
    raw = text.encode("utf-8")
    if not raw:
        return 1.0
    return len(zlib.compress(raw, 6)) / len(raw)


@dataclass(slots=True)
class DegeneracyResult:
    trajectory_id: str
    per_chunk: pd.DataFrame
    scalars: dict[str, float]

    @property
    def is_degenerate(self) -> bool:
        return bool(self.scalars["degenerate"])


def compute_degeneracy(
    texts: list[str],
    *,
    trajectory_id: str,
    token_ends: np.ndarray,
    W: int,
    params: DegeneracyParams,
    embeddings: np.ndarray | None = None,
) -> DegeneracyResult:
    """Per-chunk degeneracy diagnostics plus a trajectory-level verdict.

    ``embeddings`` is optional; when supplied, consecutive-chunk cosine
    similarity is included, which catches a trajectory that has stopped moving
    even when its surface forms keep varying.
    """
    if len(texts) != token_ends.size:
        raise AnalysisError(
            f"{len(texts)} chunk texts but {token_ends.size} token positions for {trajectory_id}"
        )
    if not texts:
        raise AnalysisError(f"no chunks for {trajectory_id}")

    words_per_chunk = [tokenize_words(t) for t in texts]
    frame = pd.DataFrame(
        {
            "trajectory_id": trajectory_id,
            "chunk_index": np.arange(len(texts), dtype=np.int64),
            "token_end": token_ends.astype(np.int64),
            "turnover": token_ends / float(W),
            "n_words": [len(w) for w in words_per_chunk],
            "type_token_ratio": [type_token_ratio(w) for w in words_per_chunk],
            "ngram_repetition": [ngram_repetition_rate(w, params.ngram) for w in words_per_chunk],
            "unigram_entropy_bits": [unigram_entropy(w) for w in words_per_chunk],
            "compression_ratio": [compression_ratio(t) for t in texts],
        }
    )
    frame["looping"] = frame["ngram_repetition"] >= params.loop_repetition_threshold

    if embeddings is not None:
        Z = np.asarray(embeddings, dtype=np.float64)
        if Z.shape[0] != len(texts):
            raise AnalysisError("embedding count does not match chunk count")
        norms = np.linalg.norm(Z, axis=1, keepdims=True)
        Zn = Z / np.where(norms > 0, norms, 1.0)
        similarity = np.concatenate([[np.nan], np.einsum("ij,ij->i", Zn[:-1], Zn[1:])])
        frame["consecutive_cosine"] = similarity
        frame["frozen"] = frame["consecutive_cosine"] >= params.self_similarity_threshold

    # The verdict uses only the post-horizon segment: pre-horizon chunks still
    # carry the seed and belong to a different (forced) process.
    post = frame[frame["turnover"] > 1.0]
    if post.empty:
        post = frame
    looping_fraction = float(post["looping"].mean())

    scalars: dict[str, float] = {
        "n_chunks": float(len(frame)),
        "n_chunks_post_horizon": float(len(post)),
        "looping_fraction": looping_fraction,
        "mean_ngram_repetition": float(post["ngram_repetition"].mean()),
        "max_ngram_repetition": float(post["ngram_repetition"].max()),
        "mean_type_token_ratio": float(post["type_token_ratio"].mean()),
        "mean_entropy_bits": float(post["unigram_entropy_bits"].mean()),
        "mean_compression_ratio": float(post["compression_ratio"].mean()),
        # A falling entropy trend is the slow form of collapse; the sign matters
        # more than the magnitude, so it is reported as a per-turnover slope.
        "entropy_trend_per_turnover": _slope(
            post["turnover"].to_numpy(), post["unigram_entropy_bits"].to_numpy()
        ),
        "degenerate": float(looping_fraction >= params.loop_chunk_fraction),
    }
    if "consecutive_cosine" in frame.columns:
        scalars["frozen_fraction"] = float(post["frozen"].mean())
        scalars["max_consecutive_cosine"] = float(post["consecutive_cosine"].max())
        scalars["degenerate"] = float(
            scalars["degenerate"] > 0 or scalars["frozen_fraction"] >= params.loop_chunk_fraction
        )

    return DegeneracyResult(trajectory_id=trajectory_id, per_chunk=frame, scalars=scalars)


def _slope(x: np.ndarray, y: np.ndarray) -> float:
    """Least-squares slope, or 0.0 when the series is too short to have one."""
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 3:
        return 0.0
    x, y = x[mask], y[mask]
    xc = x - x.mean()
    denominator = float(xc @ xc)
    if denominator == 0.0:
        return 0.0
    return float((xc @ (y - y.mean())) / denominator)


def compare_segments(result: DegeneracyResult, *, split_token: int) -> pd.DataFrame:
    """Diagnostics before and after a chosen point in the trajectory.

    Used to test whether an abrupt jump in representation space is a metastable
    transition or the onset of collapse. A jump accompanied by rising repetition
    and falling entropy is degeneracy; a jump with both unchanged is a genuine
    change of semantic regime.
    """
    frame = result.per_chunk
    columns = [
        "ngram_repetition",
        "type_token_ratio",
        "unigram_entropy_bits",
        "compression_ratio",
    ]
    if "consecutive_cosine" in frame.columns:
        columns.append("consecutive_cosine")

    before = frame[frame["token_end"] < split_token]
    after = frame[frame["token_end"] >= split_token]
    rows = []
    for column in columns:
        rows.append(
            {
                "metric": column,
                "before": float(before[column].mean()),
                "after": float(after[column].mean()),
                "delta": float(after[column].mean() - before[column].mean()),
                "n_before": len(before),
                "n_after": len(after),
            }
        )
    return pd.DataFrame(rows)
