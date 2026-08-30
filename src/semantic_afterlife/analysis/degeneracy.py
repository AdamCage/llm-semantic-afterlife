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
        default=0.083,
        gt=0.0,
        lt=1.0,
        description="n-gram repetition rate above which a chunk counts as looping. CALIBRATED, "
        "not chosen: the 99th percentile of natural English prose chunked by the same tokenizer "
        "at the same 1024-token size (237 chunks of Carroll and Darwin; mean 0.033, p95 0.063, "
        "max 0.149). An intuition-picked 0.5 was six times too high and scored a trajectory at "
        "18x natural repetition as merely 'partly' degenerate. Re-derive with "
        "scripts/calibrate_degeneracy.py if the chunk size or tokenizer changes",
    )
    loop_chunk_fraction: float = Field(
        default=0.5,
        gt=0.0,
        le=1.0,
        description="fraction of post-horizon chunks that must be looping for the trajectory to "
        "be labelled degenerate. Raised from 0.2 to 0.5 once the per-chunk threshold was "
        "calibrated: at a 1% false-positive rate per chunk, requiring half the chunks makes the "
        "trajectory-level verdict essentially certain, and the healthy reference model sits at "
        "8% of chunks flagged",
    )
    self_similarity_threshold: float = Field(
        default=0.98,
        gt=0.0,
        le=1.0,
        description="cosine between consecutive chunk embeddings above which the trajectory has "
        "effectively stopped moving. Applies only when embeddings are supplied, and only to "
        "consecutive pairs, so it cannot see a two-page cycle -- the novelty measures below are "
        "the primary instrument and this one is a cross-check",
    )
    shingle_n: int = Field(
        default=5,
        ge=2,
        description="word-shingle length for inter-chunk novelty. Long enough that natural prose "
        "almost never repeats a shingle by chance, so a low novelty score means real reuse",
    )
    fixed_point_threshold: float = Field(
        default=0.0122,
        gt=0.0,
        le=1.0,
        description="median late-phase pairwise shingle Jaccard above which the trajectory is "
        "judged to have reached a fixed point or a short cycle. CALIBRATED: the 99.9th percentile "
        "of 20,730 individual chunk pairs from natural English prose, whose *median* is 0.000 for "
        "both reference sources. Comparing a median against a far-tail quantile is deliberately "
        "conservative -- it says the typical late pair is more similar than 99.9% of natural pairs "
        "before anything is flagged. Note that a coherent single-topic book (Darwin, 201 chunks) "
        "also has a median of 0.000, so topical consistency does not inflate this statistic and "
        "the threshold is not penalising subject-matter focus",
    )
    novelty_threshold: float = Field(
        default=0.872,
        gt=0.0,
        le=1.0,
        description="fraction of a chunk's 5-word shingles that must be unseen earlier in the "
        "trajectory for the chunk to count as productive. CALIBRATED, not chosen: the 1st "
        "percentile of natural English prose chunked identically (237 chunks of Carroll and "
        "Darwin; mean novelty 0.965-0.992, minimum 0.847, and a median late-phase pairwise "
        "Jaccard of exactly 0.000). Re-derive with scripts/calibrate_degeneracy.py. "
        "The healthy/collapsed gap is so wide that any threshold between 0.3 and 0.87 gives the "
        "same verdict, so the exact value is not load-bearing -- what matters is that it is "
        "derived from a reference rather than guessed. "
        "This measure exists because n-gram repetition is computed *within* a chunk: a trajectory "
        "whose successive pages were near-identical to each other scored clean at 0.4x natural "
        "repetition with 0% looping chunks, while its late-phase pairwise Jaccard was 1.000. Every "
        "intra-chunk metric called a textual fixed point healthy",
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


def shingles(words: list[str], n: int) -> set[tuple[str, ...]]:
    if len(words) < n:
        return set()
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def novelty_series(words_per_chunk: list[list[str]], n: int) -> np.ndarray:
    """Fraction of each chunk's shingles never seen earlier in the trajectory.

    This is the measure that separates a trajectory exploring a bounded region
    from one reprinting the same page. Repetition rate cannot do it: it is
    computed inside a chunk, so a sequence of near-identical but individually
    varied pages scores as maximally healthy. That is not hypothetical -- it is
    how a converged trajectory passed every other diagnostic here.

    Runs in one pass over the trajectory against a cumulative shingle set, so it
    is linear rather than all-pairs, and it is defined on raw text so it can be
    read on a live run before any embedding exists.
    """
    seen: set[tuple[str, ...]] = set()
    out = np.full(len(words_per_chunk), np.nan)
    for i, words in enumerate(words_per_chunk):
        current = shingles(words, n)
        if not current:
            continue
        out[i] = len(current - seen) / len(current)
        seen |= current
    return out


def pairwise_similarity(words_per_chunk: list[list[str]], n: int) -> np.ndarray:
    """Upper-triangle shingle Jaccard between every pair of chunks.

    Complements novelty: a trajectory alternating between two pages has low
    novelty *and* a bimodal similarity distribution, which distinguishes a cycle
    from a fixed point. Quadratic, but chunk counts here are in the hundreds.
    """
    grams = [shingles(w, n) for w in words_per_chunk]
    values: list[float] = []
    for i in range(len(grams)):
        for j in range(i + 1, len(grams)):
            union = grams[i] | grams[j]
            values.append(len(grams[i] & grams[j]) / len(union) if union else 0.0)
    return np.asarray(values, dtype=np.float64)


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
    frame["novel_shingle_fraction"] = novelty_series(words_per_chunk, params.shingle_n)
    frame["unproductive"] = frame["novel_shingle_fraction"] < params.novelty_threshold

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
    unproductive_fraction = float(post["unproductive"].mean())

    # Pairwise similarity is summarised over the trajectory's second half, where a
    # fixed point has had time to establish itself. The median is the diagnostic
    # statistic: one repeated page lifts every late pair at once, so a high median
    # cannot be produced by a few coincidental matches.
    late = words_per_chunk[len(words_per_chunk) // 2 :]
    late_similarity = (
        pairwise_similarity(late, params.shingle_n) if len(late) >= 4 else np.asarray([np.nan])
    )

    scalars: dict[str, float] = {
        "n_chunks": float(len(frame)),
        "n_chunks_post_horizon": float(len(post)),
        "looping_fraction": looping_fraction,
        "unproductive_fraction": unproductive_fraction,
        "mean_novel_shingle_fraction": float(post["novel_shingle_fraction"].mean()),
        "min_novel_shingle_fraction": float(post["novel_shingle_fraction"].min()),
        "late_pairwise_similarity_median": float(np.nanmedian(late_similarity)),
        "late_pairwise_similarity_max": float(np.nanmax(late_similarity)),
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
    }

    # Two verdicts, deliberately not one. They answer different questions and
    # they disagreed on real data: a trajectory at 0.675 novelty -- far below
    # human prose -- had a late-phase pairwise median of 0.007, inside the
    # natural range, meaning it kept moving while recycling phrasing heavily.
    #
    # `degenerate` is the one that qualifies other measurements, so it fires only
    # on evidence that the process has stopped exploring: repetition within a
    # page, or the same page returning. Productivity is reported as a continuous
    # order parameter with no threshold, because its natural-prose reference is
    # arguably the wrong yardstick -- a human writing a book is not conditioned on
    # a sliding window of their own output and has no reason to recycle phrasing
    # the way a self-conditioned process must.
    at_fixed_point = bool(
        np.isfinite(scalars["late_pairwise_similarity_median"])
        and scalars["late_pairwise_similarity_median"] >= params.fixed_point_threshold
    )
    is_looping = looping_fraction >= params.loop_chunk_fraction
    scalars["at_fixed_point"] = float(at_fixed_point)
    scalars["degenerate"] = float(is_looping or at_fixed_point)
    scalars["degeneracy_mode"] = float((1 if is_looping else 0) + (2 if at_fixed_point else 0))
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
