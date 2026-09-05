# Stage 4 report — lock at T≤1.0 both W; H5 absent on this grid

**Status.** Computations finished 2026-09-05. Overall verdict: **PASS**.
Scientific review **APPROVED** 2026-09-05 ([`REVIEW.md`](REVIEW.md));
merge withheld.
On `or-qwen3-8b` under P1 `raw_completion`, temperature moves the
looping rate only at T=1.5. Every T≤1.0 cell is 4/4 degenerate at
`W = 4096` and at `W = 8192`. Clean-`α` is defined only at T=1.5 and
is subdiffusive in both spaces. H5 is **absent** on this grid: there
is no low-T clean-`α` to compare. This is a claim about one instruct
process, not about language models.

Branch: `cursor/stage-4-6dce`. Plan: [`PLAN.md`](PLAN.md).
Decision: [ADR-0014](../../decisions/ADR-0014-reduced-s4-temp-window.md).
S5 implication: [ADR-0015](../../decisions/ADR-0015-s5-operating-point-after-s4.md).

Generation:
`s4-w4096-new-temps-20260904T103121Z-589c8eb1` (S4.1, 8/8, $0.4379),
`s4-w8192-20260904T120057Z-ce82ce55` (S4.2, 16/16, $3.0004).
Reuse, not regenerated:
`s2-mechanism-20260901T071519Z-dfbb173a` (S2.2 raw eight).
Embeddings: `s4-embed-w4096-new-temps-20260904T120202Z-37e61e58`,
`s4-embed-w8192-20260905T090901Z-15172d14` ($0),
`s2-embed-mechanism-20260901T131051Z-55761049`.
Degeneracy: `s4-degeneracy-20260904T120745Z-92b6f79e` (S4.1),
`s4-degeneracy-20260905T091304Z-c599b6d9` (S4.2, 14/16).
S2.2 labels reused from `artifacts/stage-2/mechanism/degeneracy/`.
Grid: [`artifacts/stage-4/grid/`](../../../artifacts/stage-4/grid/).

---

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| F1 | 24/24 new trajectories COMPLETED | **PASS** | S4.1 8/8 `s4-w4096-new-temps-20260904T103121Z-589c8eb1`; S4.2 16/16 `s4-w8192-20260904T120057Z-ce82ce55`. None missing |
| F2 | S2.2 raw eight cited, not regenerated | **PASS** | `s2-mechanism-20260901T071519Z-dfbb173a`: `or-qwen3-8b__W4096__T0p3__{physics,surreal}__s{1,2}` and `or-qwen3-8b__W4096__T1__{physics,surreal}__s{1,2}`. Prefill rows were not used |
| F3 | Geometry `α` joined to degeneracy | **PASS** | `geometry_scalars` in `artifacts/stage-4/s41/geometry-*/` and `artifacts/stage-4/geometry-*/` carry `degenerate`. Grid `clean_alpha_by_cell` drops those rows |
| F4 | `α` per cell or undefined | **PASS** | [`clean_alpha_by_cell.csv`](../../../artifacts/stage-4/grid/clean_alpha_by_cell.csv). T≤1.0 both W: undefined (`n_clean = 0`). T=1.5 `W=4096`: n_clean=4, defined. T=1.5 `W=8192`: n_clean=2, defined |
| F5 | Looping rate per (W, T) with CI | **PASS** | [`looping_rate_by_cell.csv`](../../../artifacts/stage-4/grid/looping_rate_by_cell.csv). n=4. T≤1.0 both W: 4/4, CI [1, 1]. T=1.5 `W=4096`: 0/4, CI [0, 0]. T=1.5 `W=8192`: 2/4, CI [0, 1] |
| F6 | H5 present or absent on this grid | **PASS — absent** | No (W, space) pair has a low-T clean-`α` to compare: T=0.3 and T=0.7 are 4/4 degenerate. The F6 "absent" branch is the result |
| F7 | F4–F6 per embedding | **PASS** | Both spaces in `clean_alpha_by_cell` and `looping_rate_by_cell`. F6 absent in both |
| F8 | Protocol integrity | **PASS** | Reasoning tokens 0 on every completed step. Served provider = Alibaba on every step. Round-trip failures: S4.1 0; S4.2 **2** (T=1.0 surreal s2 step 117; T=1.5 physics s2 step 36). Counted, not assumed zero. [`s4_2_summarise.txt`](s4_2_summarise.txt) |
| F9 | No `n_macro` headline | **PASS** | This report does not use MSM macrostate count as an order parameter |
| F10 | Hosted spend ≤ $14 | **PASS** | S4 hosted **$3.4383** (S4.1 $0.4379 + S4.2 $3.0004; embed and analysis $0). YAML refuse $14. No third config |

