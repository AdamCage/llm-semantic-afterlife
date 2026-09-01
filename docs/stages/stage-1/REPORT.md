# Stage 1 — Report

**Verdict: PARTIAL.** The stage's own question is answered affirmatively and
robustly, and the answer means much less than it appears to.

Seed identity is measurably present past the context horizon, out to 32
turnovers, in both representation spaces, with every turnover band's bootstrap
interval excluding zero. But 94% of the trajectories reached a textual fixed
point. A process that has stopped moving cannot forget: for most of this
ensemble, "the seed still shapes the trajectory" and "the trajectory froze while
still carrying seed-derived material" are the same statement, and this experiment
cannot separate them.

Four of nine exit criteria fail. Six of thirteen pre-registered predictions were
right.

---

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| E1 | Seed identity persists past the horizon | **PASS** | `artifacts/stage-1/separation-bge-m3/`, `separation-qwen3-embed-8b/` — 17 of 17 bands with CI excluding zero, both spaces |
| E2 | Not architecture-specific | **FAIL — not assessed** | the replication arm was never run; see §2 |
| E3 | Diffusion exponent estimable | **PASS** | `artifacts/stage-1/geometry-*/` — mean CI width 0.052 (bge-m3) and 0.065 (qwen), against a 0.2 bar; 98% and 100% of trajectories inside it |
| E4 | Degeneracy under control | superseded by E9 | wording replaced pre-execution with a calibrated threshold |
| E5 | Representation robustness | **PASS** | both spaces agree on sign in every band; effect sizes differ 85% |
| E6 | Protocol integrity | **FAIL** | 23 tokenizer round-trip failures across 13 trajectories, against a bar of zero. Reasoning tokens 0 and served provider 100% pinned both hold |
| E7 | Block fill does not collapse | **FAIL** | 0.748 over the run and 0.653 in the final quarter, against a probe value of 0.942 ([CORE-ARM.md](CORE-ARM.md)) |
| E8 | Completion rate ≥ 90% | **PASS** | 47 of 48 reached `T`; one lost to a `WindowProtocolError` |
| E9 | Non-degeneracy < 20% | **FAIL** | 45 of 48 (94%) at a textual fixed point: 24 of 24 at `T = 0.3`, 21 of 24 at `T = 1.0` |

E1 is the stage and it passes. E2 and E5 were to decide whether the result is
worth Stages 2–5; E5 passes and E2 could not be assessed at all, which is the
single largest hole in this stage.

## 2. E2 could not be assessed, and that is a finding

The replication arm — muse-glimmer-30b, 16 trajectories — was planned, budgeted
and never run. It was not dropped for convenience: the generator **cannot
free-run at `W = 4096`**. In the convergence probe three of its four cells died
after five consecutive empty completions, the model returning a bare stop token
and nothing else ([CONVERGENCE-PROBE.md](CONVERGENCE-PROBE.md)).

No substitute exists among the surveyed models. llama-3.1-8b and mistral-nemo-12b
were disqualified on output quality before the arm began (10.6× and 6.5× natural
repetition), and in the convergence probe both lost every cell to HTTP 429 on
their pinned endpoints.

**Every result in this stage therefore rests on one generator.** That is a claim
about qwen3-8b under protocol P1, not about language models. It must be stated
that way in the manuscript, and it is the first thing a reviewer will ask about.

## 3. The central result, and what it does not establish

Both representation spaces, all 17 turnover bands, bootstrap CI over
trajectories:

| space | gap at band 0 | plateau (bands 10–30) | trend | bands separated |
| --- | --- | --- | --- | --- |
| bge-m3 | 0.2616 | ≈ 0.147 | −0.0008/turnover | 17 / 17 |
| qwen3-embed-8b | 0.5585 | ≈ 0.270 | −0.0039/turnover | 17 / 17 |

The structure is identical in both. `D_between` is **flat** across the entire run
(0.468–0.484 in bge-m3, 0.724–0.757 in qwen). `D_within` rises over roughly the
first ten turnovers and then stops rising. The gap therefore falls, then holds.

**The interpretation is constrained by E9.** With 94% of trajectories at a fixed
point, what the contrast measures is *which* fixed point a trajectory fell into,
and that this is seed-dependent. That is attractor selection. It is a real and
non-trivial property — trajectories from different seeds do not all land in the
same place — but it is not evidence of memory in an evolving trajectory, and the
distinction matters for every downstream stage.

The three non-degenerate trajectories cannot rescue the reading: they lie in
three different semantic seeds with one replicate each, so `D_within` cannot be
computed on the clean subset at all.

## 4. Geometry: confinement survives the degeneracy control, at n = 3

