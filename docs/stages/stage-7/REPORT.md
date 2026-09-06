# Stage 7 report — manuscript from S0–S6 artifacts

**Status.** Closed 2026-09-06. Overall verdict: **PASS** on the
writing contract (F1–F10). Mechanical `afterlife review --stage s7`
**FAIL**s `runs.complete` by design (ADR-0018; no generate
`run_id`). Do not mint `runs/s7` to green that check.

Scientific review 2026-09-06: **APPROVED WITH CHANGES**
([`REVIEW.md`](REVIEW.md)). Two phrase blockers applied in
`paper/main.tex` (F4 = ensemble domain gap, not H2; occupancy names
`raw_completion` + Alibaba). No new `run_id`. Human authorised
`--no-ff` close.

Human yes on `paper/main.tex` received 2026-09-06. Branch:
`cursor/stage-7-6dce`. Plan: [`PLAN.md`](PLAN.md). Decision:
[ADR-0018](../../decisions/ADR-0018-s7-manuscript-from-closed-stages.md).

Hosted Stage 7 spend **$0**. No `configs/stages/stage7_*.yaml`.

---

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| F1 | Traceable numbers | **PASS** | every quantitative sentence in [`paper/main.tex`](../../../paper/main.tex) has a same-line `% artifacts/` or `% docs/stages` comment with a `run_id`; `tests/test_paper_manuscript.py` |
| F2 | Limitations specific | **PASS** | `paper/main.tex` §Limitations names P1 vs sliding, `raw_completion` + Alibaba pin, one generator, closed gemini, n=2, degeneracy as sample, F4 whisker, physics s1 last-band NaN, F6 ≠ one lock |
| F3 | H1 not supported | **PASS** | paper states H1 unsupported; `validated=0` from [`k_stability.md`](../../../artifacts/stage-3/dynamics/k_stability.md) |
| F4 | H5 not present | **PASS** | paper states H5 absent; [`clean_alpha_by_cell.csv`](../../../artifacts/stage-4/grid/clean_alpha_by_cell.csv) |
| F5 | No basin / `n_macro` / architecture-independence | **PASS** | lock is not a basin; `n_macro` is not an order parameter; gemini is sign agreement, not architecture-independence |
| F6 | No LEAD citations | **PASS** | `docs/literature/related-work.md` has zero `` `LEAD` ``; `paper/refs.bib` is VERIFIED-only |
| F7 | Figures from artifacts | **PASS** | `\includegraphics` paths under `artifacts/`; inventory [`figure_inventory.csv`](../../../artifacts/stage-7/manuscript/figure_inventory.csv) |
| F8 | Spend $0 | **PASS** | no S7 generate/embed `run_id`; ledger prefix `s7` empty |
| F9 | No new generate | **PASS** | `runs/s7/` absent; no stage7 YAML |
| F10 | Notes before TeX | **PASS** | `paper/notes/` committed at `a3ae248` before `paper/main.tex` |

---

## 2. Results

The manuscript exists at [`paper/main.tex`](../../../paper/main.tex)
with [`paper/refs.bib`](../../../paper/refs.bib). Title: *Semantic
Afterlife: Lock Occupancy After the Prompt Leaves the Window*.
Occupancy three-space sign agreement is a results subsection
(§Stage 6), not the title claim.

Headline numbers are copied, not re-derived. Gemini last-band F4
remains **0.150 [0.029, 0.266]**
([`domain_separation_last_band.csv`](../../../artifacts/stage-6/occupancy/domain_separation_last_band.csv);
`s6-embed-third-space-20260906T082301Z-588eff8f`).
F6 last-band Δ CIs include 0. Waterloo gemini sign-flips
**0.033 → −0.031**.

Included figures (not redrawn):

- `artifacts/stage-1/separation-bge-m3/seed_separation.png`
- `artifacts/stage-4/grid/looping_rate_vs_T.pdf`
- `artifacts/stage-4/grid/clean_alpha_vs_T.pdf`
- `artifacts/stage-5/occupancy/domain_separation_vs_turnover.pdf`
- `artifacts/stage-6/occupancy/domain_gap_three_spaces.pdf`
- `artifacts/stage-6/occupancy/twin_delta_vs_turnover.pdf`
- `artifacts/stage-6/occupancy/last_band_distance_matrix_gemini_embed_001.pdf`

Stage 2 rate panel is SVG-only; the paper uses the CSV table.

### Protocol diagnostics (inherited; no S7 generation)

There is no S7 generate run, so block fill and stop rate are the
occupancy panel's last quarter, not a new measurement. Domain
trajectories (`domain_20`), **final quarter**: mean block fill
**0.853** 95% CI **[0.756, 0.936]**; mean stop rate **0.359**
([`protocol_by_quarter.csv`](../../../artifacts/stage-5/occupancy/protocol_by_quarter.csv);
`s5-lock-occupancy-20260905T164327Z-6780902f`).
Quarters 1–3 on the same slice: fill 0.782 / 0.831 / 0.813, stop
0.472 / 0.414 / 0.430. P1 fill is named in the paper as a confound,
not as a sliding-window measurement.

