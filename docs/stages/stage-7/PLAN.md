# Stage 7 — Can the manuscript be written from S0–S6 artifacts?

**Status.** Opened 2026-09-06 on branch `cursor/stage-7-6dce`, after
Stage 6 closed APPROVED WITH CHANGES (`ad1f244`). Decision:
[ADR-0018](../../decisions/ADR-0018-s7-manuscript-from-closed-stages.md).
No generate. No embed. `paper/main.tex` waits for an explicit
human yes after this PLAN is committed.

## 1. Question

Can a TMLR-shaped manuscript be assembled from the closed S0–S6
record without exceeding what those artifacts establish, including
the negatives?

This stage does **not** reopen occupancy, MSM, T=1.0, a second
generator, or P1 vs sliding. It does **not** treat a lock as a
basin. It does **not** treat last-band collapsed as occupancy of
one lock. It does **not** claim architecture-independence from
`gemini-embed-001`.

## 2. Entry state

From [Stage 6 REPORT](../stage-6/REPORT.md),
[Stage 6 REVIEW](../stage-6/REVIEW.md), [ADR-0018](../../decisions/ADR-0018-s7-manuscript-from-closed-stages.md):

- S0: protocol P1, no hosted base models, three usable embedders
  (bge-m3 dim 1024, qwen3-embed-8b dim 4096, gemini-embed-001 dim
  3072, all L2-normalised). Spend $0.0128.
- S1 PARTIAL: seed identity past the horizon, but 94% of
  trajectories froze.
- S2 PARTIAL: convergence is not universal; S1 reading is about
  `or-qwen3-8b` under P1.
- S3 PARTIAL: `validated_macrostates = 0`; H1 unsupported on this
  instruct-under-P1 sample.
- S4 APPROVED: T≤1.0 is 4/4 lock at both `W ∈ {4096, 8192}`; H5
  absent; T=1.5 is the only clean-`α` band and is subdiffusive.
- S5 APPROVED WITH CHANGES: ten domain seeds ensemble-
  distinguishable at last band (`bge-m3` 0.201 [0.065, 0.332];
  `qwen3-embed-8b` 0.390 [0.151, 0.593]); twins not last-band
  divergent; waterloo `bge-m3` point Δ stayed ~0.05.
- S6 APPROVED WITH CHANGES: same 28 trajectories, `gemini-embed-001`
  F4 0.150 [0.029, 0.266] (NHST whisker, physics s1 last-band NaN);
  F6 last-band Δ CIs include 0; waterloo gemini sign flip
  0.033 → −0.031. Hosted **$0**.
- Ledger **$16.34 of $200**. Kitchen-sink S6 arms parked (ADR-0017).

## 3. Experiment matrix

**Zero new trajectories. Zero new embeddings.** There is no
`configs/stages/stage7_*.yaml`. A YAML that lists generators would
print a generate estimate; that print is not a yes.

| # | Pass | Source | What it adds |
| --- | --- | --- | --- |
| S7.0 | Notes | `paper/notes/` | claim inventory, figure shortlist, limitations draft |
| S7.1 | Manuscript | `paper/main.tex` | after human yes on this PLAN |
| S7.2 | Reproducibility appendix | `paper/` | how to replay headline figures from `run_id`s |
| S7.3 | Artifact release check | `artifacts/stage-*/` | every included figure has tidy data + limitations |

Not in this opening: provider replication, chunk `{512,2048}`,
stride `S`, forced vs unforced, P1 vs sliding, T=1.0 occupancy,
T=1.5 residual, 200 seeds, a second generator, MSM / `n_macro`.

## 4. Computations

Ordered. No generate. No embed.

1. Inventory claims in `paper/notes/claims.md`. Each row: claim,
   stage, artifact path, `run_id`, allowed / forbidden in the
   paper.
2. Shortlist figures from `artifacts/stage-*/INDEX.md` into
   `paper/notes/figure-shortlist.md`. Do not redraw. PCA/UMAP
   stay labelled illustrations.
