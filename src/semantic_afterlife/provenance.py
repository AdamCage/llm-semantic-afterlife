"""Run manifests: everything needed to say what produced a number.

A manifest is written when a run starts (so that a killed run is still
attributable) and finalised when it ends. It captures the environment, the git
state, the resolved config, the pinned endpoints, the seeds, the totals, and an
integrity block hashing every output file.
"""

from __future__ import annotations

import platform
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib.metadata import distributions
from pathlib import Path
from typing import Any, ClassVar

import orjson

from .config import Settings
from .hashing import fingerprint_secret, hash_tree, sha256_obj
from .paths import RunPaths


def _git(*args: str, cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def git_state(repo: Path) -> dict[str, Any]:
    """Git SHA, branch, dirtiness, and — if dirty — the actual diff.

    Recording the diff matters: a result produced from an uncommitted tree is
    still reproducible if we kept the diff, and is otherwise lost.
    """
    sha = _git("rev-parse", "HEAD", cwd=repo)
    status = _git("status", "--porcelain", cwd=repo)
    dirty = bool(status)
    state: dict[str, Any] = {
        "sha": sha,
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD", cwd=repo),
        "dirty": dirty,
        "describe": _git("describe", "--always", "--dirty", cwd=repo),
    }
    if dirty:
        state["status"] = status
        state["diff"] = _git("diff", "HEAD", cwd=repo)
    return state


def environment_state() -> dict[str, Any]:
    return {
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "packages": {dist.name.lower(): dist.version for dist in distributions() if dist.name},
    }


@dataclass
class RunManifest:
    """Mutable manifest, written at start and finalised at end."""

    run_id: str
    stage: str
    command: str
    settings_snapshot: dict[str, Any]
    config_resolved: dict[str, Any]
    config_sha256: str
    git: dict[str, Any]
    environment: dict[str, Any]
    started_at: str
    execution_mode: str
    usd_per_rub: float
    seeds: dict[str, Any] = field(default_factory=dict)
    endpoints: dict[str, Any] = field(default_factory=dict)
    totals: dict[str, Any] = field(default_factory=dict)
    trajectories: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    finished_at: str | None = None
    status: str = "RUNNING"
    integrity: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "stage": self.stage,
            "status": self.status,
            "command": self.command,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "execution_mode": self.execution_mode,
            "usd_per_rub": self.usd_per_rub,
            "config_sha256": self.config_sha256,
            "config_resolved": self.config_resolved,
            "settings": self.settings_snapshot,
            "git": self.git,
            "environment": self.environment,
            "seeds": self.seeds,
            "endpoints": self.endpoints,
            "totals": self.totals,
            "trajectories": self.trajectories,
            "notes": self.notes,
            "integrity": self.integrity,
        }

    def write(self, paths: RunPaths) -> None:
        paths.manifest.write_bytes(
            orjson.dumps(self.to_dict(), option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS)
        )
        paths.status.write_text(self.status, encoding="utf-8")

    #: Files covered by the integrity block. Deliberately excludes anything still
    #: being written when the manifest is finalised -- ``STATUS``,
    #: ``events.jsonl`` and ``logs/`` all receive their last writes at or after
    #: finalisation, so hashing them would guarantee a mismatch on every run and
    #: train the reader to ignore integrity failures. What matters here is the
    #: reproducible output: resolved config, raw exchanges, and data.
    INTEGRITY_PATTERNS: ClassVar[tuple[str, ...]] = (
        "config.resolved.yaml",
        "requests/**/*",
        "data/**/*",
    )

    def finalise(self, paths: RunPaths, *, status: str) -> None:
        self.status = status
        self.finished_at = datetime.now(UTC).isoformat(timespec="seconds")
        self.integrity = hash_tree(paths.root, patterns=self.INTEGRITY_PATTERNS)
        self.write(paths)


def settings_snapshot(settings: Settings) -> dict[str, Any]:
    """Non-secret view of the settings, with credentials reduced to fingerprints."""
    return {
        "routerai_base_url": settings.routerai_base_url,
        "openrouter_base_url": settings.openrouter_base_url,
        "routerai_key_fingerprint": fingerprint_secret(settings.routerai_api_key),
        "openrouter_key_fingerprint": fingerprint_secret(settings.openrouter_api_key),
        "hf_token_fingerprint": fingerprint_secret(settings.hf_token),
        "execution_mode": str(settings.afterlife_execution_mode),
        "usd_per_rub": settings.afterlife_usd_per_rub,
        "budget_usd_per_run": settings.afterlife_budget_usd_per_run,
        "budget_usd_total": settings.afterlife_budget_usd_total,
        "max_concurrent_trajectories": settings.afterlife_max_concurrent_trajectories,
        "request_timeout_s": settings.afterlife_request_timeout_s,
        "max_retries": settings.afterlife_max_retries,
    }


def new_manifest(
    *,
    run_id: str,
    stage: str,
    command: str,
    settings: Settings,
    config_resolved: dict[str, Any],
    config_sha256: str | None = None,
    seeds: dict[str, Any] | None = None,
) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        stage=stage,
        command=command,
        settings_snapshot=settings_snapshot(settings),
        config_resolved=config_resolved,
        config_sha256=config_sha256 or sha256_obj(config_resolved),
        git=git_state(settings.paths.root),
        environment=environment_state(),
        started_at=datetime.now(UTC).isoformat(timespec="seconds"),
        execution_mode=str(settings.afterlife_execution_mode),
        usd_per_rub=settings.afterlife_usd_per_rub,
        seeds=seeds or {},
    )


def read_manifest(path: Path) -> dict[str, Any]:
    return orjson.loads(path.read_bytes())
