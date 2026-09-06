# Stage 6 report — occupancy signs hold in a third embedding space

> **Errata (2026-09-06).** See [`ERRATA.md`](ERRATA.md) (ADR-0019). F4 last-band points stand; F6 CIs are not valid bootstrap intervals. `run_id`s are unchanged.

**Status.** Closed 2026-09-06. Overall verdict: **PASS**.
Scientific review: **APPROVED WITH CHANGES**
([`REVIEW.md`](REVIEW.md)). F4/F6 sidecar prose aligned
(`ff6254f`). Human authorised `--no-ff` close.

On the **same** 28 `or-qwen3-8b` P1 trajectories Stage 5 used
(`W=4096`, T=0.3, 12 turnovers), the occupancy *signs* survive
`gemini-embed-001` under the pre-registered last-band rules: the
ten-domain gap CI excludes 0, and twin last-band Δ CIs include 0
(operational collapsed). Gemini F4 lower bound is 0.029 on n=20
with `n_within_pairs=9` — an NHST whisker, not a thick robustness
margin. That is sign agreement against an embedding-artifact
objection. It is not architecture-independence: gemini is a closed
model. It is not recovered semantic memory. A last-band CI that
includes 0 is not occupancy of one lock. A lock is not a semantic
basin. `n_macro` is not an order parameter. No new generate `run_id`
was minted.

Branch: `cursor/stage-6-6dce`. Plan: [`PLAN.md`](PLAN.md).
Decision: [ADR-0017](../../decisions/ADR-0017-s6-third-space-occupancy-robustness.md).

Generate (reused, not this stage):
`s5-lock-occupancy-20260905T164327Z-6780902f`,
`s2-mechanism-20260901T071519Z-dfbb173a`
(`or-qwen3-8b__W4096__T0p3__{physics,surreal}__s{1,2}`).
Two-space embeds (reused):
`s5-embed-lock-occupancy-20260906T030125Z-eab6e484`,
`s2-embed-mechanism-20260901T131051Z-55761049`.
Degeneracy (reused, not retuned):
`s5-degeneracy-20260906T030145Z-deb4c3bd` plus S2.2 labels.
Gemini embeds (this stage, `$0`):
`s6-embed-third-space-20260906T082301Z-588eff8f` (S5.1, 1152 × 3072, 24/24),
`s6-embed-third-space-20260906T082628Z-9077d587` (S2.2, 766 × 3072; assemble
keeps the raw T=0.3 four).
Occupancy assemble: [`artifacts/stage-6/occupancy/`](../../../artifacts/stage-6/occupancy/).

---

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| F1 | No new generate | **PASS** | `runs/s6/` holds two embed `run_id`s only. Sources named above |
| F2 | Gemini on S5.1 | **PASS** | `s6-embed-third-space-20260906T082301Z-588eff8f` COMPLETED, 1152 chunks, 24/24 traj, dim 3072 |
| F3 | Gemini on S2.2 four; grid 20+8 | **PASS** | [`gemini_grid_counts.csv`](../../../artifacts/stage-6/occupancy/gemini_grid_counts.csv): 20 domain + 8 twin. Physics/surreal present after `is_raw_lock_trajectory` |
| F4 | Domain last-band gap, third space | **PASS** | [`domain_separation_last_band.csv`](../../../artifacts/stage-6/occupancy/domain_separation_last_band.csv). gemini-embed-001: 0.150 [0.029, 0.266], separated |
| F5 | Sign vs S5 | **PASS** | Gemini CI excludes 0 from above, same sign as both S5 spaces (bge-m3 0.201 [0.065, 0.332]; qwen3-embed-8b 0.390 [0.151, 0.593]). Level differs |
| F6 | Twin last-band Δ, third space | **PASS** | [`twin_last_band.csv`](../../../artifacts/stage-6/occupancy/twin_last_band.csv). Gemini pooled / reactor / waterloo CIs all include 0 → operational **collapsed**. Not sameness |
| F7 | Thresholds unchanged | **PASS** | 0.083 / late Jaccard 0.0122. love s1 kept. Degenerate rows kept. [`lock_rate_by_seed.csv`](../../../artifacts/stage-6/occupancy/lock_rate_by_seed.csv) still 19/20, 10/10, love 1/2 |
| F8 | Closed architecture named | **PASS** | This report and gemini artifact limitations: gemini cannot alone prove architecture-independence |
| F9 | No basin / `n_macro` / H1 / generate | **PASS** | No new generate. This report does not call a lock a basin or headline MSM |
| F10 | Spend ≤ $2 | **PASS** | Stage 6 hosted **$0.0000**. YAML refuse $2. 72 + 48 ledger embedding charges, `cost_usd=0` |

