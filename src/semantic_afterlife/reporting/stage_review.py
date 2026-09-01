"""Mechanical review gate for a stage.

The point of this module is to make the division of labour between an executing
agent and a reviewing one real rather than aspirational. Everything here is
objectively checkable: run completeness, manifest integrity, artifact bundles,
degeneracy labelling, budget reconciliation, prediction scoring. An executing
agent runs it and fixes what it reports; the reviewer's judgement is then spent
only on what a tool cannot decide -- whether the conclusion follows from the
evidence, whether a threshold is defensible, whether a claim is overreaching.

Every check here corresponds to a way this project has already produced, or
nearly produced, a confidently wrong number. They are not hypothetical.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import orjson
import pandas as pd

from ..config import Settings
from ..hashing import sha256_file
from ..ledger import read_ledger
from ..provenance import read_manifest


class Verdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


@dataclass(slots=True)
class Check:
    name: str
    verdict: Verdict
    detail: str
    why_it_matters: str
    evidence: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "check": self.name,
            "verdict": str(self.verdict),
            "detail": self.detail,
            "why_it_matters": self.why_it_matters,
            "evidence": self.evidence,
        }


@dataclass(slots=True)
class ReviewReport:
    stage: str
    checks: list[Check]

    @property
    def failed(self) -> list[Check]:
        return [c for c in self.checks if c.verdict is Verdict.FAIL]

    @property
    def warned(self) -> list[Check]:
        return [c for c in self.checks if c.verdict is Verdict.WARN]

    @property
    def ready_for_review(self) -> bool:
        return not self.failed

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([c.as_dict() for c in self.checks])

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "ready_for_review": self.ready_for_review,
            "n_pass": sum(1 for c in self.checks if c.verdict is Verdict.PASS),
            "n_fail": len(self.failed),
            "n_warn": len(self.warned),
            "checks": [c.as_dict() for c in self.checks],
        }


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_plan_exists(settings: Settings, stage: str) -> Check:
    plan = settings.paths.stage_docs(stage) / "PLAN.md"
    if not plan.is_file():
        return Check(
            "plan.exists",
            Verdict.FAIL,
            f"{plan} is missing",
            "A stage without a plan written beforehand cannot have pre-registered "
            "predictions, so its results cannot be distinguished from post-hoc fitting.",
        )
    text = plan.read_text(encoding="utf-8")
    missing = [
        heading
        for heading in ("Exit criteria", "Pre-registered predictions", "Budget")
        if heading.lower() not in text.lower()
    ]
    if missing:
        return Check(
            "plan.exists",
            Verdict.FAIL,
            f"plan is missing required sections: {', '.join(missing)}",
            "Exit criteria and pre-registered predictions are what make the stage "
            "falsifiable rather than descriptive.",
            [str(plan)],
        )
    return Check(
        "plan.exists",
        Verdict.PASS,
        "plan present with exit criteria, predictions and budget",
        "Pre-registration is what lets the report show us being wrong on the record.",
        [str(plan)],
    )


def check_runs_complete(settings: Settings, stage: str) -> Check:
    stage_dir = settings.paths.runs / stage
    if not stage_dir.is_dir():
        return Check(
            "runs.complete",
            Verdict.FAIL,
            f"no runs directory at {stage_dir}",
            "Every number must trace to a run; with no runs there is nothing to review.",
        )
    bad: list[str] = []
    total = 0
    superseded = 0
    for run_dir in sorted(p for p in stage_dir.iterdir() if p.is_dir()):
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.is_file():
            bad.append(f"{run_dir.name}: no manifest")
            continue
        if (run_dir / "SUPERSEDED").is_file():
            # Explicitly retired, with a recorded reason. Kept on disk because
            # deleting a superseded result destroys the record of what was tried.
            superseded += 1
            continue
        total += 1
        manifest = read_manifest(manifest_path)
        if manifest.get("status") != "COMPLETED":
            bad.append(f"{run_dir.name}: status={manifest.get('status')}")
    if not total:
        return Check(
            "runs.complete",
            Verdict.FAIL,
            "no runs with manifests",
            "Every number must trace to a run.",
        )
    if bad:
        return Check(
            "runs.complete",
            Verdict.WARN,
            f"{len(bad)} of {total + len(bad)} runs incomplete: {'; '.join(bad[:5])}",
            "An incomplete run is not automatically a problem, but it must be declared as "
            "missing data in the report rather than silently excluded from the sample.",
        )
    return Check(
        "runs.complete",
        Verdict.PASS,
        f"{total} runs COMPLETED",
        "Silently reporting on a partial matrix while implying it was complete is the one "
        "failure mode that makes a whole stage worthless.",
    )


def check_integrity(settings: Settings, stage: str) -> Check:
    stage_dir = settings.paths.runs / stage
    if not stage_dir.is_dir():
        return Check("runs.integrity", Verdict.SKIP, "no runs", "")
    mismatched: list[str] = []
    checked = 0
    for run_dir in sorted(p for p in stage_dir.iterdir() if p.is_dir()):
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.is_file():
            continue
        for rel, digest in (read_manifest(manifest_path).get("integrity") or {}).items():
            target = run_dir / rel
            checked += 1
            if not target.is_file() or sha256_file(target) != digest:
                mismatched.append(f"{run_dir.name}/{rel}")
    if mismatched:
        return Check(
            "runs.integrity",
            Verdict.FAIL,
            f"{len(mismatched)} files differ from their recorded hash: {mismatched[:3]}",
            "A changed output file means the manifest no longer describes what is on disk, "
            "so nothing derived from it is traceable.",
        )
    return Check(
        "runs.integrity",
        Verdict.PASS,
        f"{checked} output files match their recorded hashes",
        "Integrity hashes are what make a run's outputs attributable after the fact.",
    )


def check_artifact_bundles(settings: Settings, stage: str) -> Check:
    root = settings.paths.stage_artifacts(stage)
    if not root.is_dir():
        return Check(
            "artifacts.bundle",
            Verdict.FAIL,
            f"no artifacts directory at {root}",
            "Artifacts are the paper's evidence base; a stage with none has produced nothing "
            "a reviewer can read.",
        )
    problems: list[str] = []
    n_figures = 0
    for meta_path in sorted(root.rglob("*.meta.json")):
        n_figures += 1
        base = meta_path.with_name(meta_path.name.removesuffix(".meta.json"))
        try:
            meta = orjson.loads(meta_path.read_bytes())
        except orjson.JSONDecodeError:
            problems.append(f"{meta_path.name}: unreadable")
            continue
        has_data = any(
            base.with_suffix(suffix).is_file() or Path(f"{base}.data{suffix}").is_file()
            for suffix in (".parquet", ".npz", ".csv")
        )
        if not has_data:
            problems.append(f"{base.name}: no source data")
        if not str(meta.get("caption", "")).strip():
            problems.append(f"{base.name}: no caption")
        if not str(meta.get("limitations") or "").strip():
            problems.append(f"{base.name}: no limitations statement")
    if not n_figures:
        return Check(
            "artifacts.bundle",
            Verdict.FAIL,
            "no figures or tables found",
            "Artifacts are the paper's evidence base.",
        )
    if problems:
        return Check(
            "artifacts.bundle",
            Verdict.FAIL,
            f"{len(problems)} incomplete bundles: {problems[:4]}",
            "A figure without its tidy source data, caption and limitations is not an "
            "artifact: nobody can check it or know what it fails to establish.",
        )
    return Check(
        "artifacts.bundle",
        Verdict.PASS,
        f"{n_figures} artifacts complete with data, captions and limitations",
        "Self-containment is what lets a reader check a figure instead of trusting it.",
    )


def check_degeneracy_labelled(settings: Settings, stage: str) -> Check:
    """Any confinement claim must know which trajectories were looping.

    S1.0 measured an MSD exponent of 0.357 and read it as semantic confinement.
    The trajectory was degenerate throughout at eighteen times natural repetition,
    so the exponent measured the loop. This check exists so that cannot recur
    silently.
    """
    stage_dir = settings.paths.runs / stage
    if not stage_dir.is_dir():
        return Check("analysis.degeneracy_labelled", Verdict.SKIP, "no runs", "")

    geometry_runs = [
        p
        for p in stage_dir.iterdir()
        if p.is_dir() and "geometry" in p.name and not (p / "SUPERSEDED").is_file()
    ]
    if not geometry_runs:
        return Check(
            "analysis.degeneracy_labelled",
            Verdict.SKIP,
            "no geometry runs in this stage",
            "",
        )
    unlabelled: list[str] = []
    labelled = 0
    for run_dir in geometry_runs:
        scalars = run_dir / "data" / "geometry_scalars.parquet"
        if not scalars.is_file():
            unlabelled.append(f"{run_dir.name}: no geometry_scalars")
            continue
        frame = pd.read_parquet(scalars)
        if "degenerate" not in frame.columns or frame["degenerate"].isna().all():
            unlabelled.append(f"{run_dir.name}: no degeneracy column")
        else:
            labelled += 1
    if unlabelled:
        return Check(
            "analysis.degeneracy_labelled",
            Verdict.FAIL,
            f"geometry without degeneracy labels: {unlabelled[:3]}",
            "An MSD exponent from a looping trajectory measures repetition, not semantics. "
            "Reporting one unlabelled is how a repetition artifact becomes a claim about "
            "semantic confinement -- which this project did once already.",
        )
    return Check(
        "analysis.degeneracy_labelled",
        Verdict.PASS,
        f"{labelled} geometry runs carry per-trajectory degeneracy labels",
        "Confinement claims are only interpretable alongside the degeneracy verdict.",
    )


def check_budget(settings: Settings, stage: str) -> Check:
    entries = read_ledger(settings.paths.ledger)
    if not entries:
        return Check(
            "budget.reconciled",
            Verdict.WARN,
            "ledger is empty",
            "Spend has to be reconciled per stage; an empty ledger means either no API work "
            "or a bypassed ledger, and those must not look the same.",
        )
    frame = pd.DataFrame(entries)
    stage_spend = float(frame[frame["run_id"].astype(str).str.startswith(stage)]["cost_usd"].sum())
    total = float(frame["cost_usd"].sum())
    remaining = settings.afterlife_budget_usd_total - total
    if remaining < 0:
        return Check(
            "budget.reconciled",
            Verdict.FAIL,
            f"project spend ${total:.4f} exceeds the ceiling of "
            f"${settings.afterlife_budget_usd_total:.2f}",
            "The ceiling exists so that a runaway loop cannot spend the project's budget; "
            "crossing it must stop work, not be noted.",
        )
    return Check(
        "budget.reconciled",
        Verdict.PASS,
        f"stage ${stage_spend:.4f}, project ${total:.4f} of "
        f"${settings.afterlife_budget_usd_total:.2f} (${remaining:.2f} left)",
        "Every stage report states actual against forecast spend.",
    )


def check_report_scores_predictions(settings: Settings, stage: str) -> Check:
    docs = settings.paths.stage_docs(stage)
    report = docs / "REPORT.md"
    if not report.is_file():
        return Check(
            "report.scores_predictions",
            Verdict.SKIP,
            "no REPORT.md yet (expected while the stage is still running)",
            "",
        )
    text = report.read_text(encoding="utf-8")
    problems = []
    if not re.search(r"\bPASS\b|\bFAIL\b|\bPARTIAL\b", text):
        problems.append("no per-criterion verdict")
    if "observed" not in text.lower():
        problems.append("prediction table not scored")
    if "threat" not in text.lower():
        problems.append("no threats-to-validity section")
    if problems:
        return Check(
            "report.scores_predictions",
            Verdict.FAIL,
            "; ".join(problems),
            "A report that does not score its own predictions and name its own weaknesses is "
            "advocacy, not a result.",
            [str(report)],
        )
    return Check(
        "report.scores_predictions",
        Verdict.PASS,
        "verdicts, scored predictions and threats present",
        "Being wrong on the record is the point of pre-registration.",
        [str(report)],
    )


def check_no_unverified_citations(settings: Settings, stage: str) -> Check:
    del stage
    path = settings.paths.root / "docs" / "literature" / "related-work.md"
    if not path.is_file():
        return Check("literature.verified", Verdict.SKIP, "no related-work.md", "")
    text = path.read_text(encoding="utf-8")
    leads = text.count("`LEAD`")
    paper = settings.paths.root / "paper" / "main.tex"
    if leads and paper.is_file() and paper.stat().st_size > 0:
        return Check(
            "literature.verified",
            Verdict.FAIL,
            f"{leads} unverified citations while paper/main.tex has content",
            "An unverified citation in a submission is worse than a missing one.",
        )
    verdict = Verdict.PASS if leads == 0 else Verdict.WARN
    return Check(
        "literature.verified",
        verdict,
        f"{leads} citations still marked LEAD",
        "Nothing enters the manuscript while still unverified.",
        [str(path)],
    )


def check_spend_matches_events(settings: Settings, stage: str) -> Check:
    """The ledger and the per-step events must agree on what was spent.

    Stage 1's cost was under-reported roughly thirtyfold, because
    ``cumulative_cost_usd`` in the step events accumulates *per trajectory* and
    its maximum was read as the run total. The ledger was correct throughout, so
    the defect was in the reading rather than the recording — which is exactly
    the kind of error a checklist cannot prevent and a comparison can.
    """
    stage_dir = settings.paths.runs / stage
    if not stage_dir.is_dir():
        return Check("budget.ledger_matches_events", Verdict.SKIP, "no runs", "")

    entries = read_ledger(settings.paths.ledger)
    if not entries:
        return Check("budget.ledger_matches_events", Verdict.SKIP, "empty ledger", "")
    frame = pd.DataFrame(entries)

    mismatches: list[str] = []
    compared = 0
    for run_dir in sorted(p for p in stage_dir.iterdir() if p.is_dir()):
        events_path = run_dir / "events.jsonl"
        if not events_path.is_file() or (run_dir / "SUPERSEDED").is_file():
            continue
        stepwise = 0.0
        found = False
        with events_path.open("rb") as handle:
            for line in handle:
                if b"generation.step.completed" not in line:
                    continue
                try:
                    payload = orjson.loads(line)
                except orjson.JSONDecodeError:
                    continue
                if payload.get("event") == "generation.step.completed":
                    stepwise += float(payload.get("cost_usd") or 0.0)
                    found = True
        if not found:
            continue
        compared += 1
        ledger_total = float(frame[frame["run_id"] == run_dir.name]["cost_usd"].sum())
        # Cached steps cost nothing and are ledgered as zero, so the two agree
        # to rounding when both are read correctly.
        if abs(ledger_total - stepwise) > max(0.01, 0.02 * max(ledger_total, stepwise)):
            mismatches.append(
                f"{run_dir.name}: ledger ${ledger_total:.4f} vs events ${stepwise:.4f}"
            )
    if not compared:
        return Check("budget.ledger_matches_events", Verdict.SKIP, "no generation runs", "")
    if mismatches:
        return Check(
            "budget.ledger_matches_events",
            Verdict.FAIL,
            f"{len(mismatches)} runs disagree: {mismatches[:3]}",
            "A spend figure that differs between the ledger and the step events means one "
            "of them is being read wrongly, and the reported cost of the stage is untrue.",
        )
    return Check(
        "budget.ledger_matches_events",
        Verdict.PASS,
        f"{compared} runs agree between ledger and step events",
        "Reported spend is the same quantity whichever record it is read from.",
    )


def check_diagnostics_are_segmented(settings: Settings, stage: str) -> Check:
    """Protocol diagnostics must be reported over the run, not averaged over it.

    Nothing in this protocol is stationary. Stage 1's block fill decayed from
    0.995 to 0.653 and its stop rate rose from 4.5% to 74%, and a criterion was
    amended on a reading taken from the first 5% of the run. A single mean hides
    exactly the behaviour that matters.
    """
    report = settings.paths.stage_docs(stage) / "REPORT.md"
    if not report.is_file():
        return Check("report.diagnostics_segmented", Verdict.SKIP, "no REPORT.md yet", "")
    text = report.read_text(encoding="utf-8").lower()
    segmented = any(
        marker in text
        for marker in ("quarter", "per segment", "by segment", "first 25", "final quarter")
    )
    mentions = any(marker in text for marker in ("block fill", "stop rate"))
    if not mentions:
        return Check(
            "report.diagnostics_segmented",
            Verdict.FAIL,
            "report does not mention block fill or stop rate",
            "Both are order parameters of this protocol, not housekeeping: the stop rate "
            "reaching 74% is what makes a 'free-running' trajectory mostly forced.",
            [str(report)],
        )
    if not segmented:
        return Check(
            "report.diagnostics_segmented",
            Verdict.FAIL,
            "block fill and stop rate are reported without segmentation over the run",
            "A run-level mean hides monotone drift. Stage 1's fill averaged 0.748 while "
            "ending at 0.653, and a criterion was amended on a reading from its first 5%.",
            [str(report)],
        )
    return Check(
        "report.diagnostics_segmented",
        Verdict.PASS,
        "protocol diagnostics reported across the run rather than averaged",
        "Drift in the diagnostics is itself a result.",
        [str(report)],
    )


def check_report_quotes_generated_text(settings: Settings, stage: str) -> Check:
    """The report must quote the model's own output, from several points.

    Twice in Stage 1 reading the text beat reading the metrics. Every intra-chunk
    diagnostic called a trajectory healthy while it reprinted the same page, and
    the novelty measure built to catch that was in turn blind to two trajectories
    converging to the same register in different words. No statistic yet devised
    here has replaced looking at the output.
    """
    report = settings.paths.stage_docs(stage) / "REPORT.md"
    if not report.is_file():
        return Check("report.quotes_text", Verdict.SKIP, "no REPORT.md yet", "")
    text = report.read_text(encoding="utf-8")
    # Block quotes or fenced blocks, either of which can carry sample output.
    quoted = [
        line
        for line in text.splitlines()
        if line.lstrip().startswith(">") and len(line.strip()) > 40
    ]
    fenced = text.count("```") // 2
    if len(quoted) + fenced < 3:
        return Check(
            "report.quotes_text",
            Verdict.FAIL,
            f"only {len(quoted)} block quotes and {fenced} fenced blocks; at least 3 "
            "samples of generated text are required",
            "Reading the output caught what every metric missed, twice in Stage 1. A report "
            "with no generated text in it is a report nobody looked at.",
            [str(report)],
        )
    return Check(
        "report.quotes_text",
        Verdict.PASS,
        f"{len(quoted) + fenced} samples of generated text present",
        "Somebody looked at what the model actually wrote.",
        [str(report)],
    )


ALL_CHECKS = (
    check_plan_exists,
    check_runs_complete,
    check_integrity,
    check_artifact_bundles,
    check_degeneracy_labelled,
    check_budget,
    check_spend_matches_events,
    check_diagnostics_are_segmented,
    check_report_quotes_generated_text,
    check_report_scores_predictions,
    check_no_unverified_citations,
)


def review_stage(settings: Settings, stage: str) -> ReviewReport:
    return ReviewReport(stage=stage, checks=[check(settings, stage) for check in ALL_CHECKS])
