"""F4/F6 sample split: twins must not enter domain D_between."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from semantic_afterlife.analysis.occupancy import (
    DOMAIN_SEED_ORDER,
    TWIN_SEED_ORDER,
    filter_raw_lock,
    last_band_gap_from_matrix,
    last_band_seed_matrix,
    leave_one_seed_out_gaps,
    lock_rate_by_seed,
    occupancy_embed_runs,
    quarantine_f6_ci_columns,
    require_occupancy_grid,
    split_domain_twin,
    unique_domain_pair_distances,
    within_pair_randomization,
)
from semantic_afterlife.analysis.separation import Trajectory
from semantic_afterlife.errors import AnalysisError


def _tid(seed: str, sto: int, *, prefix: str = "or-qwen3-8b", t: str = "T0p3") -> str:
    return f"{prefix}__W4096__{t}__{seed}__s{sto}"


def _rows(*seeds: str, prefix: str = "or-qwen3-8b", t: str = "T0p3") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trajectory_id": [
                _tid(seed, sto, prefix=prefix, t=t) for seed in seeds for sto in (1, 2)
            ],
            "semantic_seed": [seed for seed in seeds for _ in (1, 2)],
        }
    )


class TestFilterRawLock:
    def test_drops_prefill_and_other_temperatures(self) -> None:
        frame = pd.concat(
            [
                _rows("physics", "surreal"),
                _rows("physics", prefix="or-qwen3-8b-prefill"),
                _rows("physics", t="T1"),
            ],
            ignore_index=True,
        )
        kept = filter_raw_lock(frame)
        assert set(kept["trajectory_id"]) == {
            _tid("physics", 1),
            _tid("physics", 2),
            _tid("surreal", 1),
            _tid("surreal", 2),
        }


class TestSplitDomainTwin:
    def test_twins_do_not_enter_domain(self) -> None:
        frame = _rows("physics", "surreal", "waterloo-won", "waterloo-lost")
        domain, twin = split_domain_twin(frame)
        assert set(domain["semantic_seed"]) == {"physics", "surreal"}
        assert set(twin["semantic_seed"]) == {"waterloo-won", "waterloo-lost"}
        assert not set(domain["trajectory_id"]) & set(twin["trajectory_id"])

    def test_unknown_seed_raises(self) -> None:
        frame = _rows("physics", "invented-seed")
        with pytest.raises(AnalysisError, match="unrecognised"):
            split_domain_twin(frame)

    def test_require_full_grid(self) -> None:
        domain = _rows(*DOMAIN_SEED_ORDER)
        twin = _rows(*TWIN_SEED_ORDER)
        require_occupancy_grid(domain, twin)
        trimmed = domain[domain["trajectory_id"] != domain["trajectory_id"].iloc[0]]
        with pytest.raises(AnalysisError, match="expected 20"):
            require_occupancy_grid(trimmed, twin)


class TestLockRate:
    def test_reports_k_over_n_and_seed_hits(self) -> None:
        rows = []
        for seed in ("physics", "love"):
            for sto, flag in ((1, True), (2, seed == "physics")):
                rows.append(
                    {
                        "trajectory_id": _tid(seed, sto),
                        "degenerate": flag,
                    }
                )
        rates = lock_rate_by_seed(pd.DataFrame(rows))
        physics = rates.loc[rates["semantic_seed"] == "physics"].iloc[0]
        love = rates.loc[rates["semantic_seed"] == "love"].iloc[0]
        overall = rates.loc[rates["semantic_seed"] == "_domain_all"].iloc[0]
        hits = rates.loc[rates["semantic_seed"] == "_domain_seeds_with_a_lock"].iloc[0]
        assert physics["k_over_n"] == "2/2"
        assert love["k_over_n"] == "1/2"
        assert overall["k_over_n"] == "3/4"
        assert hits["k_over_n"] == "2/2"


class TestLastBandMatrix:
    def test_diagonal_is_within_and_matrix_is_symmetric(self) -> None:
        rng = np.random.default_rng(0)
        turnovers = np.linspace(0.0, 12.0, 12)
        trajectories: list[Trajectory] = []
        centres = {
            "physics": np.array([1.0, 0.0, 0.0]),
            "surreal": np.array([0.0, 1.0, 0.0]),
            "finance": np.array([0.0, 0.0, 1.0]),
        }
        for seed, centre in centres.items():
            for sto in (1, 2):
                jitter = 0.05 * rng.normal(size=(12, 3))
                embeddings = centre + jitter
                embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
                trajectories.append(
                    Trajectory(
                        trajectory_id=_tid(seed, sto),
                        semantic_seed=seed,
                        stochastic_seed=sto,
                        embeddings=embeddings,
                        turnovers=turnovers,
                        W=4096,
                        temperature=0.3,
                        generator="or-qwen3-8b",
                    )
                )
        matrix = last_band_seed_matrix(trajectories)
        seeds = ["physics", "surreal", "finance"]
        for seed in seeds:
            diag = matrix[(matrix["seed_row"] == seed) & (matrix["seed_col"] == seed)].iloc[0]
            assert diag["kind"] == "within"
            assert diag["distance"] < 0.05
        for a, b in (("physics", "surreal"), ("physics", "finance"), ("surreal", "finance")):
            ab = matrix[(matrix["seed_row"] == a) & (matrix["seed_col"] == b)].iloc[0]
            ba = matrix[(matrix["seed_row"] == b) & (matrix["seed_col"] == a)].iloc[0]
            assert ab["kind"] == "between"
            assert ab["distance"] == pytest.approx(ba["distance"])
            assert ab["distance"] > 0.5


class TestOccupancyEmbedRuns:
    def test_gemini_is_not_the_s5_two_space_embed(self) -> None:
        s51, s22 = occupancy_embed_runs("gemini-embed-001")
        assert s51.startswith("s6-embed-")
        assert s22.startswith("s6-embed-")
        bge_s51, bge_s22 = occupancy_embed_runs("bge-m3")
        qwen_s51, qwen_s22 = occupancy_embed_runs("qwen3-embed-8b")
        assert bge_s51.startswith("s5-embed-")
        assert qwen_s51 == bge_s51
        assert bge_s22.startswith("s2-embed-")
        assert qwen_s22 == bge_s22
        assert s51 != bge_s51
        assert s22 != bge_s22

    def test_unknown_space_raises(self) -> None:
        with pytest.raises(AnalysisError, match="no occupancy embed runs"):
            occupancy_embed_runs("invented-space")


def _toy_domain_matrix() -> pd.DataFrame:
    """Three seeds: close within, far between; one missing within diagonal."""
    rows = [
        ("physics", "physics", "within", np.nan),
        ("surreal", "surreal", "within", 0.10),
        ("finance", "finance", "within", 0.20),
        ("physics", "surreal", "between", 0.80),
        ("surreal", "physics", "between", 0.80),
        ("physics", "finance", "between", 0.90),
        ("finance", "physics", "between", 0.90),
        ("surreal", "finance", "between", 1.00),
        ("finance", "surreal", "between", 1.00),
    ]
    return pd.DataFrame(rows, columns=["seed_row", "seed_col", "kind", "distance"])


class TestSeedPairInference:
    def test_unique_pairs_drop_nan_and_dedupe_between(self) -> None:
        pairs = unique_domain_pair_distances(_toy_domain_matrix())
        assert set(pairs["pair_kind"]) == {"within", "between"}
        assert int((pairs["pair_kind"] == "within").sum()) == 2
        assert int((pairs["pair_kind"] == "between").sum()) == 3

    def test_gap_is_unweighted_mean_of_finite_pairs(self) -> None:
        stats = last_band_gap_from_matrix(_toy_domain_matrix())
        assert stats["n_within_pairs"] == 2
        assert stats["n_between_pairs"] == 3
        assert stats["d_within"] == pytest.approx(0.15)
        assert stats["d_between"] == pytest.approx(0.90)
        assert stats["gap"] == pytest.approx(0.75)

    def test_leave_one_seed_out_drops_that_seed_only(self) -> None:
        loo = leave_one_seed_out_gaps(_toy_domain_matrix())
        physics = loo.loc[loo["dropped_seed"] == "physics"].iloc[0]
        assert int(physics["n_within_pairs"]) == 2
        assert int(physics["n_between_pairs"]) == 1
        assert physics["gap"] == pytest.approx(1.00 - 0.15)

    def test_randomization_observed_gap_is_extreme(self) -> None:
        result = within_pair_randomization(_toy_domain_matrix(), n_perm=199, seed=0)
        assert result["gap"] == pytest.approx(0.75)
        assert result["n_perm"] == 199
        assert float(result["p_value"]) == pytest.approx(
            (1.0 + int(result["n_extreme"])) / 200.0
        )
        # Two smallest of five unique distances: 1 / C(5,2) = 0.1 of permutations.
        assert 0.02 < float(result["p_value"]) < 0.20

    def test_mixed_embeddings_are_refused(self) -> None:
        frame = _toy_domain_matrix()
        frame["embedding"] = ["bge-m3"] * 5 + ["qwen3-embed-8b"] * 4
        with pytest.raises(AnalysisError, match="multiple embeddings"):
            last_band_gap_from_matrix(frame)

    def test_committed_matrix_gaps_match_headline_points(self) -> None:
        root = Path(__file__).resolve().parents[1]
        matrix = pd.read_csv(root / "artifacts/stage-6/occupancy/last_band_distance_matrix.csv")
        expected = {"bge-m3": 0.201, "qwen3-embed-8b": 0.390, "gemini-embed-001": 0.150}
        for space, gap in expected.items():
            stats = last_band_gap_from_matrix(matrix.loc[matrix["embedding"] == space])
            assert stats["gap"] == pytest.approx(gap, abs=0.002)
            assert int(stats["n_within_pairs"]) == 9
            assert int(stats["n_between_pairs"]) == 45


class TestF6Quarantine:
    def test_drops_ci_columns_and_keeps_point_delta(self) -> None:
        frame = pd.DataFrame(
            {
                "band": [12],
                "scope": ["all"],
                "delta": [0.03],
                "d_twin": [0.3],
                "d_control": [0.27],
                "delta_ci_low": [-0.4],
                "delta_ci_high": [0.5],
                "divergent": [False],
                "n_twin_pairs": [4],
                "n_control_pairs": [4],
                "embedding": ["bge-m3"],
            }
        )
        canonical, legacy = quarantine_f6_ci_columns(frame)
        assert "delta_ci_low" not in canonical.columns
        assert "delta_ci_high" not in canonical.columns
        assert float(canonical["delta"].iloc[0]) == pytest.approx(0.03)
        assert "delta_ci_low" in legacy.columns
        assert float(legacy["delta"].iloc[0]) == pytest.approx(0.03)
