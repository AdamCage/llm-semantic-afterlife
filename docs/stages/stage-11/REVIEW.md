# Stage 11 review

Reviewer: Cursor Grok 4.7 (scientific supervisor)   Date: 2026-09-25
Gate: PASS (`afterlife review --stage s11`, exit 0; `.cache/review-s11.json`)
Verdict: **APPROVED WITH CHANGES**

One phrase blocker. No new `run_id`. Do not merge from this review.
Do not start S12. Do not pool with S9 Qwen or S10 OLMo. Do not
change F1 or `N_confirm=3`. Do not write `paper/main.tex`.

Re-ran the gate this review (2026-09-25): exit 0, one WARN
`runs.complete` on
`s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427`
(STATUS=FAILED, 0/40 empty completions). That is E2 PARTIAL, named
in the report, not a hole. Everything the gate checks is taken as
true.

---

## Answer to the stage question

On local Ministral 3 8B Base vs Instruct and local Gemma 4 12B Base
vs IT, P1 `raw_completion` / `serialization: raw_bytes`, `W=4096`,
`B=1024`, `T=49152`, T=0.3, **two estimands**, not pooled with S9
or S10:

1. **Persistence among completers.** Ministral last-band \(G_t\) is
   positive and the seed-cluster interval excludes 0 on both rungs
   in both spaces (BGE 0.138 [0.063, 0.158] and 0.150 [0.084,
   0.158]; Qwen-embed 0.240 [0.127, 0.272] and 0.224 [0.139,
   0.228]). The Instruct sign matches S9 Qwen Instruct (`+`).
   Magnitudes are not compared. Where that interval excludes 0,
   \(G_t>0\) is seed-conditioned separation of late registers /
   loop families, not recovered prompt memory. LOO point estimates
   stay positive in both spaces on both rungs (no seed flips the
   point). Gemma Base BGE is an identified **negative** (−0.011
   [−0.038, −0.006]); every LOO point stays negative. Gemma Base
   Qwen-embed is a point `+` whose interval includes 0 (0.014
   [−0.021, 0.019]): \(G_t>0\) is **not established**. Gemma IT
   last-band is unidentified (0 within, 0 between). The
   necessary-condition sentence is not licensed. The licensed
   sentence is *did not replicate in the Gemma condition*.

2. **Completion.** Ministral Base and Instruct are both 40/40.
   Empty-completion deaths are 0 and 0. That is neither the S9
   pattern nor the S10 pattern. Gemma Base is 38/40. Gemma IT is
   **0/40**, run `STATUS=FAILED`, empty completions, not OOM.
   Failed cells stay in the sample. They are not unlocks and they
   do not enter last-band \(G_t\).

P2 and P11 are false on the record. That is a successful stage.
Confirmed escape through 12W is 0/40 on Ministral Base, 4/40 on
Ministral Instruct (biology 1, programming 3), and 15/38 on Gemma
Base (9 of 10 seeds). The lock is not absorbing.

---

## Answers the executor marked as disputed

### 1. Is the identified BGE negative called a sign disagreement with the unestablished Qwen-embed?

**In the lede, no. In §2 and in the threat heading, yes. That
sentence does not follow.**

The lede states the two spaces separately: BGE interval excludes 0
on the negative side; Qwen-embed \(G_t>0\) is not established. It
does not say the signs disagree. Surprise 3 says the other space
does not establish the opposite sign. [`HANDOFF.md`](HANDOFF.md)
says this is not an established cross-space sign flip. P12 is
scored as the not-established case, not “true on the point.”

Two later sentences undo that care:

- §2: “Gemma Base itself does not agree across spaces.”
- §5 heading: “Gemma cross-space disagreement.”

P4 defines agreement on **identified** signs, and this project’s
establishment bit is `ci_excludes_0`, not the point glyph. Gemma
Base Qwen-embed has `sign=+` and `identified=True` in
[`gt_last_band.csv`](../../../artifacts/stage-11/gt_last_band/gt_last_band.csv)
because `identified` means finite \(G\) with between-pairs
([`scripts/s11_assemble.py`](../../../scripts/s11_assemble.py)),
while `ci_excludes_0=False`. Reading those glyphs as the two sides
of an agreement test is the S10 error (“positive where identified”
/ “true on the point”). Opposite point estimates are not a sign
disagreement. The body under the threat heading already says
\(G_t>0\) is not established; the heading names the disagreement
the body refuses.

The figure plots the pink Qwen bar next to the blue negative bar.
Its interval crosses 0, and
[`gt_last_band_figure.meta.json`](../../../artifacts/stage-11/gt_last_band_figure/gt_last_band_figure.meta.json)
already says a CI that includes 0 is not an established gap. The
figure does not need a rebuild for this blocker. The prose does.

### 2. Are confirmed escape and Gemma IT 0/40 softened?

**No.**

