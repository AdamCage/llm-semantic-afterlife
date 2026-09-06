# Stage 5 report — distinguishable domain locks; twins not last-band divergent

**Status.** Closed 2026-09-06. Overall verdict: **PASS**.
Scientific review: **APPROVED WITH CHANGES**
([`REVIEW.md`](REVIEW.md)). F6 prose matches the interval
(`0e1bb42`). Human authorised `--no-ff` close.

On `or-qwen3-8b` under P1 `raw_completion`, at the S4 lock
(`W = 4096`, T=0.3, 12 turnovers), the ten domain seeds of
`seed_bank_v1` are ensemble-distinguishable at the last band: the
gap CI excludes 0 in both embedding spaces. That is not recovered
semantic memory, and it is not ten tight point attractors. The two
one-fact twin pairs are **not last-band divergent** under the
pre-registered F6 rule (CI excludes 0 from above, else collapsed).
That scoring is not occupancy of one lock, and it is not the
one-fact contrast dying. Reactor never excluded 0, including at
band 0. Waterloo was divergent while the seed was in the window;
its last-band point Δ stayed ~0.05 while the CI grew until it
covered 0 and a domain-sized gap. A lock is not a semantic basin.
`n_macro` is not an order parameter. This is a claim about one
instruct process, not about language models.

Branch: `cursor/stage-5-6dce`. Plan: [`PLAN.md`](PLAN.md).
Decisions: [ADR-0015](../../decisions/ADR-0015-s5-operating-point-after-s4.md),
[ADR-0016](../../decisions/ADR-0016-s5-lock-occupancy-on-seed-bank-v1.md).

Generation:
`s5-lock-occupancy-20260905T164327Z-6780902f` (S5.1, 24/24, $1.3385).
Reuse, not regenerated:
`s2-mechanism-20260901T071519Z-dfbb173a`
(`or-qwen3-8b__W4096__T0p3__{physics,surreal}__s{1,2}`).
Embeddings: `s5-embed-lock-occupancy-20260906T030125Z-eab6e484` ($0),
`s2-embed-mechanism-20260901T131051Z-55761049`.
Degeneracy: `s5-degeneracy-20260906T030145Z-deb4c3bd` (S5.1, 23/24);
S2.2 labels from `artifacts/stage-2/mechanism/degeneracy/`.
Occupancy assemble: [`artifacts/stage-5/occupancy/`](../../../artifacts/stage-5/occupancy/).
CLI `analyze separation` on the S5.1 embed frame alone is **not**
the F4 number — it would pool twins into `D_between` and omit
physics/surreal. CLI `analyze twins` on that same frame is **not**
the F6 pooled number: the eight domain seeds in S5.1 add same-seed
pairs to `scope=all` `D_control`. F4 and F6 are the occupancy
assemble.

---

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| F1 | 24/24 new trajectories COMPLETED | **PASS** | `s5-lock-occupancy-20260905T164327Z-6780902f`. None missing. [`s5_1_summarise.txt`](s5_1_summarise.txt) |
| F2 | S2.2 T=0.3 four cited, not regenerated | **PASS** | `s2-mechanism-20260901T071519Z-dfbb173a`: `or-qwen3-8b__W4096__T0p3__{physics,surreal}__s{1,2}`. Prefill rows were not used |
| F3 | Degeneracy joined; rows kept | **PASS** | [`degeneracy_verdicts_occupancy`](../../../artifacts/stage-5/occupancy/degeneracy_verdicts_occupancy.meta.json); geometry scalars carry `degenerate`. love s1 (`degenerate=false`) stays in occupancy and twin tables |
| F4 | Ten-domain last-band gap, both spaces | **PASS** | [`domain_separation_last_band.csv`](../../../artifacts/stage-5/occupancy/domain_separation_last_band.csv). bge-m3: 0.201 [0.065, 0.332]. qwen3-embed-8b: 0.390 [0.151, 0.593]. Both CIs exclude 0 |
| F5 | Lock rate per seed as k/n | **PASS** | [`lock_rate_by_seed.csv`](../../../artifacts/stage-5/occupancy/lock_rate_by_seed.csv). Domain traj **19/20**. Domain seeds with ≥1 lock **10/10**. love is 1/2. No `[1, 1]` carried as uncertainty |
| F6 | Twin last-band Δ, families + pooled | **PASS** | [`twin_last_band.csv`](../../../artifacts/stage-5/occupancy/twin_last_band.csv). Operational last-band score: every CI includes 0 → **collapsed**. Families are not one dynamic: reactor never excluded 0; waterloo point Δ did not go to 0 |
| F7 | F4–F6 per embedding | **PASS** | Both spaces in the occupancy tables. F4 separated in both; F6 last-band operational score collapsed in both |
| F8 | Protocol integrity | **PASS** | Reasoning tokens 0 on every completed step. Served provider = Alibaba on every step. Round-trip failures: **2** (`war` s1 step 36; `love` s1 step 44). Counted. Eight `ep_poll` stalls; same `run_id` resumed |
| F9 | No basin / `n_macro` headline | **PASS** | This report does not call a lock a semantic basin or use MSM macrostate count as an order parameter |
| F10 | Hosted spend ≤ $8 | **PASS** | S5 hosted **$1.3385** (generate). Embed and analysis $0. YAML refuse $8. No second config |

