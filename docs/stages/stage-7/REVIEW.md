# Stage 7 review
Reviewer: Cursor Grok 4.6 (scientific supervisor)   Date: 2026-09-06
Gate: FAIL `runs.complete` (expected writing-stage; see [`REVIEW-BRIEF.md`](REVIEW-BRIEF.md) §1). `afterlife review --stage s7 --json .cache/review-s7.json` exit 1. Other listed checks PASS. Do not mint `runs/s7`. Occupancy CIs were not re-bootstrapped.
Verdict: **APPROVED WITH CHANGES**

Do not merge from this review. Do not generate, embed, retune 0.083 / 0.0122, rewrite TeX during review, open parked arms, or `--no-ff` into `main`. Executor rewords on this branch; human close is later.

---

## Answer to the stage question

A TMLR-shaped manuscript **can** be assembled from the closed S0–S6 record without selling H1, H5, architecture-independence, one lock, a basin, or language models as a class. Headline occupancy numbers in `paper/main.tex` match the closed CSVs (F4 last-band 0.201 / 0.390 / 0.150 with the gemini whisker [0.029, 0.266]; F6 last-band CIs include 0; waterloo gemini 0.033 → −0.031). Negatives that the stages actually ran — `validated=0`, H5 absent, gemma 0/8, F6 ≠ one lock — are stated as negatives. Two sentences still exceed that record: the abstract packs F4 as “seed-domain identity” in three spaces, and occupancy is not named as P1 `raw_completion` on the Alibaba pin. Both close by reword. No new `run_id`.

---

## Blocking findings

1. **Sentence.** Abstract: “last-band occupancy still carries seed-domain identity in three embedding spaces.” Related: Figure 1 caption “seed-family identity surviving the horizon”; Discussion “What is not established” omits recovered prompt memory.

   **Problem.** Closed S5/S6 law, and [ADR-0018](../../decisions/ADR-0018-s7-manuscript-from-closed-stages.md): F4 is an **ensemble last-band gap** whose CI excludes 0 from above, not recovered semantic memory. S5 review: distinguishable ≠ recovered memory. S6 review: sign agreement, not recovered memory. S1 REPORT §3 already constrained E1 the same way: with 94% freeze, the contrast is which fixed point a trajectory fell into, “not evidence of memory in an evolving trajectory.” A last-band CI of 0.150 [0.029, 0.266] on n=20, `n_within_pairs=9`, does not support “carries identity.” The next abstract sentence correctly calls gemini an NHST whisker, but that does not unwrite the identity verb. Q2 is structurally right (title is lock occupancy; gemini is §Stage 6) and still fails the brief’s abstract check: three-space identity is co-headlined before the whisker.

   **Resolve (reword, no new run).** Replace “carries seed-domain identity” with last-band **ensemble distinguishability** / domain gap (CI excludes 0 from above), and keep the whisker in that same result sentence. Add to §Limitations or the Discussion “not established” list: F4 is not recovered prompt memory (H2). Align the Stage 1 caption with `seed_separation.meta.json` (“not that the information is recoverable”) and S1 REPORT §3. Do not generate.

2. **Sentence.** Protocol §3.1 / occupancy setup: “All occupancy numbers … use `or-qwen3-8b` … P1” with T=0.3, W=4096, twelve turnovers, and no `raw_completion` and no Alibaba pin. Limitations “one generator, one protocol, one temperature” repeats P1 without the continuation mechanism.

   **Problem.** Brief §4.3: occupancy sentences must stay on `or-qwen3-8b`, P1 **`raw_completion`**, T=0.3, W=4096, 12 turnovers, 28 trajectories. `paper/notes/limitations.md` already named the Alibaba pin and `raw_completion`; `paper/main.tex` dropped both. Glossary: P1 is re-prompt; `raw_completion` is a continuation mechanism. Stage 2 measured `assistant_prefill` vs raw on this generator. A reader who reproduces occupancy under chat/prefill wrapping is in another regime. Provider identity is a named confound on this project; S5 F8 is “served provider = Alibaba on every step.”

   **Resolve (reword, no new run).** Name `raw_completion` and the Alibaba pin next to the occupancy numbers (and once in §Limitations). Optional same paragraph: quantization is unknown. Do not generate. Do not open P1 vs sliding.

