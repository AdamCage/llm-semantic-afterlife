---
name: stage-kickoff
description: Open a new research stage in this repository — verify the previous stage closed, write PLAN.md with pre-registered predictions, create the stage config and artifact directories, and produce a cost estimate before any spending. Use when starting stage N, planning the next experiment batch, or when asked "what's next".
---

# Stage kickoff

## 0. Refuse if the previous stage is not closed

```bash
ls docs/stages/stage-<N-1>/REPORT.md
```

No report ⇒ stop and close stage `N-1` first (skill: `stage-close`). The only
exception is `S0`, which has no predecessor.

Read, in order: `docs/research-plan.md` (the entry for stage N),
`docs/stages/stage-<N-1>/REPORT.md` (§7 *Implications for the plan*), and any
ADR added since the plan was last revised. The plan entry for stage N is a
sketch written earlier — the previous report is what actually determines the
stage. Where they conflict, the report wins and the plan gets amended.

## 1. Draft the plan

Create `docs/stages/stage-N/PLAN.md` following the section order mandated by
`.cursor/rules/40-stage-protocol.mdc`. Two sections are the ones agents
usually get wrong:

**Exit criteria** must be falsifiable and quantitative, written before data
exists. Bad: "understand whether attractors exist." Good: "for ≥3 of 4 models,
the number of MSM macrostates is stable (±1) across `K ∈ {50,100,200,400}`
microstates and across both embedding spaces, with implied timescales flat over
`τ ∈ [4,16]` chunks."

**Pre-registered predictions** state what we expect and with what confidence,
so the report can show us being wrong. Write them as a table with a
`predicted` column and an empty `observed` column that the report fills in.

## 2. Encode the matrix as config, not prose

Write `configs/stages/stageN_<name>.yaml`. The plan's experiment matrix must be
mechanically derivable from this file — if the numbers in `PLAN.md` and the
YAML disagree, the YAML is authoritative and the plan is wrong.

Then verify the matrix expands to what you intended:

```bash
afterlife plan --config configs/stages/stageN_<name>.yaml
```

This prints the expanded cell list, total trajectories, total tokens, and
per-model breakdown without contacting any API.

## 3. Estimate cost and get approval

```bash
afterlife estimate --config configs/stages/stageN_<name>.yaml
```

Report to the human: total USD, remaining project budget, wall-clock estimate,
and the per-model split. **Wait for explicit approval** before any generation.
If the estimate exceeds the stage budget in the research plan, do not scale the
budget — propose a reduced matrix and explain what statistical power is lost.

## 4. Scaffold

```bash
mkdir -p docs/stages/stage-N artifacts/stage-N
```

Add a `docs/stages/stage-N/README.md` one-pager: question, matrix in one table,
status checkboxes per computation. This is the stage's progress dashboard;
update it as passes complete so the human can see state at a glance.

## 5. Commit before executing

Commit the plan and config *before* the first API call. The commit SHA becomes
the provenance anchor for every run in the stage, and it proves the predictions
were registered before the data arrived.
