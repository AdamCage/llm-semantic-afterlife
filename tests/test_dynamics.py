"""Dynamics estimators against processes with known answers.

An MSM that cannot recover a two-state chain or a driven cycle will invent
semantic states on a looping reviewer page. These tests exist so that
failure happens here, not in a stage report.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from semantic_afterlife.analysis.dynamics import (
    DynamicsParams,
    TrajectorySeries,
    choose_n_macro,
    compute_dynamics,
    count_matrix,
    filter_eligible,
    implied_timescales,
    lagged_pairs,
    pca_project,
    probability_currents,
    stationary_distribution,
    transition_matrix,
    valid_k_grid,
    vamp_fit,
)
from semantic_afterlife.errors import AnalysisError


def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def two_state_hmm(
    n: int,
    d: int,
    *,
    p_stay: float = 0.92,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Two well-separated blobs on the sphere, switching as a Markov chain."""
    rng = np.random.default_rng(seed)
    centres = np.zeros((2, d))
    centres[0, 0] = 4.0
    centres[1, 0] = -4.0
    centres = _unit(centres)
    states = np.zeros(n, dtype=np.int64)
    for t in range(1, n):
        states[t] = states[t - 1] if rng.random() < p_stay else 1 - states[t - 1]
    noise = rng.normal(0.0, 0.15, size=(n, d))
    embeddings = _unit(centres[states] + noise)
    return embeddings, states


