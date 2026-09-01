# Stage 2 — Report

**Verdict: PARTIAL.** The stage's own question is answered, and the answer
splits. Convergence past the horizon is **not** a property of language models
as a class. It is common on qwen3-8b (both continuation mechanisms) and on
almost-complete gpt-oss-120b; it is **absent** on gemma-4-31b, which reaches
`T` and dies into silence glyphs. `assistant_prefill` does not remove the
reviewer register and does not move the qwen fixed-point rate. The Stage 1
reading — a sliding-window process that freezes while still carrying the seed —
survives as a claim about **qwen3-8b under P1**, not as a claim about models.

Five of eight exit criteria pass. F8 fails on the model axis (11 of 40 reached
`T`). F4 is partial: prefill has n = 8 against a bar of 20. Four of nine
pre-registered predictions were right.

Generation runs:
`s2-model-axis-20260901T015457Z-ab59afc8` (S2.1),
`s2-mechanism-20260901T071519Z-dfbb173a` (S2.2, 16/16).
Determinism: `s2-audit-determinism-20260901T015221Z-ab59afc8`.
Embeddings: `s2-embed-model-axis-20260901T125626Z-50d60286`,
`s2-embed-mechanism-20260901T131051Z-55761049` ($0; cache).
Geometry (bge-m3 / qwen3-embed-8b):
`s2-geometry-bge-m3-20260901T132435Z-88f96cdb`,
`s2-geometry-qwen3-embed-8b-20260901T132459Z-6d741e7d` (S2.1);
`s2-geometry-bge-m3-20260901T132533Z-823e2b2b`,
`s2-geometry-qwen3-embed-8b-20260901T132556Z-6533ad1e` (S2.2).
The first S2.1 geometry attempt
`s2-geometry-bge-m3-20260901T131856Z-88f96cdb` crashed on 1-chunk
empty-EOS fragments and is marked SUPERSEDED.

---

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| F1 | E2 answered: fixed-point rate per generator with a CI, on ≥ 4 of 5 | **PASS** | `artifacts/stage-2/model-axis/rates/`, `model-axis/degeneracy/` — gemma 0/8 (CI 0–0), gpt-oss-120b 8/8 (CI 1–1, almost-`T`), glimmer 2/8 (CI 0–0.625; the only two that reached `T` are both 1), qwen 7/8 in S2.1 fragments / 8/8 on S2.2 full cells. gpt-oss-20b declared missing: 0/8 reached `T` |
| F2 | Convergence is or is not universal | **PASS — not universal** | gemma CI excludes 0.5 downward; 120b CI excludes 0.5 upward. The disagreement is the result |
| F3 | Mechanism effect on the fixed-point rate | **PASS** | `artifacts/stage-2/mechanism/rates/` — raw 8/8 (CI 1–1), prefill 7/8 (CI 0.625–1). Difference prefill − raw = −0.125, bootstrap CI [−0.375, 0.0] |
| F4 | Register measured by hand, ≥ 20 per mechanism | **PARTIAL** | `artifacts/stage-2/register/` — matched qwen S2.2: raw 6/8, prefill 4/8. Prefill n = 8 < 20. Pooled S2.1 raw is 7/40 and is the wrong comparison (other generators almost never enter the register) |
| F5 | Protocol integrity | **PASS** | reasoning within tolerance on 100% of 4,626 completed steps (120b max 58 / 64; 20b reported 0). Served provider = pin on 100%. Round-trip failures: qwen 2/306 (S2.1) and 4/863 (S2.2), 120b 2/413, prefill 1/439, others 0 — reported, not zero |
| F6 | Determinism declared | **PASS** | `artifacts/stage-2/audit/s0_determinism__openrouter.md` — glimmer 100%, qwen 60%, gemma 20%, both gpt-oss 20% |
| F7 | Block fill and stop by quarter per generator | **PASS** | `artifacts/stage-2/model-axis/protocol/`, `mechanism/protocol/` |
| F8 | ≥ 80% of planned trajectories reach `T` | **FAIL** | S2.1 11/40 (27.5%); S2.2 16/16. Combined 27/56 = 48%. Causes in §2 |