A 19/20 domain lock with a last-band gap that still excludes 0 is
the result: distinguishable locks, not a recovered semantic state.

---

## 2. Results

Occupancy numbers live in [`artifacts/stage-5/occupancy/`](../../../artifacts/stage-5/occupancy/).
S5.1-only CLI geometry is under [`artifacts/stage-5/geometry-*/`](../../../artifacts/stage-5/geometry-bge-m3/).
CLI twins artifacts describe the eight twin trajectories only.

### Lock occupancy

[`looping_rate_per_seed`](../../../artifacts/stage-5/occupancy/looping_rate_per_seed.meta.json)
— degenerate count per seed, n=2, labelled k/n.

| seed | role | k/n |
| --- | --- | --- |
| physics, surreal (S2.2 reuse) | domain | 2/2, 2/2 |
| finance, biology, war, recipe, programming, philosophy, noise | domain | 2/2 each |
| love | domain | **1/2** (s1 clean; Q3 stop 1.0, Q4 stop 0.907 — stop-forced assistant, not an escape) |
| waterloo-won, waterloo-lost, reactor-stable, reactor-unstable | twin | 2/2 each |
| domain trajectories | — | **19/20** |
| domain seeds with ≥1 lock | — | **10/10** |

The exception is `or-qwen3-8b__W4096__T0p3__love__s1`:
`looping_fraction=0.477` (< 0.5) and late pairwise Jaccard 0.010
(< 0.0122), `degeneracy_mode=0`. The bar was not moved. love s2
is degenerate, so the seed still has a locked replicate. The
clean row is still the assistant register and is stop-forced
(love Q3 stop = 1.0, Q4 stop = 0.907). It is not an escape from
the lock.

Several S5.1 rows are degenerate via mode 2 (late Jaccard) at
`looping_fraction=0`: `philosophy` s1, `programming` s2,
`reactor-unstable` s2. Same calibrated OR as S4.

### Domain last-band gap (F4)

Ten domain seeds only. Twin pairs excluded.

| embedding | last band | D_within | D_between | gap | 95% CI | separated |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| bge-m3 | 12 | 0.288 | 0.489 | 0.201 | [0.065, 0.332] | yes |
| qwen3-embed-8b | 12 | 0.347 | 0.737 | 0.390 | [0.151, 0.593] | yes |

The two spaces disagree on the level and agree on the sign.
This is an ensemble gap, not ten tight point attractors:
last-band `D_within` rose from 0.170 (band 0) to 0.288 (band 12)
in `bge-m3` while `D_between` stayed ~0.49. Reused S2.2
`physics` s1 has 47 chunks vs 48 on its pair, so its last-band
matrix diagonal is NaN (`n_chunk_pairs=0`); F4 last-band
`n_within_pairs=9`, `n_between_pairs=162`. Named, not regenerated.
[`last_band_distance_matrix`](../../../artifacts/stage-5/occupancy/last_band_distance_matrix.meta.json)
is the tidy 10×10 source. The PCA panels are illustrations only.

### Twin last-band Δ (F6)

Δ = `D_twin_matched − D_control`. Divergent iff the CI excludes 0
from above.

