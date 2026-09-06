# Stage 4 — Does temperature or W move anything on qwen3-8b?

**Status.** Opened 2026-09-03 on branch `cursor/stage-4-6dce`, after
Stage 3 closed PARTIAL and the S3.0 follow-up merged to `main`.
Decision: [ADR-0014](../../decisions/ADR-0014-reduced-s4-temp-window.md).
Generate authorised 2026-09-04 (human yes on the $2.47 / $3.33
estimate). S4.1 then S4.2. Scientific review **APPROVED** 2026-09-05
([`REVIEW.md`](REVIEW.md)). Closed `--no-ff` to `main` as `5c07751`.

## 1. Question

On the one instruct process we can already measure (`or-qwen3-8b` under
P1 `raw_completion`), do temperature and the imposed window `W` change
the after-horizon dynamics — looping rate, stop/fill, and MSD `α` on
*non-degenerate* trajectories — or is T=1.0 still a lock at both
`W = 4096` and `W = 8192`?

This stage does **not** ask whether H1 holds (Stage 3: unsupported on
this sample). It does **not** treat `n_macro` as an order parameter.
It does **not** claim a result about language models as a class.

## 2. Entry state

From [Stage 2](../stage-2/REPORT.md), [Stage 3](../stage-3/REPORT.md),
[ADR-0010](../../decisions/ADR-0010-stage2-findings-replan-s3.md),
[ADR-0013](../../decisions/ADR-0013-project-ceiling-200.md),
[ADR-0014](../../decisions/ADR-0014-reduced-s4-temp-window.md):

- Convergence is not universal. On qwen3-8b under P1 it is: S2.2 raw
  is 8/8 textual fixed points at `W = 4096`, T ∈ {0.3, 1.0}.
- Prefill is not a lever. Headline protocol stays `raw_completion`.
- H1 has no validated macrostate on the restricted instruct sample.
  7–8/8 F4 trajectories were degenerate.
- S3.0 (`gemma-3-1b-pt`, `W = 256`) loops the seed; T=1.0 is a token
  lock, not diffusion. That regime does not transfer here.
- OpenRouter is funded. Project ceiling **$200**; ledger **$11.57**.
  The OpenRouter *key* monthly remainder is ~$47 and can refuse first.
- Eight reusable cells already exist:

  `s2-mechanism-20260901T071519Z-dfbb173a`, generator `or-qwen3-8b`
  (not prefill), `W = 4096`, T ∈ {0.3, 1.0}, seeds physics/surreal,
  stochastic 1/2, 8/8 COMPLETED, 47–48 chunks. Embeddings:
  `s2-embed-mechanism-20260901T131051Z-55761049`.

## 3. Experiment matrix

The **scientific** grid is 1 generator × 2 windows × 4 temperatures ×
2 semantic seeds × 2 stochastic replicates = **32 trajectories**,
12 turnovers each. Eight of those are reused. New generation is two
configs; if PLAN prose and YAML disagree, **YAML wins**.

| # | Pass | Config | What it adds | Trajectories | Tokens (fill=1) |
| --- | --- | --- | --- | --- | --- |
| S4.0 | Reuse S2.2 raw | — | `W=4096`, T ∈ {0.3, 1.0} | 8 existing | 0 new |
| S4.1 | New temps at 4096 | `configs/stages/stage4_w4096_new_temps.yaml` | T ∈ {0.7, 1.5} | 8 new | 1.491M in + 0.393M out |
| S4.2 | First W=8192 | `configs/stages/stage4_w8192.yaml` | all four T | 16 new | 11.993M in + 1.573M out |

`B = S = 1024`, `chunk_size = 1024`, protocol P1, `forcing = unforced`,
`reasoning_effort: none`, embeddings `bge-m3` and `qwen3-embed-8b`.
Seeds: `physics`, `surreal`. Stochastic: 1, 2.

Not in this opening: T ∈ {0.0, 0.2, 0.5, 1.2}, `W ∈ {16384, 32768}`,
a second generator, Glimmer's 2048 local window, coder models, a local
base pair.

## 4. Computations

Ordered. Degeneracy before geometry. No generate until estimate approval.

