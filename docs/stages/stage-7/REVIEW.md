# Stage 7 review
Reviewer: scientific supervisor (via human)   Date: 2026-09-06
Gate: **FAIL** `runs.complete` (`afterlife review --stage s7`, exit 1).
Cause: no `runs/s7/`. Expected for a writing stage (ADR-0018). Do not
mint a dummy generate directory. Other brief checks PASS:
`plan.exists`, `artifacts.bundle`, `budget.reconciled` (stage $0.00;
project $16.34 of $200), `report.diagnostics_segmented`,
`report.quotes_text`, `report.scores_predictions`,
`literature.verified`. Occupancy CIs were **not** recalculated.

Verdict: **APPROVED WITH CHANGES**

Do not merge from this review. Do not generate, embed, retune
0.083 / 0.0122, drop degenerate rows, headline H1, H5, a lock-as-basin,
architecture-independence, one lock, or “language models as a class.”
The two blockers close by **rewording phrases only**. No new `run_id`.
Stage close is `--no-ff` into `main` only after the human says close.

---

## Answer to the stage question

A TMLR-shaped manuscript can be assembled from the closed S0–S6
record without selling H1, H5, architecture-independence, one lock, a
basin, or language models as a class. The numbers in the tables match
the closed CSVs. The two blockers are overclaimed *sentences*, not
missing measurements.

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
unmoved.

---

## Blocking findings

1. **Claim.** Abstract: “last-band occupancy still carries seed-domain
   identity in three embedding spaces.”
   (`paper/main.tex` abstract.)

   **Problem.** F4 is an *ensemble last-band domain gap* (CI excludes 0
   from above), not recovered memory. Stages 5 and 6 and ADR-0018 already
   closed that reading. Three embedding spaces must not lead the
   abstract before the gemini whisker **0.029**. Distinguishable ≠
   recovered prompt memory (H2).

   **Resolve (reword, no new `run_id`).** Replace identity language
   with ensemble distinguishability / domain gap. State explicitly that
   F4 is not recovered prompt memory (H2). Keep the following sentence
   that the third space is an NHST whisker, not architecture-independent
   robustness. Same-line `% artifacts/… @ run_id` comments stay.

2. **Claim.** Occupancy is named as `or-qwen3-8b` + P1, without
   `raw_completion` and without the Alibaba pin.
   (`paper/main.tex` §Protocol “Generator, window, and P1”; also the
   one-generator Limitations paragraph.)

   **Problem.** In the glossary, P1 (re-prompt: send `Tail_W` as a
   fresh prompt) and continuation mechanism (`raw_completion` /
   `assistant_prefill` / `chat_instructed`) are different axes. Stage 2
   already measured prefill versus raw (7/8 vs 8/8, CI includes 0).
   Occupancy generation was P1 **and** `raw_completion`, served
   provider **Alibaba** on every completed step. Omitting the mechanism
   and pin lets a reader treat P1 as the occupancy protocol in full.

   **Resolve (reword, no new `run_id`).** Name `raw_completion` and the
   Alibaba pin in the protocol subsection and in Limitations. Do not
   imply that P1 versus sliding was measured. Do not imply that prefill
   is the occupancy protocol.

---

## Non-blocking observations

1. Intro “occupancy signs hold in three embedding spaces” is closer to
   the allowed claim than the abstract’s “identity,” but should not be
   read as recovered memory either. The executor may tighten it in the
   same pass as blocker 1.
2. Body tables and S5/S6 sections already use “domain gap,” “NHST
   whisker,” and “operational collapsed ≠ one lock.” Do not relitigate
   those numbers.
3. Gate FAIL `runs.complete` remains expected after the rewords. Do
   not mint `runs/s7`.

---

## Claims I judge supported

- A TMLR-shaped paper from closed S0–S6 is possible on this wording
  contract, once the two blockers are reworded.
- Textual lock as the typical $T{=}0.3$ occupancy outcome on
  `or-qwen3-8b` (19/20 domain trajectories; love 1/2 kept).
- F4 last-band ensemble domain gap, CI excludes 0 from above, in
  `bge-m3`, `qwen3-embed-8b`, and `gemini-embed-001`, with gemini as
  an NHST whisker — as a *results subsection*, not a title claim.
- F6 last-band operational collapsed (CI includes 0), not occupancy
  of one lock; waterloo gemini sign-flip 0.033 → −0.031.
- H1 unsupported (`validated=0`). H5 absent. `or-gemma-4-31b` 0/8.
- Degeneracy is the sample; thresholds 0.083 / 0.0122 unmoved.
- Hosted Stage 7 spend $0; no `stage7_*.yaml`; no `runs/s7`.

## Claims I judge unsupported or overreaching

- Last-band occupancy “carries seed-domain identity” / recovered
  prompt memory (H2).
- Three-space occupancy as a headline before the 0.029 whisker, or as
  architecture-independence.
- Occupancy protocol = P1 without `raw_completion` and without the
  Alibaba pin.
- H1, H5, one lock, a basin, `n_macro` as an order parameter, or
  language models as a class.
