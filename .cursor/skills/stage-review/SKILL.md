---
name: stage-review
description: Act as scientific supervisor for a stage — run the mechanical gate, then judge whether the conclusions follow from the evidence. Use when asked to review a stage, sign off on a merge to main, check whether results are publishable, or audit another agent's work on this repository.
---

# Reviewing a stage

You are the scientific supervisor. Your attention is the expensive resource in
this project; spend none of it on anything a tool can decide.

## 1. Run the gate first, and stop if it fails

```bash
afterlife review --stage N --json .cache/review-N.json
```

If it exits non-zero, **do not review**. Return the failures to the executor and
stop. Reviewing work that fails the mechanical gate teaches the executor that the
gate is optional, and it wastes the review on problems that were already
detected.

If it passes, treat everything it checks as settled: plan present with
pre-registered predictions, runs complete, output hashes intact, artifact bundles
self-contained, degeneracy labelled wherever confinement is claimed, budget
reconciled, report scoring its own predictions. Do not re-derive any of it.

## 2. Read in this order

1. `docs/stages/stage-N/PLAN.md` — **before** the report. You need the
   pre-registered predictions in mind before seeing the outcome, or you will
   read the report's framing as the plan's intent.
2. `docs/stages/stage-N/REPORT.md` §1 (verdicts) and §3 (prediction scoring).
3. `artifacts/stage-N/INDEX.md`, then the figures that carry the headline claim.
4. The `.meta.json` limitations line of each of those figures.
5. `docs/decisions/` for any ADR added during the stage.

## 3. The seven questions

For each headline claim, in order. Any "no" is a blocking finding.

1. **Does the conclusion follow?** Not "is the number correct" — the gate covers
   traceability — but "does this number support this sentence". Read the sentence
   and the figure side by side and ask what else could produce that figure.
2. **Is every threshold calibrated?** Ask what reference each was calibrated
   against, and whether that reference matches the data's regime. An
   intuition-chosen threshold is a defect regardless of whether the result
   survives it. This project shipped one six times too high, which inverted the
   reading of an entire trajectory.
3. **Was the measurement taken in the regime it is applied to?** Check every
   parameter carried over from a probe: window size, prompt length, temperature,
   trajectory length, model, endpoint. This project's most repeated error is a
   number measured in one regime and trusted in another — three separate times.
4. **Is the claim generalised from one instance?** Count the generators, seeds,
   temperatures, embedding spaces and providers behind each claim. Three of four
   generators here behave differently from each other; one instance is a claim
   about one instance.
5. **Is every confound named?** Degeneracy, provider identity, quantization,
   template overhead, reasoning tokens, continuation forced past a stop token,
   probe leakage, autocorrelated bootstrap units. Each has contaminated a result
   in this project. A confound that is real and unnamed is the finding.
6. **Do the artifacts state what they cannot establish?** A limitations line that
   paraphrases the caption is not one. It should name the alternative explanation
   the figure fails to exclude.
7. **Is a negative result being softened?** Look for hedging around a failed
   prediction. A falsified hypothesis stated plainly is a successful stage; a
   hedged one is a damaged paper.

## 4. Verdict

Write to `docs/stages/stage-N/REVIEW.md`:

```
# Stage N review
Reviewer: <model/agent>   Date: YYYY-MM-DD
Gate: PASS (afterlife review --stage N, exit 0)
Verdict: APPROVED | APPROVED WITH CHANGES | REJECTED

## Blocking findings
(numbered; each names the claim, the problem, and what would resolve it)

## Non-blocking observations

## Claims I judge supported
(explicitly — the executor needs to know what not to relitigate)

## Claims I judge unsupported or overreaching
```

Be specific about what would resolve each blocking finding: a measurement, a
calibration, a reworded claim, or an additional arm. "Needs more rigour" is not
actionable.

## 5. Only after APPROVED

Merge per `.cursor/rules/70-roles-and-branches.mdc`: `--no-ff` into `main`, then
delete the branch. The review file is part of the stage's record and is committed
with it.

## What not to do

- Do not rewrite the executor's code during review. Report and return.
- Do not approve because the work is thorough. Thoroughness is not correctness.
- Do not reject on style, naming, or anything a linter could have caught.
- Do not accept "the trend is clear" in place of an interval.