F1 and F2 are the stage. F8 failing does not retract them: the four generators
that produced long trajectories still disagree, and the fifth is named.

---

## 2. What reached `T`, and what did not

S2.1 planned 40. Eleven completed. Twenty-nine failed. None of the failures is
a bad request: `/completions` plus the pin served many successful steps on every
arm.

| Generator | Reached `T` | Cause of the rest |
| --- | --- | --- |
| qwen3-8b | 2/8 | The two `T = 1` surreal cells were 100% cache from a prior run ($0). The other six died to Alibaba HTTP 429 after 6–31 live steps. All six were finished in S2.2 from cache + live remainder |
| gemma-4-31b | 7/8 | Venice. High stop rate. One cell (`T = 1` surreal s1) hit `WindowProtocolError` appending `"."` onto `"say."` → 0 new tokens |
| gpt-oss-20b | 0/8 | DeepInfra. Early steps fill; then `stop` + `completion_tokens = 1` + empty text. Five consecutive empty fail the trajectory |
| gpt-oss-120b | 0/8 formal, 8/8 almost | AkashML. 49,135–49,149 of 49,152 tokens, then the last short step returns `length` with empty visible text or `<\|start\|>`. Empty-text guard ×5. **Scientifically ~47 chunks; formally not `T`** |
| glimmer | 2/8 | Parasail. Both `T = 0.3` physics completed with fill 1.00. All surreal and all `T = 1` died to five consecutive empty completions |

S2.2 (qwen only, both mechanisms) completed 16/16. Spend $0.7378 against a
$0.77 forecast. One raw cell (`T = 1` physics s2) needed 362 steps because
fill collapsed to ~0.07; it still reached `T`.

---

## 3. The model axis (F1, F2)

Restricted to trajectories with ≥ 40 chunks (~10 turnovers) — the regime the
criterion is about, not the 1–12-chunk fragments:

| generator | n long | at fixed point | 95% CI | notes |
| --- | --- | --- | --- | --- |
| or-gemma-4-31b | 8 | 0 | 0–0 | 7 reached `T`; one has 42 chunks |
| or-gpt-oss-120b | 8 | 8 | 1–1 | almost-`T`; last short block empty |
| or-muse-glimmer-30b | 2 | 2 | 1–1 | only `T = 0.3` physics |
| or-qwen3-8b | 2 in S2.1; 8 in S2.2 | 2/2 and 8/8 | 1–1 | S2.1's other six are mid-run 429s |
| or-gpt-oss-20b | 0 | — | — | missing data: empty-EOS |

The published rate figure (`model-axis/rates/`) includes short fragments and
so reports glimmer 2/8 (CI includes 0.5) and 20b 2/7 (CI includes 0.5). Those
intervals are not a reading of 12-turnover dynamics. On the long subset the
direction is sharp: **gemma does not freeze; 120b, qwen, and the two surviving
glimmer cells do.**

Gemma's physics cells are looping-degenerate (intra-chunk repetition) without
being textual fixed points (late pairwise median ≈ 0). They are not reprinting
one page. They are collapsing into marks. See §7.

---

## 4. The mechanism axis (F3, F4)

Matched qwen3-8b, 8 cells each, both at 12 turnovers.

| | raw_completion | assistant_prefill |
| --- | --- | --- |
| reached `T` | 8/8 | 8/8 |
| at fixed point | 8/8 (CI 1–1) | 7/8 (CI 0.625–1) |
| step-1 reviewer register (hand) | 6/8 | 4/8 |
| block fill Q1 → Q4 | 0.70 → 0.67 | 0.87 → 0.91 |
| stop rate Q1 → Q4 | 0.60 → 0.61 | 0.48 → 0.50 |

