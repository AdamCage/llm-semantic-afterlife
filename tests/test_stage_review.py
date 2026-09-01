"""The review gate is the merge criterion, so a bug in it is worse than most.

A gate that passes bad work teaches the executor that the gate is decorative; a
gate that fails good work teaches them to route around it. Both failures are
tested here against synthetic stage directories.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from semantic_afterlife.config import Settings
from semantic_afterlife.hashing import sha256_file
from semantic_afterlife.reporting.stage_review import (
    Verdict,
    check_artifact_bundles,
    check_degeneracy_labelled,
    check_diagnostics_are_segmented,
    check_integrity,
    check_plan_exists,
    check_report_quotes_generated_text,
    check_runs_complete,
    check_spend_matches_events,
    review_stage,
)

STAGE = "s9"


@pytest.fixture
def settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("AFTERLIFE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("AFTERLIFE_ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("AFTERLIFE_CACHE_DIR", str(tmp_path / "cache"))
    created = Settings()
    created.paths.ensure()
    # `stage_docs` resolves against the repo root, which is read-only for tests,
    # so plan checks are exercised through their own temp path below.
    return created


def write_run(
    settings: Settings,
    name: str,
    *,
    status: str = "COMPLETED",
    integrity: dict[str, str] | None = None,
    superseded: bool = False,
    degeneracy: bool | None = True,
) -> Path:
    run = settings.paths.run(STAGE, name).ensure()
    if degeneracy is not None and "geometry" in name:
        frame = pd.DataFrame(
            {"trajectory_id": ["t0"], "msd_alpha": [0.4], "degenerate": [degeneracy]}
        )
        frame.to_parquet(run.data_dir / "geometry_scalars.parquet", index=False)
    run.manifest.write_text(
        json.dumps({"status": status, "integrity": integrity or {}}), encoding="utf-8"
    )
    if superseded:
        (run.root / "SUPERSEDED").write_text("reason: test\n", encoding="utf-8")
    return run.root


def write_artifact(settings: Settings, name: str, *, data: bool, limitations: bool) -> None:
    out = settings.paths.stage_artifacts(STAGE) / "block"
    out.mkdir(parents=True, exist_ok=True)
    if data:
        pd.DataFrame({"x": [1, 2]}).to_parquet(out / f"{name}.data.parquet", index=False)
    meta = {"name": name, "caption": "a caption"}
    if limitations:
        meta["limitations"] = "what this does not establish"
    (out / f"{name}.meta.json").write_text(json.dumps(meta), encoding="utf-8")


class TestRunCompleteness:
    def test_all_completed_passes(self, settings: Settings) -> None:
        write_run(settings, "a")
        write_run(settings, "b")
        assert check_runs_complete(settings, STAGE).verdict is Verdict.PASS

    def test_a_failed_run_warns_rather_than_blocks(self, settings: Settings) -> None:
        """A failed run is missing data to declare, not necessarily a defect."""
        write_run(settings, "a")
        write_run(settings, "b", status="FAILED")
        assert check_runs_complete(settings, STAGE).verdict is Verdict.WARN

    def test_no_runs_fails(self, settings: Settings) -> None:
        assert check_runs_complete(settings, STAGE).verdict is Verdict.FAIL

    def test_superseded_runs_are_excluded(self, settings: Settings) -> None:
        """A retired run must not block the gate, but must stay on disk."""
        write_run(settings, "a")
        write_run(settings, "b", status="FAILED", superseded=True)
        check = check_runs_complete(settings, STAGE)
        assert check.verdict is Verdict.PASS
        assert (settings.paths.runs / STAGE / "b").is_dir()


class TestIntegrity:
    def test_matching_hashes_pass(self, settings: Settings) -> None:
        root = write_run(settings, "a")
        target = root / "data" / "out.txt"
        target.write_text("payload", encoding="utf-8")
        write_run(settings, "a", integrity={"data/out.txt": sha256_file(target)})
        assert check_integrity(settings, STAGE).verdict is Verdict.PASS

    def test_tampered_file_fails(self, settings: Settings) -> None:
        root = write_run(settings, "a")
        target = root / "data" / "out.txt"
        target.write_text("payload", encoding="utf-8")
        write_run(settings, "a", integrity={"data/out.txt": sha256_file(target)})
        target.write_text("tampered", encoding="utf-8")
        assert check_integrity(settings, STAGE).verdict is Verdict.FAIL

    def test_missing_file_fails(self, settings: Settings) -> None:
        write_run(settings, "a", integrity={"data/gone.txt": "0" * 64})
        assert check_integrity(settings, STAGE).verdict is Verdict.FAIL


class TestArtifactBundles:
    def test_complete_bundle_passes(self, settings: Settings) -> None:
        write_artifact(settings, "fig", data=True, limitations=True)
        assert check_artifact_bundles(settings, STAGE).verdict is Verdict.PASS

    def test_missing_source_data_fails(self, settings: Settings) -> None:
        write_artifact(settings, "fig", data=False, limitations=True)
        check = check_artifact_bundles(settings, STAGE)
        assert check.verdict is Verdict.FAIL
        assert "source data" in check.detail

    def test_missing_limitations_fails(self, settings: Settings) -> None:
        """A figure that does not say what it cannot establish is not an artifact."""
        write_artifact(settings, "fig", data=True, limitations=False)
        check = check_artifact_bundles(settings, STAGE)
        assert check.verdict is Verdict.FAIL
        assert "limitations" in check.detail

    def test_no_artifacts_fails(self, settings: Settings) -> None:
        assert check_artifact_bundles(settings, STAGE).verdict is Verdict.FAIL


class TestDegeneracyLabelling:
    def test_labelled_geometry_passes(self, settings: Settings) -> None:
        write_run(settings, "x-geometry-1", degeneracy=True)
        assert check_degeneracy_labelled(settings, STAGE).verdict is Verdict.PASS

    def test_unlabelled_geometry_fails(self, settings: Settings) -> None:
        """The specific failure this check was written for: S1.0 reported an
        exponent of 0.357 as confinement on a trajectory that was degenerate
        throughout."""
        run = settings.paths.run(STAGE, "x-geometry-1").ensure()
        pd.DataFrame({"trajectory_id": ["t0"], "msd_alpha": [0.4]}).to_parquet(
            run.data_dir / "geometry_scalars.parquet", index=False
        )
        run.manifest.write_text(json.dumps({"status": "COMPLETED"}), encoding="utf-8")
        assert check_degeneracy_labelled(settings, STAGE).verdict is Verdict.FAIL

    def test_superseded_geometry_is_ignored(self, settings: Settings) -> None:
        write_run(settings, "x-geometry-old", degeneracy=None, superseded=True)
        write_run(settings, "x-geometry-new", degeneracy=False)
        assert check_degeneracy_labelled(settings, STAGE).verdict is Verdict.PASS

    def test_no_geometry_runs_skips(self, settings: Settings) -> None:
        write_run(settings, "generation-only")
        assert check_degeneracy_labelled(settings, STAGE).verdict is Verdict.SKIP


class TestPlanCheck:
    def test_missing_plan_fails(self, settings: Settings) -> None:
        assert check_plan_exists(settings, "s99").verdict is Verdict.FAIL

    def test_real_stage_plans_pass(self, settings: Settings) -> None:
        """The committed plans must satisfy the gate they will be judged by."""
        for stage in ("0", "1"):
            assert check_plan_exists(Settings(), stage).verdict is Verdict.PASS


class TestLessonsFromStageOne:
    """Three checks that exist because a checklist did not prevent the mistake.

    Each corresponds to something Stage 1 got wrong in a way no amount of care
    would reliably catch: a cost read from the wrong field, a diagnostic averaged
    over a non-stationary run, and metrics trusted without anyone reading the
    output they summarised.
    """

    def _report(
        self,
        settings: Settings,
        tmp_path: Path,
        body: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> Settings:
        """Write a stage report into a temporary tree, never the real one.

        ``Settings.paths`` is derived from ``repo_root()`` and has no setter, so
        the root is redirected at its source. This matters: the first version of
        this fixture wrote ``docs/stages/stage-9/REPORT.md`` into the working copy
        and committed it.
        """
        monkeypatch.setattr("semantic_afterlife.config.repo_root", lambda: tmp_path)
        scoped = Settings()
        docs = scoped.paths.stage_docs(STAGE)
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "REPORT.md").write_text(body, encoding="utf-8")
        return scoped

    def test_ledger_and_events_agreeing_passes(self, settings: Settings) -> None:
        run = settings.paths.run(STAGE, "gen").ensure()
        run.manifest.write_text(json.dumps({"status": "COMPLETED"}), encoding="utf-8")
        run.events.write_text(
            "\n".join(
                json.dumps({"event": "generation.step.completed", "cost_usd": 0.5})
                for _ in range(4)
            ),
            encoding="utf-8",
        )
        settings.paths.ledger.parent.mkdir(parents=True, exist_ok=True)
        settings.paths.ledger.write_text(
            "\n".join(
                json.dumps({"run_id": "gen", "kind": "completion", "cost_usd": 0.5})
                for _ in range(4)
            ),
            encoding="utf-8",
        )
        assert check_spend_matches_events(settings, STAGE).verdict is Verdict.PASS

    def test_a_thirtyfold_disagreement_fails(self, settings: Settings) -> None:
        """The Stage 1 error, reproduced: per-trajectory read as per-run."""
        run = settings.paths.run(STAGE, "gen").ensure()
        run.manifest.write_text(json.dumps({"status": "COMPLETED"}), encoding="utf-8")
        run.events.write_text(
            "\n".join(
                json.dumps({"event": "generation.step.completed", "cost_usd": 0.5})
                for _ in range(12)
            ),
            encoding="utf-8",
        )
        settings.paths.ledger.parent.mkdir(parents=True, exist_ok=True)
        settings.paths.ledger.write_text(
            json.dumps({"run_id": "gen", "kind": "completion", "cost_usd": 0.2}), encoding="utf-8"
        )
        check = check_spend_matches_events(settings, STAGE)
        assert check.verdict is Verdict.FAIL
        assert "disagree" in check.detail

    def test_segmented_diagnostics_pass(
        self, settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        scoped = self._report(
            settings,
            tmp_path,
            "# R\nBlock fill by quarter: 0.99, 0.88, 0.77, 0.65. Stop rate rises to 74%.\n",
            monkeypatch,
        )
        assert check_diagnostics_are_segmented(scoped, STAGE).verdict is Verdict.PASS

    def test_an_unsegmented_average_fails(
        self, settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        scoped = self._report(
            settings,
            tmp_path,
            "# R\nMean block fill 0.748 and stop rate 54.5% over the run.\n",
            monkeypatch,
        )
        check = check_diagnostics_are_segmented(scoped, STAGE)
        assert check.verdict is Verdict.FAIL
        assert "segmentation" in check.detail

    def test_omitting_the_diagnostics_entirely_fails(
        self, settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        scoped = self._report(settings, tmp_path, "# R\nEverything went fine.\n", monkeypatch)
        assert check_diagnostics_are_segmented(scoped, STAGE).verdict is Verdict.FAIL

    def test_quoted_output_passes(
        self, settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        body = "# R\n" + "".join(
            f"> sample {i}: the cartographers had been instructed to survey the piano\n\n"
            for i in range(3)
        )
        scoped = self._report(settings, tmp_path, body, monkeypatch)
        assert check_report_quotes_generated_text(scoped, STAGE).verdict is Verdict.PASS

    def test_a_report_with_no_generated_text_fails(
        self, settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        scoped = self._report(
            settings, tmp_path, "# R\nNovelty was 0.87 and the gap was 0.147.\n", monkeypatch
        )
        check = check_report_quotes_generated_text(scoped, STAGE)
        assert check.verdict is Verdict.FAIL
        assert "generated text" in check.detail

    def test_fenced_blocks_count_as_samples(
        self, settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        body = "# R\n" + "".join(f"```\nsample {i}\n```\n" for i in range(3))
        scoped = self._report(settings, tmp_path, body, monkeypatch)
        assert check_report_quotes_generated_text(scoped, STAGE).verdict is Verdict.PASS


class TestReportAssembly:
    def test_review_report_blocks_on_any_failure(self, settings: Settings) -> None:
        write_run(settings, "a")
        report = review_stage(settings, STAGE)
        assert not report.ready_for_review
        assert report.failed
        # Serialisable, since the executor and reviewer exchange it as JSON.
        assert json.loads(json.dumps(report.as_dict()))["stage"] == STAGE

    def test_verdict_counts_are_consistent(self, settings: Settings) -> None:
        write_run(settings, "a")
        report = review_stage(settings, STAGE)
        payload = report.as_dict()
        assert payload["n_fail"] == len(report.failed)
        assert payload["n_warn"] == len(report.warned)
        assert payload["ready_for_review"] == report.ready_for_review