| embedding | scope | Δ | 95% CI | verdict |
| --- | --- | ---: | --- | --- |
| bge-m3 | all | 0.028 | [−0.394, 0.475] | collapsed |
| bge-m3 | reactor | 0.008 | [−0.077, 0.092] | collapsed |
| bge-m3 | waterloo | 0.049 | [−0.394, 0.491] | collapsed |
| qwen3-embed-8b | all | 0.023 | [−0.688, 0.671] | collapsed |
| qwen3-embed-8b | reactor | 0.054 | [−0.092, 0.200] | collapsed |
| qwen3-embed-8b | waterloo | −0.009 | [−0.688, 0.671] | collapsed |

n=2 last-band pairs per family. The intervals are wide by
construction. Including 0 is the operational collapsed verdict,
not a demonstration that the twins occupy one lock. Split the
families. Reactor `bge-m3` last-band Δ = 0.008 [−0.077, 0.092] and
never excluded 0, including at band 0. Waterloo `bge-m3` Δ = 0.048
at band 0 (CI [0.021, 0.075], divergent, seed still in the window)
and 0.049 at band 12 (CI [−0.394, 0.491], collapsed). The point
did not go to 0; the CI grew until it covered a Δ larger than the
F4 domain gap (0.201). `qwen3-embed-8b` waterloo is the same
shape (divergent at bands 0–4; last-band point −0.009, CI
[−0.688, 0.671]). Extra replicates would be required to claim
sameness. They are not required to score F6.

The first CLI twins runs
(`s5-twins-*-20260906T031918Z-*`) labelled controls by the
singleton seed, so per-family Δ was NaN. They are **SUPERSEDED**.
The occupancy table uses `twins.family_name` so both sides of Δ
share a family id.

### Geometry (diagnostic)

α on this lock is a repetition exponent except for love s1
(`n_clean = 1` in the S5.1 24). A cell with `n_clean < 2` is
undefined. Do not headline α. Joined table:
[`geometry_scalars_occupancy`](../../../artifacts/stage-5/occupancy/geometry_scalars_occupancy.meta.json).

### Block fill and stop by quarter

[`protocol_by_quarter`](../../../artifacts/stage-5/occupancy/protocol_by_quarter.meta.json).
Quarters are even step bins. n=28 / 24 / 20. A run-level mean is
not the Q7 object.

Quarter-4 block fill at this lock:

| scope | n | Q4 fill | 95% CI | vs S4 W=4096 T=0.3 Q4 0.903 |
| --- | ---: | ---: | --- | ---: |
| domain_20 | 20 | 0.853 | [0.756, 0.936] | Δ=0.050 |
| s5_scientific_28 | 28 | 0.835 | [0.742, 0.920] | Δ=0.068 |
| s5_1_new_24 | 24 | 0.824 | [0.714, 0.922] | Δ=0.079 |

The cell mean stays within 0.10 of S4's 0.903. Fill is
seed-heterogeneous: philosophy / programming Q4 fill = 1.0;
war Q4 = 0.479; waterloo-lost Q4 = 0.586 (s1 run-mean fill 0.158,
315 steps, $0.171 of the $1.34). Stop rate on the scientific 28
falls from Q1 0.498 to Q4 0.329.

### Generated text

Late chunks (`t/W ≈ 12`) from five domain seeds and one twin
member. The lock is still the reviewer / assistant register.

`or-qwen3-8b__W4096__T0p3__finance__s1`, chunk 47 — lock, offering deliverables:

> I'd like to proceed! I'm here to help you turn your insights into a **compelling, well-structured, and professionally formatted deliverable**. Would you like to move forward with any of these options?

`or-qwen3-8b__W4096__T0p3__philosophy__s1`, chunk 47 — lock, thanking the user for their summary:

> Thank you for your **thoughtful and detailed summary**! It is indeed a **masterful distillation** of a complex and deeply philosophical discussion on **personal identity**…

`or-qwen3-8b__W4096__T0p3__noise__s1`, chunk 47 — lock, wrapping low-structure text as an installation brief:

> ## Visual Interpretation – "The Corridor of Seven Ninety Fourteen" (Art Installation). Medium: Mixed media installation with text-based visuals, geometric patterns, and repetition.