1. `afterlife generate --config configs/stages/stage4_w4096_new_temps.yaml`
   then `--config configs/stages/stage4_w8192.yaml`. Artifacts under
   `runs/s4/`. Stop if a config's forecast or live spend hits its
   `budget_usd`.
2. `python scripts/summarise_run.py <run_id>` per generation run:
   fill, stop, round-trip, reasoning, served provider = `alibaba`.
3. `afterlife embed --run <new_run>` for each new generation run
   (both spaces; `api: routerai` as configured).
4. `afterlife analyze degeneracy --run <gen>` on S4.1, S4.2, **and**
   the reused S2.2 raw subset (labels already exist; re-join, do not
   invent a new threshold).
5. `afterlife analyze geometry --run <embed>` and
   `analyze separation --run <embed>`, both spaces. `α` is reported
   only for trajectories with `degenerate = false`. Pairing for
   separation is **within the same (W, T)** — do not pool temperatures
   into `D_within` (S3.0 follow-up).
6. Figures: looping rate vs T faceted by W; fill and stop by quarter
   vs T; MSD `α` vs T with CI, degenerate rows labelled or dropped
   per the rule above. UMAP if drawn is an illustration.

## 5. Exit criteria

Falsifiable, quantitative, fixed before any Stage 4 number exists.

| # | Criterion | Threshold |
| --- | --- | --- |
| F1 | **New trajectories exist** | 24/24 planned new trajectories COMPLETED, or each missing one is named with cause |
| F2 | **Reuse cited** | the eight S2.2 raw cells are named by `run_id` and trajectory_id in the report; they are not silently regenerated |
| F3 | **Degeneracy first** | every geometry figure that states an `α` joins a per-trajectory degeneracy verdict |
| F4 | **`α` per cell or undefined** | each of the 8 (W, T) cells reports MSD `α` with a trajectory-bootstrap CI on the clean subset, **or** `α` is marked undefined because `n_clean < 2` |
| F5 | **Looping rate per cell** | degenerate fraction per (W, T) with a trajectory-bootstrap 95% CI (n = 4 per cell) |
| F6 | **H5 scored on this grid** | either a temperature band is named where clean-`α` CI at the high-T end excludes the low-T end in **both** spaces at **one** W, or the report says the transition is absent on this grid |
| F7 | **Both spaces** | F4–F6 are stated per embedding; a one-space result is not a result |
| F8 | **Protocol integrity** | reasoning tokens within the existing guard on every completed step; served provider = pin; round-trip failures counted, not assumed zero |
| F9 | **No `n_macro` headline** | the report does not use MSM macrostate count as an order parameter |
| F10 | **Spend** | Stage 4 hosted spend ≤ the sum of the two YAML `budget_usd` ($14). Stop and ask before any third config |

A cell that is 4/4 degenerate can still pass F4 (undefined) and F5
(rate = 1). That is a result.

## 6. Pre-registered predictions

