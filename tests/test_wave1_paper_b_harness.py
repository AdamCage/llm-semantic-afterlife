"""Wave-1 Paper B harness: quant isolation, unload, serialization, persistence."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from semantic_afterlife.analysis.persistence import (
    TrajectoryEmbed,
    capped_late_jaccard,
    gap_vs_turnover,
    integer_l0_band_edges,
    log_turnover_bands,
    loo_by_seed,
    prefix_lock_escape,
)
from semantic_afterlife.config import (
    ExecutionMode,
    ExperimentConfig,
    GeneratorConfig,
    SamplingConfig,
    Settings,
    WindowConfig,
)
from semantic_afterlife.errors import ConfigError, ProviderError, ReasoningLeakError
from semantic_afterlife.generation.trajectory import build_request, plan_trajectories
from semantic_afterlife.providers.base import CompletionRequest, EmbeddingRequest
from semantic_afterlife.providers.local import (
    _LOAD_KEYS,
    LocalClient,
    LocalGeneration,
    _architecture_module_guesses,
    _resolve_model_class,
    assert_no_thinking,
)
from semantic_afterlife.providers.local_embed import LocalEmbedClient, ScriptedEmbedBackend
from semantic_afterlife.tokenization import WhitespaceTokenizer


class RecordingBackend:
    def __init__(self) -> None:
        self.generate_extras: list[dict[str, object]] = []

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
        self.generate_extras.append(dict(extra))
        return LocalGeneration(token_ids=[1, 2, 3], finish_reason="length")


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        afterlife_execution_mode=ExecutionMode.LIVE,
        afterlife_runs_dir=str(tmp_path / "runs"),
        afterlife_artifacts_dir=str(tmp_path / "artifacts"),
        afterlife_cache_dir=str(tmp_path / "cache"),
        afterlife_budget_usd_per_run=1.0,
        afterlife_budget_usd_total=1.0,
    )


class _FakeTransformers:
    def __init__(self, **attrs: object) -> None:
        self.__version__ = "5.17.0-fake"
        for key, value in attrs.items():
            setattr(self, key, value)


def test_resolve_class_from_config_architectures() -> None:
    mistral = object()
    gemma = object()
    causal = object()
    namespace = _FakeTransformers(
        Mistral3ForConditionalGeneration=mistral,
        Gemma4UnifiedForConditionalGeneration=gemma,
        AutoModelForCausalLM=causal,
    )
    cls, name = _resolve_model_class(namespace, causal, "Mistral3ForConditionalGeneration")
    assert cls is mistral
    assert name == "Mistral3ForConditionalGeneration"
    cls, name = _resolve_model_class(namespace, causal, "Gemma4UnifiedForConditionalGeneration")
    assert cls is gemma
    assert name == "Gemma4UnifiedForConditionalGeneration"
    cls, name = _resolve_model_class(namespace, causal, "Qwen3ForCausalLM")
    assert cls is causal
    assert name == "AutoModelForCausalLM"


def test_resolve_mistral_uses_image_text_auto_when_named_missing() -> None:
    auto = object()
    causal = object()
    cls, name = _resolve_model_class(
        _FakeTransformers(AutoModelForImageTextToText=auto),
        causal,
        "Mistral3ForConditionalGeneration",
    )
    assert cls is auto
    assert name == "AutoModelForImageTextToText"


def test_resolve_gemma_falls_back_to_causal_lm() -> None:
    causal = object()
    cls, name = _resolve_model_class(
        _FakeTransformers(), causal, "Gemma4UnifiedForConditionalGeneration"
    )
    assert cls is causal
    assert name == "AutoModelForCausalLM"


def test_resolve_mistral_without_class_raises() -> None:
    with pytest.raises(ProviderError, match="Mistral3ForConditionalGeneration"):
        _resolve_model_class(_FakeTransformers(), object(), "Mistral3ForConditionalGeneration")


def test_architecture_module_guesses() -> None:
    assert "mistral3" in _architecture_module_guesses(
        "Mistral3ForConditionalGeneration", "mistral3"
    )
    assert "gemma4" in _architecture_module_guesses(
        "Gemma4UnifiedForConditionalGeneration", "gemma4"
    )


def test_load_keys_cover_quant_fields() -> None:
    for key in (
        "load_in_4bit",
        "load_in_8bit",
        "bnb_4bit_quant_type",
        "bnb_4bit_use_double_quant",
        "bnb_4bit_compute_dtype",
        "device_map",
        "revision",
        "quantization",
        "serialization",
        "text_only",
        "enable_thinking",
    ):
        assert key in _LOAD_KEYS


@pytest.mark.asyncio
async def test_quant_keys_do_not_reach_generate(tmp_path: Path) -> None:
    backend = RecordingBackend()
    client = LocalClient(
        _settings(tmp_path),
        tokenizer=WhitespaceTokenizer(),
        backend=backend,
    )
    extra = {
        "device": "cpu",
        "dtype": "float32",
        "load_in_4bit": True,
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_use_double_quant": True,
        "bnb_4bit_compute_dtype": "bfloat16",
        "device_map": "cuda",
        "revision": "abc123",
        "sampler_note": "ok",
    }
    request = CompletionRequest(
        model_id="local/test",
        max_tokens=4,
        temperature=0.3,
        prompt="hello world",
        extra=extra,
    )
    await client.complete(request)
    assert backend.generate_extras
    leaked = set(backend.generate_extras[0]) & set(_LOAD_KEYS)
    assert not leaked
    assert backend.generate_extras[0].get("sampler_note") == "ok"


@pytest.mark.asyncio
async def test_unload_clears_resolved(tmp_path: Path) -> None:
    backend = RecordingBackend()
    client = LocalClient(
        _settings(tmp_path),
        tokenizer=WhitespaceTokenizer(),
        backend=backend,
    )
    client._resolved["local/test"] = (WhitespaceTokenizer(), backend)
    await client.unload("local/test")
    assert client._resolved == {}


def test_thinking_guard_raises() -> None:
    with pytest.raises(ReasoningLeakError):
        assert_no_thinking("hello <think>secret</think> world", model_id="qwen")
    assert_no_thinking("plain text", model_id="qwen")


def test_raw_bytes_serialization_forces_prompt() -> None:
    generator = GeneratorConfig(
        slug="x",
        model_id="m",
        api="local",
        tokenizer_repo="mock",
        continuation="chat_instructed",
        continuation_instruction="Continue the text.",
        serialization="raw_bytes",
        is_base_model=False,
    )
    request = build_request(
        generator,
        SamplingConfig(temperature=0.3),
        prompt="SEED TEXT",
        max_tokens=8,
        seed=1,
    )
    assert request.prompt == "SEED TEXT"
    assert request.messages is None


def test_plan_rejects_multiple_local_generators() -> None:
    a = GeneratorConfig(
        slug="a",
        model_id="m1",
        api="local",
        tokenizer_repo="mock",
        continuation="raw_completion",
        is_base_model=True,
    )
    b = GeneratorConfig(
        slug="b",
        model_id="m2",
        api="local",
        tokenizer_repo="mock",
        continuation="raw_completion",
        is_base_model=True,
    )

    class Bank:
        def by_id(self, seed_id: str):
            return type("S", (), {"id": seed_id})()

    config = ExperimentConfig(
        stage="s8",
        name="multi",
        generators=(a, b),
        windows=(WindowConfig(W=64, block_size=16, target_tokens=64, chunk_size=32),),
        sampling=(SamplingConfig(temperature=0.3),),
        semantic_seeds=("physics",),
        stochastic_seeds=(1,),
    )
    with pytest.raises(ConfigError):
        plan_trajectories(config, Bank())


def test_gap_positive_for_two_clusters() -> None:
    rng = np.random.default_rng(0)
    turnovers = np.linspace(1.0, 12.0, 12)
    trajectories = []
    for seed_i, center in enumerate((np.ones(8), -np.ones(8))):
        for rep in range(2):
            emb = np.stack([center + 0.05 * rng.normal(size=8) for _ in turnovers])
            trajectories.append(
                TrajectoryEmbed(
                    trajectory_id=f"s{seed_i}-r{rep}",
                    seed_id=f"seed{seed_i}",
                    embeddings=emb.astype(np.float64),
                    turnovers=turnovers,
                )
            )
    bands = log_turnover_bands(12.0, start=1.0, n_bands=4)
    frame = gap_vs_turnover(trajectories, band_edges=bands)
    assert (frame["G"].dropna() > 0).all()


def test_gap_near_zero_for_noise() -> None:
    rng = np.random.default_rng(1)
    turnovers = np.linspace(1.0, 12.0, 12)
    trajectories = []
    for seed_i in range(3):
        for rep in range(2):
            emb = rng.normal(size=(len(turnovers), 8))
            trajectories.append(
                TrajectoryEmbed(
                    trajectory_id=f"s{seed_i}-r{rep}",
                    seed_id=f"seed{seed_i}",
                    embeddings=emb,
                    turnovers=turnovers,
                )
            )
    bands = log_turnover_bands(12.0, start=1.0, n_bands=4)
    frame = gap_vs_turnover(trajectories, band_edges=bands)
    assert float(np.nanmean(np.abs(frame["G"]))) < 0.35


def test_prefix_lock_escape_recovery() -> None:
    turnovers = np.arange(1, 25, dtype=np.float64)
    degenerate = np.zeros_like(turnovers, dtype=bool)
    degenerate[4:19] = True
    result = prefix_lock_escape(degenerate, turnovers, n_confirm=3)
    assert result.confirmed_lock
    assert result.tau_lock == 7.0
    assert result.confirmed_escape
    assert result.tau_escape == 22.0


def test_loo_by_seed_drops_one() -> None:
    rng = np.random.default_rng(2)
    turnovers = np.linspace(1.0, 12.0, 12)
    trajectories = []
    for seed_i, center in enumerate((np.ones(4), -np.ones(4), np.array([1.0, -1.0, 1.0, -1.0]))):
        for rep in range(2):
            emb = np.stack([center + 0.02 * rng.normal(size=4) for _ in turnovers])
            trajectories.append(
                TrajectoryEmbed(
                    trajectory_id=f"s{seed_i}-r{rep}",
                    seed_id=f"seed{seed_i}",
                    embeddings=emb,
                    turnovers=turnovers,
                )
            )
    edges = integer_l0_band_edges(12.0)
    loo = loo_by_seed(trajectories, band_edges=edges)
    assert set(loo["held_out_seed"]) == {"seed0", "seed1", "seed2"}
    assert len(loo) == 3


def test_capped_jaccard_runs() -> None:
    sets = [{(f"w{i}",)} for i in range(100)]
    sets[0] = sets[1]
    value = capped_late_jaccard(sets, cap=16, seed=0)
    assert 0.0 <= value <= 1.0


@pytest.mark.asyncio
async def test_local_embed_scripted() -> None:
    client = LocalEmbedClient(backend=ScriptedEmbedBackend(dim=16))
    response = await client.embed(
        EmbeddingRequest(model_id="mock-bge", inputs=("alpha", "beta"))
    )
    assert len(response.vectors) == 2
    assert len(response.vectors[0]) == 16


@pytest.mark.asyncio
async def test_local_client_embed_delegates(tmp_path: Path) -> None:
    client = LocalClient(_settings(tmp_path))
    client._embed_client = LocalEmbedClient(backend=ScriptedEmbedBackend(dim=8))
    response = await client.embed(EmbeddingRequest(model_id="mock-bge", inputs=("alpha",)))
    assert len(response.vectors) == 1
    assert len(response.vectors[0]) == 8
