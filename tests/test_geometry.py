"""Estimators are validated against processes with known answers.

An estimator that cannot recover the truth on synthetic data will produce a
confident wrong number on real data. Each test below constructs a process whose
answer is known analytically and checks that the estimator finds it.
"""

from __future__ import annotations

import numpy as np
import pytest

from semantic_afterlife.analysis.geometry import (
    GeometryParams,
    autocorrelation,
    bootstrap_mean_ci,
    compute_geometry,
    cosine_distance_to,
    fit_msd_exponent,
    integrated_autocorrelation_time,
    mean_squared_displacement,
    recurrence_matrix,
    recurrence_quantification,
    step_displacement,
)
from semantic_afterlife.errors import AnalysisError

# The estimators L2-normalise their input, because embedding geometry is
# spherical: only direction carries meaning. Synthetic processes must therefore
# live on the sphere too, otherwise the test measures the normalisation rather
# than the estimator. A Euclidean ballistic path, for instance, converges to a
# single direction once normalised and would look *sub*diffusive.


def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def brownian(n: int, d: int, *, sigma: float = 0.05, seed: int = 0) -> np.ndarray:
    """Brownian motion on the unit sphere: MSD exponent alpha = 1 at short lags."""
    rng = np.random.default_rng(seed)
    x = np.zeros((n, d))
    x[0] = _unit(rng.normal(size=d))
    for t in range(1, n):
        x[t] = _unit(x[t - 1] + rng.normal(0.0, sigma, size=d))
    return x


def ornstein_uhlenbeck(
    n: int, d: int, *, theta: float = 0.15, sigma: float = 0.08, seed: int = 0
) -> np.ndarray:
    """Spherical process pulled towards a fixed pole: MSD saturates, alpha < 1."""
    rng = np.random.default_rng(seed)
    pole = _unit(rng.normal(size=d))
    x = np.zeros((n, d))
    x[0] = pole.copy()
    for t in range(1, n):
        x[t] = _unit(x[t - 1] + theta * (pole - x[t - 1]) + rng.normal(0.0, sigma, size=d))
    return x


def ballistic(n: int, d: int, *, omega: float = 0.004, seed: int = 0) -> np.ndarray:
    """Constant-speed motion along a great circle: alpha near 2 at short lags."""
    rng = np.random.default_rng(seed)
    e1 = _unit(rng.normal(size=d))
    e2 = rng.normal(size=d)
    e2 = _unit(e2 - (e2 @ e1) * e1)
    t = np.arange(n)[:, None]
    return _unit(
        np.cos(omega * t) * e1[None, :]
        + np.sin(omega * t) * e2[None, :]
        + rng.normal(0.0, 0.0005, size=(n, d))
    )


class TestMSD:
    def test_brownian_motion_gives_exponent_one(self) -> None:
        Z = brownian(4000, 16, sigma=0.02, seed=3)
        lags, msd, pairs = mean_squared_displacement(Z, max_lag=100)
        fit = fit_msd_exponent(lags, msd, pairs)
        assert fit["alpha"] == pytest.approx(1.0, abs=0.15)
        assert fit["r_squared"] > 0.95

    def test_confined_process_is_subdiffusive(self) -> None:
        Z = ornstein_uhlenbeck(4000, 16, seed=5)
        lags, msd, pairs = mean_squared_displacement(Z, max_lag=200)
        fit = fit_msd_exponent(lags, msd, pairs)
        assert fit["alpha"] < 0.6

    def test_directed_drift_is_superdiffusive(self) -> None:
        Z = ballistic(2000, 16, seed=7)
        lags, msd, pairs = mean_squared_displacement(Z, max_lag=100)
        fit = fit_msd_exponent(lags, msd, pairs)
        assert fit["alpha"] > 1.3

    def test_three_regimes_are_ordered(self) -> None:
        """The estimator must rank the regimes correctly, not just hit tolerances."""

        def alpha_of(Z: np.ndarray) -> float:
            lags, msd, pairs = mean_squared_displacement(Z, max_lag=150)
            return fit_msd_exponent(lags, msd, pairs)["alpha"]

        confined = alpha_of(ornstein_uhlenbeck(3000, 16, seed=11))
        diffusive = alpha_of(brownian(3000, 16, sigma=0.01, seed=11))
        directed = alpha_of(ballistic(3000, 16, seed=11))
        assert confined < diffusive < directed

    def test_pair_counts_decrease_with_lag(self) -> None:
        lags, _msd, pairs = mean_squared_displacement(brownian(500, 8), max_lag=50)
        assert pairs[0] > pairs[-1]
        assert np.all(np.diff(pairs) < 0)
        assert pairs[0] == 500 - lags[0]

    def test_too_short_series_is_rejected(self) -> None:
        with pytest.raises(AnalysisError):
            mean_squared_displacement(np.zeros((3, 4)))


