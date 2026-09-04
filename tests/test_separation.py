"""The seed-separation contrast, validated on processes with known answers.

This is the measurement Stage 1's verdict rests on, so it is tested against three
synthetic worlds whose answer is known by construction: one where seed identity
persists, one where it decays away, and one where there was never any seed
structure at all. An estimator that cannot tell those apart cannot be trusted to
report on real trajectories.
"""

from __future__ import annotations

import numpy as np
import pytest

from semantic_afterlife.analysis.separation import (
    SeparationParams,
    Trajectory,
    compute_separation,
    pairwise_distances,
)
from semantic_afterlife.errors import AnalysisError

N_CHUNKS = 40
DIM = 24
PARAMS = SeparationParams(n_boot=300, turnover_bin=4.0)


def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def build(
    *,
    n_seeds: int = 3,
    n_repeats: int = 2,
    persistence: float = 1.0,
    noise: float = 0.25,
    rng_seed: int = 0,
) -> list[Trajectory]:
    """Trajectories whose seed identity persists to a controllable degree.

    ``persistence`` 1.0 keeps each seed's direction for the whole trajectory;
    0.0 removes it immediately, so every trajectory is drawn from one common
    distribution regardless of its label.
    """
    rng = np.random.default_rng(rng_seed)
    centres = _unit(rng.normal(size=(n_seeds, DIM)))
    turnovers = np.linspace(0.0, 16.0, N_CHUNKS)
    out: list[Trajectory] = []
    for seed_index in range(n_seeds):
        for repeat in range(n_repeats):
            # Seed influence decays geometrically at rate `persistence`.
            weights = persistence**turnovers
            base = weights[:, None] * centres[seed_index][None, :]
            drift = rng.normal(scale=noise, size=(N_CHUNKS, DIM))
            out.append(
                Trajectory(
                    trajectory_id=f"s{seed_index}_r{repeat}",
                    semantic_seed=f"seed{seed_index}",
                    stochastic_seed=repeat,
                    embeddings=_unit(base + drift),
                    turnovers=turnovers,
                )
            )
    return out


class TestPairwiseDistances:
    def test_labels_within_and_between_correctly(self) -> None:
        pairs = pairwise_distances(build(n_seeds=2, n_repeats=2))
        # 4 trajectories: 2 within-pairs (one per seed), 4 between-pairs.
        counts = pairs.groupby(["left", "right"]).first()["kind"].value_counts()
        assert counts["within"] == 2
        assert counts["between"] == 4

    def test_pairs_are_truncated_to_the_shorter_member(self) -> None:
        trajectories = build(n_seeds=2, n_repeats=2)
        trajectories[0].embeddings = trajectories[0].embeddings[:10]
        trajectories[0].turnovers = trajectories[0].turnovers[:10]
        pairs = pairwise_distances(trajectories)
        involving = pairs[(pairs["left"] == "s0_r0") | (pairs["right"] == "s0_r0")]
        assert involving["chunk_index"].max() == 9

    def test_single_trajectory_is_rejected(self) -> None:
        with pytest.raises(AnalysisError):
            pairwise_distances(build(n_seeds=1, n_repeats=1))

    def test_cross_temperature_pairs_are_not_within(self) -> None:
        """Same semantic seed at two temperatures is not D_within (S3.0 confound)."""
        low = build(n_seeds=2, n_repeats=2, rng_seed=0)
        high = build(n_seeds=2, n_repeats=2, rng_seed=1)
        for traj in low:
            traj.temperature = 0.3
            traj.W = 4096
        for traj in high:
            traj.temperature = 1.5
            traj.W = 4096
            traj.trajectory_id = traj.trajectory_id + "_T15"
        pairs = pairwise_distances(low + high)
        kinds = pairs.groupby(["left", "right"]).first()["kind"]
        assert (kinds == "within").sum() == 4  # two temps × two seeds
        assert (kinds == "between").sum() == 8  # two temps × four cross-seed pairs
        mixed = pairs[
            pairs["left"].str.contains("_T15") != pairs["right"].str.contains("_T15")
        ]
        assert mixed.empty


