# Stage 6 review
Reviewer: scientific supervisor (via human)   Date: 2026-09-06
Gate: **FAIL on this reviewer VM** (`afterlife review --stage s6`, exit 1).
Cause: `runs/s6` is absent. Raw runs are git-ignored. Artifact bundles
on the committed record: 24/24 PASS (`artifacts.bundle`). Last CI on
`6e23fe3` is 6/6 green. Generate/embed hashes were not re-derived here.
The executor previously showed gate exit 0 on a machine that has
`runs/s6`. Literature WARN (1 LEAD citation) is not a blocker: this
stage does not write `paper/main.tex`. Same pattern as S3–S5.

Verdict: **APPROVED WITH CHANGES**

Do not merge from this review. Do not generate, re-embed, retune
0.083 / 0.0122, drop degenerate rows, headline `α` or `n_macro`,
call a lock a basin, call last-band collapsed occupancy of one lock,
or open T=1.0 / T=1.5 / 200 seeds / a second generator / MSM.
Stage close is `--no-ff` into `main` only after the sidecar/REPORT
prose changes below and the human says close.

---

## Answer to the stage question

On the same 28 `or-qwen3-8b` P1 trajectories Stage 5 used
(`W=4096`, T=0.3, 12 turnovers), the S5 occupancy *signs* hold in
`gemini-embed-001` under the pre-registered rules: F4 last-band
domain gap 0.150 [0.029, 0.266] excludes 0 (separated); F6 last-band
Δ CIs include 0 (operational collapsed) for pooled, reactor, and
waterloo. That is sign agreement with both S5 spaces, not
architecture-independence (gemini is closed), not recovered semantic
memory, and not occupancy of one lock.

Grid is 20 domain + 8 twin after `is_raw_lock_trajectory`, not the
16-trajectory S2.2 gemini parquet. Kitchen-sink arms were not opened.

---

## Blocking findings

1. **Claim.** F4 as “robustness” / three-space sign agreement sold
   without naming the interval’s thinness.
   [`domain_separation_last_band.meta.json`](../../../artifacts/stage-6/occupancy/domain_separation_last_band.meta.json),
   [`domain_gap_three_spaces.meta.json`](../../../artifacts/stage-6/occupancy/domain_gap_three_spaces.meta.json),
   REPORT §2 F4.

   **Problem.** Gemini last-band gap 0.150 [0.029, 0.266] on n=20,
   `n_within_pairs=9`. The lower bound 0.029 is an NHST whisker,
   closer to 0 than `bge-m3` 0.065. Reused S2.2 physics s1 has 47
   chunks vs 48; last-band `D_within` diagonal is NaN
   (`n_chunk_pairs=0`). Named in the S5 REPORT, missing from S6.
   Q1 remains **Right** against the pre-registered rule.

   **Resolve (reword, no new arm).** Rewrite those two sidecars’
   limitations to name the whisker, `n_within_pairs=9`, and physics
   s1. Put the physics s1 sentence back in REPORT §2. Do not
   generate. Do not add an extra arm.

2. **Claim.** F6 sidecar still narrates S5 `bge-m3` “point Δ stayed
   ~0.05.”
   [`twin_last_band.meta.json`](../../../artifacts/stage-6/occupancy/twin_last_band.meta.json)

   **Problem.** Gemini waterloo: band 0 Δ 0.033 [0.001, 0.065]
   (divergent on a 0.001 whisker) → band 12 −0.031 (sign flip; CI
   includes 0). The REPORT already says this; the sidecar does not.
   Collapsed ≠ one lock.

   **Resolve (reword, no new arm).** Rewrite limitations for the
   *gemini* alternative (sign-flipped point Δ; reactor never
   excluded 0). Extra replicates remain the price of *claiming
   sameness*, not of closing the stage once the sidecar matches
   the interval.

---

## Non-blocking observations

1. **Q5.** \|gemini−bge\|=0.0509 against an uncalibrated PLAN
   threshold `> 0.05` is arithmetically Right, not “gemini is not a
   copy of bge.” vs qwen 0.240 is the real level shift.

2. **F8.** Closed ≠ architecture-independence is already in REPORT
   prose.

3. **S2.2 surplus.** Assemble filter held: 20+8, not 16 traj.

---

## Claims I judge supported

- **F4 last-band sign in gemini**, same rule as S5: CI excludes 0.
  Q1 Right. Distinguishable ≠ recovered semantic memory.
- **F6 operational last-band collapsed** in gemini, families split.
  Q2/Q3 Right on the NHST rule. Not sameness.
- **F1 / F7 / F9 / F10.** No generate; thresholds unmoved; love s1
  kept; no basin / `n_macro` headline; hosted $0.
- **F8.** Gemini cannot alone prove architecture-independence.

## Claims I judge unsupported or overreaching

- Selling gemini F4 as thick “robustness” without the 0.029 whisker
  and physics s1 last-band dropout.
- Selling gemini F6 via the S5 `bge-m3` point-Δ≈0.05 story.
- Reading three-space sign agreement as architecture-independence.
- Opening T=1.0 / a second generator / MSM because the sign agreed.