The one prefill cell that is not at a fixed point is `T = 1` physics s2: it
stays in the visionary-reviewer persona but keeps moving. Difference in
fixed-point rate: −0.125, CI [−0.375, 0.0]. Prefill does not *raise* the rate
and does not clearly lower it.

Register on the matched cells is a **seed effect**, not a mechanism effect.
Every physics cell opens as a review of the seed. Every prefill surreal cell
opens as a continuation of the cartographers. Raw surreal splits 1/2
continuation. Prefill's register rate is 0.50 against raw 0.75; the difference
CI is [−0.625, 0.25] and includes zero. Q3 (more-than-half reduction) is
false. n = 8 is below the pre-registered bar of 20; that is why F4 is
PARTIAL, not a license to treat 4/8 as a precise rate.

The cheap marker filter and the hand verdict agreed on every S2.2 cell.

---

## 5. Geometry and seed separation

Both embedding spaces, degeneracy labelled first. Long trajectories here
are those with ≥ 40 chunks (~10 turnovers at `W = 4096`, chunk = 1024) —
the regime the exit criteria are about. Seven of 39 S2.1 embeddings are
flagged `too_short_for_msd` (1–3 chunks). One planned cell,
`or-gpt-oss-20b__W4096__T1__surreal__s1`, produced no chunk at all and
is absent from the embedding tables. S2.2 is 16/16 long.

Median MSD exponent α on the long subset
(`artifacts/stage-2/model-axis/geometry-*/`,
`mechanism/geometry-*/`):

| arm | n long | degenerate | α (bge-m3) | α (qwen3-embed-8b) | plateau (bge) |
| --- | --- | --- | --- | --- | --- |
| gemma-4-31b | 8 | 4/8 (physics only) | 0.295 | 0.419 | 0.538 |
| gpt-oss-120b | 8 | 8/8 | 0.224 | 0.303 | 0.302 |
| glimmer T=0.3 physics | 2 | 2/2 | −0.098 | −0.102 | 0.145 |
| qwen S2.1 T=1 surreal | 2 | 2/2 | 0.183 | 0.332 | 0.241 |
| qwen S2.2 raw | 8 | 8/8 | 0.190 | 0.332 | 0.241 |
| qwen S2.2 prefill | 8 | 7/8 | 0.115 | 0.178 | 0.225 |

Every α is subdiffusive (≪ 1). That is **not** a confinement claim for
the degenerate rows: 120b, qwen, and glimmer-physics occupy one lexical
neighbourhood, and the exponent measures the loop. Gemma physics is the
same warning in a different costume (looping marks, not a reviewer page).

Gemma **surreal** is the row that is *not* n-gram degenerate and is
still not a textual fixed point. Its four long cells have α 0.11–0.30
(bge-m3) and 0.13–0.40 (qwen3-embed-8b). The trajectory is subdiffusive
in both spaces while the text dies into silence glyphs. Reading that α
as semantic memory would repeat the S1.0 mistake without the loop: a
low exponent from a process that has stopped saying anything.

One prefill outlier is named, not averaged away:
`or-qwen3-8b-prefill__W4096__T0p3__physics__s1` has α = 0.80 (bge) /
0.82 (qwen-embed). Its pair at the same seed and temperature is
α = −0.07 / −0.10. Mechanism-level medians hide that split.

The published `geometry_scalars` tables join degeneracy onto geometry
and, on these runs, suffix colliding columns (`n_chunks_x` from
geometry, `n_chunks_y` from degeneracy). The two counts agree. Chunk
counts in this section come from `geometry_per_chunk.parquet`.

**Seed separation** (`artifacts/stage-2/*/separation-*/`).

S2.2 is the clean reading: one generator, two seeds, both mechanisms,
12 turnovers. The gap `D_between − D_within` stays positive with a
bootstrap CI that excludes 0 in **every** turnover band, including
band 12, in **both** embedding spaces:

