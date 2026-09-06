"""Twin-seed contrast: recover no-detected-divergence vs divergence on synthetic embeddings."""

from __future__ import annotations

import numpy as np
import pytest

from semantic_afterlife.analysis.separation import Trajectory
from semantic_afterlife.analysis.twins import (
    TwinParams,
    compute_twin_contrast,
    family_name,
    twin_pairs_from_bank,
    twin_pairwise_distances,
    weighted_band_delta,
)
from semantic_afterlife.config import SeedBank, SeedSpec
from semantic_afterlife.errors import AnalysisError

N_CHUNKS = 24
DIM = 16
PARAMS = TwinParams(n_boot=400, turnover_bin=4.0, seed=1)
PAIRS = [("waterloo-won", "waterloo-lost")]


def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def _traj(
    seed: str,
    sto: int,
    embeddings: np.ndarray,
    *,
    turnovers: np.ndarray | None = None,
) -> Trajectory:
    if turnovers is None:
        turnovers = np.linspace(0.0, 12.0, embeddings.shape[0])
    return Trajectory(
        trajectory_id=f"{seed}__s{sto}",
        semantic_seed=seed,
        stochastic_seed=sto,
        embeddings=embeddings,
        turnovers=turnovers,
        W=4096,
        temperature=0.3,
        generator="or-qwen3-8b",
    )


def _four(*, offset: float, noise: float, rng_seed: int = 0) -> list[Trajectory]:
    """won/lost share a centre; ``offset`` moves lost along one axis."""
    rng = np.random.default_rng(rng_seed)
    centre = _unit(rng.normal(size=DIM))
    shift = np.zeros(DIM, dtype=np.float64)
    shift[0] = offset
    out: list[Trajectory] = []
    for seed, extra in (("waterloo-won", 0.0), ("waterloo-lost", 1.0)):
        base = _unit(centre + extra * shift)
        for sto in (1, 2):
            jitter = rng.normal(scale=noise, size=(N_CHUNKS, DIM))
            out.append(_traj(seed, sto, _unit(base + jitter)))
    return out


class TestTwinPairsFromBank:
    def test_reads_twin_of_once(self) -> None:
        bank = SeedBank(
            version="t",
            description="t",
            seeds=(
                SeedSpec(id="waterloo-won", domain="h", text="a"),
                SeedSpec(id="waterloo-lost", domain="h", text="b", twin_of="waterloo-won"),
                SeedSpec(id="physics", domain="p", text="c"),
            ),
        )
        assert twin_pairs_from_bank(bank) == [("waterloo-won", "waterloo-lost")]

    def test_unknown_twin_of_raises(self) -> None:
        bank = SeedBank(
            version="t",
            description="t",
            seeds=(SeedSpec(id="a", domain="h", text="x", twin_of="missing"),),
        )
        try:
            twin_pairs_from_bank(bank)
        except AnalysisError as exc:
            assert "unknown twin_of" in str(exc)
        else:
            raise AssertionError("expected AnalysisError")


class TestTwinDistances:
    def test_labels_matched_and_control(self) -> None:
        pairs = twin_pairwise_distances(_four(offset=0.0, noise=0.05), twin_pairs=PAIRS)
        kinds = pairs.groupby(["left", "right"]).first()["kind"].value_counts()
        assert kinds["twin_matched"] == 2  # s1-s1 and s2-s2
        assert kinds["control"] == 2  # won s1-s2, lost s1-s2
        assert "twin_crossed" not in kinds

    def test_does_not_pair_across_temperature(self) -> None:
        traj = _four(offset=1.0, noise=0.02)
        moved = traj[0]
        traj[0] = Trajectory(
            trajectory_id=moved.trajectory_id,
            semantic_seed=moved.semantic_seed,
            stochastic_seed=moved.stochastic_seed,
            embeddings=moved.embeddings,
            turnovers=moved.turnovers,
            W=4096,
            temperature=1.5,
            generator="or-qwen3-8b",
        )
        pairs = twin_pairwise_distances(traj, twin_pairs=PAIRS)
        involved = set(pairs["left"]) | set(pairs["right"])
        assert moved.trajectory_id not in involved


class TestTwinContrast:
    def test_no_detected_divergence_when_twins_share_a_centre(self) -> None:
        result = compute_twin_contrast(
            _four(offset=0.0, noise=0.04, rng_seed=2),
            twin_pairs=PAIRS,
            params=PARAMS,
        )
        assert result.scalars["divergent_at_last_band"] == 0.0
        assert result.scalars["no_detected_divergence_at_last_band"] == 1.0
        assert result.scalars["delta_ci_low"] <= 0.0

    def test_divergent_when_twins_are_offset(self) -> None:
        result = compute_twin_contrast(
            _four(offset=3.0, noise=0.03, rng_seed=3),
            twin_pairs=PAIRS,
            params=PARAMS,
        )
        assert result.scalars["divergent_at_last_band"] == 1.0
        assert result.scalars["no_detected_divergence_at_last_band"] == 0.0
        assert result.scalars["delta_ci_low"] > 0.0
        assert result.scalars["d_twin_last"] > result.scalars["d_control_last"]

    def test_family_scope_keeps_control_and_matched(self) -> None:
        result = compute_twin_contrast(
            _four(offset=3.0, noise=0.03, rng_seed=3),
            twin_pairs=PAIRS,
            params=PARAMS,
        )
        family = family_name("waterloo-won", PAIRS)
        last = result.per_band[
            (result.per_band["scope"] == family)
            & (result.per_band["band"] == result.per_band["band"].max())
        ].iloc[0]
        assert int(last["n_twin_pairs"]) == 2
        assert int(last["n_control_pairs"]) == 2
        assert bool(last["divergent"]) is True
        assert bool(last["no_detected_divergence"]) is False


class TestTwinBootstrapMultiplicity:
    def test_set_filter_is_not_a_bootstrap(self) -> None:
        """A draw [0,0,1,1] must not collapse to the unique set {0,1}.

        Two twin_matched pairs with distances 1 and 0, both controls 0.5.
        Doubling trajectories 0 and 2 weights the far pair 4:1 vs 1:1.
        """
        left = np.array([0, 1, 0, 2])
        right = np.array([2, 3, 1, 3])
        is_twin = np.array([True, True, False, False])
        distances = np.array([1.0, 0.0, 0.5, 0.5])
        unique = np.array([1, 1, 1, 1])
        doubled = np.array([2, 1, 2, 1])
        delta_unique = weighted_band_delta(left, right, is_twin, distances, unique)
        delta_doubled = weighted_band_delta(left, right, is_twin, distances, doubled)
        assert delta_unique == pytest.approx(0.0)
        assert delta_doubled == pytest.approx(0.3)

    def test_compute_contrast_emits_no_detected_divergence_column(self) -> None:
        result = compute_twin_contrast(
            _four(offset=0.0, noise=0.04, rng_seed=2),
            twin_pairs=PAIRS,
            params=PARAMS,
        )
        assert "no_detected_divergence" in result.per_band.columns
        assert "collapsed" not in result.per_band.columns
