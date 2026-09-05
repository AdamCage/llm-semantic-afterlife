"""Run context: the boilerplate that makes every invocation a recorded run.

Analysis passes and audits are runs too. Giving them the same manifest, event
log, integrity block and ledger as a generation pass is what makes
"no number without a run_id" enforceable rather than aspirational.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import yaml

from .config import Settings, get_settings
from .errors import ResumeError
from .ledger import Ledger
from .logging_utils import EventLogger, configure_logging, get_console, get_logger
from .paths import make_run_id
from .provenance import load_manifest, new_manifest

logger = get_logger("runctx")


class RunContext:
    """Bundles paths, manifest, event log and ledger for one invocation."""

    def __init__(
        self,
        *,
        stage: str,
        slug: str,
        config_resolved: dict[str, Any],
        config_sha256: str,
        settings: Settings,
        stage_budget_usd: float | None = None,
        resume_run_id: str | None = None,
    ) -> None:
        self.settings = settings
        self.stage = stage
        if resume_run_id:
            try:
                existing = settings.paths.ensure().find_run(resume_run_id)
            except FileNotFoundError as exc:
                raise ResumeError(f"cannot resume {resume_run_id}: no run directory") from exc
            if not existing.manifest.is_file():
                raise ResumeError(f"cannot resume {resume_run_id}: no manifest")
            self.manifest = load_manifest(existing.manifest)
            if self.manifest.config_sha256 != config_sha256:
                raise ResumeError(
                    f"cannot resume {resume_run_id}: config hash "
                    f"{self.manifest.config_sha256[:8]} != {config_sha256[:8]}"
                )
            if self.manifest.stage != stage:
                raise ResumeError(
                    f"cannot resume {resume_run_id}: stage {self.manifest.stage} != {stage}"
                )
            if self.manifest.status == "COMPLETED":
                raise ResumeError(f"cannot resume {resume_run_id}: already COMPLETED")
            self.run_id = resume_run_id
            self.paths = existing.ensure()
            self.manifest.status = "RUNNING"
            self.manifest.finished_at = None
            self.manifest.command = " ".join(sys.argv)
            self.note(f"resumed: {' '.join(sys.argv)}")
            opening = "run.resumed"
            mirror = f"resume {self.run_id} ({settings.afterlife_execution_mode})"
        else:
            self.run_id = make_run_id(stage, slug, config_sha256)
            self.paths = settings.paths.ensure().run(stage, self.run_id).ensure()
            self.manifest = new_manifest(
                run_id=self.run_id,
                stage=stage,
                command=" ".join(sys.argv),
                settings=settings,
                config_resolved=config_resolved,
                config_sha256=config_sha256,
            )
            self.paths.resolved_config.write_text(
                yaml.safe_dump(config_resolved, sort_keys=True, allow_unicode=True),
                encoding="utf-8",
            )
            opening = "run.started"
            mirror = f"run {self.run_id} ({settings.afterlife_execution_mode})"

        configure_logging(settings.afterlife_log_level, log_file=self.paths.run_log)
        self.events = EventLogger(self.paths.events, self.run_id)
        self.manifest.write(self.paths)
        self.ledger = Ledger(
            settings.paths.ledger,
            run_id=self.run_id,
            per_run_ceiling_usd=settings.afterlife_budget_usd_per_run,
            total_ceiling_usd=settings.afterlife_budget_usd_total,
            stage_ceiling_usd=stage_budget_usd,
        )
        self.events.event(
            opening,
            stage=stage,
            slug=slug,
            config_sha256=config_sha256,
            execution_mode=str(settings.afterlife_execution_mode),
            git_sha=self.manifest.git.get("sha"),
            git_dirty=self.manifest.git.get("dirty"),
            mirror=mirror,
        )
        if self.manifest.git.get("dirty"):
            logger.warning(
                "git tree is dirty; the diff is recorded in the manifest, but prefer committing "
                "before a run that produces reportable numbers"
            )

    @property
    def artifacts_dir(self):  # type: ignore[no-untyped-def]
        return self.settings.paths.stage_artifacts(self.stage)

    def note(self, text: str) -> None:
        self.manifest.notes.append(text)

    def finish(self, status: str = "COMPLETED", **totals: Any) -> None:
        self.manifest.totals.update(totals)
        self.manifest.totals.update(self.ledger.summary())
        self.manifest.finalise(self.paths, status=status)
        self.events.event(
            "run.finished",
            status=status,
            **self.ledger.summary(),
            mirror=f"{status.lower()} {self.run_id} — spent ${self.ledger.run_spend_usd:.4f} "
            f"(project ${self.ledger.project_spend_usd:.2f} of "
            f"${self.settings.afterlife_budget_usd_total:.2f})",
        )
        self.events.close()


@contextmanager
def run_context(
    *,
    stage: str,
    slug: str,
    config_resolved: dict[str, Any],
    config_sha256: str,
    settings: Settings | None = None,
    stage_budget_usd: float | None = None,
    resume_run_id: str | None = None,
) -> Iterator[RunContext]:
    """Open a run, finalising the manifest on success *and* on failure.

    A crashed run must still leave a readable manifest and event log; otherwise a
    multi-hour failure teaches us nothing. ``resume_run_id`` reopens an
    unfinished directory so step checkpoints are not regenerated.
    """
    context = RunContext(
        stage=stage,
        slug=slug,
        config_resolved=config_resolved,
        config_sha256=config_sha256,
        settings=settings or get_settings(),
        stage_budget_usd=stage_budget_usd,
        resume_run_id=resume_run_id,
    )
    try:
        yield context
    except BaseException as exc:
        context.note(f"aborted: {type(exc).__name__}: {exc}")
        context.events.event(
            "run.failed", level="ERROR", error_type=type(exc).__name__, error=str(exc)
        )
        context.finish(status="FAILED")
        get_console().print_exception(show_locals=False)
        raise
    else:
        if context.manifest.status == "RUNNING":
            context.finish()