class TestAutocorrelation:
    def test_white_noise_decorrelates_immediately(self) -> None:
        rng = np.random.default_rng(0)
        lags, acf = autocorrelation(rng.normal(size=5000), max_lag=20)
        assert acf[0] == pytest.approx(1.0)
        assert abs(acf[1]) < 0.06
        assert integrated_autocorrelation_time(lags, acf) < 1.5

    def test_ar1_has_the_known_decay(self) -> None:
        phi = 0.8
        rng = np.random.default_rng(1)
        x = np.zeros(20000)
        for t in range(1, x.size):
            x[t] = phi * x[t - 1] + rng.normal()
        _lags, acf = autocorrelation(x, max_lag=6)
        for lag in (1, 2, 3):
            assert acf[lag] == pytest.approx(phi**lag, abs=0.05)

    def test_constant_series_returns_zeros_not_nan(self) -> None:
        lags, acf = autocorrelation(np.full(100, 3.0), max_lag=5)
        assert np.all(np.isfinite(acf))
        assert acf[0] == 0.0
        assert lags[0] == 0


class TestRecurrence:
    def test_periodic_signal_is_highly_deterministic(self) -> None:
        t = np.linspace(0, 8 * np.pi, 600)
        Z = np.stack([np.sin(t), np.cos(t), np.zeros_like(t)], axis=1)
        R, epsilon = recurrence_matrix(Z, quantile=0.05)
        rqa = recurrence_quantification(R)
        assert epsilon > 0
        assert rqa["recurrence_rate"] == pytest.approx(0.05, abs=0.02)
        assert rqa["determinism"] > 0.9
        assert rqa["max_diagonal_line"] > 20

    def test_white_noise_has_little_diagonal_structure(self) -> None:
        rng = np.random.default_rng(2)
        R, _epsilon = recurrence_matrix(rng.normal(size=(600, 12)), quantile=0.05)
        rqa = recurrence_quantification(R)
        assert rqa["max_diagonal_line"] < 10

    def test_periodic_beats_noise_on_determinism(self) -> None:
        t = np.linspace(0, 8 * np.pi, 500)
        periodic = np.stack([np.sin(t), np.cos(t)], axis=1)
        rng = np.random.default_rng(3)
        noise = rng.normal(size=(500, 2))
        det_periodic = recurrence_quantification(recurrence_matrix(periodic)[0])["determinism"]
        det_noise = recurrence_quantification(recurrence_matrix(noise)[0])["determinism"]
        assert det_periodic > det_noise


class TestDistances:
    def test_cosine_distance_to_self_is_zero(self) -> None:
        rng = np.random.default_rng(4)
        Z = rng.normal(size=(50, 8))
        assert cosine_distance_to(Z, Z[0])[0] == pytest.approx(0.0, abs=1e-12)

    def test_opposite_vector_has_distance_two(self) -> None:
        v = np.array([[1.0, 0.0, 0.0]])
        assert cosine_distance_to(v, -v[0])[0] == pytest.approx(2.0)

    def test_step_displacement_length(self) -> None:
        rng = np.random.default_rng(5)
        Z = rng.normal(size=(30, 6))
        assert step_displacement(Z).shape == (29,)

    def test_zero_reference_is_rejected(self) -> None:
        with pytest.raises(AnalysisError):
            cosine_distance_to(np.ones((4, 3)), np.zeros(3))