---

## Non-blocking observations

1. **Geng alignment.** “Stage 4 is consistent with a later onset of non-looping behaviour at T=1.5” imports transient/mixing language. The next clauses correctly refuse a mixing time and call the rows subdiffusive. Prefer “the T=1.5, W=4096 cell is 0/4 looping,” without “onset.”

2. **S4 heading.** “lock until T=1.5” can be read as including 1.5. Body and table are correct (T≤1.0 is 4/4; T=1.5 W=4096 is 0/4). Reword the heading to “lock at T≤1.0.”

3. **S4 reuse.** `looping_rate_vs_T.meta.json` states W=4096 T∈{0.3,1.0} are reused S2.2 raw eight. The paper’s S4 section does not. Name the reuse; the 4/4 rates still hold.

4. **Figure 6 caption “same 28.”** F4 is n=20 domain (twins excluded); the table already says n=20, `n_within=9`. Inherit the sidecar’s “twin pairs are excluded.”

5. **Love stop-forced.** S5 non-blocking leftover: love s1 is the kept 1/2 row and is high-stop in Q3/Q4. Paper names 1/2 and that love is inside the ten F4 seeds. Naming the stop-forced register next to 1/2 would match S5; it is not required to unwrite a false claim.

6. **S1 STATUS FAILED** is true in [`CORE-ARM.md`](../stage-1/CORE-ARM.md), not in S1 `REPORT.md` (the same-line cite). Fact stands; retarget the comment if touching that paragraph.

7. **S1 plateau ≈0.147** matches S1 REPORT (bands 10–30). The figure meta’s `gap_post_horizon_mean` is 0.157. Both are closed aggregations; do not treat 0.147 as a new measurement.

8. **This VM’s ledger** in the gate print is `$9.027 of $50`. Closed S6/S7 reports are `$16.34 of $200`. Treat the paper’s spend as the closed-stage figure. Do not retune it from a gitignored partial ledger.

9. **S4 T=0.7** one physics replicate is degenerate via the late-Jaccard arm at looping_fraction 0.0465 (`looping_rate_vs_T.meta.json`). Collapsing T≤1.0 as 4/4 remains true. Naming that path is optional.

10. **Wu & Noé year.** `refs.bib` journal year 2020 vs related-work “J. Nonlinear Sci. 2019” is a volume-year vs online-first mismatch, not an invented author. Spot-check: Zekri (Zekri, Odonnat, Benechehab, Bleistein, Boullé, Redko) and Wang (Wang, Li, Yan, Cheng, Zhang) match the arXiv/ACL records. No Holtzman/Shumailov. No `LEAD`.

---

## Claims I judge supported