3. Draft limitations in `paper/notes/limitations.md` in the
   50-paper.mdc order, plus S5–S6 occupancy specifics (F4 whisker,
   physics s1, F6 ≠ one lock, closed gemini).
4. **Stop.** Commit the PLAN and notes. Do not write
   `paper/main.tex` until the human says yes.
5. After yes: assemble `paper/main.tex` from notes and artifacts.
   Every quantitative sentence carries a LaTeX comment with
   artifact path and `run_id`. Cite only `VERIFIED` literature.
6. `afterlife review --stage s7` once REPORT exists. A missing
   generate `run_id` is expected; do not mint one to green a
   runs.complete check.

## 5. Exit criteria

| # | Criterion | How it is scored |
| --- | --- | --- |
| F1 | **Traceable numbers** | every quantitative sentence in `paper/main.tex` has a same-line comment with artifact path and `run_id` |
| F2 | **Limitations specific** | names P1 vs sliding, one generator, closed gemini, n=2, degeneracy as sample, F4 whisker, physics s1 last-band NaN, F6 ≠ one lock |
| F3 | **H1 not supported** | the paper does not claim H1 established; S3 `validated_macrostates = 0` is stated |
| F4 | **H5 not present** | the paper does not claim a temperature confinement→diffusion transition; S4 grid is named |
| F5 | **No basin / `n_macro` / architecture-independence** | a lock is not a basin; `n_macro` is not an order parameter; gemini agreement is sign, not architecture-independence |
| F6 | **No LEAD citations** | manuscript cites only `VERIFIED` entries from `docs/literature/related-work.md` |
| F7 | **Figures from artifacts** | included figures are the committed `artifacts/` files, not redrawn |
| F8 | **Spend $0** | no new hosted generate or embed `run_id` |
| F9 | **No new generate** | `runs/s7/` empty or absent |
| F10 | **Notes before TeX** | `paper/notes/` committed before `paper/main.tex` exists |

## 6. Pre-registered predictions

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| Q1 | The paper can be assembled without a new generate `run_id` | 0.90 | |
| Q2 | Occupancy three-space sign agreement is a results subsection, not the title claim | 0.70 | |
| Q3 | The title/abstract will not say “metastable semantic states” as an established finding | 0.75 | |
| Q4 | Gemini F4 will be reported with the 0.029 whisker, not as thick robustness | 0.85 | |
| Q5 | F6 will be reported as operational collapsed, not occupancy of one lock | 0.85 | |
| Q6 | Related-work citations in the manuscript will all be `VERIFIED` | 0.80 | |
| Q7 | Hosted S7 spend is $0 | 0.95 | |
| Q8 | No `configs/stages/stage7_*.yaml` is added | 0.90 | |

## 7. Budget and wall-clock

**$0 API.** YAML refuse is not applicable (no stage YAML). Project
ceiling **$200**; remaining **$183.66**. Stop and ask before any
API call or any `paper/main.tex` commit.

Wall clock is writing, not generation. No 4 h embed watch.

## 8. Stage-specific risks

| Risk | Mitigation |
| --- | --- |
| Writing `paper/main.tex` before PLAN/notes | F10; this PLAN |
| Filling the 50-paper MSM/half-life outline anyway | ADR-0018; F3–F5 |
| Citing a `LEAD` identifier | F6; related-work status table |
| Selling gemini F4 as thick robustness | Q4; S6 REVIEW blockers |
| Selling F6 collapsed as one lock | Q5; S5/S6 law |
| Accidental generate to green `runs.complete` | F8–F9; HANDOFF |
| Redrawing figures for the paper | F7 |

## 9. Definition of done

- [x] `paper/notes/claims.md`, `figure-shortlist.md`, `limitations.md` committed
- [ ] Human yes on `paper/main.tex`
- [ ] `paper/main.tex` scores F1–F10
- [ ] `REPORT.md` scores Q1–Q8
- [ ] Hosted spend $0
- [ ] No `stage7_*.yaml`