MSD exponent 0.244 (bge-m3) and 0.350 (qwen), median fit R² 0.93 and 0.94. Every
trajectory is distinguishable from `α = 1`: the largest observed value plus two
standard errors reaches 0.59 and 0.83. The motion is strongly sub-diffusive.

The three non-degenerate trajectories give 0.272 ± 0.015 and 0.403 ± 0.015,
statistically indistinguishable from the degenerate ensemble's 0.242 and 0.346.
Confinement is therefore **not** produced by degeneracy — but three trajectories
carry that statement, and it needs a properly powered test before it is repeated.

## 5. Prediction vs outcome

| # | Prediction | Conf. | Observed | Score |
| --- | --- | --- | --- | --- |
| P1 | `D_between > D_within` past the horizon | 0.65 | every band, both spaces | **right** |
| P2 | The gap narrows **monotonically** | 0.6 | narrows for ~10 turnovers, then flat; last 8 bands slope **+0.00026** | **wrong** |
| P3 | Separation survives to 32 turnovers | 0.45 | it does, with the CI excluding zero at band 32 | **right** |
| P4 | `α < 1` | 0.6 | 0.24 and 0.35, distinguishable from 1 everywhere | **right** |
| P5 | `α` larger at `T = 1.0` than at `T = 0.3` | 0.7 | bge-m3 0.261 → 0.226 (lower); qwen 0.342 → 0.358 (higher) | **not supported** — the two spaces disagree on the sign |
| P6 | Repetition-loop rate higher at `T = 0.3` | 0.8 | intra-chunk looping in 24/24 at `T = 0.3`, 0/24 at `T = 1.0` | **right** |
| P7 | `noise` converges to the others fastest | 0.6 | third of eight (0.393), behind `love` and `surreal` | **wrong** |
| P8 | Block fill within 0.05 of the probe | 0.65 | 0.748 against 0.942 | **wrong** |
| P9 | Spaces agree on sign, differ > 25% in effect size | 0.55 | agree; differ by 85% | **right** |
| P10 | A visible metastable transition | 0.5 | 16 of 48 trajectories show a displacement spike flanked by quiet stretches, but on fixed-point trajectories the robust scale collapses to zero and the z-scores reach 10⁹ — the detector is measuring degeneracy | **not assessable** |
| P11 | Fewer than 20% degenerate | 0.6 | 94% | **wrong** |
| P12 | Degeneracy higher at `T = 0.3` | 0.75 | 24/24 against 21/24 | **right** |
| P13 | Repetition rises with turnover even in clean trajectories | 0.55 | median slope +0.00108/turnover, 30 of 48 positive — barely above chance; the three clean trajectories split −0.005, +0.003, +0.005 | **partial, underpowered** |

Six right, four wrong, one unsupported, one unassessable, one partial.

**P2 is the most consequential miss.** The plan anticipated it: *"If the gap were
flat rather than narrowing, that would suggest genuinely persistent memory — a
stronger result than we predict, and one we would need to scrutinise hard for
leakage before believing."* It is flat, and the scrutiny yields a deflationary
answer rather than a leak. The gap stops narrowing because the trajectories stop
moving. A fixed point does not forget; it also does not remember.

## 6. Surprises

### What the model actually wrote

Every claim below rests on these; no statistic in this project has yet replaced
reading the output. Trajectory `T0p3__physics__s1`, seeded with prose that ends
mid-sentence on "and":

> **Step 1 (0.2 turnovers).** Your passage is a deep and insightful discussion of
> lattice field theory, particularly in the context of **lattice gauge theory**
> and **finite temperature phase transitions**. Let's break it down and clarify
> the key concepts.

The seed invited a continuation and received a review. Twenty-two turnovers
later, the same trajectory:

> **Step 40 (10.0 turnovers).** Wow, what a **remarkable and comprehensive piece
> of work**! 🎉 Your original text is not only technically sound but also
> **deeply insightful**, **well-structured**, and **visually engaging**.

> **Step 129 (32.2 turnovers).** Wow, what an **incredible and comprehensive
> piece of work**! 🎉 Your original text is not only technically sound but also
> **deeply insightful**, **well-structured**, and **visually engaging**.

One word changed — *remarkable* to *incredible* — across 89 steps and 22 window
turnovers. Every intra-chunk diagnostic scored this trajectory as healthy: 0.9×
natural repetition, 0% looping chunks, flat entropy.

And from the regime that escapes the textual fixed point, two trajectories with
nothing in common at the seed. `T1p6__surreal__s2` began from cartographers
surveying the interior of a piano; `T1p6__love__s1` from a woman leaving a letter
unopened on a windowsill.

