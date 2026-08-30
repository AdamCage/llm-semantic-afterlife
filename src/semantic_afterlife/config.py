"""Settings (environment) and experiment configuration (YAML).

Two distinct things live here and must not be confused:

* :class:`Settings` — *how* we run: credentials, ceilings, paths, log level.
  Comes from the environment, never committed, never part of a result's identity.
* the ``*Config`` models — *what* we run: the scientific parameters. Come from
  ``configs/**``, are hashed into the ``run_id``, and are copied verbatim into
  every manifest.

A number that changes a result belongs in the second group. A magic literal in a
function body belongs nowhere.
"""

from __future__ import annotations

import copy
import os
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .errors import ConfigError, MissingCredentialsError
from .hashing import sha256_obj
from .paths import ProjectPaths, repo_root


class ExecutionMode(StrEnum):
    """How requests are served."""

    LIVE = "live"
    """Real API calls; responses written to the cache."""

    REPLAY = "replay"
    """Cache only. A miss is an error. Used by CI and reproducibility audits."""

    MOCK = "mock"
    """Deterministic synthetic generator. No network, no cost."""


# ---------------------------------------------------------------------------
# Settings (environment)
# ---------------------------------------------------------------------------


class Settings(BaseSettings):
    """Environment-sourced runtime settings. See ``.env.example``."""

    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    routerai_api_key: str | None = None
    routerai_base_url: str = "https://routerai.ru/api/v1"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    hf_token: str | None = None

    afterlife_budget_usd_per_run: float = 5.0
    afterlife_budget_usd_total: float = 50.0
    afterlife_usd_per_rub: float = 0.0125
    afterlife_execution_mode: ExecutionMode = ExecutionMode.LIVE

    afterlife_runs_dir: str = "runs"
    afterlife_artifacts_dir: str = "artifacts"
    afterlife_cache_dir: str = "cache"

    afterlife_log_level: str = "INFO"
    afterlife_log_chunk_text: bool = False

    afterlife_max_concurrent_trajectories: int = 4
    afterlife_request_timeout_s: float = 300.0
    afterlife_max_retries: int = 6

    # -- derived ------------------------------------------------------------

    @property
    def paths(self) -> ProjectPaths:
        root = repo_root()

        def resolve(value: str) -> Path:
            path = Path(value)
            return path if path.is_absolute() else root / path

        return ProjectPaths(
            root=root,
            runs=resolve(self.afterlife_runs_dir),
            artifacts=resolve(self.afterlife_artifacts_dir),
            cache=resolve(self.afterlife_cache_dir),
        )

    def api_key(self, provider: str) -> str:
        keys = {"routerai": self.routerai_api_key, "openrouter": self.openrouter_api_key}
        if provider not in keys:
            raise ConfigError(f"unknown provider {provider!r}; expected one of {sorted(keys)}")
        key = keys[provider]
        if not key:
            raise MissingCredentialsError(
                f"{provider.upper()}_API_KEY is not set. Copy .env.example to .env and fill it in."
            )
        return key

    def base_url(self, provider: str) -> str:
        urls = {"routerai": self.routerai_base_url, "openrouter": self.openrouter_base_url}
        if provider not in urls:
            raise ConfigError(f"unknown provider {provider!r}")
        return urls[provider].rstrip("/")

    def has_key(self, provider: str) -> bool:
        try:
            self.api_key(provider)
        except MissingCredentialsError:
            return False
        return True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide settings singleton.

    Cached so that a long run cannot pick up a mid-flight ``.env`` edit and
    silently change its own provenance.
    """
    return Settings()


# ---------------------------------------------------------------------------
# Experiment configuration (YAML)
# ---------------------------------------------------------------------------


class StrictModel(BaseModel):
    """Reject unknown keys: a typo in a config must fail loudly, not silently."""

    model_config = ConfigDict(extra="forbid", frozen=True)


ContinuationMechanism = Literal["raw_completion", "assistant_prefill", "chat_instructed"]
ForcingCondition = Literal["unforced", "fixed"]


class GeneratorConfig(StrictModel):
    """One generator model, pinned to a specific endpoint (ADR-0003)."""

    slug: str = Field(description="short identifier used in run ids and figures")
    model_id: str = Field(description="provider-side model id, e.g. 'qwen/qwen3-8b'")
    api: Literal["routerai", "openrouter", "mock"] = "routerai"

    provider_slug: str | None = Field(
        default=None,
        description="upstream provider tag to pin; None means unpinned (audits only)",
    )
    allow_fallbacks: bool = Field(
        default=False,
        description="ADR-0003: preferences only become constraints when this is False",
    )
    service_tier: str | None = None
    country: str | None = None

    tokenizer_repo: str = Field(description="HF repo whose tokenizer defines generator tokens")
    tokenizer_revision: str | None = None

    continuation: ContinuationMechanism = "chat_instructed"
    is_base_model: bool = False
    continuation_instruction: str | None = None
    system_prompt: str | None = None
    prefill_user_stub: str | None = Field(
        default=None,
        description="user message inserted before an assistant prefill for providers that "
        "reject an assistant-first conversation; any non-empty value is external forcing "
        "and is recorded as such",
    )

    native_context: int | None = None
    price_usd_per_m_input: float | None = None
    price_usd_per_m_output: float | None = None

    notes: str | None = None

    @model_validator(mode="after")
    def _check_forcing(self) -> GeneratorConfig:
        if self.continuation == "chat_instructed" and not self.continuation_instruction:
            raise ConfigError(
                f"generator {self.slug!r} uses chat_instructed continuation but has no "
                "continuation_instruction; the instruction is a permanent external force and "
                "must be recorded explicitly (methodology.md 1.3)"
            )
        return self

    @property
    def forcing(self) -> ForcingCondition:
        return "fixed" if self.system_prompt else "unforced"


class EmbeddingConfig(StrictModel):
    """One representation space."""

    slug: str
    model_id: str
    api: Literal["routerai", "openrouter", "local", "mock"] = "routerai"
    expected_dim: int | None = None
    architecture: str = Field(description="'causal-decoder' | 'bidirectional-encoder' | 'closed'")
    max_batch: int = 16
    price_usd_per_m_input: float | None = None
    normalise: bool = Field(
        default=True,
        description="store an explicitly L2-normalised copy regardless of provider behaviour",
    )
    notes: str | None = None


class WindowConfig(StrictModel):
    """Sliding-window protocol parameters (methodology.md 1)."""

    W: int = Field(gt=0, description="sliding window in generator tokens")
    block_size: int = Field(gt=0, description="B: tokens requested per API call")
    target_tokens: int = Field(gt=0, description="T: generated tokens per trajectory")
    chunk_size: int = Field(default=1024, gt=0, description="analysis unit, non-overlapping")
    protocol: Literal["P1_reprompt", "P2_sliding_attention"] = "P1_reprompt"

    @model_validator(mode="after")
    def _check_geometry(self) -> WindowConfig:
        if self.block_size > self.W:
            raise ConfigError(f"block_size={self.block_size} exceeds W={self.W}")
        if self.target_tokens < self.W:
            raise ConfigError(
                f"target_tokens={self.target_tokens} is below W={self.W}: the trajectory would "
                "never pass the context horizon, so nothing this project measures would be defined"
            )
        if self.chunk_size % 1 or self.W % self.block_size:
            # Non-divisibility is legal but makes step/chunk alignment awkward to reason about.
            pass
        return self

    @property
    def stride(self) -> int:
        """S: tokens by which the window advances per step. ``S = B`` (ADR-0001)."""
        return self.block_size

    @property
    def n_steps(self) -> int:
        return -(-self.target_tokens // self.block_size)

    @property
    def turnovers(self) -> float:
        """R = T/W: how many times the whole memory is replaced."""
        return self.target_tokens / self.W

    @property
    def n_chunks(self) -> int:
        return self.target_tokens // self.chunk_size

    @property
    def estimated_input_tokens(self) -> int:
        """The cost law: ``input ≈ T·W/S``, ramped while the window is still filling."""
        total = 0
        produced = 0
        for _ in range(self.n_steps):
            total += min(produced, self.W)
            produced += self.block_size
        return total


class SamplingConfig(StrictModel):
    temperature: float = Field(ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, gt=0.0, le=1.0)
    top_k: int | None = None
    repetition_penalty: float | None = Field(
        default=None,
        description="left None by default: penalties would suppress exactly the degenerate "
        "repetition we are trying to measure (risks.md R3)",
    )
    logprobs: bool = False
    top_logprobs: int | None = None


class SeedSpec(StrictModel):
    """A semantic seed: the initial condition of one trajectory family."""

    id: str
    domain: str
    text: str
    language: str = "en"
    twin_of: str | None = Field(
        default=None, description="id of the seed this is a minimal perturbation of (S5)"
    )


class SeedBank(StrictModel):
    version: str
    description: str
    seeds: tuple[SeedSpec, ...]

    def by_id(self, seed_id: str) -> SeedSpec:
        for seed in self.seeds:
            if seed.id == seed_id:
                return seed
        raise ConfigError(f"unknown semantic seed {seed_id!r}")


class ExperimentConfig(StrictModel):
    """A full experiment matrix: one stage's worth of work."""

    stage: str
    name: str
    description: str = ""

    generators: tuple[GeneratorConfig, ...]
    embeddings: tuple[EmbeddingConfig, ...] = ()
    windows: tuple[WindowConfig, ...]
    sampling: tuple[SamplingConfig, ...]
    semantic_seeds: tuple[str, ...]
    stochastic_seeds: tuple[int, ...]
    seed_bank: str = "configs/seeds/seed_bank_v1.yaml"

    max_concurrent: int | None = None
    budget_usd: float | None = None

    @property
    def cells(self) -> list[dict[str, Any]]:
        """The expanded factorial: one dict per trajectory to be generated."""
        out: list[dict[str, Any]] = []
        for generator in self.generators:
            for window in self.windows:
                for sampling in self.sampling:
                    for semantic_seed in self.semantic_seeds:
                        for stochastic_seed in self.stochastic_seeds:
                            out.append(
                                {
                                    "generator": generator.slug,
                                    "W": window.W,
                                    "block_size": window.block_size,
                                    "target_tokens": window.target_tokens,
                                    "temperature": sampling.temperature,
                                    "semantic_seed": semantic_seed,
                                    "stochastic_seed": stochastic_seed,
                                }
                            )
        return out

    @property
    def n_trajectories(self) -> int:
        return len(self.cells)

    def generator(self, slug: str) -> GeneratorConfig:
        for generator in self.generators:
            if generator.slug == slug:
                return generator
        raise ConfigError(f"unknown generator {slug!r}")

    def window(self, W: int, block_size: int) -> WindowConfig:
        for window in self.windows:
            if window.W == W and window.block_size == block_size:
                return window
        raise ConfigError(f"unknown window W={W} block_size={block_size}")

    def sampling_for(self, temperature: float) -> SamplingConfig:
        for sampling in self.sampling:
            if sampling.temperature == temperature:
                return sampling
        raise ConfigError(f"unknown temperature {temperature}")


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigError(f"config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ConfigError(f"config file {path} must contain a mapping at the top level")
    return data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _resolve_includes(raw: dict[str, Any], *, root: Path, seen: frozenset[Path]) -> dict[str, Any]:
    """Expand an ``include:`` list of YAML paths, merged left to right.

    Keeps model and embedding definitions in one file each rather than duplicated
    across every stage config, so that a pinned provider is pinned in one place.
    """
    includes = raw.pop("include", [])
    if isinstance(includes, str):
        includes = [includes]
    merged: dict[str, Any] = {}
    for item in includes:
        path = (root / item).resolve()
        if path in seen:
            raise ConfigError(f"circular include detected at {path}")
        child = _resolve_includes(_read_yaml(path), root=root, seen=seen | {path})
        merged = _deep_merge(merged, child)
    return _deep_merge(merged, raw)


def _resolve_libraries(raw: dict[str, Any]) -> dict[str, Any]:
    """Expand ``generators: [slug, ...]`` against ``generator_library``.

    Model definitions — including the pinned provider and tokenizer — live in one
    place (``configs/models/``) and stage configs merely select from them by slug.
    Duplicating a pinned endpoint across stage files is exactly how endpoints end
    up silently disagreeing between stages.
    """
    for field_name, library_name in (
        ("generators", "generator_library"),
        ("embeddings", "embedding_library"),
    ):
        selected = raw.get(field_name)
        library = raw.pop(library_name, None) or {}
        if selected is None:
            continue
        if not isinstance(selected, list):
            raise ConfigError(f"{field_name} must be a list, got {type(selected).__name__}")
        expanded: list[Any] = []
        for item in selected:
            if isinstance(item, str):
                if item not in library:
                    raise ConfigError(
                        f"{field_name}: {item!r} is not defined in {library_name}; "
                        f"available: {sorted(library)}"
                    )
                entry = dict(library[item])
                entry.setdefault("slug", item)
                expanded.append(entry)
            else:
                expanded.append(item)
        raw[field_name] = expanded
    return raw


def load_raw_config(path: Path | str) -> dict[str, Any]:
    """Read a config file and fully resolve its includes, without validation."""
    root = repo_root()
    path = Path(path)
    if not path.is_absolute():
        path = root / path
    merged = _resolve_includes(_read_yaml(path), root=root, seen=frozenset({path.resolve()}))
    return _resolve_libraries(merged)


def load_experiment_config(path: Path | str) -> tuple[ExperimentConfig, dict[str, Any], str]:
    """Load, validate and hash an experiment config.

    Returns the typed config, the fully resolved raw mapping (what gets copied
    into the manifest), and the config hash that names the run.
    """
    raw = load_raw_config(path)
    try:
        config = ExperimentConfig.model_validate(raw)
    except Exception as exc:  # pydantic ValidationError, re-typed for callers
        raise ConfigError(f"invalid experiment config {path}: {exc}") from exc
    resolved = config.model_dump(mode="json")
    return config, resolved, sha256_obj(resolved)


def load_seed_bank(path: Path | str) -> SeedBank:
    raw = load_raw_config(path)
    try:
        return SeedBank.model_validate(raw)
    except Exception as exc:
        raise ConfigError(f"invalid seed bank {path}: {exc}") from exc


def in_ci() -> bool:
    return os.environ.get("CI", "").lower() in {"1", "true", "yes"}
