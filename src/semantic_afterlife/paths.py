"""The only module that knows the on-disk layout.

Every other module asks for a path here rather than composing one, so that the
layout documented in ``.cursor/rules/10-reproducibility.mdc`` has exactly one
implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


def repo_root() -> Path:
    """Locate the repository root by walking up for a marker file."""
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "AGENTS.md").is_file():
            return candidate
    # Installed as a package outside the repo: fall back to the CWD.
    return Path.cwd()


def utc_stamp() -> str:
    """Compact UTC timestamp used inside ``run_id``."""
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def make_run_id(stage: str, slug: str, config_sha256: str) -> str:
    """``<stage>-<slug>-<UTC timestamp>-<8 hex of config hash>``.

    Deterministic apart from the timestamp, so two runs of the same config are
    recognisably siblings.
    """
    return f"{stage}-{slug}-{utc_stamp()}-{config_sha256[:8]}"


@dataclass(frozen=True, slots=True)
class RunPaths:
    """Canonical directory layout for a single result-producing invocation."""

    root: Path
    run_id: str

    @property
    def manifest(self) -> Path:
        return self.root / "manifest.json"

    @property
    def resolved_config(self) -> Path:
        return self.root / "config.resolved.yaml"

    @property
    def events(self) -> Path:
        return self.root / "events.jsonl"

    @property
    def status(self) -> Path:
        return self.root / "STATUS"

    @property
    def requests_dir(self) -> Path:
        return self.root / "requests"

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    @property
    def run_log(self) -> Path:
        return self.logs_dir / "run.log"

    def trajectory_requests(self, trajectory_id: str) -> Path:
        return self.requests_dir / f"{trajectory_id}.jsonl"

    def trajectory_steps(self, trajectory_id: str) -> Path:
        """Append-only per-step checkpoint: the resume source of truth."""
        return self.data_dir / "trajectories" / f"{trajectory_id}.steps.jsonl"

    def trajectory_text(self, trajectory_id: str) -> Path:
        return self.data_dir / "trajectories" / f"{trajectory_id}.text"

    def embeddings(self, embedding_slug: str) -> Path:
        return self.data_dir / f"embeddings_{embedding_slug}.parquet"

    def chunks(self) -> Path:
        return self.data_dir / "chunks.parquet"

    def ensure(self) -> RunPaths:
        for directory in (
            self.root,
            self.requests_dir,
            self.data_dir,
            self.data_dir / "trajectories",
            self.logs_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        return self


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    """Top-level directories, resolved from settings."""

    root: Path
    runs: Path
    artifacts: Path
    cache: Path

    @property
    def ledger(self) -> Path:
        return self.runs / "_ledger" / "spend.jsonl"

    @property
    def response_cache(self) -> Path:
        return self.cache / "responses"

    @property
    def embedding_cache(self) -> Path:
        return self.cache / "embeddings"

    @property
    def tokenizer_cache(self) -> Path:
        return self.cache / "tokenizers"

    @property
    def configs(self) -> Path:
        return self.root / "configs"

    def stage_artifacts(self, stage: str) -> Path:
        return self.artifacts / f"stage-{stage.lstrip('sS')}"

    def stage_docs(self, stage: str) -> Path:
        return self.root / "docs" / "stages" / f"stage-{stage.lstrip('sS')}"

    def run(self, stage: str, run_id: str) -> RunPaths:
        return RunPaths(root=self.runs / stage / run_id, run_id=run_id)

    def find_run(self, run_id: str) -> RunPaths:
        """Locate a run by id without knowing its stage."""
        matches = sorted(self.runs.glob(f"*/{run_id}"))
        if not matches:
            raise FileNotFoundError(
                f"no run directory found for run_id={run_id!r} under {self.runs}"
            )
        return RunPaths(root=matches[0], run_id=run_id)

    def ensure(self) -> ProjectPaths:
        for directory in (
            self.runs,
            self.runs / "_ledger",
            self.artifacts,
            self.cache,
            self.response_cache,
            self.embedding_cache,
            self.tokenizer_cache,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        return self
