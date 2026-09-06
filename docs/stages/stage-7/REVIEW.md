# Stage 7 review
Reviewer: Cursor Grok 4.6 (scientific supervisor)   Date: 2026-09-06
Gate: **FAIL** `runs.complete` (`afterlife review --stage s7`, exit 1).
Cause: no `runs/s7/`. Expected for a writing stage (ADR-0018). Do not
mint a dummy generate directory. Other brief checks PASS:
`plan.exists`, `artifacts.bundle`, `budget.reconciled` (stage $0.00;
project $16.34 of $200), `report.diagnostics_segmented`,
`report.quotes_text`, `report.scores_predictions`,
`literature.verified`. Occupancy CIs were **not** recalculated.

Verdict: **APPROVED** (re-verified 2026-09-06 after reword;
original blockers closed). First pass was **APPROVED WITH CHANGES**.

Do not merge from this review. Do not generate, embed, retune
0.083 / 0.0122, drop degenerate rows, headline H1, H5, a lock-as-basin,
architecture-independence, one lock, or “language models as a class.”
Stage close is `--no-ff` into `main` only after the human says close.

---

## Answer to the stage question

A TMLR-shaped manuscript can be assembled from the closed S0–S6
record without selling H1, H5, architecture-independence, one lock, a
basin, or language models as a class. After the 2026-09-06 reword
(`25e7f70`), occupancy sentences match those artifacts, including the
negatives. The two blockers were overclaimed sentences, not missing
measurements, and both are closed.

---

## Re-verification (2026-09-06, after `25e7f70`)

Checked `origin/cursor/stage-7-6dce` at `9fbfa87` against the two
blockers. No new generate/embed. Occupancy CIs not re-bootstrapped.
Lexical tests `test_abstract_f4_is_domain_gap_not_recovered_memory`
and `test_occupancy_protocol_names_raw_completion_and_alibaba` added
by the executor; they encode the blockers, they do not replace this
judgement.

**Blocker 1 — closed.** Abstract no longer says occupancy “carries
seed-domain identity.” It states an ensemble domain gap (F4
distinguishability) and that the gap is not recovered prompt memory
(H2). Three-space language no longer precedes the whisker sentence.
Intro, S5, and Discussion repeat distinguishability ≠ H2. Hunt-list
items (H1, H5, architecture-independence, one lock, basin, LMs as a
class) remain denied.

**Blocker 2 — closed.** §Protocol names served provider Alibaba and
continuation mechanism `raw_completion`, distinct from P1 (glossary).
Limitations repeats P1 + `raw_completion` + Alibaba and that they are
not synonyms. Prefill vs raw is cited as a Stage 2 arm, not as the
occupancy protocol. P1 vs sliding remains unmeasured.

**Residual, not blocking.** Figure 1 caption still says “seed-family
identity surviving the horizon” on the degenerate-majority S1 panel.
That is the registered S1 E1 wording (`paper/notes/claims.md` allowed
list), not the occupancy F4 overclaim. Optional: inherit
`seed_separation.meta.json` “not that the information is recoverable.”
Geng “later onset,” S4 heading “lock until T=1.5,” and F4 caption
“same 28” (twins excluded in the table) are unchanged non-blocking
nits.

---

## What follows from the artifacts

Copied numbers match the closed occupancy tables (not re-derived here):

- F4 last-band gaps **0.201 / 0.390 / 0.150**; gemini
  **[0.029, 0.266]**
  ([`domain_separation_last_band.csv`](../../../artifacts/stage-6/occupancy/domain_separation_last_band.csv)).
- F6 last-band CIs include 0
  ([`twin_last_band.csv`](../../../artifacts/stage-6/occupancy/twin_last_band.csv)).
- Waterloo gemini **0.033 → −0.031**
  ([`twin_per_band.csv`](../../../artifacts/stage-6/occupancy/twin_per_band.csv)).

Negations already in the manuscript: `validated=0`; H5 absent;
`or-gemma-4-31b` 0/8; F6 ≠ one lock; thresholds **0.083 / 0.0122**
unmoved; F4 is not H2.

---

## Blocking findings

None remaining. Original blockers (kept for the record):

1. **Claim (closed).** Abstract: “last-band occupancy still carries
   seed-domain identity in three embedding spaces.” Reworded to
   ensemble domain gap + explicit “not recovered prompt memory (H2).”

2. **Claim (closed).** Occupancy named as `or-qwen3-8b` + P1 without
   `raw_completion` and without the Alibaba pin. Named in §Protocol
   and §Limitations.

---

## Non-blocking observations

1. Intro occupancy sentence was tightened in the same pass as blocker
   1 (distinguishability, not H2; whisker in the same paragraph).
2. Body tables and S5/S6 sections still use “domain gap,” “NHST
   whisker,” and “operational collapsed ≠ one lock.” Do not relitigate
   those numbers.
3. Gate FAIL `runs.complete` remains expected. Do not mint `runs/s7`.
4. S1 figure caption may still inherit “not recoverable” from its
   `.meta.json`; not required to close the occupancy identity blocker.
5. Optional nits unchanged: Geng “later onset”; S4 heading “until
   T=1.5”; F4 three-space caption “same 28” while the test is n=20
   (twins excluded).

---

## Claims I judge supported

- A TMLR-shaped paper from closed S0–S6 is possible on the present
  wording.
- Textual lock as the typical $T{=}0.3$ occupancy outcome on
  `or-qwen3-8b` (19/20 domain trajectories; love 1/2 kept).
- F4 last-band ensemble domain gap, CI excludes 0 from above, in
  `bge-m3`, `qwen3-embed-8b`, and `gemini-embed-001`, with gemini as
  an NHST whisker — as a *results subsection*, not recovered memory
  and not a title claim of architecture-independence.
- F6 last-band operational collapsed (CI includes 0), not occupancy
  of one lock; waterloo gemini sign-flip 0.033 → −0.031.
- Occupancy regime is `or-qwen3-8b`, P1, `raw_completion`, Alibaba,
  T=0.3, W=4096, 12 turnovers.
- H1 unsupported (`validated=0`). H5 absent. `or-gemma-4-31b` 0/8.
- Degeneracy is the sample; thresholds 0.083 / 0.0122 unmoved.
- Hosted Stage 7 spend $0; no `stage7_*.yaml`; no `runs/s7`.

## Claims I judge unsupported or overreaching

These remain unsupported; the reword no longer asserts them:

- Last-band occupancy as recovered prompt memory (H2).
- Three-space occupancy as a headline before the 0.029 whisker, or as
  architecture-independence.
- Occupancy protocol = P1 without `raw_completion` and without the
  Alibaba pin.
- H1, H5, one lock, a basin, `n_macro` as an order parameter, or
  language models as a class.

---

## Seven questions (after reword)

| # | Question | Verdict |
| --- | --- | --- |
| 1 | Does the sentence follow? | **Yes** for F4 as ensemble gap; identity language removed. |
| 2 | Thresholds calibrated? | **Yes.** 0.083 / 0.0122 unmoved. F4/F6 operational rules unchanged. |
| 3 | Measured in the applied regime? | **Yes.** `raw_completion` + Alibaba named. Other regimes not sold as occupancy. |
| 4 | One instance? | **Yes, scoped.** |
| 5 | Confounds named? | **Yes** on the occupancy pin/mechanism. |
| 6 | Artifacts state what they cannot establish? | **Yes** for occupancy figures. S1 caption still uses E1 “identity” language (non-blocking). |
| 7 | Negatives softened? | **No** on H1, H5, whisker, F6 ≠ one lock, H2. |