A 4/4 degenerate cell is a result, not missing data. F4's undefined
cells and F5's rate=1 are the same fact.

---

## 2. Results

Order parameters live in [`artifacts/stage-4/grid/`](../../../artifacts/stage-4/grid/).
S4.1-only CLI figures are snapshotted under [`artifacts/stage-4/s41/`](../../../artifacts/stage-4/s41/).
S4.2 CLI geometry/separation overwrite the unprefixed `geometry-*` /
`separation-*` directories and describe the sixteen `W=8192`
trajectories only.

### Looping rate

[`looping_rate_vs_T`](../../../artifacts/stage-4/grid/looping_rate_vs_T.meta.json)
— degenerate fraction vs T, faceted by W, n=4, trajectory-bootstrap 95% CI.

| W | T=0.3 | T=0.7 | T=1.0 | T=1.5 |
| ---: | ---: | ---: | ---: | ---: |
| 4096 | 4/4 [1, 1] | 4/4 [1, 1] | 4/4 [1, 1] | 0/4 [0, 0] |
| 8192 | 4/4 [1, 1] | 4/4 [1, 1] | 4/4 [1, 1] | 2/4 [0, 1] |

`W = 8192` does not unlock T≤1.0. T=1.5 is the only temperature that
is not a lock, and at the new window it is only a coin flip (CI
covers the whole [0, 1] interval).

S4.1 T=0.7 physics s1 is `degenerate=True` at `looping_fraction`
0.0465 — below the 0.083 per-chunk n-gram bar — because late-phase
shingle Jaccard hits the calibrated fixed-point arm (mode 2). The
threshold was not moved. The other three T=0.7 cells at `W=4096` are
mode 3 (loop + fixed point).

S4.2 T=1.5: physics s1 and surreal s2 are clean; physics s2 and
surreal s1 are mode 2.

### Clean MSD `α`

[`clean_alpha_vs_T`](../../../artifacts/stage-4/grid/clean_alpha_vs_T.meta.json).
T≤1.0: undefined in both spaces (`n_clean = 0`). Those exponents, if
fitted, measure repetition.

| embedding | W | T=1.5 n_clean | `α` | 95% CI |
| --- | ---: | ---: | ---: | ---: |
| bge-m3 | 4096 | 4 | 0.149 | [0.140, 0.158] |
| bge-m3 | 8192 | 2 | 0.146 | [0.086, 0.207] |
| qwen3-embed-8b | 4096 | 4 | 0.277 | [0.241, 0.318] |
| qwen3-embed-8b | 8192 | 2 | 0.247 | [0.172, 0.322] |

Both spaces, both windows: CIs exclude free diffusion (`α = 1`).
The two spaces disagree on the level (≈0.15 vs ≈0.26) and agree on
the sign (subdiffusive). A one-space result is not a result; here
they agree on F6.

H5 needs a high-T clean-`α` CI that excludes the low-T clean-`α` in
both spaces at one W. Low-T clean-`α` does not exist. Absent.

### Seed separation, same-(W, T) only

[`separation_last_band_by_cell.csv`](../../../artifacts/stage-4/grid/separation_last_band_by_cell.csv).
Pairs are formed only inside a matched (W, T) cell. CLI
`separation_per_band` figures that pool bands across T inside one
embed run are not the Q7 object.

Last-band gap CI excludes 0 in **all eight cells × two spaces**,
including the new `W=8192` T=0.3 cell:

- bge-m3: gap 0.256, CI [0.249, 0.262]
- qwen3-embed-8b: gap 0.694, CI [0.693, 0.695]

The seed still shapes the locked trajectory after twelve turnovers
at the larger window. That is not recovery and not a semantic state.

### Block fill and stop by quarter

[`protocol_by_quarter_vs_T`](../../../artifacts/stage-4/grid/protocol_by_quarter_vs_T.meta.json).
Quarters are even step bins. n=4 per cell. A run-level mean is not
reported.

Quarter-4 block fill:

| W | T=0.3 | T=0.7 | T=1.0 | T=1.5 |
| ---: | ---: | ---: | ---: | ---: |
| 4096 | 0.903 [0.75, 1.00] | 0.747 [0.54, 0.95] | 0.434 [0.24, 0.65] | 0.679 [0.54, 0.89] |
| 8192 | 0.980 [0.95, 1.00] | 0.861 [0.74, 0.96] | 0.745 [0.39, 0.98] | 0.607 [0.40, 0.88] |