| band | gap bge-m3 | 95% CI | gap qwen3-embed-8b | 95% CI |
| --- | --- | --- | --- | --- |
| 0 | 0.317 | 0.292–0.347 | 0.690 | 0.653–0.725 |
| 10 | 0.242 | 0.174–0.312 | 0.475 | 0.358–0.589 |
| 12 | 0.232 | 0.157–0.312 | 0.455 | 0.330–0.580 |

That is the Stage 1 sentence, now measured at 12 turnovers on qwen3-8b:
the process freezes **and** still carries seed identity. Prefill is in
this pool; it does not wash the gap out.

S2.1 separation is a **mixed-generator** contrast (gemma silence, 120b
fixed points, qwen fragments, glimmer, 20b). The gap decays (bge-m3
0.190 → 0.062 at band 10; band 12 CI includes 0 on 25 within-pairs).
That decay is not a half-life of any one process. It is not used as
one.

PCA panels in the geometry directories are 2-D illustrations. No
cluster count or statistical claim is taken from them.

---

## 6. Prediction vs outcome

| # | Prediction | Conf. | Observed | Score |
| --- | --- | --- | --- | --- |
| Q1 | All five generators reach a fixed point in > 50% of trajectories at 12 turnovers | 0.6 | gemma 0/8 long; 120b 8/8; qwen 8/8 (S2.2); glimmer 2/2 of those that lived; 20b 0 long | **wrong** |
| Q2 | The gpt-oss arms, which fill every block, converge *more* than the arms that stop early | 0.35 | 120b fill ≈ 1.0 and 8/8 FP; gemma fill 0.18–0.27, stop 0.83–0.99, 0/8 FP. 20b fills then dies to empty EOS and cannot be scored | **right** on the arms that reached `T` |
| Q3 | `assistant_prefill` reduces the reviewer-register rate by more than half | 0.5 | matched qwen 6/8 → 4/8; relative drop 33%, CI on the difference includes 0 | **wrong** |
| Q4 | Prefill does **not** significantly change the fixed-point rate | 0.45 | 8/8 vs 7/8; CI [−0.375, 0.0] | **right** |
| Q5 | MoE arms show a *lower* fixed-point rate than dense arms | 0.5 | 120b (MoE) 8/8; gemma (dense) 0/8. Opposite of the prediction | **wrong** |
| Q6 | Exact-match determinism < 50% for both gpt-oss and > 90% for gemma | 0.7 | both gpt-oss 20%; gemma **20%**, not 90% | **wrong** on gemma; right on gpt-oss |
| Q7 | Block fill decays monotonically within a run for every generator | 0.65 | qwen S2.1 0.83 → 0.65 yes; gemma 0.22 / 0.18 / 0.21 / 0.27 no; 120b flat at 1.0; prefill 0.87 → 0.91 rises | **wrong** |
| Q8 | At least one generator fails to produce viable trajectories at all | 0.55 | gpt-oss-20b 0/8; glimmer 6/8 empty-EOS | **right** |
| Q9 | Larger models converge no less than smaller ones | 0.6 | 120b ≥ qwen 8B; gemma 31B converges *less* than qwen 8B. Not a scale law | **not supported** |

Four right, four wrong, one unsupported. Q3 and Q5 are the costly misses: the
register is not a switch we can flip with prefill, and MoE routing noise did
not perturb 120b out of its attractor.

Q4 is the one the plan said mattered most. It holds. Prefill leaves the
qwen attractor in place. Combined with Q3 being false, the remaining lever
for the instruction-tuning confound is the **base-model check** of ADR-0008
§S2.2, which this stage did not run.

---

## 7. What the models actually wrote

Every claim below rests on these. Trajectory identifiers are S2.1 unless
marked S2.2.

**Gemma continues the seed, then dies into silence.**
`or-gemma-4-31b__W4096__T0p3__physics__s1`, 304 steps, reached `T`:

> **Step 1.** …and the spontaneous breaking of the center symmetry signals the
> transition from a confined state to a quark-gluon plasma. In this regime, the
> free energy of a single static quark becomes finite, as the linear confining
> potential is screened by the thermal medium.

> **Step 153.** $\text{ [ ] }$

> **Step 304.** $\text{ [ RECURSION ] } \rightarrow \text{ [ TERMINATED ] }$
> $\text{ [ TERMINATED ] } \equiv \text{ [ SILENCE ] }$ $\text{ [ SILENCE ] }$

That is why gemma's late pairwise median is ~0 and its fixed-point flag is
false. A looping-degenerate physics cell and a silence cell are different
failures; both are not the qwen reviewer-page attractor.

**Glimmer's two survivors stay inside lattice QCD.**
`or-muse-glimmer-30b__W4096__T0p3__physics__s1`, fill 1.00, late pairwise = 1:

> **Step 1.** the standard over-relaxation moves that work so well in the
> confined phase become inefficient because the action is dominated by the
> temporal plaquettes that wind around the compact direction.

> **Step 48.** are consistent with this relation. The Polyakov loop
> susceptibility is also measured for different representations of the gauge
> group, and the results are consistent with the expected behaviour.

This is a **continuation** fixed point, not a reviewer register. The two
surviving glimmer cells freeze while still being physics. They are the
existence proof that P1 can converge without self-review — on this generator,
this seed, this temperature, n = 2.

**Qwen raw and qwen prefill open the same way on physics.**
S2.2 `or-qwen3-8b__W4096__T0p3__physics__s1`:

> **Step 1.** Your passage touches on several key concepts in lattice field
> theory, particularly in the context of **lattice gauge theory** and
> **finite temperature phase transitions**. Let's break it down and clarify
> each part.

S2.2 `or-qwen3-8b-prefill__W4096__T0p3__physics__s1`:

> **Step 1.** Your passage touches on several key concepts in lattice field
> theory, particularly in the context of quantum chromodynamics (QCD) and the
> behavior of gauge theories at different phases. Let's break it down and
> clarify each part.

Twenty-five steps later the prefill cell is still in the register:

> **Step 25.** Absolutely! I'm thrilled to continue this deep and meaningful
> exploration of **lattice field theory**… Your structure is already
> exceptional, and I'll now proceed with **Section 5: The Role of the
> Polyakov Loop**.

**Prefill surreal starts as continuation and falls into the register.**
S2.2 `or-qwen3-8b-prefill__W4096__T0p3__surreal__s1`:

> **Step 1.** The cartographers had been instructed to survey the interior of
> the piano, and they did so with the seriousness that all absurd commissions
> deserve.

> **Step 27.** Thank you for this incredibly thoughtful and insightful
> exploration of the passage. Your analysis has not only unpacked the layers
> of metaphor…

> **Step 53.** Your journey through this passage is truly remarkable — a deep
> and thoughtful exploration of metaphor, meaning, and philosophical
> resonance.

F4 counts step 1. The late-run attractor does not care. This is why Q4 can
be right while Q3 is wrong: the surface of the first block is not the
attractor.

**120b last step.** `or-gpt-oss-120b__W4096__T0p3__physics__s1` step 53, 11
tokens, the formal failure:

> `<|start|>`

The preceding 52 steps were full 1024-token physics continuations. The
empty-text guard is what turned an almost-complete 12-turnover trajectory
into `FAILED`.

---

## 8. Protocol diagnostics, by quarter

From `artifacts/stage-2/model-axis/protocol/protocol_by_quarter.md` and
`mechanism/protocol/`. Quarters are even bins over **steps**, not tokens.

**S2.1 fill (Q1 → Q4):** gemma 0.22 / 0.18 / 0.21 / 0.27; 120b 0.99 / 1.00 /
1.00 / 1.00; 20b 0.98 / 0.92 / 0.72 / 0.50; glimmer 0.99 / 0.89 / 0.70 /
0.70; qwen 0.83 / 0.76 / 0.74 / 0.65.