Agreement of sign across three spaces is sign agreement against an
embedding-artifact objection, not a recovered semantic state and
not a thick robustness margin.

---

## 2. Results

Numbers live in [`artifacts/stage-6/occupancy/`](../../../artifacts/stage-6/occupancy/).
F4/F6 are the occupancy assemble, not CLI `analyze separation` or
CLI twins `scope=all` on an S5.1 frame.

### Domain last-band gap (F4)

Ten domain seeds only. Twin pairs excluded.

| embedding | last band | D_within | D_between | gap | 95% CI | separated |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| bge-m3 | 12 | 0.288 | 0.489 | 0.201 | [0.065, 0.332] | yes |
| qwen3-embed-8b | 12 | 0.347 | 0.737 | 0.390 | [0.151, 0.593] | yes |
| gemini-embed-001 | 12 | 0.200 | 0.350 | 0.150 | [0.029, 0.266] | yes |

Gemini agrees on **sign** and is closer in level to `bge-m3` than
to `qwen3-embed-8b`. The gap is still an ensemble, not ten point
attractors: gemini `D_within` rose from 0.098 (band 0) to 0.200
(band 12) while `D_between` stayed ~0.35. The last-band CI
[0.029, 0.266] is an NHST whisker on n=20, `n_within_pairs=9`.
Reused S2.2 `physics` s1 has 47 chunks vs 48 on its pair, so its
last-band matrix diagonal is NaN (`n_chunk_pairs=0`); F4 last-band
`n_between_pairs=162`. Named, not regenerated. That lower bound is
closer to 0 than `bge-m3`'s 0.065. Q1 remains Right against the
pre-registered rule; it is not a thick robustness margin.
[`domain_gap_three_spaces`](../../../artifacts/stage-6/occupancy/domain_gap_three_spaces.meta.json)
is the comparison panel. PCA panels are illustrations only.

### Twin last-band Δ (F6)

Δ = `D_twin_matched − D_control`. Divergent iff the CI excludes 0
from above.

| embedding | scope | Δ | 95% CI | verdict |
| --- | --- | ---: | --- | --- |
| gemini-embed-001 | all | −0.012 | [−0.286, 0.223] | collapsed |
| gemini-embed-001 | reactor | 0.008 | [−0.071, 0.087] | collapsed |
| gemini-embed-001 | waterloo | −0.031 | [−0.286, 0.223] | collapsed |

S5 two-space last-band scores are unchanged (every CI includes 0).
n=2 last-band pairs per family. Including 0 is the operational
collapsed verdict, **not** occupancy of one lock.

Split the families. Gemini **reactor** never excluded 0, including
at band 0 (Δ 0.018 [−0.019, 0.054]). Gemini **waterloo** was
divergent at band 0 (Δ 0.033 [0.001, 0.065], seed still in the
window) and collapsed at band 12 (point −0.031). The point moved
by 0.064 from band 0, inside the pre-registered 0.10 band; it did
not go to a demonstrated zero. Extra replicates would be required
to claim sameness.

### Lock occupancy (unchanged; F7)

Same degeneracy labels. Domain traj **19/20**. Seeds with ≥1 lock
**10/10**. love **1/2** (s1 kept). Thresholds not moved.

### Block fill and stop by quarter

Reused generate; Stage 6 minted no completion tokens.
[`protocol_by_quarter`](../../../artifacts/stage-6/occupancy/protocol_by_quarter.meta.json).

| scope | n | Q4 fill | 95% CI | Q4 stop |
| --- | ---: | ---: | --- | ---: |
| domain_20 | 20 | 0.853 | [0.756, 0.936] | 0.359 |
| s5_scientific_28 | 28 | 0.835 | [0.742, 0.920] | 0.329 |
| s5_1_new_24 | 24 | 0.824 | [0.714, 0.922] | 0.338 |