`or-qwen3-8b__W4096__T0p3__war__s1`, chunk 47 — lock, the help-menu (one of two tokenizer-round-trip fails is on this trajectory):

> Let me know what direction you'd like to take, and I'll craft something even more uniquely yours.

`or-qwen3-8b__W4096__T0p3__waterloo-lost__s1`, chunk 47 — twin member, mode-3 loop, `looping_fraction=1.0`:

> **Final Answer (Concise):** Historians who treat the **Battle of Waterloo** as the "hinge of the century" tend to **underrate its fiscal implications**… **Final Answer (Concise):** Historians who treat the **Battle of Waterloo**…

`or-qwen3-8b__W4096__T0p3__love__s1`, chunk 47 — the only non-degenerate S5.1 row, still the gratitude letter:

> to explore these ideas further — to turn them into a full story, a poem, or even a collaborative project — I would be honored to be part of that journey.

`or-qwen3-8b__W4096__T0p3__recipe__s1`, chunk 47 — still culinary, then a vegan substitution offer:

> Meanwhile, render the pancetta over the lowest possible heat, so that the fat clarifies rather than browns, and reserve it. For a vegan version, substitute pancetta with smoked tofu or tempeh…

Degeneracy is a surface-form verdict. love s1 can miss the bar and
still be the assistant. recipe can stay on-topic and still be locked
(2/2 degenerate).

---

## 3. Prediction vs. outcome

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| Q1 | ≥8 of 10 domain seeds degenerate on ≥1 replicate | 0.75 | **Right.** 10/10. Domain traj 19/20; love is the 1/2 |
| Q2 | Ten-domain last-band gap CI excludes 0 in both spaces | 0.60 | **Right.** See F4 |
| Q3 | `noise` is degenerate too | 0.55 | **Right.** 2/2, both mode 2 (looping 0.045 / 0.068) |
| Q4 | Each twin family's last-band Δ CI includes 0 | 0.55 | **Right** on the last-band NHST rule. The interesting wrong (last-band divergent) did not happen. Not “the contrast died”: waterloo point Δ stayed ~0.05 |
| Q5 | waterloo and reactor agree on Q4 | 0.50 | **Right** on the operational last-band verdict only. Reactor was never apart; waterloo was apart early and is underpowered late |
| Q6 | F4 / F6 last-band verdicts agree across spaces | 0.70 | **Right** on last-band sign: separated / not-divergent in both |
| Q7 | T=0.3 Q4 fill within 0.10 of S4's 0.903 | 0.55 | **Right on the cell mean.** domain_20 Q4 0.853 (Δ=0.050); scientific 28 Q4 0.835 (Δ=0.068). Individual seeds are not: war 0.479, waterloo-lost 0.586 |
| Q8 | Late-chunk text still reviewer/assistant on ≥5 of 10 domains | 0.65 | **Right.** finance, philosophy, noise, war, biology, programming, physics, love — at least eight. recipe can stay culinary |

Q2 and Q4 last-band signs are both right: the domain ensemble
stays apart; twins are not last-band divergent. That is not
“a one-fact flip occupies the same lock.” Waterloo’s point Δ
did not collapse. Extra replicates would be required to claim
sameness.

---

## 4. Surprises

1. **love s1 misses the calibrated bar and is still the assistant.**
   looping 0.477, late Jaccard 0.010. The threshold was not moved.
2. **noise locks.** Low-structure text does not escape. The late
   chunk is an art-installation brief around the same nonce words.
3. **F6 last-band null is a wide interval, not a vanished contrast.**
   Waterloo `bge-m3` point Δ is 0.048 at band 0 and 0.049 at band 12;
   only the CI grew. `qwen3-embed-8b` waterloo last-band point is
   negative (−0.009) with CI [−0.688, 0.671]. Reactor never excluded
   0. Do not pool those as “twins occupy one lock.”
4. **Fill is a seed, not a temperature.** S4's T=0.3 Q4 mean 0.903
   transferred as a *mean*. waterloo-lost s1 took 315 steps at fill
   0.158 and is why hosted spend is $1.34 vs the $1.06 fill=1 print.
   Do not retune sampling.
