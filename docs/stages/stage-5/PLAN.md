# Stage 5 — Do different seeds occupy different locks?

**Status.** Opened 2026-09-05 on branch `cursor/stage-5-6dce`, after
Stage 4 closed APPROVED (`5c07751`). Decision:
[ADR-0015](../../decisions/ADR-0015-s5-operating-point-after-s4.md),
[ADR-0016](../../decisions/ADR-0016-s5-lock-occupancy-on-seed-bank-v1.md).
Generate is **not** authorised.

## 1. Question

On `or-qwen3-8b` under P1 `raw_completion`, at the lock Stage 4
characterised (`W = 4096`, T=0.3, 12 turnovers), do the ten domain
seeds of `seed_bank_v1` occupy distinguishable late-window locks, and
does a one-fact twin pair stay apart relative to the same-seed
stochastic control?

This stage does **not** ask whether H1 holds. It does **not** treat
`n_macro` as an order parameter. It does **not** call a lock a
semantic basin. It does **not** claim a result about language models
as a class. Degenerate trajectories are the sample.

## 2. Entry state

From [Stage 4](../stage-4/REPORT.md), [Stage 4 REVIEW](../stage-4/REVIEW.md),
[ADR-0015](../../decisions/ADR-0015-s5-operating-point-after-s4.md):

- T≤1.0 is 4/4 lock at both `W ∈ {4096, 8192}` on this process.
- T=1.5 is the only clean-`α` and is subdiffusive, still the
  assistant register. That is object (b); not this opening.
- Last-band seed gap at `W=8192` T=0.3 (physics vs surreal) excludes
  0 in both spaces. Occupancy of distinguishable locks is the
  hypothesis that measurement suggests.
- The two T=1.0 locks are not one mechanism (Q4 stop 0.954 vs 0.450).
  T=0.3 is the lock whose fill transferred (Δ=0.077).
- `seed_bank_v1` has 10 domains + 2 twin pairs. There are not 200
  seeds.
- Reusable cells:
  `s2-mechanism-20260901T071519Z-dfbb173a`,
  `or-qwen3-8b__W4096__T0p3__{physics,surreal}__s{1,2}` (4/4),
  embeddings `s2-embed-mechanism-20260901T131051Z-55761049`.
- Project ledger **$15.00 of $200**. OpenRouter key remainder is the
  tighter cap.

## 3. Experiment matrix

The **scientific** grid is 1 generator × 1 window × 1 temperature ×
14 semantic seeds × 2 stochastic replicates = **28 trajectories**,
12 turnovers each. Four are reused. New generation is one config; if
PLAN prose and YAML disagree, **YAML wins**.

| # | Pass | Config | What it adds | Trajectories | Tokens (fill=1) |
| --- | --- | --- | --- | ---: | --- |
| S5.0 | Reuse S2.2 raw T=0.3 | — | physics, surreal | 4 existing | 0 new |
| S5.1 | Remaining bank | `configs/stages/stage5_lock_occupancy.yaml` | 8 domains + 4 twins | 24 new | 4.473M in + 1.180M out |

`B = S = 1024`, `chunk_size = 1024`, protocol P1, `forcing = unforced`,
`reasoning_effort: none`, embeddings `bge-m3` and `qwen3-embed-8b`.
Stochastic: 1, 2.

New seeds: `finance`, `biology`, `war`, `love`, `recipe`,
`programming`, `philosophy`, `noise`, `waterloo-won`,
`waterloo-lost`, `reactor-stable`, `reactor-unstable`.

F4 (domain last-band gap) uses the **ten domain seeds only**.
F6 (twins) uses the **two twin pairs only**. Do not pool them into
one `D_between`.

Not in this opening: T=1.0 occupancy, T=1.5 residual, `W=8192`,
seed_bank_v2, a second generator, MSM / `n_macro`.

## 4. Computations

Ordered. Degeneracy before geometry. No generate until estimate
approval. Degenerate rows stay in occupancy and twin contrasts.

1. `afterlife generate --config configs/stages/stage5_lock_occupancy.yaml`.
   Artifacts under `runs/s5/`. Stop if live spend hits `budget_usd`.
2. `python scripts/summarise_run.py <run_id>`: fill, stop, round-trip,
   reasoning, served provider = `alibaba`.
3. `afterlife embed --run <new_run>` (both spaces).
4. `afterlife analyze degeneracy --run <gen>` on S5.1 **and** the
   reused S2.2 T=0.3 four. Threshold 0.083 / half of post-horizon
   chunks, plus late Jaccard 0.0122. Do not invent a new bar.
5. `afterlife analyze separation --run <embed>` on the **ten domain
   seeds only**, same-(W, T) pairing (already the default).
6. `afterlife analyze twins --run <embed>` on the twin pairs
   (`twin_of` in the seed bank). Last-band Δ vs control, both spaces.
7. Geometry is diagnostic, not the headline. `α` on this lock is
   expected undefined or a repetition exponent; report it labelled
   degenerate.
8. Figures: last-band 10×10 cosine-distance matrix (tidy source; any
   2-D view is an illustration); domain separation vs turnover; twin
   Δ vs turnover with CI; looping rate per seed. Quote late chunks
   from ≥3 domains and one twin member.

## 5. Exit criteria

Falsifiable, quantitative, fixed before any Stage 5 number exists.