class TestComputeGeometry:
    def _run(self, Z: np.ndarray, *, W: int = 8192, chunk: int = 1024):  # type: ignore[no-untyped-def]
        positions = (np.arange(Z.shape[0]) + 1) * chunk
        return compute_geometry(
            Z,
            trajectory_id="t0",
            token_positions=positions,
            W=W,
            params=GeometryParams(),
        )

    def test_returns_tidy_frames_with_expected_columns(self) -> None:
        result = self._run(brownian(200, 16, seed=6))
        assert {"chunk_index", "token_end", "turnover", "past_horizon"} <= set(
            result.per_chunk.columns
        )
        assert {"lag_chunks", "msd", "n_pairs"} <= set(result.msd.columns)
        assert result.per_chunk.shape[0] == 200

    def test_burn_in_marks_the_horizon(self) -> None:
        result = self._run(brownian(200, 16, seed=6), W=8192, chunk=1024)
        # W = 8 chunks, so the first 8 chunks are pre-horizon.
        assert int(result.per_chunk["past_horizon"].sum()) == 192
        assert result.scalars["n_chunks_post_horizon"] == 192
        assert result.scalars["burn_in_applied"] == 1.0

    def test_short_series_falls_back_and_records_it(self) -> None:
        """A trajectory too short to have a post-horizon segment must be flagged."""
        result = self._run(brownian(10, 8, seed=6), W=8192, chunk=1024)
        assert result.scalars["burn_in_applied"] == 0.0

    def test_single_chunk_does_not_crash(self) -> None:
        """S2.1 left 1-chunk failed trajectories (gpt-oss-20b, glimmer empty-EOS).

        Concatenating a 2-element finite-difference onto a length-1
        displacement used to raise ValueError and abort the whole run.
        """
        result = self._run(brownian(1, 8, seed=6), W=4096, chunk=1024)
        assert result.scalars["n_chunks"] == 1
        assert result.scalars["too_short_for_msd"] == 1.0
        assert result.per_chunk.shape[0] == 1
        assert np.isnan(result.per_chunk["step_displacement"].iloc[0])
        assert result.msd.empty
        assert result.autocorrelation.empty

    def test_three_chunks_skip_msd(self) -> None:
        result = self._run(brownian(3, 8, seed=6), W=4096, chunk=1024)
        assert result.scalars["n_chunks"] == 3
        assert result.scalars["too_short_for_msd"] == 1.0
        assert result.msd.empty
        # Early-return path skips ACF as well as MSD when n < 4.
        assert result.autocorrelation.empty

    def test_mismatched_positions_are_rejected(self) -> None:
        with pytest.raises(AnalysisError):
            compute_geometry(
                brownian(50, 8),
                trajectory_id="t",
                token_positions=np.arange(10),
                W=1024,
                params=GeometryParams(),
            )

    def test_seed_distance_is_included_when_given(self) -> None:
        Z = brownian(120, 12, seed=8)
        positions = (np.arange(120) + 1) * 1024
        result = compute_geometry(
            Z,
            trajectory_id="t",
            token_positions=positions,
            W=8192,
            params=GeometryParams(),
            seed_embedding=Z[0],
        )
        assert "distance_from_seed" in result.per_chunk.columns
        assert "mean_distance_from_seed" in result.scalars


class TestBootstrap:
    def test_ci_brackets_the_mean(self) -> None:
        rng = np.random.default_rng(9)
        values = rng.normal(5.0, 1.0, size=40)
        out = bootstrap_mean_ci(values, n_boot=500, seed=1)
        assert out["ci_low"] < out["mean"] < out["ci_high"]
        assert out["n"] == 40

    def test_ci_narrows_with_more_replicates(self) -> None:
        rng = np.random.default_rng(10)
        small = bootstrap_mean_ci(rng.normal(0, 1, 10), n_boot=800, seed=1)
        large = bootstrap_mean_ci(rng.normal(0, 1, 400), n_boot=800, seed=1)
        assert (large["ci_high"] - large["ci_low"]) < (small["ci_high"] - small["ci_low"])

    def test_empty_input_is_reported_not_raised(self) -> None:
        out = bootstrap_mean_ci(np.array([]), n_boot=10)
        assert out["n"] == 0
        assert np.isnan(out["mean"])
