"""Config loading, the cost law, and budget enforcement."""

from __future__ import annotations

from pathlib import Path

import pytest

from semantic_afterlife.config import (
    WindowConfig,
    load_experiment_config,
    load_seed_bank,
)
from semantic_afterlife.costs import estimate_experiment, summarise, trajectory_tokens
from semantic_afterlife.errors import BudgetExceededError, ConfigError
from semantic_afterlife.ledger import Ledger, Usage


class TestWindowConfig:
    def test_turnovers_and_steps(self) -> None:
        window = WindowConfig(W=8192, block_size=1024, target_tokens=262144)
        assert window.n_steps == 256
        assert window.turnovers == 32.0
        assert window.stride == 1024
        assert window.n_chunks == 256

    def test_block_larger_than_window_is_rejected(self) -> None:
        with pytest.raises(ConfigError):
            WindowConfig(W=512, block_size=1024, target_tokens=8192)

    def test_trajectory_shorter_than_window_is_rejected(self) -> None:
        """A trajectory that never crosses the horizon measures nothing we care about."""
        with pytest.raises(ConfigError):
            WindowConfig(W=8192, block_size=1024, target_tokens=4096)

    def test_input_tokens_follow_the_cost_law(self) -> None:
        """input ~ T*W/S once the window has filled, with a ramp before that."""
        window = WindowConfig(W=8192, block_size=1024, target_tokens=262144)
        asymptotic = window.target_tokens * window.W // window.stride
        assert window.estimated_input_tokens < asymptotic
        assert window.estimated_input_tokens > asymptotic * 0.95

    def test_amplification_scales_with_W_over_S(self) -> None:
        small = WindowConfig(W=8192, block_size=1024, target_tokens=262144)
        large = WindowConfig(W=32768, block_size=1024, target_tokens=262144)
        small_in, small_out = trajectory_tokens(small)
        large_in, large_out = trajectory_tokens(large)
        assert small_out == large_out
        # Four times the window, four times the input cost, one quarter the turnovers.
        assert large_in / small_in == pytest.approx(4.0, rel=0.05)
        assert large.turnovers == pytest.approx(small.turnovers / 4)


