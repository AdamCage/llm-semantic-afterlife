# Stage 13 plan — Paper B cross-family synthesis

## 1. Question

What do the closed S9–S11 records establish when they are read together,
without pooling families, and how does the closed S12 count sit beside
that story.

## 2. Entry state

S12 is closed on `main` (`162b7782`). The judged count is 0/8 confirmed
escape through 4,999,168 original tokens: 1220.5 turnovers from L0 token
0, lock at 0.75, 1219.75 turnovers after the lock. That count is not a
pooled rate and not a permanence claim
(`docs/stages/stage-12/REPORT.md`,
`artifacts/stage-12/tau_escape/tau_escape.meta.json`).

S9–S11 are closed. Their confirmatory numbers stay in the published
`gt_last_band.csv` files. This stage does not re-estimate \(G_t\), does
not retune F1 or `N_confirm`, and does not recompute S12 flags.

Gemma Base BGE is an identified negative. The Gemma Base Qwen-embed sign
is not established. Cross-space sign agreement for Gemma is not
identified. ADR-0023 and ADR-0025 still freeze the estimands. There is
no S14.

## 3. Experiment matrix

Zero new trajectories. `configs/stages/stage13_synthesis.yaml` selects no
generator and no seed. The window block names the published L0 regime
(\(W=4096\), \(B=1024\), \(T=49152\)) so the file remains a stage config.
It is not a generate request.

Sources, copied not recomputed:

| Stage | Artifact |
| --- | --- |
| S9 | `artifacts/stage-9/gt_last_band/gt_last_band.csv` |
| S9 | `artifacts/stage-9/generate_status/generate_status.csv` |
| S9 | `artifacts/stage-9/protocol_by_quarter/protocol_by_quarter.csv` |
| S10 | `artifacts/stage-10/gt_last_band/gt_last_band.csv` |
| S10 | `artifacts/stage-10/generate_status/generate_status.csv` |
| S10 | `artifacts/stage-10/protocol_by_quarter/protocol_by_quarter.csv` |
| S11 | `artifacts/stage-11/gt_last_band/gt_last_band.csv` |
| S11 | `artifacts/stage-11/generate_status/generate_status.csv` |
| S11 | `artifacts/stage-11/protocol_by_quarter/protocol_by_quarter.csv` |
| S12 | `artifacts/stage-12/tau_escape/tau_escape.data.parquet` |

`afterlife plan` on an empty cell list has no columns to group. The
authoritative matrix is 0 trajectories. `afterlife estimate` is the cost
check and must print `$0.00`. Any positive forecast stops the stage.

## 4. Computations

1. Commit this plan before assembly.
2. `uv run python scripts/s13_assemble.py` — one local run under
   `runs/s13/`, copying the files above into `artifacts/stage-13/`.
3. `afterlife review --stage s13` until exit 0.
4. Only then, add a Paper B section to `paper/main.tex`. Do not rewrite
   the Paper A text. Every new quantitative sentence carries an artifact
   path and `run_id`.

No `afterlife generate`. No embed. No hosted call. No GPU.

## 5. Exit criteria

| # | Criterion |
| --- | --- |
| E1 | One S13 run, cost $0, and no new generate `run_id` |
| E2 | Headline \(G_t\) table is the concatenation of the three published CSVs, with family kept as a column and no pooled row |
| E3 | Gemma Base BGE stays an identified negative and Gemma Base Qwen-embed stays not established, both copied from the S11 CSV |
| E4 | S12 table is the published parquet: 0/8 `confirmed_escape_through_tmin`, separate from the \(G_t\) figure |
| E5 | Figure bundles have tidy data, a caption, and a limitations line; the plotted quantity is the published high-dimensional \(G_t\) |
| E6 | Ledger spend on the S13 run is $0 |
| E7 | The report names reprompt versus native sliding attention, embedding-space dependence, provider non-determinism, and finite trajectory length |

## 6. Pre-registered predictions

These are commitments about the assembly, written before the assembly
run. The measurements themselves are already closed. The `observed`
column is filled only in `REPORT.md`.

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| P1 | The assembled table has a family column and no row whose family is pooled | 0.90 | |
| P2 | Gemma Base BGE: published \(G_t<0\) and `ci_excludes_0`; Gemma Base Qwen-embed: `ci_excludes_0` is false | 0.95 | |
| P3 | S12 published flag `confirmed_escape_through_tmin` is false on all 8 rows, and those rows are not appended to the \(G_t\) table | 0.95 | |
| P4 | The S13 command line does not call generate, embed, or a hosted client | 0.99 | |
| P5 | New captions and the report do not use permanence language, do not say attention on every layer is dispensable, and do not say Gemma disagrees across spaces | 0.90 | |

## 7. Budget and wall-clock

Forecast $0. Ceiling $0. A positive forecast or any GPU generate stops
the stage. Wall-clock is the assembly script, under one hour. The CLI
treats `budget_usd: 0.0` as an undeclared budget because zero is falsy
in `afterlife estimate`; the ceiling in this plan is still $0.

## 8. Risks specific to this stage

| Risk | Mitigation |
| --- | --- |
| Pooling families into one rate | E2. A pooled family row aborts the script |
| Reading 0/8 as a permanent lock | E4 and P5. S12 stays on its own figure |
| Gemma cross-space overclaim | P2. Copy the S11 booleans. Do not say the spaces disagree |
| Recomputing flags or \(G_t\) | The script only reads published columns |
| Rewriting Paper A | `paper/main.tex` is appended to, and only after the gate |
| A 2-D projection used as a statistic | The figure plots the published scalar \(G_t\) with its published interval |
| Dirty tree from unrelated untracked scripts | Do not stage them. The assembly hashes published inputs, not those scripts |