- **Lock is typical on this instruct process at T=0.3**, not on language models: S1 45/48 (24/24 at T=0.3); occupancy 19/20 domain and 10/10 domain seeds; love 1/2; S2 gemma 0/8 is the existence proof against a class claim.
- **H1 unsupported.** `validated=0` in every cell of `artifacts/stage-3/dynamics/k_stability.md`. `n_macro` is not an order parameter. Microstate currents are not H4.
- **H5 absent.** T≤1.0 both W 4/4 looping; T=1.5 W=4096 0/4; clean α only at T=1.5 and subdiffusive. Degenerate-row MSD α is not confined semantic motion (S1 α=0.244 / 0.350 labelled as such).
- **F4 last-band separated** in three spaces on the occupancy panel, under the pre-registered CI-excludes-0-from-above rule, with gemini 0.150 [0.029, 0.266] named as an NHST whisker, not thick robustness, not architecture-independence. Levels 0.201 / 0.390 / 0.150 disagree. Physics s1 last-band `D_within` NaN, `n_within_pairs=9`, named.
- **F6 operational collapsed** (CI includes 0), explicitly not occupancy of one lock. Waterloo gemini sign-flip 0.033 [0.001, 0.065] → −0.031 named; reactor never excluded 0. S5 waterloo `bge-m3` point Δ≈0.049 is not narrated as gemini’s.
- **Zekri is the unique-stationary null**, not a licence for several token-level stationary measures. Wang cycles and Ko & Geiping interlocutor attractors are not imported as findings about this P1 afterlife. No novelty claim for “attractors in LLMs” or “tracking embeddings over time.”
- **P1 vs sliding was not measured** (ADR-0017). Degeneracy is the sample (19/20). Thresholds 0.083 / 0.0122 unmoved. Fill/stop last quarter on `domain_20`: 0.853 [0.756, 0.936] / 0.359, named as a P1 confound. Gemini last-band matrix is pairwise distances, not a cluster count and not a 2-D projection used as evidence. Hosted S7 $0; `runs/s7/` absent.
- **Q1, Q3–Q8** in the PLAN: right as scored. Q2 right as *title vs subsection*; abstract still needs the reword in blocker 1.

---

## Claims I judge unsupported or overreaching

- Last-band occupancy “carries seed-domain identity” (abstract). Ensemble gap ≠ recovered memory.
- Three-space sign agreement as a co-headline with the lock, before the 0.029 whisker is the bound (abstract lead). Sign agreement belongs in §Stage 6, as Q2 registered.
- Occupancy as a result for “P1” without `raw_completion` and without the Alibaba pin.
- Any reading of F6 last-band CI∋0 as one shared lock (the paper does **not** make this claim; keep it that way).
- H1, H5, architecture-independence, lock-as-basin, `n_macro` as order parameter, language models as a class, P1 vs sliding, mixing times, macrostate currents (the paper does **not** establish these; keep the denials).

---

## Seven questions (manuscript)

| # | Question | Verdict |
| --- | --- | --- |
| 1 | Does the sentence follow? | **No** for abstract “identity” (blocker 1). Yes for the occupancy tables vs `domain_separation_last_band.csv` / `twin_last_band.csv` / `twin_per_band.csv`. |
| 2 | Thresholds calibrated? | **Yes.** 0.083 / 0.0122 unmoved. F4 = CI excludes 0 from above. F6 collapsed = CI includes 0, not an equivalence test. Not re-derived. |
| 3 | Measured in the applied regime? | **No** until `raw_completion` + Alibaba are named (blocker 2). S2 gemma 0/8, S4 T=1.5 0/4, S3 local W=256 are not sold as the occupancy result. |
| 4 | One instance? | **Yes, scoped.** One instruct generator for occupancy; S2 already falsifies universality of the lock. |
| 5 | Confounds named? | **Partial.** Degeneracy-as-sample, physics s1, love-inside-F4, provider non-determinism 60%, fill/stop, P1 vs sliding parked: named. Template and provider pin: missing (blocker 2). |
| 6 | Artifacts state what they cannot establish? | **Mostly.** Included-figure captions stay inside their `.meta.json` bounds except S1 “identity surviving” vs “not recoverable.” Paper §Limitations is specific on F2 items except recovered memory (blocker 1). |
| 7 | Negatives softened? | **No** on H1, H5, gemini whisker, F6 ≠ one lock. Geng “later onset” is the only hedge (non-blocking). |

---

## Gate (not a scientific fail)

```
plan.exists PASS
runs.complete FAIL   no /workspace/runs/s7   ← expected; ADR-0018
artifacts.bundle PASS
budget.reconciled PASS   (gate print on this VM: stage $0; do not relitigate $16.34)
report.diagnostics_segmented PASS
report.quotes_text PASS
report.scores_predictions PASS
literature.verified PASS
```