Stop rate on the scientific 28 still falls from Q1 ~0.50 to Q4
0.329. Fill remains seed-heterogeneous. Do not retune.

### Generated text (reused S5 generate)

Late chunks (`t/W ≈ 12`). The lock is still the reviewer /
assistant register. Stage 6 did not regenerate these strings.

`or-qwen3-8b__W4096__T0p3__finance__s1` — lock, offering deliverables:

> I'd like to proceed! I'm here to help you turn your insights into a **compelling, well-structured, and professionally formatted deliverable**. Would you like to move forward with any of these options?

`or-qwen3-8b__W4096__T0p3__philosophy__s1` — lock, thanking the user:

> Thank you for your **thoughtful and detailed summary**! It is indeed a **masterful distillation** of a complex and deeply philosophical discussion on **personal identity**.

`or-qwen3-8b__W4096__T0p3__noise__s1` — lock, nonce text wrapped as an installation brief:

> Visual Interpretation – "The Corridor of Seven Ninety Fourteen" (Art Installation). Medium: Mixed media installation with text-based visuals, geometric patterns, and repetition.

`or-qwen3-8b__W4096__T0p3__love__s1` — the only non-degenerate S5.1 row, still the gratitude letter:

> to explore these ideas further — to turn them into a full story, a poem, or even a collaborative project — I would be honored to be part of that journey.

`or-qwen3-8b__W4096__T0p3__waterloo-lost__s1` — twin member, still Waterloo fiscal prose:

> Historians who treat the **Battle of Waterloo** as the "hinge of the century" tend to underrate its fiscal implications.

`or-qwen3-8b__W4096__T0p3__physics__s1` — reused S2.2, lattice-QCD assistant:

> The choice of **update algorithm** (e.g., Hybrid Monte Carlo, overrelaxation, cluster updates) becomes **crucial** to maintain efficiency and accuracy.

---

## 3. Prediction vs. outcome

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| Q1 | Gemini last-band domain gap CI excludes 0 (same sign as both S5 spaces) | 0.60 | **Right.** 0.150 [0.029, 0.266] |
| Q2 | Gemini last-band twin Δ CI includes 0 for reactor | 0.55 | **Right.** 0.008 [−0.071, 0.087]; never excluded 0, including band 0 |
| Q3 | Gemini last-band twin Δ CI includes 0 for waterloo | 0.50 | **Right** on the last-band NHST rule. Point Δ = −0.031, not a demonstrated zero |
| Q4 | Gemini F4/F6 last-band *signs* agree with both S5 spaces (Q1–Q3 jointly) | 0.50 | **Right.** Separated / not-divergent in all three spaces |
| Q5 | Gemini gap *level* differs from both S5 spaces by > 0.05 | 0.55 | **Right** arithmetically. vs bge-m3 Δ=0.0509 against an uncalibrated `> 0.05`; vs qwen3-embed-8b Δ=0.240 is the real level shift. Not “gemini is not a copy of bge” |
| Q6 | Waterloo gemini point Δ at band 12 is within 0.10 of band 0 | 0.40 | **Right.** Band 0 = 0.033, band 12 = −0.031, \|Δ\| = 0.064. Sign flipped; contrast did not vanish to a proven zero |
| Q7 | Embed ledger cost is $0 | 0.60 | **Right.** `$0.0000` on both gemini runs |
| Q8 | No new generate `run_id` is minted | 0.90 | **Right.** Two `s6-embed-third-space-*` ids only |

Q1 being right is the pre-registered sign, not a thick robustness
margin (gemini lower bound 0.029; physics s1 drops out of last-band
`D_within`). Q5 being Right on `> 0.05` vs bge is a 0.0009 whisker;
vs qwen 0.240 is why gemini cannot be treated as a copy of that
space. Q6 being right on the 0.10 band does not make waterloo
“the same lock.”

---

## 4. Surprises

1. **Gemini F4 is the smallest of the three gaps** (0.150 vs 0.201 /
   0.390) and still excludes 0. Closed embedder, dim 3072, L2-normalised.
