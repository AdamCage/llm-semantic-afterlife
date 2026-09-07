"""ADR-0022 occupancy replication config: full 28-trajectory grid."""

from __future__ import annotations

from pathlib import Path

from semantic_afterlife.analysis.occupancy import DOMAIN_SEED_ORDER, TWIN_SEED_ORDER
from semantic_afterlife.config import load_experiment_config
from semantic_afterlife.costs import estimate_experiment, summarise

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "configs/stages/stage5_lock_occupancy_replication.yaml"


def test_replication_yaml_is_full_occupancy_grid() -> None:
    config, _resolved, _sha = load_experiment_config(CONFIG)
    seeds = tuple(config.semantic_seeds)
    assert seeds[:2] == ("physics", "surreal")
    assert set(DOMAIN_SEED_ORDER).issubset(seeds)
    assert set(TWIN_SEED_ORDER).issubset(seeds)
    assert len(seeds) == 14
    assert config.n_trajectories == 28
    assert config.budget_usd == 8.0
    window = config.windows[0]
    assert window.W == 4096
    assert window.block_size == 1024
    assert window.target_tokens == 49152
    total = summarise(estimate_experiment(config))
    assert total["n_trajectories"] == 28
    assert total["total_usd"] < 10.0
    assert total["total_usd"] <= config.budget_usd