class TestConfigLoading:
    def test_stage0_smoke_loads(self, repo: Path) -> None:
        config, resolved, sha = load_experiment_config(repo / "configs/stages/stage0_smoke.yaml")
        assert config.stage == "s0"
        assert config.n_trajectories == 2
        assert len(sha) == 64
        assert resolved["generators"][0]["slug"] == "mock-hmm"

    def test_generator_library_is_resolved_by_slug(self, repo: Path) -> None:
        config, _resolved, _sha = load_experiment_config(repo / "configs/stages/stage0_audit.yaml")
        slugs = {g.slug for g in config.generators}
        assert "qwen3-8b" in slugs
        assert all(g.tokenizer_repo for g in config.generators)

    def test_pinning_defaults_to_no_fallbacks(self, repo: Path) -> None:
        """ADR-0003: preferences only become constraints with allow_fallbacks=false."""
        config, _resolved, _sha = load_experiment_config(repo / "configs/stages/stage0_audit.yaml")
        assert all(g.allow_fallbacks is False for g in config.generators)

    def test_unknown_slug_is_rejected(self, repo: Path, tmp_path: Path) -> None:
        path = tmp_path / "bad.yaml"
        path.write_text(
            "include:\n  - configs/models/generators.yaml\n"
            "stage: s0\nname: bad\n"
            "generators: [does-not-exist]\n"
            "windows:\n  - {W: 2048, block_size: 512, target_tokens: 4096}\n"
            "sampling:\n  - {temperature: 0.5}\n"
            "semantic_seeds: [physics]\nstochastic_seeds: [1]\n",
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="does-not-exist"):
            load_experiment_config(path)

    def test_config_hash_is_stable(self, repo: Path) -> None:
        _c1, _r1, sha1 = load_experiment_config(repo / "configs/stages/stage0_smoke.yaml")
        _c2, _r2, sha2 = load_experiment_config(repo / "configs/stages/stage0_smoke.yaml")
        assert sha1 == sha2

    def test_chat_instructed_requires_an_explicit_instruction(self, tmp_path: Path) -> None:
        """The instruction is permanent external forcing and must be recorded."""
        path = tmp_path / "bad.yaml"
        path.write_text(
            "stage: s0\nname: bad\n"
            "generators:\n"
            "  - slug: g\n    model_id: a/b\n    tokenizer_repo: mock\n"
            "    continuation: chat_instructed\n"
            "windows:\n  - {W: 2048, block_size: 512, target_tokens: 4096}\n"
            "sampling:\n  - {temperature: 0.5}\n"
            "semantic_seeds: [physics]\nstochastic_seeds: [1]\n",
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="continuation_instruction"):
            load_experiment_config(path)

    def test_unknown_key_is_rejected(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.yaml"
        path.write_text(
            "stage: s0\nname: bad\ntypo_key: 1\n"
            "generators:\n  - slug: g\n    model_id: a/b\n    tokenizer_repo: mock\n"
            "    continuation: raw_completion\n"
            "windows:\n  - {W: 2048, block_size: 512, target_tokens: 4096}\n"
            "sampling:\n  - {temperature: 0.5}\n"
            "semantic_seeds: [physics]\nstochastic_seeds: [1]\n",
            encoding="utf-8",
        )
        with pytest.raises(ConfigError):
            load_experiment_config(path)


class TestSeedBank:
    def test_loads_and_indexes(self, repo: Path) -> None:
        bank = load_seed_bank(repo / "configs/seeds/seed_bank_v1.yaml")
        assert len(bank.seeds) >= 10
        assert bank.by_id("physics").domain == "physics"

    def test_twin_pairs_are_linked(self, repo: Path) -> None:
        bank = load_seed_bank(repo / "configs/seeds/seed_bank_v1.yaml")
        twins = [s for s in bank.seeds if s.twin_of]
        assert twins
        for twin in twins:
            assert bank.by_id(twin.twin_of)

    def test_twins_differ_only_slightly(self, repo: Path) -> None:
        """The sensitivity experiment needs minimal, not arbitrary, perturbations."""
        import difflib

        bank = load_seed_bank(repo / "configs/seeds/seed_bank_v1.yaml")
        for twin in (s for s in bank.seeds if s.twin_of):
            other = bank.by_id(twin.twin_of)
            # autojunk=False: the default heuristic reports near-identical prose as
            # dissimilar once the strings exceed 200 characters.
            ratio = difflib.SequenceMatcher(None, twin.text, other.text, autojunk=False).ratio()
            assert ratio > 0.85, f"{twin.id} and {other.id} differ too much ({ratio:.2f})"

    def test_unknown_seed_raises(self, repo: Path) -> None:
        bank = load_seed_bank(repo / "configs/seeds/seed_bank_v1.yaml")
        with pytest.raises(ConfigError):
            bank.by_id("nope")


PILOT_CONFIGS = (
    "configs/stages/stage1_pilot_core.yaml",
    "configs/stages/stage1_pilot_replication.yaml",
)


class TestEstimates:
    @pytest.mark.parametrize("path", PILOT_CONFIGS)
    def test_matrix_estimate_counts_trajectories(self, repo: Path, path: str) -> None:
        config, _resolved, _sha = load_experiment_config(repo / path)
        estimates = estimate_experiment(config)
        total = summarise(estimates)
        assert total["n_trajectories"] == config.n_trajectories
        assert total["output_tokens"] > 0

    @pytest.mark.parametrize("path", PILOT_CONFIGS)
    def test_input_dominates_for_large_W_over_S(self, repo: Path, path: str) -> None:
        config, _resolved, _sha = load_experiment_config(repo / path)
        for estimate in estimate_experiment(config):
            assert estimate.input_tokens > 5 * estimate.output_tokens

    @pytest.mark.parametrize("path", PILOT_CONFIGS)
    def test_pilot_forecast_stays_within_its_declared_budget(self, repo: Path, path: str) -> None:
        """The budget guard is only meaningful if the committed configs satisfy it."""
        config, _resolved, _sha = load_experiment_config(repo / path)
        total = summarise(estimate_experiment(config))
        assert config.budget_usd is not None
        assert total["total_usd"] <= config.budget_usd

    def test_block_fill_inflates_the_input_forecast(self) -> None:
        """S0.7: models stop early, so reaching T costs more window re-sends.

        Measured against the live micro-trajectory: assuming full blocks
        underestimated input by 20.7%; the measured fill of 0.88 brings it to
        -0.6%.
        """
        window = WindowConfig(W=2048, block_size=512, target_tokens=8192, chunk_size=512)
        full_input, full_output = trajectory_tokens(window, block_fill=1.0)
        real_input, real_output = trajectory_tokens(window, block_fill=0.88)

        assert real_input > full_input
        # Output is bounded by T either way; only the input side scales.
        assert real_output == full_output == window.target_tokens

        observed_input = 33375
        assert abs(real_input / observed_input - 1.0) < 0.05
        assert abs(full_input / observed_input - 1.0) > 0.15


class TestLedger:
    def _ledger(self, tmp_path: Path, **kwargs: float) -> Ledger:
        return Ledger(
            tmp_path / "spend.jsonl",
            run_id="test-run",
            per_run_ceiling_usd=kwargs.get("per_run", 1.0),
            total_ceiling_usd=kwargs.get("total", 10.0),
            stage_ceiling_usd=kwargs.get("stage"),
        )

    def test_reserve_under_ceiling_passes(self, tmp_path: Path) -> None:
        self._ledger(tmp_path).reserve(0.5, what="probe")

    def test_reserve_over_per_run_ceiling_raises(self, tmp_path: Path) -> None:
        with pytest.raises(BudgetExceededError, match="per-run ceiling"):
            self._ledger(tmp_path, per_run=0.1).reserve(0.5, what="probe")

    def test_reserve_over_stage_ceiling_raises(self, tmp_path: Path) -> None:
        with pytest.raises(BudgetExceededError, match="stage budget"):
            self._ledger(tmp_path, per_run=10.0, total=100.0, stage=0.2).reserve(0.5, what="probe")

    def test_recorded_spend_accumulates_and_persists(self, tmp_path: Path) -> None:
        ledger = self._ledger(tmp_path)
        for _ in range(3):
            ledger.record(
                Usage(prompt_tokens=100, completion_tokens=50, cost_usd=0.01), kind="completion"
            )
        assert ledger.run_spend_usd == pytest.approx(0.03)

        reopened = self._ledger(tmp_path)
        assert reopened.project_spend_usd == pytest.approx(0.03)
        assert reopened.remaining_project_usd == pytest.approx(10.0 - 0.03)

    def test_historical_spend_counts_towards_the_total_ceiling(self, tmp_path: Path) -> None:
        first = self._ledger(tmp_path, per_run=10.0, total=0.05)
        first.record(Usage(prompt_tokens=1, completion_tokens=1, cost_usd=0.04), kind="completion")
        second = self._ledger(tmp_path, per_run=10.0, total=0.05)
        with pytest.raises(BudgetExceededError, match="total"):
            second.reserve(0.02, what="probe")

    def test_cache_hits_cost_nothing(self, tmp_path: Path) -> None:
        ledger = self._ledger(tmp_path)
        ledger.record(Usage.zero(), kind="completion")
        assert ledger.run_spend_usd == 0.0