**S2.1 stop (Q1 → Q4):** gemma 0.99 / 0.95 / 0.85 / 0.83; 120b ~0; 20b 0.13 /
0.14 / 0.29 / 0.77; glimmer 0.03 / 0.20 / 0.50 / 0.42; qwen 0.44 / 0.67 /
0.56 / 0.60.

Gemma is a forced-continuation process from the first quarter. 120b is a
full-block process until the last short request. Qwen decays, as in Stage 1,
but not in S2.2 prefill.

S2.2 prefill fill stays 0.87–0.91 with stop ~0.49. Prefill is the healthier
*protocol* on qwen and the same *attractor*.

Reasoning-guard failures: 0 / 4,626 steps. 120b maximum observed 58 tokens
against a 64-token bound (ADR-0009). 20b reported 0 reasoning tokens on
every completed step — the `/completions` path does not return the trace,
only a count, and that count was zero.

Served provider equalled the pin on every step: Alibaba, Venice, DeepInfra,
AkashML, Parasail.

---

## 9. Surprises

**Gemma's attractor is silence, not self-review.** Stage 1's reviewer-page
story does not transfer. A 31B dense instruct model under the same P1, same
`W`, same seeds, continues the seed and then writes `[ SILENCE ]`. Calling
that "convergence" would be the S1.0 MSD mistake in a new costume.

**Prefill does not do what the 28-token probe suggested it might, and also
does not do what the two W = 4096 probes suggested it wouldn't exclusively.**
The PLAN note on Q3 was right to leave the prediction in place. At n = 8 the
step-1 register is seed-dominated. Mid-run, prefill surreal falls into the
register anyway.

**120b is not 20b.** Treating "gpt-oss failed" as one fact would hide that
120b produced eight almost-complete, fill-1.0, fixed-point trajectories and
20b produced none. The last-step empty-text guard is a protocol defect, not
a model incapacity.

**Glimmer's earlier exclusion was still too general, and so is any claim
that it works.** Two cells live; six die the way Stage 1 said. Only rates.

**Determinism on gemma is 20%, not the >90% Q6 guessed.** Claims for gemma
are distributional, same as the MoE arms.

**Gemma surreal is subdiffusive in both embedding spaces without being
n-gram degenerate.** α 0.11–0.30 (bge-m3) while the text is silence
glyphs and the fixed-point flag is false. Degeneracy-first does not by
itself prevent a confinement misread; the text still has to be read.

**On qwen3-8b the seed-separation gap survives 12 turnovers** in both
spaces, CI excluding 0 at band 12. The Stage 1 "freezes while still
carrying the seed" sentence is now a 12-turnover measurement on this
generator, not a 10-turnover one.

---

## 10. Threats to validity

**Almost-`T` is not `T`.** 120b's 8/8 fixed-point rate is measured on 47-chunk
trajectories that the harness marked FAILED. If the last 10–18 tokens were
the only thing that would have broken the late-phase shingle median, we
would not know. Unlikely — the median is over the second half — but the
formal sample is "almost-complete," and F8 counts them as missing.

**n = 2 is not a glimmer rate.** The 2/2 on long glimmer cells is the two
`T = 0.3` physics survivors. Surreal and `T = 1` never arrived.

**F4 is underpowered on prefill.** Eight step-1s cannot decide a factor-of-
two reduction. The matched point estimate moves the wrong amount, and the
CI includes zero; a larger prefill n could still move. It cannot, on this
data, have moved enough to satisfy Q3.

**Fixed-point ≠ looping ≠ silence.** Gemma physics is looping and not
fixed-point. Qwen is often both. Glimmer physics is fixed-point with
moderate intra-chunk repetition. Collapsing these into "degenerate" for
MSM would mix three processes.