T=0.3 transfers across W (Δ fill = 0.077). T=1.0 does not
(Δ = 0.311). The T=1.0 cell mean is one collapsed replicate plus
three healthier ones: at `W=4096`, physics s2 Q4 fill is 0.175; at
`W=8192`, physics s2 Q4 fill is 0.201 (605 steps to reach `T`,
run-mean fill 0.159, $0.62 of the $3.00). Stop rate at `W=4096`
T=1.0 Q4 is 0.954 [0.93, 0.97].

### Generated text

Reading the output still beats the metrics. Three late-chunk samples
(`t/W ≈ 12`).

`or-qwen3-8b__W8192__T0p3__physics__s1`, chunk 94 — lock, reviewer register:

> How Would You Like to Proceed? Let me know your preference, and I'll prepare the final output accordingly. … Would you like to proceed with **Option 1 (PDF generation)**, **Option 2 (Slide deck)**, or **Option 3 (Blog post)**? Just let me know, and I’ll get started right away!

`or-qwen3-8b__W4096__T0p7__physics__s1`, chunk 46 — mode-2 fixed point at looping_fraction 0.0465:

> You're absolutely right — the content you've shared has indeed been **duplicated and corrupted**, likely due to a **copy-paste error** or formatting issue during the transfer. This has led to multiple repetitions of the same LaTeX content … Here is the **single, clean, and fully compilable version** of your LaTeX document.

`or-qwen3-8b__W8192__T1p5__physics__s1`, chunk 94 — `degenerate=false`, still the assistant selling a toolkit:

> Your groundbreaking **Polyakov Loop Heatmap Visualization Toolkit** is now *fully ready-to-deploy* — and your moment of impact has arrived. I’m sending the final ZIP file to you.

Clean is not "left the register." Degeneracy is a surface-form
verdict. T=1.5 can pass it and still be a help-assistant looping a
product pitch about the seed's topic.

---

## 3. Prediction vs. outcome

| # | Prediction | Confidence | Observed |
| --- | --- | --- | --- |
| Q1 | T=1.5 at `W=4096` is not diffusion: clean-`α` undefined or its CI includes the T=0.3 value | 0.70 | **Right as not-diffusion.** Clean-`α` is defined (bge-m3 0.149 [0.140, 0.158]; qwen3-embed-8b 0.277 [0.241, 0.318]); both CIs exclude 1. The T=0.3 comparison arm is unavailable (`n_clean = 0`) |
| Q2 | Degenerate fraction at T=0.3 ≥ T=1.5 at each W | 0.55 | **Right.** 1.0 ≥ 0.0 at `W=4096`; 1.0 ≥ 0.5 at `W=8192` |
| Q3 | `W=8192` vs `W=4096` looping CIs overlap at matched T | 0.60 | **Right.** T≤1.0 both [1, 1]. T=1.5: [0, 0] overlaps [0, 1] |
| Q4 | `W=8192` Q4 fill within 0.10 of S2.2 `W=4096` Q4 fill at the same T | 0.50 | **Wrong** at T=1.0 (0.745 vs 0.434, Δ=0.311). T=0.3 holds (0.980 vs 0.903, Δ=0.077). The transfer we have been wrong about before failed again, at the temperature that already collapses fill |
| Q5 | H5 absent on this grid | 0.65 | **Right.** F6 absent branch. No low-T clean-`α` |
| Q6 | At least one (W, T=1.5) cell has `n_clean < 2` | 0.50 | **Wrong.** `W=4096` n_clean=4; `W=8192` n_clean=2. Both defined |
| Q7 | `W=8192` T=0.3 last-band CI excludes 0 in both spaces | 0.55 | **Right.** See §2 |
| Q8 | F6 verdict agrees across spaces | 0.70 | **Right.** Absent in both |

Q5 was the load-bearing one. It held. Q4 and Q6 being wrong is the
useful part: fill does not transfer at T=1.0, and T=1.5 produced
enough clean trajectories to *state* an `α` that is still not
diffusion.

---

## 4. Surprises

1. **`W = 8192` is the same lock.** The new window was the expensive
   arm. T≤1.0 did not move.
2. **T=1.5 can be clean and still be a salesperson.** Degeneracy
   missed the register. The quote in §2 is the evidence.
3. **Mode-2 fixed points below the n-gram bar.** S4.1 T=0.7 physics
   s1 and two of four S4.2 T=1.5 cells. The calibrated OR of
   (looping fraction ≥ 0.5) and (late Jaccard ≥ 0.0122) is doing
   the work the n-gram rate alone would miss. Threshold not changed.
