"""Planning-only stages must remain valid CLI inputs without generation."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from semantic_afterlife.cli import app
from semantic_afterlife.config import load_experiment_config


@pytest.mark.usefixtures("isolated_env")
def test_plan_accepts_zero_trajectory_synthesis(repo: Path) -> None:
    result = CliRunner().invoke(
        app, ["plan", "--config", str(repo / "configs/stages/stage13_synthesis.yaml")]
    )

    assert result.exit_code == 0, result.output
    assert "0 trajectories" in result.output
    assert "matrix: no rows" in result.output


@pytest.mark.usefixtures("isolated_env")
def test_plan_still_expands_nonempty_matrix(repo: Path) -> None:
    config = repo / "configs/stages/stage0_smoke.yaml"
    experiment, _, _ = load_experiment_config(config)

    result = CliRunner().invoke(app, ["plan", "--config", str(config)])

    assert result.exit_code == 0, result.output
    assert experiment.n_trajectories > 0
    assert f"{experiment.n_trajectories} trajectories" in result.output
    assert "matrix: no rows" not in result.output


@pytest.mark.usefixtures("isolated_env")
def test_estimate_handles_zero_trajectory_synthesis(repo: Path) -> None:
    result = CliRunner().invoke(
        app, ["estimate", "--config", str(repo / "configs/stages/stage13_synthesis.yaml")]
    )

    assert result.exit_code == 0, result.output
    assert "forecast cost" in result.output
    assert "$0.00" in result.output