class TestSeparation:
    def test_persistent_seeds_give_a_positive_gap(self) -> None:
        result = compute_separation(build(persistence=1.0, noise=0.2), params=PARAMS)
        assert result.scalars["gap_post_horizon_mean"] > 0
        assert result.scalars["separated_at_last_band"] == 1.0
        assert (result.per_band["gap_ci_low"] > 0).all()

    def test_absent_seed_structure_gives_a_gap_bracketing_zero(self) -> None:
        """The null case. A method that finds separation here finds it anywhere."""
        result = compute_separation(build(persistence=0.0, noise=1.0), params=PARAMS)
        assert abs(result.scalars["gap_post_horizon_mean"]) < 0.05
        assert result.scalars["bands_separated_fraction"] < 0.5

    def test_decaying_seed_influence_shows_a_negative_trend(self) -> None:
        result = compute_separation(build(persistence=0.8, noise=0.2), params=PARAMS)
        assert result.scalars["gap_trend_per_turnover"] < 0
        assert result.per_band["gap"].iloc[0] > result.per_band["gap"].iloc[-1]

    def test_persistent_beats_decaying_beats_absent(self) -> None:
        """Ordering matters more than any single tolerance.

        Uses the post-horizon mean rather than a single band, and more
        replicates than the other tests: at six trajectories the sampling noise
        of the contrast (~0.05) exceeds the signal from a weakly persistent seed,
        which is itself worth knowing about the design -- three seeds by two
        repetitions cannot resolve a decayed seed influence.
        """

        def gap(persistence: float) -> float:
            return compute_separation(
                build(n_seeds=4, n_repeats=4, persistence=persistence, noise=0.2),
                params=PARAMS,
            ).scalars["gap_post_horizon_mean"]

        strong, weak, absent = gap(1.0), gap(0.9), gap(0.0)
        assert strong > weak > absent
        assert abs(absent) < 0.02

    def test_the_contrast_is_underpowered_at_the_pilot_replicate_count(self) -> None:
        """Six trajectories cannot separate a weak signal from nothing.

        Recorded as a test because it bears on the Stage 1 matrix: the pilot's
        three stochastic repetitions per semantic seed are enough for a strong
        effect and not enough for a marginal one. If the observed gap is small,
        the honest reading is "underpowered", not "absent".
        """
        weak = compute_separation(
            build(n_seeds=3, n_repeats=2, persistence=0.85, noise=0.2), params=PARAMS
        )
        null = compute_separation(
            build(n_seeds=3, n_repeats=2, persistence=0.0, noise=0.2), params=PARAMS
        )
        # The point estimates are not reliably ordered at this sample size.
        assert abs(weak.scalars["gap_last_band"] - null.scalars["gap_last_band"]) < 0.1

    def test_confidence_interval_brackets_the_estimate(self) -> None:
        result = compute_separation(build(persistence=1.0), params=PARAMS)
        for _, row in result.per_band.iterrows():
            assert row["gap_ci_low"] <= row["gap"] <= row["gap_ci_high"]

    def test_more_trajectories_narrow_the_interval(self) -> None:
        """The bootstrap must respond to the replicate count, not the pair count."""

        def width(n_repeats: int) -> float:
            result = compute_separation(
                build(n_seeds=3, n_repeats=n_repeats, persistence=0.9), params=PARAMS
            )
            return float((result.per_band["gap_ci_high"] - result.per_band["gap_ci_low"]).mean())

        assert width(6) < width(2)


class TestGuards:
    def test_one_semantic_seed_is_rejected(self) -> None:
        with pytest.raises(AnalysisError, match="two distinct semantic seeds"):
            compute_separation(build(n_seeds=1, n_repeats=4), params=PARAMS)

    def test_missing_within_control_is_rejected(self) -> None:
        """Without D_within there is no control, so the contrast is uninterpretable."""
        with pytest.raises(AnalysisError, match="no control"):
            compute_separation(build(n_seeds=4, n_repeats=1), params=PARAMS)

    def test_mismatched_embedding_and_turnover_lengths_are_rejected(self) -> None:
        with pytest.raises(AnalysisError):
            Trajectory(
                trajectory_id="t",
                semantic_seed="a",
                stochastic_seed=1,
                embeddings=np.zeros((5, DIM)),
                turnovers=np.zeros(3),
            )