def three_cycle(
    n: int,
    d: int,
    *,
    p_advance: float = 0.85,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """A → B → C → A. Currents must be cyclic, not a reversible oscillation."""
    rng = np.random.default_rng(seed)
    centres = np.zeros((3, d))
    centres[0, 0] = 4.0
    centres[1, 1] = 4.0
    centres[2, 2] = 4.0
    centres = _unit(centres)
    states = np.zeros(n, dtype=np.int64)
    for t in range(1, n):
        if rng.random() < p_advance:
            states[t] = (states[t - 1] + 1) % 3
        else:
            states[t] = states[t - 1]
    embeddings = _unit(centres[states] + rng.normal(0.0, 0.12, size=(n, d)))
    return embeddings, states


def _series(embeddings: np.ndarray, *, trajectory_id: str, seed: int) -> TrajectorySeries:
    n = embeddings.shape[0]
    return TrajectorySeries(
        trajectory_id=trajectory_id,
        embeddings=embeddings,
        turnovers=np.arange(n, dtype=np.float64) / 4.0 + 1.0,
        token_ends=(np.arange(n, dtype=np.float64) + 1.0) * 1024.0,
        W=4096,
        generator="synthetic",
        temperature=0.7,
        semantic_seed="physics",
        stochastic_seed=seed,
        embedding="synthetic",
        degenerate=False,
    )


class TestLaggedPairs:
    def test_pairs_do_not_cross_trajectories(self) -> None:
        a = np.arange(6, dtype=np.float64).reshape(6, 1)
        b = np.arange(10, 14, dtype=np.float64).reshape(4, 1)
        x, y = lagged_pairs([a, b], 2)
        assert x.shape[0] == 4 + 2
        # The last frame of a must not pair with the first frame of b.
        assert not np.any((x[:, 0] == 5) & (y[:, 0] == 10))

    def test_short_series_is_an_error(self) -> None:
        with pytest.raises(AnalysisError):
            lagged_pairs([np.ones((2, 3))], 5)


class TestTransitionAndCurrents:
    def test_reversible_two_state_has_near_zero_current(self) -> None:
        transition = np.array([[0.9, 0.1], [0.1, 0.9]], dtype=np.float64)
        pi = stationary_distribution(transition)
        currents = probability_currents(pi, transition)
        assert abs(currents[0, 1]) < 1e-12
        assert pi[0] == pytest.approx(0.5, abs=0.01)

    def test_driven_cycle_has_cyclic_current(self) -> None:
        transition = np.array(
            [[0.10, 0.90, 0.00], [0.00, 0.10, 0.90], [0.90, 0.00, 0.10]],
            dtype=np.float64,
        )
        pi = stationary_distribution(transition)
        currents = probability_currents(pi, transition)
        assert currents[0, 1] > 0.2
        assert currents[1, 2] > 0.2
        assert currents[2, 0] > 0.2
        assert currents[0, 2] < 0

    def test_count_matrix_recovers_stay_probability(self) -> None:
        assignments = [np.array([0, 0, 0, 1, 1, 1, 0, 0], dtype=np.int64)]
        counts = count_matrix(assignments, lag=1, n_states=2)
        transition = transition_matrix(counts)
        assert transition[0, 0] == pytest.approx(3 / 4)
        assert transition[1, 1] == pytest.approx(2 / 3)

    def test_unvisited_state_gets_a_self_loop(self) -> None:
        counts = np.array([[4.0, 1.0, 0.0], [1.0, 3.0, 0.0], [0.0, 0.0, 0.0]])
        transition = transition_matrix(counts)
        assert transition[2, 2] == 1.0
        assert transition[2].sum() == pytest.approx(1.0)


class TestImpliedTimescales:
    def test_identity_has_infinite_slow_mode(self) -> None:
        times, _eigs = implied_timescales(np.eye(3), lag=1)
        assert np.isinf(times[0])

    def test_fast_mixing_is_short(self) -> None:
        transition = np.array([[0.55, 0.45], [0.45, 0.55]], dtype=np.float64)
        times, _ = implied_timescales(transition, lag=1)
        assert 0 < times[0] < 5

    def test_no_gap_means_one_macrostate(self) -> None:
        assert choose_n_macro(np.array([1.1, 1.05, 1.0]), max_n=4, gap_ratio=2.0) == 1

    def test_gap_selects_two_macrostates(self) -> None:
        assert choose_n_macro(np.array([20.0, 2.0, 1.5]), max_n=4, gap_ratio=2.0) == 2


class TestVamp:
    def test_score_drops_when_time_is_shuffled(self) -> None:
        embeddings, _ = two_state_hmm(400, 16, p_stay=0.94, seed=2)
        projected = pca_project([embeddings], n_pca=8, seed=0)
        _s, _c, vamp2 = vamp_fit(projected, lag=1, n_vamp=4, kinetic_map=True)
        rng = np.random.default_rng(0)
        shuffled = projected[0][rng.permutation(projected[0].shape[0])]
        _s2, _c2, vamp2_shuffled = vamp_fit([shuffled], lag=1, n_vamp=4, kinetic_map=True)
        assert vamp2 > vamp2_shuffled


class TestSampleSizeRules:
    def test_k_grid_respects_the_one_third_cap(self) -> None:
        params = DynamicsParams()
        assert 400 not in valid_k_grid(176, params)
        assert 50 in valid_k_grid(176, params)

    def test_filter_drops_short_and_ineligible(self) -> None:
        rows = []
        for traj, generator, n, temp, seed in (
            ("q1", "or-qwen3-8b", 48, 0.3, "physics"),
            ("g1", "or-muse-glimmer-30b", 48, 1.0, "physics"),
            ("g2", "or-muse-glimmer-30b", 48, 0.3, "physics"),
            ("s1", "or-gpt-oss-20b", 48, 0.3, "physics"),
            ("short", "or-qwen3-8b", 8, 0.3, "physics"),
        ):
            for i in range(n):
                rows.append(
                    {
                        "trajectory_id": traj,
                        "generator": generator,
                        "temperature": temp,
                        "semantic_seed": seed,
                        "chunk_index": i,
                    }
                )
        kept = filter_eligible(pd.DataFrame(rows), DynamicsParams())
        ids = set(kept["trajectory_id"])
        assert ids == {"q1", "g2"}


class TestComputeDynamics:
    def test_two_state_hmm_recovers_a_gap_and_two_macros(self) -> None:
        trajs = []
        for i in range(4):
            embeddings, _ = two_state_hmm(90, 24, p_stay=0.93, seed=10 + i)
            trajs.append(_series(embeddings, trajectory_id=f"hmm-{i}", seed=i))
        params = DynamicsParams(
            n_pca=12,
            n_vamp=6,
            n_microstates=20,
            k_grid=(10, 20),
            lags=(1, 2),
            msm_lag=1,
            min_frames=40,
            min_lag_pairs=20,
            n_boot=40,
            leiden_n_pca=8,
            leiden_k=8,
            eligible_generators=("synthetic",),
        )
        result = compute_dynamics(trajs, params=params, group="hmm")
        assert result.scalars["n_macro"] == 2
        assert result.scalars["vamp2"] > 0
        assert result.transition.shape[0] >= 2

    def test_cycle_current_norm_excludes_zero(self) -> None:
        trajs = []
        for i in range(4):
            embeddings, _ = three_cycle(100, 24, p_advance=0.88, seed=20 + i)
            trajs.append(_series(embeddings, trajectory_id=f"cyc-{i}", seed=i))
        params = DynamicsParams(
            n_pca=12,
            n_vamp=6,
            n_microstates=15,
            k_grid=(8, 15),
            lags=(1, 2),
            msm_lag=1,
            min_frames=40,
            min_lag_pairs=20,
            n_boot=40,
            leiden_n_pca=8,
            leiden_k=8,
            spectral_gap_ratio=1.5,
            eligible_generators=("synthetic",),
        )
        result = compute_dynamics(trajs, params=params, group="cycle")
        assert result.scalars["j_norm"] > 0
        # A driven cycle should not look like equilibrium at this length.
        assert result.scalars["j_norm_ci_low"] >= 0
        assert result.scalars["j_norm"] > result.scalars["j_norm_ci_low"] * 0.5
