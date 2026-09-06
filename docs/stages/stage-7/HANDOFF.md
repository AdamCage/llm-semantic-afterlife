# Stage 7 — handoff

Operational detail. The contract is [`PLAN.md`](PLAN.md).
Report: [`REPORT.md`](REPORT.md).

**Branch:** `cursor/stage-7-6dce` (from `main` `ad1f244`).
Human yes on `paper/main.tex` received 2026-09-06. Do not raise
ceilings. Do **not** `afterlife generate`. Do not mint `runs/s7`
to green `runs.complete`.

**Object.** Manuscript from S0–S6 artifacts. Headline: last-band
occupancy signs on `or-qwen3-8b` P1 after eviction, including a
gemini F4 NHST whisker. Not MSM. Not H5. Not architecture-
independence.

**Gate.** `afterlife review --stage s7` is expected to FAIL
`runs.complete` (no generate directory). That FAIL is not a
missing experiment. Scientific review of the *manuscript* is
[`REVIEW-BRIEF.md`](REVIEW-BRIEF.md): judge `paper/main.tex`, do
not mint `runs/s7`.

## Do not

- `afterlife generate` or `afterlife embed` for this stage
- Add `configs/stages/stage7_*.yaml`
- Headline H1, H5, `n_macro`, a lock-as-basin, or architecture-
  independence from gemini
- Call last-band collapsed occupancy of one lock
- Cite unverified literature
- Redraw figures; include from `artifacts/`
- Open T=1.0 / T=1.5 / 200 seeds / a second generator / MSM
- Merge S7 without scientific review

Scientific review: [`REVIEW.md`](REVIEW.md) (**APPROVED WITH
CHANGES**, 2026-09-06). Phrase blockers applied in `paper/main.tex`.
**Do not merge.** Close is a later human `--no-ff` into `main`.
Original assignment: [`REVIEW-BRIEF.md`](REVIEW-BRIEF.md).
