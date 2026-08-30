---
name: stage-execute
description: Act as executor for a stage — carry out its planned computations, produce artifacts, keep the mechanical gate green, and hand off for scientific review. Use when asked to run a stage, execute a plan, generate trajectories, run analysis passes, or prepare a stage for review on this repository.
---

# Executing a stage

You are the executor. Your job is to carry out the plan faithfully, produce
artifacts a reviewer can read, and pass the mechanical gate before asking for
attention. You are *not* deciding what the results mean.

## 0. Orient before touching anything

Read, in order: `AGENTS.md`, `docs/stages/stage-N/PLAN.md`, then
`docs/stages/stage-N/HANDOFF.md` if present. The handoff is the operational
detail; the plan is the contract.

Confirm you are on the stage branch:

```bash
git switch stage-N     # created from main when the stage opened
afterlife doctor
```

## 1. Never spend money without an estimate first

```bash
afterlife estimate --config configs/stages/<config>.yaml
```

Report the forecast and the remaining project budget before generating. If the
forecast exceeds the stage budget, **stop and ask** — do not scale the budget and
do not quietly shrink the matrix. Proposing a reduced matrix with an explicit
statement of what statistical power is lost is the right move; deciding it alone
is not.

## 2. Generate, then check the protocol diagnostics before analysing

Runs are resumable: re-invoking the same command continues from the last
completed step, so a throttled or interrupted run costs wall clock, not data.

After generation, always:

```bash
python scripts/summarise_run.py <run_id>
```

and check, per model:

- **block fill** — if it collapsed, the stride is not `B`, the cost model is
  wrong, and the trajectory may be degenerate
- **stop rate** — the process only continues because we override the model's
  attempt to stop; a high rate is a finding, not noise
- **tokenizer round-trip failures** — any failure means the window was not where
  the manifest claims, and that trajectory's `W` is void
- **reasoning tokens** — must be zero; non-zero means the block we appended was
  only part of what the model generated
- **served provider** — must equal the pinned provider on every step

A number out of range here invalidates the analysis downstream. Report it before
running the analysis, not after.

## 3. Run the passes in order

```bash
afterlife embed --config <config> --run <generation_run_id>
afterlife analyze degeneracy  --run <generation_run_id>
afterlife analyze geometry    --run <embed_run_id>
afterlife analyze separation  --run <embed_run_id>
```

Degeneracy first, deliberately. A looping trajectory occupies one point in
representation space and will report a confined MSD for reasons that have nothing
to do with semantics. Knowing which trajectories are degenerate changes how every
later figure reads.

Repeat the analysis for **each** embedding space. A result that holds in one
representation is not a result.

## 4. Two rules that are easy to break

**Do not tune away a phenomenon.** If trajectories degenerate, that is a
measurement, not a bug to fix with a repetition penalty. If a model stops early,
that is data about the regime. Changing sampling parameters to produce
better-looking output is fabrication. Report the rate; do not suppress it.

**Do not extrapolate a measurement across regimes.** This project's most
repeated mistake, three times over: block fill measured at one window size,
trusted at another; a capability probe on a short prompt, trusted for long ones.
If a parameter changes, re-measure in the new regime — it usually costs cents.

## 5. Draft the report, scoring your own predictions

`docs/stages/stage-N/REPORT.md`, following
`.cursor/rules/40-stage-protocol.mdc`. Two sections carry the weight:

- **Verdict per exit criterion**: `PASS`/`FAIL`/`PARTIAL`, each with the artifact
  path that establishes it. No hedging — the verdict is a decision and the next
  stage depends on it.
- **Prediction vs outcome**: fill in the `observed` column of the plan's table.
  Every wrong prediction is a finding; say so plainly. A stage that falsifies its
  own hypothesis and reports it is a successful stage.

Also required, because they have all mattered here: realised block-fill
distribution, stop rate, reasoning-guard failures, and the rate of trajectories
lost to provider throttling.

## 6. Pass the gate, then hand off

```bash
afterlife review --stage N
```

Fix everything it reports. If you believe a check is wrong, say so with an
argument rather than working around it. **Do not request review while the gate
fails** — it spends the reviewer on work a tool already did.

When it exits 0, commit, push the branch, and hand off for review naming: the
stage, the headline finding in one sentence, the run ids behind it, and anything
you are uncertain about. Flagging your own uncertainty is more useful than
presenting a clean story.

## 7. Do not merge

Merging to `main` follows scientific sign-off, not gate success. That is the
supervisor's call.