| # | Criterion | Threshold |
| --- | --- | --- |
| F1 | **New trajectories exist** | 24/24 COMPLETED, or each missing one named with cause |
| F2 | **Reuse cited** | the four S2.2 T=0.3 cells named by `run_id` and trajectory_id; not regenerated |
| F3 | **Degeneracy first** | every occupancy / twin / geometry table joins a per-trajectory verdict. Degenerate rows are **kept** |
| F4 | **Domain last-band gap** | `D_between − D_within` at the last band on the ten domain seeds, trajectory-bootstrap 95% CI, **both** spaces — or marked undefined if a space lacks `D_within` |
| F5 | **Lock rate per seed** | degenerate fraction per domain seed (n=2) and overall (n=20 domain traj). No `[1, 1]` carried as if it were uncertainty when all four-of-four Bernoulli cells collapse; report k/n |
| F6 | **Twin last-band Δ** | for each twin family and for the pooled twins: Δ = `D_twin_matched − D_control` with CI, both spaces. Verdict `divergent` iff CI excludes 0 from above; else `collapsed` |
| F7 | **Both spaces** | F4–F6 stated per embedding |
| F8 | **Protocol integrity** | reasoning 0 on every completed step; served provider = pin; round-trip failures counted |
| F9 | **No basin / `n_macro` headline** | the report does not call a lock a semantic basin or use MSM macrostate count as an order parameter |
| F10 | **Spend** | Stage 5 hosted spend ≤ YAML `budget_usd` ($8). Stop and ask before a second config |

A 20/20 domain lock with a last-band gap that still excludes 0 is a
result: distinguishable locks, not a recovered semantic state.

## 6. Pre-registered predictions

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| Q1 | ≥8 of 10 domain seeds are degenerate on at least one stochastic replicate | 0.75 | |
| Q2 | Ten-domain last-band gap CI excludes 0 in **both** spaces (S4 Q7 on two seeds, now ten) | 0.60 | |
| Q3 | `noise` is degenerate too: low-structure text does not escape the lock | 0.55 | |
| Q4 | Each twin family's last-band Δ CI **includes 0** (twins collapse to the control). The interesting wrong is divergent | 0.55 | |
| Q5 | waterloo and reactor agree on Q4 (same last-band verdict in a given space) | 0.50 | |
| Q6 | F4 / F6 last-band verdicts agree across the two embedding spaces | 0.70 | |
| Q7 | T=0.3 Q4 block fill stays within 0.10 of S4's W=4096 T=0.3 Q4 mean 0.903 | 0.55 | |
| Q8 | Late-chunk quoted text is still the reviewer / assistant register on ≥5 of 10 domain seeds | 0.65 | |

Q2 and Q4 can both be right: domains stay apart, twins do not.
Q2 right and Q4 wrong would mean even a one-fact flip occupies a
distinguishable lock.

## 7. Budget and wall clock

`afterlife estimate` on 2026-09-05 is the number the CLI prints.
`or-qwen3-8b` has no `expected_block_fill`, so that print is
**fill = 1**. S4 T=0.3 Q4 fill was 0.903 at `W=4096`
([`artifacts/stage-4/grid/protocol_by_quarter_cell.csv`](../../../artifacts/stage-4/grid/protocol_by_quarter_cell.csv)).
If this table and
[`estimate-20260905.log`](estimate-20260905.log) disagree, the log
wins.

Prices: OpenRouter catalogue `$0.117 / $0.455` per M.

| item | fill=1 (CLI) | fill=0.90 (S4 T=0.3) | YAML ceiling |
| --- | ---: | ---: | ---: |
| S5.0 reuse | $0 | $0 | — |
| S5.1 (24 traj) | $1.06 | ~$1.17 | $8 |
| **new hosted** | **$1.06** | **~$1.17** | **$8 stop-and-ask** |
| embed + analysis | ~$0 | ~$0 | RouterAI cache in S4 |

Project remaining $185 of $200. The $120 master-plan sketch is not
this opening's refuse. Wall clock: S4.1's eight `W=4096` trajectories
were tens of minutes each at concurrency 2; 24 cells are ~3× that
if the endpoint holds. Stop and ask if wall clock exceeds 24 h or a
run is throttled to empty completions.

Do not generate until the human says yes to this estimate.

## 8. Stage-specific risks

| Risk | Mitigation |
| --- | --- |
| Reading occupancy as semantic basins | F9; degeneracy kept; quotes required |
| Dropping degenerate rows before the gap | F3; lock *is* the sample |
| Pooling twins into domain `D_between` | F4 vs F6 split |
| Carrying lock CI `[1, 1]` into the manuscript | F5: report k/n (S4 REVIEW) |
| Mixing T=1.0 or T=1.5 into the same occupancy map | one (W, T) |
| Inventing 200 seeds when the bank has 14 | ADR-0016 |
| Treating one process as a class | every sentence names `or-qwen3-8b` under P1 |

## 9. Definition of done

- [ ] Estimate approved; then 24 new trajectories or named losses
- [ ] S2.2 T=0.3 four cited, not regenerated
- [ ] Degeneracy, domain separation, twins, both spaces
- [ ] `artifacts/stage-5/` populated
- [ ] `REPORT.md` scores F1–F10 and Q1–Q8
- [ ] `afterlife review --stage s5` exits 0
- [ ] Master plan consistent with ADR-0015 / ADR-0016
- [ ] Spend ≤ $8 hosted
