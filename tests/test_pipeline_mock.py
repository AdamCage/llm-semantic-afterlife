"""End-to-end pipeline over the offline fixture.

The mock generator is a hidden Markov chain over five topics with a deliberately
non-reversible transition matrix, so this exercises the real code paths — window,
chunker, checkpointing, resume, embedding, geometry — against a process whose
structure we know.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from semantic_afterlife.config import (
    GeneratorConfig,
    SamplingConfig,
    SeedSpec,
    Settings,
    WindowConfig,
)
from semantic_afterlife.generation.trajectory import (
    TrajectoryRunner,
    build_request,
    step_seed,
    trajectory_id,
)
from semantic_afterlife.hashing import sha256_obj
from semantic_afterlife.ledger import Ledger
from semantic_afterlife.logging_utils import EventLogger, read_events
from semantic_afterlife.providers.mock import TOPIC_NAMES, TRANSITION_MATRIX, MockClient
from semantic_afterlife.tokenization import WhitespaceTokenizer

GENERATOR = GeneratorConfig(
    slug="mock-hmm",
    model_id="mock/hmm-5topic",
    api="mock",
    tokenizer_repo="mock",
    continuation="raw_completion",
    is_base_model=True,
    provider_slug="mock",
    price_usd_per_m_input=0.0,
    price_usd_per_m_output=0.0,
)
WINDOW = WindowConfig(W=1024, block_size=256, target_tokens=4096, chunk_size=256)
SAMPLING = SamplingConfig(temperature=0.7)
SEED = SeedSpec(id="physics", domain="physics", text="quantum entropy momentum lattice photon")


def _runner(tmp_path: Path, *, target_tokens: int | None = None) -> TrajectoryRunner:
    from semantic_afterlife.paths import RunPaths

    paths = RunPaths(root=tmp_path / "run", run_id="test-run").ensure()
    window = (
        WINDOW
        if target_tokens is None
        else WINDOW.model_copy(update={"target_tokens": target_tokens})
    )
    return TrajectoryRunner(
        generator=GENERATOR,
        window_config=window,
        sampling=SAMPLING,
        seed_spec=SEED,
        stochastic_seed=1,
        tokenizer=WhitespaceTokenizer(),
        client=MockClient(),
        paths=paths,
        events=EventLogger(paths.events, "test-run"),
        ledger=Ledger(
            tmp_path / "spend.jsonl",
            run_id="test-run",
            per_run_ceiling_usd=1.0,
            total_ceiling_usd=1.0,
        ),
    )


class TestTrajectoryRunner:
    def test_completes_and_reaches_the_target(self, tmp_path: Path) -> None:
        runner = _runner(tmp_path)
        result = asyncio.run(runner.run())
        assert result.status == "COMPLETED"
        assert result.generated_tokens >= WINDOW.target_tokens
        assert result.n_chunks > 0
        assert result.roundtrip_failures == 0

    def test_writes_checkpoints_text_and_events(self, tmp_path: Path) -> None:
        runner = _runner(tmp_path)
        asyncio.run(runner.run())
        steps = runner.paths.trajectory_steps(runner.id)
        text = runner.paths.trajectory_text(runner.id)
        assert steps.is_file() and steps.stat().st_size > 0
        assert text.is_file() and len(text.read_text(encoding="utf-8")) > 1000
        assert runner.paths.trajectory_requests(runner.id).is_file()

        events = read_events(runner.paths.events)
        names = {event["event"] for event in events}
        assert "generation.trajectory.started" in names
        assert "generation.step.completed" in names
        assert "generation.trajectory.finished" in names

    def test_every_step_logs_the_window_state(self, tmp_path: Path) -> None:
        runner = _runner(tmp_path)
        asyncio.run(runner.run())
        steps = [
            event
            for event in read_events(runner.paths.events)
            if event["event"] == "generation.step.completed"
        ]
        assert steps
        for event in steps:
            assert event["prompt_tokens_local"] <= WINDOW.W
            assert event["tokenizer_roundtrip_ok"] is True
            assert "past_horizon" in event
            assert "turnovers" in event
        # The seed must actually leave the window during the trajectory.
        assert any(event["past_horizon"] for event in steps)
        assert not steps[0]["past_horizon"]

    def test_resume_does_not_duplicate_work(self, tmp_path: Path) -> None:
        """A killed run must continue, not restart or double-count."""
        first = _runner(tmp_path, target_tokens=2048)
        first_result = asyncio.run(first.run())

        # Same paths, longer target: the second runner replays the checkpoint.
        second = _runner(tmp_path, target_tokens=4096)
        second_result = asyncio.run(second.run())

        assert second_result.generated_tokens > first_result.generated_tokens
        assert second_result.n_steps > first_result.n_steps
        resumed = [
            event
            for event in read_events(second.paths.events)
            if event["event"] == "generation.trajectory.resumed"
        ]
        assert resumed and resumed[0]["steps_replayed"] == first_result.n_steps


class TestResultsFrame:
    """A batch where everything failed must still produce a readable summary.

    Measured the hard way in S1.0: every trajectory failed before its first
    response, so `served_providers` was an empty mapping in every row, pyarrow
    could not infer a struct type, and the parquet write crashed -- losing the
    record at the exact moment it was most needed.
    """

    def _result(self, tid: str, **overrides: object):  # type: ignore[no-untyped-def]
        from semantic_afterlife.generation.trajectory import TrajectoryResult

        base = {
            "trajectory_id": tid,
            "status": "FAILED",
            "generated_tokens": 0,
            "n_steps": 0,
            "n_chunks": 0,
            "stop_events": 0,
            "empty_completions": 0,
            "roundtrip_failures": 0,
            "horizon_tokens": 0,
            "seed_tokens": 0,
            "cost_usd": 0.0,
            "prompt_tokens_total": 0,
            "completion_tokens_total": 0,
        }
        base.update(overrides)
        return TrajectoryResult(**base)  # type: ignore[arg-type]

    def test_all_failed_batch_is_writable(self, tmp_path: Path) -> None:
        from semantic_afterlife.generation.trajectory import results_to_frame

        frame = results_to_frame([self._result("a"), self._result("b")])
        frame.to_parquet(tmp_path / "trajectories.parquet", index=False)
        assert (tmp_path / "trajectories.parquet").is_file()
        assert list(frame["served_providers"]) == ["{}", "{}"]

    def test_mixed_batch_preserves_provider_counts(self, tmp_path: Path) -> None:
        from semantic_afterlife.generation.trajectory import results_to_frame

        frame = results_to_frame(
            [
                self._result("a"),
                self._result("b", status="COMPLETED", served_providers={"DeepInfra": 3}),
            ]
        )
        frame.to_parquet(tmp_path / "t.parquet", index=False)
        recovered = pd.read_parquet(tmp_path / "t.parquet")
        assert json.loads(recovered["served_providers"].iloc[1]) == {"DeepInfra": 3}

    def test_stop_event_rate_is_defined_for_zero_steps(self) -> None:
        """Division by the step count must not blow up on a failed trajectory."""
        assert self._result("a").as_dict()["stop_event_rate"] == 0.0


class TestRequestConstruction:
    def test_raw_completion_sends_a_prompt(self) -> None:
        request = build_request(GENERATOR, SAMPLING, prompt="abc", max_tokens=16, seed=1)
        assert request.prompt == "abc"
        assert request.messages is None
        assert request.allow_fallbacks is False

    def test_assistant_prefill_puts_the_window_in_an_assistant_turn(self) -> None:
        generator = GENERATOR.model_copy(update={"continuation": "assistant_prefill"})
        request = build_request(generator, SAMPLING, prompt="abc", max_tokens=16, seed=1)
        assert request.messages is not None
        assert request.messages[-1] == {"role": "assistant", "content": "abc"}

    def test_chat_instructed_includes_the_instruction(self) -> None:
        generator = GENERATOR.model_copy(
            update={
                "continuation": "chat_instructed",
                "continuation_instruction": "Continue the text.",
            }
        )
        request = build_request(generator, SAMPLING, prompt="abc", max_tokens=16, seed=1)
        assert request.messages is not None
        assert "Continue the text." in request.messages[-1]["content"]

    def test_system_prompt_marks_the_run_as_forced(self) -> None:
        unforced = GENERATOR.model_copy(update={"continuation": "assistant_prefill"})
        forced = unforced.model_copy(update={"system_prompt": "You are helpful."})
        assert unforced.forcing == "unforced"
        assert forced.forcing == "fixed"
        request = build_request(forced, SAMPLING, prompt="abc", max_tokens=16, seed=1)
        assert request.messages is not None
        assert request.messages[0]["role"] == "system"


class TestStepSeed:
    def test_is_deterministic_and_step_dependent(self) -> None:
        assert step_seed(7, 3) == step_seed(7, 3)
        assert step_seed(7, 3) != step_seed(7, 4)
        assert step_seed(7, 3) != step_seed(8, 3)

    def test_stays_in_range(self) -> None:
        for step in range(0, 5000, 97):
            assert 0 <= step_seed(12345, step) < 2**31 - 1

    def test_trajectory_ids_are_unique_per_cell(self) -> None:
        ids = {
            trajectory_id(
                generator="g",
                W=W,
                temperature=temperature,
                semantic_seed=seed,
                stochastic_seed=stochastic,
            )
            for W in (4096, 8192)
            for temperature in (0.3, 1.0)
            for seed in ("physics", "love")
            for stochastic in (1, 2)
        }
        assert len(ids) == 16


class TestMockFixture:
    def test_transition_matrix_is_row_stochastic(self) -> None:
        assert np.allclose(TRANSITION_MATRIX.sum(axis=1), 1.0)

    def test_transition_matrix_is_deliberately_non_reversible(self) -> None:
        """Ground truth for the irreversibility estimators: J != 0 by construction."""
        assert not np.allclose(TRANSITION_MATRIX, TRANSITION_MATRIX.T)

    def test_topics_have_disjoint_vocabularies(self) -> None:
        from semantic_afterlife.providers.mock import TOPICS

        seen: set[str] = set()
        for name in TOPIC_NAMES:
            words = set(TOPICS[name])
            assert not (words & seen), f"{name} shares vocabulary with an earlier topic"
            seen |= words

    def test_generation_is_reproducible_for_a_fixed_seed(self) -> None:
        client = MockClient()
        request = build_request(
            GENERATOR, SAMPLING, prompt="quantum entropy", max_tokens=64, seed=5
        )
        first = asyncio.run(client.complete(request))
        second = asyncio.run(client.complete(request))
        assert first.text == second.text

    def test_embeddings_separate_topics(self) -> None:
        """Without topic structure in the fixture, downstream analysis would test nothing."""
        from semantic_afterlife.providers.base import EmbeddingRequest
        from semantic_afterlife.providers.mock import TOPICS

        client = MockClient()
        texts = tuple(" ".join(TOPICS[name] * 4) for name in TOPIC_NAMES)
        response = asyncio.run(client.embed(EmbeddingRequest(model_id="mock", inputs=texts)))
        matrix = np.asarray(response.vectors)
        matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
        similarity = matrix @ matrix.T
        off_diagonal = similarity[~np.eye(len(TOPIC_NAMES), dtype=bool)]
        assert off_diagonal.max() < 0.5


class TestSettings:
    def test_secrets_are_never_serialised(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from semantic_afterlife.provenance import settings_snapshot

        monkeypatch.setenv("ROUTERAI_API_KEY", "super-secret-value")
        settings = Settings()
        snapshot = settings_snapshot(settings)
        assert "super-secret-value" not in sha256_obj(snapshot)
        assert "super-secret-value" not in str(snapshot)
        assert snapshot["routerai_key_fingerprint"].startswith("sha256:")

    def test_missing_key_raises_a_typed_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from semantic_afterlife.errors import MissingCredentialsError

        monkeypatch.delenv("ROUTERAI_API_KEY", raising=False)
        monkeypatch.setenv("ROUTERAI_API_KEY", "")
        with pytest.raises(MissingCredentialsError):
            Settings().api_key("routerai")