| # | Prediction | Confidence | Observed |
| --- | --- | --- | --- |
| Q1 | T=1.5 at `W = 4096` is **not** a diffusion regime: clean-`α` is undefined or its CI includes the T=0.3 value. S2 T=1.0 was already 8/8 fixed points | 0.70 | Right as not-diffusion; T=0.3 arm undefined. REPORT §3 |
| Q2 | Degenerate fraction at T=0.3 is ≥ the fraction at T=1.5, at each W (higher T less locked). Stage 1's T=1.6 escaped the *textual* fixed point on a different matrix; we may be wrong here | 0.55 | Right. 1.0 ≥ 0.0 and 1.0 ≥ 0.5 |
| Q3 | `W = 8192` vs `W = 4096` at matched T: looping rate CIs overlap. A W-effect on lock rate is not predicted | 0.60 | Right. T=1.5 [0,0] overlaps [0,1] |
| Q4 | Block fill at `W = 8192` stays within 0.10 of the S2.2 `W = 4096` quarter-4 mean for the same T. Qwen's viability sweep was stable across W; this is the transfer we have been wrong about before | 0.50 | Wrong at T=1.0 (Δ=0.311). T=0.3 holds (Δ=0.077) |
| Q5 | H5 is **absent** on this grid (F6's "absent" branch). The interesting wrong is a clean-`α` split in both spaces | 0.65 | Right. Absent |
| Q6 | At least one (W, T=1.5) cell has `n_clean < 2`, so `α` is undefined there | 0.50 | Wrong. n_clean = 4 and 2 |
| Q7 | Seed-separation last-band CI at `W = 8192`, T=0.3, same-T pairing, excludes 0 in both spaces (Stage 1/2 qwen gap survived 12 turnovers at 4096; this asks the new W) | 0.55 | Right. Both spaces exclude 0 |
| Q8 | Cross-space agreement: the F6 verdict (transition present vs absent) is the same in bge-m3 and qwen3-embed-8b | 0.70 | Right. Absent in both |

Q5 is the one that matters. A pretty MSD slope on four looping
trajectories is the Stage 1 trap; F3/F4 exist to stop that.

## 7. Budget and wall clock

`afterlife estimate` on 2026-09-03 is the number that the CLI prints.
`or-qwen3-8b` has no `expected_block_fill`, so that print is **fill = 1**,
step-summed while the window fills (not the `T·W/S` approximation).
S2.2 raw fill was 0.70 → 0.67
([`artifacts/stage-2/mechanism/protocol/`](../../../artifacts/stage-2/mechanism/protocol/protocol_by_quarter.md));
fill < 1 raises input. The sensitivity row uses fill = 0.65, the
S2.2-quarter mean. If the table and
[`estimate-20260903.log`](estimate-20260903.log) disagree, the log wins.

Prices: OpenRouter catalogue `$0.117 / $0.455` per M.

| item | fill=1 (CLI) | fill=0.65 (S2.2) | YAML ceiling |
| --- | ---: | ---: | ---: |
| S4.0 reuse | $0 | $0 | — |
| S4.1 (8 traj) | $0.35 | $0.45 | $4 |
| S4.2 (16 traj) | $2.12 | $2.88 | $10 |
| **new hosted** | **$2.47** | **$3.33** | **$14 stop-and-ask** |
| embed + geometry + same-(W, T) separation | ~$1 | ~$1 | run-level |

Project remaining $188.43 of $200 (ADR-0013). OpenRouter key monthly
remainder ~$47 is the tighter cap. Wall clock: S2 qwen was tens of
minutes per `W=4096` trajectory at concurrency 2; S4.2 is ~2× the
tokens per traj. Stop and ask if wall clock exceeds 24 h or a run is
throttled to empty completions.

Generate authorised 2026-09-04 against this estimate. Do not add a
third config without a new yes.

## 8. Stage-specific risks

| Risk | Mitigation |
| --- | --- |
| Reading a loop as subdiffusive confinement | F3/F4; `α` undefined if `n_clean < 2` |
| Pooling T into seed-separation `D_within` | same-(W, T) pairing only (S3.0 lesson) |
| Fill collapse at `W = 8192` (the transfer we have gotten wrong) | Q4 is a prediction; summarise_run before embed; F8 |
| Treating one model as a class | every sentence names `or-qwen3-8b` under P1 |
| Regenerating S2.2 "for cleanliness" | F2; those cells are the W=4096 T=0.3/1.0 row |
| Key monthly cap mid-run | estimate first; S4.1 before S4.2; resume, do not restart |
| Quietly adding gemma/glimmer when qwen looks dull | ADR-0014; park in backlog |

## 9. Definition of done

- [x] Estimate approved 2026-09-04; then 24 new trajectories or named losses
- [x] S2.2 raw eight cited, not regenerated
- [x] Degeneracy, geometry, separation, both spaces; `α` rule held
- [x] `artifacts/stage-4/` populated
- [x] `REPORT.md` scores F1–F10 and Q1–Q8
- [x] `afterlife review --stage s4` exits 0
- [x] Master plan consistent with ADR-0014 / ADR-0015
- [x] Spend ≤ $14 hosted ($3.44 actual)
- [x] `REVIEW.md` APPROVED 2026-09-05; merged `--no-ff` as `5c07751`