P11 is scored **false**, with Instruct 4/40 and Gemma Base 15/38.
P2 is scored **false**, both Ministral cells 0/40, and the report
says this is not an OLMo-style inversion either. “P2 and P11 are
wrong on the record” is the right register.

Gemma IT 0/40 is in the status line, the lede, the generate table,
E2 (**PARTIAL**), P8 (40/40), and the carry-forward. The run is
`STATUS=FAILED`. Last-band is unidentified, not a zero gap and not
a flip. Lock-table \(n=8\) (8/8 locked, 4 escapes, 5 seeds) is
named as deaths after `min_chunks=8` and before \(T=49152\), not
as a completer set. Those 4 IT escapes are correctly absent from
the P11 tally: P11 is escape **through 12W**. They are not hidden;
they are in the lock table with the denominator labelled
lock-table \(n\).

Gemma Base 15/38 is not in the first Gemma paragraph. It is in the
lock table, surprise 2 (“common”), and the sentence that the lock
is not absorbing. The count is plain. “Not a claim that the
process then settled” limits what an F1 exit is. It does not shrink
15/38.

---

## Blocking findings

1. **“Does not agree” / “cross-space disagreement” is not licensed
   for Gemma Base.** Claim: Gemma Base signs disagree across BGE-M3
   and Qwen-embed. Problem: only BGE has a sign whose interval
   excludes 0 (negative). Qwen-embed 0.014 [−0.021, 0.019] does not
   establish a sign. Agreement and disagreement are predicates on
   two established signs. **Resolves by rewrite, no new run.**
   Delete both phrases. Keep surprise 3’s sentence (“the other
   space does not establish the opposite sign”) as the only
   cross-space sentence. The replacement in §2 should say: BGE is
   an identified negative; the Qwen-embed sign is not established;
   cross-space sign agreement is not identified. Rename the §5
   heading so it does not say “disagreement.” Apply the same clause
   to the S11 one-liners in
   [`docs/research-plan.md`](../../research-plan.md) and
   [`docs/research-plan.ru.md`](../../research-plan.ru.md): BGE
   identified negative, Qwen-embed sign not established, IT 0/40.
   The Russian line currently cites only IT 0/40. Do not quote
   `sign=+` from the CSV where `ci_excludes_0` is false.

---

## Non-blocking observations

- Gemma Base last-band is the completer estimand. All 15 confirmed
  escapes in
  [`persistence_locks.csv`](../../../artifacts/stage-11/persistence/gemma-base-local-bge-m3/persistence_locks.csv)
  have \(\tau_{\mathrm{escape}}\le 10.5\), before band 12–13. The
  report does not claim the negative on the still-locked subset
  (23/38). Do not add that claim without a restricted \(G_t\).
  Ministral Instruct’s 4 escapes are also before the last band
  (\(\tau\in\{1.75,2\}\)) and the last-band gap there stays large
  and positive, so escape-before-the-band does not by itself
  manufacture a negative sign.
- The pink bar on `gt_last_band_figure` is easy to read as a small
  positive twin of the blue negative bar. The meta line already
  blocks that reading. A paper figure would need the “not
  established” mark on the panel, not only in `.meta.json`. Not
  this stage’s job.
- LOO for the four Ministral cells stays positive, and Gemma BGE
  LOO stays negative. The report relies on the intervals, which is
  the pre-registered rule. Citing the LOO direction in one clause
  would make the robustness visible; it is not required to license
  the claims above.

---

## Claims I judge supported

- Ministral completer last-band \(G_t>0\) in both spaces on both
  rungs; intervals exclude 0; Instruct sign matches S9 Qwen
  Instruct; magnitudes not pooled.
- Ministral completion is 40/40 on both rungs. P2 is false. This
  pair does not reproduce S9’s Base-worse completion or S10’s
  post-training collapse.
- Every Ministral lock-table trajectory locks (`N_confirm=3`).
  Confirmed escape through 12W is 0/40 Base and 4/40 Instruct. P11
  is false. The lock is not absorbing and not a semantic state.
- Gemma positive last-band gap did not replicate. The
  necessary-condition sentence about full attention is not used.
  No causal `sliding_window=1024` claim.
- Gemma Base BGE last-band is an identified negative. Same-seed
  pairs are farther apart than different-seed pairs **in that
  space**. LOO points stay negative.
- Gemma Base Qwen-embed \(G_t>0\) is not established.
- Gemma IT is 0/40 completers, `STATUS=FAILED`, empty completions,
  not OOM. Last-band unidentified. Lock-table \(n=8\) is not a 12W
  sample.
- Gemma Base confirmed escape 15/38, spread across 9 of 10 seeds,
  is an F1 surface-form exit, not a macrostate transition.
- Native-chat remains deferred. Families are not averaged.

## Claims I judge unsupported or overreaching

- “Gemma Base itself does not agree across spaces.”
- The heading “Gemma cross-space disagreement,” read as established
  opposite signs.
