"""Local provider (ADR-0011): cache, $0 ledger, tokenizer identity, pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from semantic_afterlife.config import (
    ExecutionMode,
    GeneratorConfig,
    SamplingConfig,
    SeedSpec,
    Settings,
    WindowConfig,
    load_experiment_config,
)
from semantic_afterlife.generation.trajectory import TrajectoryRunner, build_request
from semantic_afterlife.ledger import Ledger
from semantic_afterlife.logging_utils import EventLogger
from semantic_afterlife.paths import RunPaths
from semantic_afterlife.providers.cache import ResponseCache
from semantic_afterlife.providers.local import LocalClient, LocalGeneration
from semantic_afterlife.providers.registry import build_client
from semantic_afterlife.tokenization import WhitespaceTokenizer


class ScriptedBackend:
    def __init__(self, token_ids: list[int], finish_reason: str = "length") -> None:
        self.token_ids = token_ids
        self.finish_reason = finish_reason
        self.calls: list[list[int]] = []

    def generate(
        self,
        input_ids: list[int],
        *,
        max_tokens: int,
        temperature: float,
        top_p: float,
        top_k: int | None,
        repetition_penalty: float | None,
        seed: int | None,
        extra: dict[str, object],
    ) -> LocalGeneration:
        self.calls.append(list(input_ids))
        return LocalGeneration(
            token_ids=self.token_ids[:max_tokens],
            finish_reason=self.finish_reason,
        )


def _settings(tmp_path: Path, *, mode: ExecutionMode = ExecutionMode.LIVE) -> Settings:
    return Settings(
        afterlife_execution_mode=mode,
        afterlife_runs_dir=str(tmp_path / "runs"),
        afterlife_artifacts_dir=str(tmp_path / "artifacts"),
        afterlife_cache_dir=str(tmp_path / "cache"),
        afterlife_budget_usd_per_run=1.0,
        afterlife_budget_usd_total=1.0,
    )


def _client(
    tmp_path: Path,
    tokenizer: WhitespaceTokenizer,
    backend: ScriptedBackend,
    *,
    cache: ResponseCache | None = None,
    mode: ExecutionMode = ExecutionMode.LIVE,
) -> LocalClient:
    return LocalClient(
        _settings(tmp_path, mode=mode),
        cache=cache,
        tokenizer=tokenizer,
        backend=backend,
    )


@pytest.mark.asyncio
async def test_local_complete_is_free_and_counts_tokens(tmp_path: Path) -> None:
    tokenizer = WhitespaceTokenizer()
    continuation = " lattice photon gauge boson."
    ids = tokenizer.encode(continuation)
    backend = ScriptedBackend(ids)
    client = _client(tmp_path, tokenizer, backend)

    response = await client.complete(
        build_request(
            GeneratorConfig(
                slug="local-test",
                model_id="local/test",
                api="local",
                tokenizer_repo="mock",
                continuation="raw_completion",
                is_base_model=True,
                provider_slug="local",
                extra_body={"device": "cpu", "dtype": "float32"},
            ),
            SamplingConfig(temperature=0.7),
            prompt="quantum entropy",
            max_tokens=32,
            seed=1,
        )
    )

    assert response.text == continuation
    assert response.served_provider == "local"
    assert response.usage.cost_usd == 0.0
    assert response.usage.completion_tokens == len(ids)
    assert response.usage.prompt_tokens == tokenizer.count("quantum entropy")
    assert len(backend.calls) == 1


@pytest.mark.asyncio
async def test_local_stop_truncates_decoded_text(tmp_path: Path) -> None:
    tokenizer = WhitespaceTokenizer()
    ids = tokenizer.encode(" hello STOP more")
    backend = ScriptedBackend(ids)
    client = _client(tmp_path, tokenizer, backend)
    from semantic_afterlife.providers.base import CompletionRequest

    response = await client.complete(
        CompletionRequest(
            model_id="local/test",
            max_tokens=32,
            temperature=0.7,
            prompt="seed",
            stop=("STOP",),
        )
    )
    assert "STOP" not in response.text
    assert response.text.endswith(" hello ")


@pytest.mark.asyncio
async def test_local_replay_hits_cache_without_calling_backend(tmp_path: Path) -> None:
    tokenizer = WhitespaceTokenizer()
    ids = tokenizer.encode(" lattice")
    backend = ScriptedBackend(ids)
    cache = ResponseCache(tmp_path / "responses")
    live = _client(tmp_path, tokenizer, backend, cache=cache, mode=ExecutionMode.LIVE)
    request = build_request(
        GeneratorConfig(
            slug="local-test",
            model_id="local/test",
            api="local",
            tokenizer_repo="mock",
            continuation="raw_completion",
            is_base_model=True,
            provider_slug="local",
        ),
        SamplingConfig(temperature=0.3),
        prompt="quantum",
        max_tokens=8,
        seed=7,
    )
    first = await live.complete(request)
    assert first.from_cache is False
    assert len(backend.calls) == 1

    replay_backend = ScriptedBackend(ids)
    replay = _client(tmp_path, tokenizer, replay_backend, cache=cache, mode=ExecutionMode.REPLAY)
    second = await replay.complete(request)
    assert second.from_cache is True
    assert second.text == first.text
    assert replay_backend.calls == []


@pytest.mark.asyncio
async def test_local_embed_is_refused(tmp_path: Path) -> None:
    from semantic_afterlife.errors import ProviderError
    from semantic_afterlife.providers.base import EmbeddingRequest

    client = _client(tmp_path, WhitespaceTokenizer(), ScriptedBackend([1]))
    with pytest.raises(ProviderError, match="embeddings are not implemented"):
        await client.embed(EmbeddingRequest(model_id="local/test", inputs=("x",)))


def test_build_client_local_in_live_mode(
    isolated_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AFTERLIFE_EXECUTION_MODE", "live")
    from semantic_afterlife.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    client = build_client("local", settings, reuse=False)
    assert client.name == "local"


def test_local_smoke_config_loads(repo: Path) -> None:
    config, _resolved, sha = load_experiment_config(repo / "configs/stages/local_base_smoke.yaml")
    assert config.stage == "harness"
    assert config.n_trajectories == 2
    slugs = {g.slug for g in config.generators}
    assert slugs == {"local-gemma-3-270m", "local-gemma-3-1b-pt"}
    assert all(g.api == "local" for g in config.generators)
    assert all(g.is_base_model for g in config.generators)
    assert all(g.continuation == "raw_completion" for g in config.generators)
    assert config.windows[0].turnovers == 2.0
    assert len(sha) == 64


@pytest.mark.asyncio
async def test_trajectory_runner_accepts_local_client(tmp_path: Path) -> None:
    tokenizer = WhitespaceTokenizer()
    phrase = " lattice photon gauge boson renormalisation hamiltonian spin."
    backend = ScriptedBackend(tokenizer.encode(phrase))
    client = _client(tmp_path, tokenizer, backend)
    paths = RunPaths(root=tmp_path / "run", run_id="local-test").ensure()
    runner = TrajectoryRunner(
        generator=GeneratorConfig(
            slug="local-test",
            model_id="local/test",
            api="local",
            tokenizer_repo="mock",
            continuation="raw_completion",
            is_base_model=True,
            provider_slug="local",
            price_usd_per_m_input=0.0,
            price_usd_per_m_output=0.0,
        ),
        window_config=WindowConfig(W=64, block_size=16, target_tokens=64, chunk_size=32),
        sampling=SamplingConfig(temperature=0.7),
        seed_spec=SeedSpec(
            id="physics",
            domain="physics",
            text="quantum entropy momentum lattice photon",
        ),
        stochastic_seed=1,
        tokenizer=tokenizer,
        client=client,
        paths=paths,
        events=EventLogger(paths.events, "local-test"),
        ledger=Ledger(
            tmp_path / "spend.jsonl",
            run_id="local-test",
            per_run_ceiling_usd=1.0,
            total_ceiling_usd=1.0,
        ),
    )
    result = await runner.run()
    assert result.status == "COMPLETED"
    assert result.generated_tokens >= 64
    assert result.cost_usd == 0.0
    assert result.served_providers == {"local": result.n_steps}
    assert result.n_chunks >= 2
