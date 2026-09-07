"""ADR-0022 occupancy replication config: full 28-trajectory grid."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from semantic_afterlife.analysis.occupancy import DOMAIN_SEED_ORDER, TWIN_SEED_ORDER
from semantic_afterlife.config import load_experiment_config
from semantic_afterlife.costs import estimate_experiment, summarise

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "configs/stages/stage5_lock_occupancy_replication.yaml"
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from assemble_occupancy_replication import (  # noqa: E402
    _guard_out_dir,
    missing_data_from_trajectories,
)


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


def test_guard_refuses_stage5_and_stage6_occupancy() -> None:
    with pytest.raises(SystemExit, match="forbids"):
        _guard_out_dir(REPO / "artifacts/stage-5/occupancy")
    with pytest.raises(SystemExit, match="forbids"):
        _guard_out_dir(REPO / "artifacts/stage-6/occupancy")
    with pytest.raises(SystemExit, match="occupancy tree"):
        _guard_out_dir(REPO / "artifacts/stage-5/occupancy/nested")


def test_guard_allows_replication_dir() -> None:
    target = REPO / "artifacts/occupancy-replication"
    assert _guard_out_dir(target) == target


def test_assemble_cli_refuses_stage5_occupancy_out() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "assemble_occupancy_replication.py"),
            "--embed-two-space",
            "unused",
            "--embed-gemini",
            "unused",
            "--degeneracy",
            "unused.csv",
            "--out",
            "artifacts/stage-5/occupancy",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "forbids" in combined


def test_missing_data_keeps_failed_and_short_chunks() -> None:
    frame = pd.DataFrame(
        {
            "trajectory_id": [
                "or-qwen3-8b__W4096__T0p3__noise__s2",
                "or-qwen3-8b__W4096__T0p3__philosophy__s1",
                "or-qwen3-8b__W4096__T0p3__physics__s1",
            ],
            "status": ["FAILED", "COMPLETED", "COMPLETED"],
            "error": ["WindowProtocolError: collapsed", float("nan"), float("nan")],
            "generated_tokens": [49151, 49152, 49152],
            "n_chunks": [47, 47, 48],
            "roundtrip_failures": [1, 2, 0],
        }
    )
    missing = missing_data_from_trajectories(frame)
    assert set(missing["trajectory_id"]) == {
        "or-qwen3-8b__W4096__T0p3__noise__s2",
        "or-qwen3-8b__W4096__T0p3__philosophy__s1",
    }
    assert "physics" not in " ".join(missing["trajectory_id"])
