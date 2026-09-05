"""Resume must reopen the same run_id; a new id would regenerate paid steps."""

from __future__ import annotations

from pathlib import Path

import pytest

from semantic_afterlife.config import Settings, get_settings
from semantic_afterlife.errors import ResumeError
from semantic_afterlife.provenance import load_manifest
from semantic_afterlife.runctx import RunContext, run_context


def _settings() -> Settings:
    return get_settings()


def _open(
    settings: Settings,
    *,
    sha: str = "ab" * 16,
    stage: str = "s4",
    slug: str = "resume-test",
    resume_run_id: str | None = None,
) -> RunContext:
    return RunContext(
        stage=stage,
        slug=slug,
        config_resolved={"name": "resume-test", "windows": [{"W": 8192}]},
        config_sha256=sha,
        settings=settings,
        resume_run_id=resume_run_id,
    )


class TestResumeRun:
    def test_resume_keeps_run_id_and_started_at(self, isolated_env: Path) -> None:
        settings = _settings()
        first = _open(settings)
        run_id = first.run_id
        started = first.manifest.started_at
        first.events.close()

        resumed = _open(settings, resume_run_id=run_id)
        assert resumed.run_id == run_id
        assert resumed.manifest.started_at == started
        assert resumed.manifest.status == "RUNNING"
        assert any(note.startswith("resumed:") for note in resumed.manifest.notes)
        assert load_manifest(resumed.paths.manifest).run_id == run_id
        resumed.events.close()

    def test_resume_refuses_a_completed_run(self, isolated_env: Path) -> None:
        settings = _settings()
        with run_context(
            stage="s4",
            slug="resume-done",
            config_resolved={"name": "done"},
            config_sha256="cd" * 16,
            settings=settings,
        ) as context:
            run_id = context.run_id

        with pytest.raises(ResumeError, match="already COMPLETED"):
            _open(settings, sha="cd" * 16, slug="resume-done", resume_run_id=run_id)

    def test_resume_refuses_a_config_hash_mismatch(self, isolated_env: Path) -> None:
        settings = _settings()
        first = _open(settings, sha="11" * 16)
        run_id = first.run_id
        first.events.close()

        with pytest.raises(ResumeError, match="config hash"):
            _open(settings, sha="22" * 16, resume_run_id=run_id)

    def test_resume_refuses_a_stage_mismatch(self, isolated_env: Path) -> None:
        settings = _settings()
        first = _open(settings, stage="s4")
        run_id = first.run_id
        first.events.close()

        with pytest.raises(ResumeError, match="stage"):
            _open(settings, stage="s3", resume_run_id=run_id)

    def test_resume_missing_run_is_typed(self, isolated_env: Path) -> None:
        settings = _settings()
        with pytest.raises(ResumeError, match="no run directory"):
            _open(settings, resume_run_id="s4-does-not-exist-00000000T000000Z-deadbeef")