### Surface form the occupancy lock actually writes

The manuscript's object is a lock, not a basin. Last-chunk heads
from the occupancy panel (`s5-lock-occupancy-20260905T164327Z-6780902f`,
[`late_chunk_quotes.md`](../../../artifacts/stage-5/occupancy/late_chunk_quotes.md)):

> I'd like to proceed! I'm here to help you turn your insights into a **compelling, well-structured, and professionally formatted deliverable**.

> Thank you for your **thoughtful and detailed summary**! It is indeed a **masterful distillation** of a complex and deeply philosophical discussion on **personal identity**

> hinge water hinge water / the numeral again seventeen / kettle furlong azimuth

Those three registers (assistant-reviewer on finance and philosophy;
noise still in the assistant wrapping a nonsense score) are why
degeneracy is the sample.

---

## 3. Prediction vs outcome

| # | Prediction | Observed | Score |
| --- | --- | --- | --- |
| Q1 | The paper can be assembled without a new generate `run_id` | `paper/main.tex` exists; `runs/s7/` absent | **right** |
| Q2 | Occupancy three-space sign agreement is a results subsection, not the title claim | Title is lock occupancy after eviction; gemini is §Stage 6 | **right** |
| Q3 | Title/abstract will not say “metastable semantic states” as an established finding | Absent from title/abstract; S3 named as `validated=0` | **right** |
| Q4 | Gemini F4 will be reported with the 0.029 whisker, not as thick robustness | Table F4; “NHST whisker”; “not thick robustness” | **right** |
| Q5 | F6 will be reported as operational collapsed, not occupancy of one lock | Table F6 caption and limitations | **right** |
| Q6 | Related-work citations in the manuscript will all be `VERIFIED` | Seven citations; legend no longer uses `` `LEAD` `` | **right** |
| Q7 | Hosted S7 spend is $0 | No S7 ledger rows | **right** |
| Q8 | No `configs/stages/stage7_*.yaml` is added | glob empty | **right** |

No pre-registered prediction was wrong.

---

## 4. Surprises

- Scientific review (2026-09-06) was **APPROVED WITH CHANGES** on
  two sentences, not on the occupancy numbers. Abstract sold F4 as
  seed-domain identity in three spaces; protocol named P1 without
  `raw_completion` / Alibaba. Both closed by reword. No new
  `run_id`.
- The generate-oriented review gate (`runs.complete`) cannot pass a
  writing stage without a dummy run. That is a tooling mismatch,
  not a missing experiment. ADR-0018 already forbade minting one.
- Related-work's status table used the token `` `LEAD` `` in the
  legend. With `paper/main.tex` present, `check_no_unverified_citations`
  counts that string and would FAIL. The legend now says
  “unverified” in plain text; no unverified paper is cited.
- Stage 2's committed rate figure is SVG-only
  (`rates/fixed_point_rate.svg`). The paper uses the CSV table
  rather than inventing a PNG.

---

## 5. Threats to validity

| Threat | State |
| --- | --- |
| Same-line comments miss a number | lexical test `test_quantitative_lines_have_same_line_comments`; remaining risk is a qualitative sentence that smuggles a quantity in words |
| Bibliography author invention | authors checked against arXiv/ACL records named in related-work |
| Gate FAIL `runs.complete` misread as “stage not done” | this report: expected; do not mint `runs/s7` |
| Title still contains “Semantic Afterlife” while occupancy is the measured object | Q2 scored on subsection vs title *claim*; the working title is retained with an honest abstract |
| No `pdflatex` in the default agent image | source + path tests; compile is documented in `paper/README.md` |
| Author line | GitHub owner display name Adam Cage; no invented affiliation |

---

## 6. Cost actuals vs estimate

| item | estimate | actual | `run_id` |
| --- | ---: | ---: | --- |
| S7 generate | $0 | **$0** | none |
| S7 embed | $0 | **$0** | none |
| **new hosted** | **$0** | **$0** | — |

Project ledger remains **$16.34 of $200** (Stage 6 close). YAML
refuse is not applicable (no stage YAML).

---

## 7. Implications for the plan

- Planned stages S0–S7 are complete. There is no S8 in this plan.
  Venue submission, Zenodo, and parked arms are not a stage.
- `afterlife review --stage s7` remaining FAIL is `runs.complete`.
  That check assumes a generate directory. The writing-stage
  exception is ADR-0018; do not mint `runs/s7`.
- Parked arms stay parked (ADR-0017): T=1.0 occupancy, T=1.5
  residual, second generator, P1 vs sliding, MSM.
