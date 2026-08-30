---
name: stage-close
description: Close a research stage — verify every planned computation has a complete run, assemble artifacts, write REPORT.md with an explicit verdict per exit criterion, reconcile spend, and re-plan the next stage. Use when a stage's computations are finished, when asked to write up results, or before starting the next stage.
---

# Stage close

Closing a stage is where the project accumulates value. Do it thoroughly even
— especially — when the result is negative.

## 1. Verify completeness before writing anything

```bash
afterlife verify --stage N
```

Checks that every cell in the stage config has a run with `STATUS=COMPLETED`,
that manifests are complete, that output hashes match the integrity block, and
that no run was produced from a dirty git tree without a recorded diff.

Any gap must be either filled or explicitly declared in the report as
**missing data with a reason**. Silently reporting on a partial matrix while
implying it was complete is the one failure mode that makes the whole stage
worthless.

## 2. Assemble artifacts

```bash
afterlife report --stage N
```

Produces `artifacts/stage-N/` with figures (html + png + svg + `.data.parquet`
+ `.meta.json`), tables (csv + parquet + md + html), and
`artifacts/stage-N/INDEX.md` linking everything with captions.

Then read every figure as a hostile reviewer. Specifically check: is the
context horizon `t = W` marked; is uncertainty shown; is `n` stated; does any
claim rest on a 2-D projection; are units on the axes; does the caption say
what the figure *cannot* establish.

## 3. Write `docs/stages/stage-N/REPORT.md`

Follow the section order in `.cursor/rules/40-stage-protocol.mdc`. Guidance for
the sections that carry the most weight:

**Verdict per exit criterion.** One line each: criterion, `PASS`/`FAIL`/
`PARTIAL`, the artifact path that establishes it. No prose hedging — the
verdict is a decision, and the plan for stage N+1 depends on it.

**Prediction vs. outcome.** Fill in the `observed` column of the table from
`PLAN.md`. Every wrong prediction is a finding; say so plainly and consider
what it implies about the mechanism.

**Surprises.** Anything unplanned. Include things you noticed and dismissed —
a reviewer may not dismiss them. Candidates that keep showing up in this
project: degenerate repetition loops, provider-side non-determinism, an EOS
storm on instruct models, tokenizer round-trip failures, chunk-boundary
artifacts.

**Threats to validity.** Be specific and current. "Embedding dependence" is not
a threat statement; "attractor count differs by 2 between Qwen3-Embedding and
BGE-M3 at `W=8k`, ARI 0.61, so the macrostate decomposition is only partially
representation-independent" is.

## 4. Reconcile money

```bash
afterlife ledger --stage N
```

Report actual vs. estimated spend and the remaining project budget. A large
overrun is itself a planning finding — record why.

## 5. Update the master plan and re-plan

Amend `docs/research-plan.md` (and the `.ru` mirror) for stage N+1 based on what
was actually learned. If the amendment changes scope, method, or a stated
non-negotiable, add an ADR in the same commit.

## 6. Commit as one atomic unit

Report + artifacts + plan amendment + ADR in a single commit, so the repository
history reads as a sequence of decisions with their evidence attached.