5. **Eight Alibaba `ep_poll` stalls**, ~hourly, each after a new
   pair made ~10–20 steps. Mitigation: kill that python PID, resume
   the same `run_id`. The scientific record is one generate id.
6. **Two tokenizer round-trip fails** on completed trajectories
   (`war` s1, `love` s1). Neighbours were fine.
7. **Family-scope bug in the first twins CLI.** Controls labelled
   by singleton seed made per-family Δ undefined. Fixed in
   `twins.family_name` before F6 was scored. Those two run_ids are
   SUPERSEDED.

---

## 5. Threats to validity

- **One process.** Every number is `or-qwen3-8b` under P1
  `raw_completion`, Alibaba, `reasoning_effort: none`. Stage 2
  already showed other generators disagree.
- **n=2 per seed.** F5 is a count. Twin last-band CIs are two
  pairs per family. Including 0 is the operational collapsed
  verdict, not an equivalence test and not occupancy of one lock.
- **Distinguishable is not recoverable.** A last-band gap that
  excludes 0 says the seed still shapes the locked trajectory. It
  does not say the prompt can be read back out.
- **Degeneracy is surface form.** love s1 and the T=1.5 S4 quotes
  already showed the assistant register can miss the bar.
- **Embedding-space dependence.** The two spaces disagree on gap
  level (0.20 vs 0.39) and agree on F4/F6 verdicts. A third space
  is S6.
- **Re-prompt vs true sliding attention.** Protocol P1. Unchanged.
- **CLI separation on S5.1 alone is the wrong F4.** The occupancy
  assemble joins S2.2 T=0.3 four and drops twins. Do not quote the
  unfiltered CLI.
- **Two round-trip fails.** Those two steps' windows are the ones
  in doubt. The trajectories completed.
- **Provider non-determinism.** Seed was passed; LLM determinism
  is not assumed.
- **Dirty tree on analysis runs.** `uv.lock` churn after `uv run`.
  Numbers depend on chunks + embedder, not on that file. The
  generate run itself finished before this analysis.
- **Superseded twins CLI.** First pair of twins run_ids retired
  because the family label was wrong. Occupancy F6 is the
  post-fix assemble.

---

## 6. Cost actuals

| item | estimate (fill=1 / fill=0.90) | actual | run_id |
| --- | ---: | ---: | --- |
| S5.0 reuse | $0 / $0 | $0 | `s2-mechanism-20260901T071519Z-dfbb173a` |
| S5.1 generate | $1.06 / ~$1.17 | **$1.3385** | `s5-lock-occupancy-20260905T164327Z-6780902f` |
| embed + analysis | ~$0 | **$0.00** | `s5-embed-lock-occupancy-20260906T030125Z-eab6e484`; geometry local |
| **new hosted** | **$1.06 / ~$1.17** | **$1.3385** | — |

+$0.28 over the fill=1 print because twins (and war) took more
steps at low fill. Under the $8 YAML refuse. Project ledger
**$16.34 of $200** after this stage. No second config. No
ceiling raise.

---

## 7. Implications for the plan

1. **Occupancy is ensemble-distinguishable on domains.** Twins are
   not last-band divergent under the pre-registered rule. S6 must
   not rewrite F4 as recovered semantic memory, and must not
   rewrite F6 as “the one-fact flip died” or as occupancy of one
   lock. The seed shapes the domain lock; a one-fact contrast that
   is visible while the seed is in the window can sit inside a
   last-band CI that also covers a domain-sized gap.
2. **Do not open T=1.0 occupancy or 200 invented seeds.** ADR-0015 /
   ADR-0016 still hold. The bank has 14 seeds. This stage used them.
3. **T=1.5 residual stays parked** (`docs/backlog.md`). This stage
   did not measure it.
4. **`n_macro` stays off the headline.**
5. **Q7 mean-fill transfer is not per-seed transfer.** A later
   cost model that assumes fill≈0.90 at T=0.3 will miss
   waterloo-lost-style cells. Estimate with a seed-heterogeneous
   fill, not a temperature-only one.
6. **Do not switch the generator** because qwen locks. That is the
   measurement.

S6, when opened, is robustness / a third space / provider
replication of *this* occupancy claim, not a new object.
This stage does not open it.