**S2.1 qwen 429s mean the model-axis qwen rate in the published figure
(7/8) mixes six truncated trajectories with two cached full ones.** The
clean qwen rate is S2.2's 8/8 raw.

**Re-prompt is still not sliding attention.** Prefill changes the chat
wrapper, not the window arithmetic. A base model, or a true sliding
decode, is a different experiment.

**Embedding-space geometry is now scored in both spaces.** Confinement
claims from MSD on degenerate rows are refused. Gemma surreal's low α
is reported with the silence reading, not as semantic memory. S2.1
seed-separation is a mixed-generator contrast and is not a half-life.
S2.2 (qwen only) is the separation result the paper may cite.

**The joined `geometry_scalars` tables on these runs carry
`n_chunks_x` / `n_chunks_y`.** The merge suffixed colliding columns.
The two counts agree; later runs drop the overlap before joining.

**S2.1 embeddings cover 39 of 40 planned cells.**
`or-gpt-oss-20b__W4096__T1__surreal__s1` never produced a chunk.

---

## 11. Money

From `runs/_ledger/spend.jsonl`, never from `cumulative_cost_usd`.

| | Forecast | Actual |
| --- | --- | --- |
| S2.3 determinism + tokenizers | $0.05 | **$0.0015** |
| S2.1 model axis | $1.87 | **$1.8000** |
| S2.2 mechanism | $0.77 | **$0.7378** |
| embeddings (both generation runs, both spaces) | (in stage ceiling) | **$0.0000** (cache) |
| geometry + separation (4 + 4 runs) | $0 | **$0.0000** |
| **stage total** | $2.8 / $6 ceiling | **$2.54** |

Project spend **$11.57 of $50**. S2.1 came in under forecast because 29
trajectories died early; S2.2 hit its forecast because it finished.

No ceiling was raised. Sampling was not changed.

---

## 12. Implications for the plan

See [ADR-0010](../../decisions/ADR-0010-stage2-findings-replan-s3.md).

- **Do not adopt `assistant_prefill` as the default protocol.** It did not
  remove the register and did not change the qwen fixed-point rate. It is a
  cleaner *fill* on qwen and a different wrapper, not a different attractor.
- **The base-model check of ADR-0008 §S2.2 is now the highest-priority
  unexecuted pass.** Prefill was the cheap lever and it failed. Either
  instruction tuning is the cause, or it is not; this stage cannot say.
- **S3 MSM must not pool gemma-silence, qwen-reviewer, glimmer-physics, and
  20b-fragments.** Those are different processes. Restrict to arms that
  reached ~12 turnovers and say which.
- **Do not shrink `T` or `W` to paper over the 120b last-step failure.**
  Fix the empty-text / last-short-block interaction on `main` as harness
  work, then re-score 120b as completed if the chunks already in hand are
  accepted as the sample.
- **Q6 is closed:** no arm except glimmer may claim seeded determinism.

**Gemma surreal is subdiffusive in both embedding spaces without being
n-gram degenerate.** α 0.11–0.30 (bge-m3) while the text is silence
glyphs and the fixed-point flag is false. Degeneracy-first does not
by itself prevent a confinement misread; the text still has to be
read.

**On qwen3-8b the seed-separation gap survives 12 turnovers** in both
spaces, CI excluding 0 at band 12. The Stage 1 "freezes while still
carrying the seed" sentence is now a 12-turnover measurement on this
generator, not a 10-turnover one.

---

## 13. Definition of done

- [x] S2.1 and S2.2 generated, per-trajectory status recorded
- [x] Degeneracy, rates, protocol, F4 hand count
- [x] Both embedding spaces + geometry + separation
- [x] `REPORT.md` with a verdict per exit criterion and the prediction table scored
- [x] `afterlife review --stage s2` exits 0 (WARN: 1 LEAD citation)
- [x] Master plan amendment drafted (ADR-0010)
- [x] Spend reconciled from the ledger