4. **Fill collapse is a trajectory, not a temperature.** T=1.0
   physics s2 collapses at both W (Q4 fill 0.175 and 0.201). The
   other three T=1.0 replicates at `W=8192` Q4 fill 0.82–1.00.
   Cell means hide that.
5. **Two isolated tokenizer round-trip fails** on otherwise healthy
   length-1024 blocks. Neighbours were fine. Not a window-void for
   the run; counted under F8.
6. **S4.2 wall clock.** Generate needed repeated PID-kill +
   `--resume-run` after TCP stalls (`ep_poll`, ~15 min useful work
   then ~45 min silence). The scientific record is one `run_id`.
   The operational record is twenty-odd resume sessions.

---

## 5. Threats to validity

- **One process.** Every number is `or-qwen3-8b` under P1
  `raw_completion`, Alibaba, `reasoning_effort: none`. Stage 2
  already showed gemma-4-31b and gpt-oss-120b disagree with qwen.
- **n=4.** T=1.5 `W=8192` looping CI is [0, 1]. It does not decide
  a direction. The 4/4 lock at T≤1.0 does.
- **Clean-`α` at `W=8192` T=1.5 is n=2.** The CI is a two-point
  bootstrap. It is enough to exclude `α = 1` in both spaces; it is
  not enough to compare the two windows' exponents.
- **H5 is absent because the comparison is undefined**, not because
  we measured two clean-`α`s and they overlapped. A later grid that
  produces a clean low-T cell could still show a transition.
- **Degeneracy is surface form.** T=1.5 clean text is still the
  reviewer/assistant register. A confinement claim on those
  trajectories would need a different instrument.
- **Re-prompt vs true sliding attention.** Protocol P1. Unchanged.
- **Same-(W, T) pairing.** Held in the grid table. Do not read the
  S4.2 CLI `separation_per_band` (one embed run, all four T) as Q7.
- **Two round-trip fails.** The check is
  `len(encode(decode(last_W))) == W` on one cut. The run is not
  void; those two steps' windows are the ones in doubt.
- **Provider non-determinism.** OpenRouter/Alibaba. Seed was passed;
  LLM determinism is not assumed. Replay would have to come from
  the response cache.
- **Dirty tree on the embed run.**
  `s4-embed-w8192-20260905T090901Z-15172d14` recorded `git_dirty`.
  The diff is in that manifest. Numbers depend on chunks + embedder,
  not on the dirty files (`uv.lock` churn, in-progress artifacts).
- **S4.1 T=0.7 last separation band is 10, not 12** in some rows
  (chunk-length / pairing truncation). The gap CI still excludes 0.

---

## 6. Cost actuals

| item | estimate (fill=1 / fill=0.65) | actual | run_id |
| --- | ---: | ---: | --- |
| S4.0 reuse | $0 / $0 | $0 | `s2-mechanism-20260901T071519Z-dfbb173a` |
| S4.1 generate | $0.35 / $0.45 | **$0.4379** | `s4-w4096-new-temps-20260904T103121Z-589c8eb1` |
| S4.2 generate | $2.12 / $2.88 | **$3.0004** | `s4-w8192-20260904T120057Z-ce82ce55` |
| embed + analysis | ~$1 | **$0.00** | RouterAI cache; geometry local |
| **new hosted** | **$2.47 / $3.33** | **$3.4383** | — |

+$0.11 over the authorised S2.2-calibrated generate estimate
($3.33), because fill collapse at T=1.0 raised input. Under the $7
per-run ceiling and the $14 YAML stop-and-ask. Project ledger
**$15.00 of $200** (ADR-0013) after this stage. No third config. No
ceiling raise.

---

## 7. Implications for the plan

1. **H5 is absent on this grid.** Do not carry a "temperature unlocks
   diffusion on qwen" sentence into S5. ADR-0015.
2. **T=1.0 is characterised: it is a lock at both W.** S5 must not
   open 200 seeds there and call the occupancy a semantic basin.
3. **The only clean-`α` band is T=1.5**, and it is still the
   reviewer register. If S5 wants non-degenerate geometry, that is
   the residual object, and it needs its own question.
4. **`W = 8192` is not a lever on lock rate** at T≤1.0. 16k / 32k
   stay parked (ADR-0014). A W-effect on *fill* at T=1.0 is real
   (Q4 wrong) and is not a semantic result.
5. **`n_macro` stays off the headline.**
6. **Do not switch the generator to Gemma** because qwen loops.
   Stage 2 already measured gemma-4-31b: silence, not health.

S5 PLAN, when opened, picks object (a) lock occupancy or (b) T=1.5
residual, estimates, and waits for a generate-yes. This stage does
not open it.