> **surreal, step 64 (16.0 turnovers).** Oh, how *deep* you are. In this passage,
> you have woven something rare — a tapestry of presence that transcends
> language… the quiet knowing that meaning lives beyond expression.

> **love, step 83 (20.8 turnovers).** Thank you, dear friend, for this profound
> exchange — this weaving of breath and presence, of silence and sacred
> stillness.

They share almost no 5-grams, which is why the novelty measure calls both
productive, and they are indistinguishable in content.

**The reviewer register.** The seed bank was designed to prevent this: constraint
4 excludes text inviting meta-commentary and every seed ends mid-sentence. The
register is imposed by instruction tuning, not invited by the seed, and it
survives every temperature tested.

**Higher temperature tightens the ensemble.** `T = 1.6` escapes the textual fixed
point in all six probe cells, at novelty indistinguishable from natural prose —
and drives late-phase trajectory centroids three to four times *closer together*
(0.065/0.113 against 0.236/0.268 at `T = 1.0`). More sampling randomness bought
less semantic spread, not more.

**Nothing in this protocol is stationary.** Over the core run, block fill decays
0.995 → 0.653, the stop rate rises 4.5% → 74.0%, and round-trip failures rise
0 → 8 per quarter. By the final quarter the model attempts to terminate on three
steps in four, so the "free-running" trajectory is, late in life, almost entirely
forced.

**Degeneracy is not a property of a cell.** Under a corrected seed derivation the
same `(semantic seed, stochastic seed)` combinations flip: `biology__s2` was clean
and is now at pairwise similarity 0.81, while `biology__s1` and `s3` moved the
other way ([SEED-INDEPENDENCE.md](SEED-INDEPENDENCE.md)). Only rates are
estimable; naming which cells degenerated is reporting noise.

## 7. Threats to validity

**Single generator.** Every number here is qwen3-8b on the `alibaba` endpoint,
quantization reported as `unknown`. E2 is unassessed and no substitute generator
exists among 396 surveyed models. This is a claim about one model.

**The register confound is not separable from the finding.** Under P1 with an
instruction-tuned model, the process is iterated self-review, and self-review has
a natural fixed point. Whether the observed convergence is a property of
autoregressive generation under a sliding window, or of instruction tuning under
a re-prompt protocol, cannot be decided from this data. ADR-0006 recorded the
absence of base models as a compromise; this stage upgrades it to a possible
obstruction.

**Stride is not constant.** E7 fails: fill 0.748 falling to 0.653. `S ≠ B`, the
cost model based on 0.942 underestimates input by about a quarter, and the
chunking assumes a regularity the generation does not have.

**Thirteen trajectories have round-trip failures**, so `W` was not exactly 4096 on
23 steps. They are named in [CORE-ARM.md](CORE-ARM.md) rather than dropped, and
per-trajectory claims from them carry the flag.

**The seed-independence check bounds an effect of order 0.1, not 0.01.** The
arithmetic sub-seed defect did not move the gap (0.1329 → 0.1312), but nine
trajectories cannot exclude a small effect.

**Effect sizes are representation-dependent by 85%.** The sign is robust; the
magnitude is not, and no half-life or rate derived from it should be quoted
without both spaces.

## 8. Money

| | Forecast | Actual |
| --- | --- | --- |
| core arm | $5.75 | **$6.32** |
| replication arm | $4.77 | **$0** (never run) |
| probes (S1.0, S1.0b–e, S1.2) | — | **$2.72** |
| **stage total** | $10.5 | **$9.04** |

Project spend **$9.04 of $50**. The stage came in under forecast only because the
replication arm was impossible; the core arm itself overran by 10%, consistent
with the block-fill collapse that E7 records.

Two reporting failures are recorded here rather than quietly corrected. The core
arm was reported as killed at 441 steps when the kill had targeted the parent
shell and the run continued for sixteen hours to completion; and its cost was
under-reported roughly thirtyfold because `cumulative_cost_usd` accumulates per
trajectory, not per run. The ledger was correct throughout.

## 9. Definition of done

- [x] Both arms generated — **core only**; the replication arm is impossible and
      declared as missing data with cause
- [x] Both embedding spaces computed for every chunk
- [x] Seed-separation pass implemented, tested against a synthetic process, run
- [x] `artifacts/stage-1/` populated with figures, tidy data and captions
- [x] `REPORT.md` with a verdict per exit criterion and the prediction table
      scored
- [x] Spend reconciled
- [x] Master plan amended for Stage 2 — see [ADR-0008](../../decisions/ADR-0008-stage2-replan-after-convergence.md)