2. **Gemini waterloo point Δ flipped sign** (+0.033 at band 0,
   −0.031 at band 12) while staying inside 0.10. S5 `bge-m3` point
   stayed ~0.05. Do not narrate a common point-Δ story across spaces.
3. **Wall clock.** Both gemini embeds finished in ~2.5 min each with
   `cost_usd=0`. S5 two-space embed saw RouterAI 503s; this opening
   did not. Do not generalise that the endpoint is healthy.
4. **S2.2 surplus is real and was filtered.** 766 gemini rows, 16
   traj; occupancy kept four raw T=0.3 physics/surreal cells.

---

## 5. Threats to validity

- **Closed architecture.** `gemini-embed-001` cannot carry the
  independent-architecture argument. Three-space *sign* agreement
  answers “this is an embedding artifact of bge/qwen.” It does not
  answer “every embedding space would agree.”
- **One generator, one protocol, one lock.** Every trajectory is
  `or-qwen3-8b` under P1 `raw_completion`, Alibaba, T=0.3, `W=4096`.
  Stage 2 already showed other generators disagree.
- **n=2 per seed.** Twin last-band CIs are two pairs per family.
  Including 0 is not an equivalence test and not occupancy of one
  lock.
- **Distinguishable is not recoverable.** Gemini F4 excluding 0
  does not recover the prompt.
- **Degeneracy is surface form.** love s1 still misses the bar and
  is still the assistant. Thresholds were not moved.
- **Re-prompt vs true sliding attention.** Protocol P1. Unchanged.
- **CLI separation on S5.1 alone is still the wrong F4.** Twins
  would enter `D_between`; physics/surreal would be omitted.
- **S2.2 surplus.** Prefill and T=1.0 gemini rows exist on the S2.2
  embed run. Occupancy assemble drops them. Do not analyse the
  unfiltered parquet as the occupancy grid.
- **Provider non-determinism / missing embed price.** Ledger
  `cost_usd=0` because RouterAI usage/yaml price are empty, as in
  S5. Catalogue-ish ~$0.30 was the hand forecast, not a billed
  number.
- **Dirty tree on embed manifests.** `uv.lock` churn after `uv run`
  at launch. Vectors depend on chunk text + embedder, not that file.
- **No geometry pass in this stage.** `α` is not headlined. S5
  geometry remains diagnostic on the same trajectories.

---

## 6. Cost actuals

| item | estimate | actual | run_id |
| --- | ---: | ---: | --- |
| S6.0 reuse generate | $0 | $0 | S5.1 + S2.2 named above |
| S6.1 gemini S5.1 | catalogue-ish ~$0.18 of ~$0.30 | **$0.00** | `s6-embed-third-space-20260906T082301Z-588eff8f` |
| S6.1 gemini S2.2 | remainder of ~$0.30 | **$0.00** | `s6-embed-third-space-20260906T082628Z-9077d587` |
| **new hosted** | **~$0.30 (hand) / YAML $2 refuse** | **$0.00** | — |

The CLI `afterlife estimate` generate print ($1.06) was **not**
spent. Project ledger still **$16.34 of $200**. No second config.
No ceiling raise. No generate.

---

## 7. Implications for the plan

1. **The S5 occupancy *sign* is not a two-space accident.** Gemini
   F4 excludes 0 under the pre-registered rule; gemini F6 last-band
   CIs include 0. Report that as sign agreement, not as a thick
   robustness margin, not as a semantic state, and not as
   architecture-independence. Name the 0.029 whisker and physics s1.
2. **Do not open T=1.0 occupancy, T=1.5, 200 seeds, a second
   generator, or MSM** because the third space agreed. Those arms
   stay parked (ADR-0017).
3. **Do not treat gemini level (0.150) as interchangeable with
   bge-m3 (0.201) or qwen3-embed-8b (0.390).** Sign transferred;
   magnitude did not.
4. **`n_macro` stays off the headline.**
5. **Provider replication / chunk ablation / forced vs unforced**
   remain later estimates, not this opening.
6. **S7 manuscript** is the next stage: write from these artifacts.
   Do not write `paper/main.tex` from this REPORT alone.
