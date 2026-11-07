# Stage 12 review

Reviewer: Cursor Grok 4.7 (scientific supervisor)   Date: 2026-11-07
Gate: PASS (`afterlife review --stage s12`, exit 0; `.cache/review-s12.json`)
Verdict: **APPROVED WITH CHANGES**

The pre-registered count stands: 0/8 confirmed escapes through
\(T_{\min}\). The automated report's clock sentence does not, and the
result paragraph can be quoted without the cohort that makes 0/8
mean anything. Reword only. No new `run_id`. Do not merge from this
review. Do not start S13. Do not open L1 or L2-persistence-to-lock.
Do not retune F1 or `N_confirm`. Do not regenerate. Do not write
`paper/main.tex`.

Gate re-run this review (2026-11-07): exit 0. Plan, 16 completed
runs, output hashes, artifact bundle, budget, and the report's own
score sheet are taken as settled. The judgement below is the part
the gate does not decide.

---

## Answer to the stage question

On the eight pre-registered continuations (Ministral 3 8B Base NF4
and Qwen3 8B Instruct NF4; seeds `physics` and `love`; L0 descendants
`s1` and `s2`; \(W=4096\), \(B=1024\), temperature 0.3, `top_p=1`,
P1 `raw_bytes` reprompt, local), **no cell has a confirmed escape
through 4,999,168 original generated tokens**.

That token count is 1220.5 turnovers from the first L0 token. The
lock event is at 0.75 on that same axis. Time from the lock to the
censor point is 1219.75 turnovers. \(\tau_{\mathrm{escape}}\) is
blank on every row and `censored` is true on every row. The required
phrase is *no confirmed escape through \(T\)*. The report uses it.
The report and `artifacts/stage-12/` do not call the lock absorbing.
Leave that wording. Do not upgrade 0/8 into a permanence claim.

The concatenation is the one the plan specified. L0 chunk turnovers
for these eight ids run 0.25 through 12.0 (48 chunks, 49,152 tokens).
Continuation chunk turnovers run 0.25 through 1208.5 and are shifted
by +12 before `prefix_lock_escape`. The joined grid has no shared
turnover: L0 ends at 12.0, the continuation begins at 12.25. Both
sides are looping on every chunk (L0 48/48, continuation 4834/4834,
max non-looping run 0). A boundary error in the shift cannot create
or hide an escape in this cohort.

`N_confirm=3` and the frozen 3-gram cut 0.083 do not decide the
count. The same chunk-row counter as L0 is in force (three chunks of
1024 tokens, 0.75\(W\)). The longest non-looping run on either side
of the join is 0. The lowest continuation 3-gram repetition is
0.9378 (`qi-physics-s1`); the other seven minima lie between 0.9528
and 0.9906. Within each continuation the rate is flat. The result
would survive any cut from the frozen 0.083 up to that minimum, and
any confirmation window of one or more chunks.

Each continuation prompt is a full window: `seed_tokens=4096` on all
eight manifests, `eviction_start_tokens=0`, and
`prompt_tokens_total=19,800,064` \(= 4834 \times 4096\). Every
completed step finished `length`. Chunks with continuation turnover
\(> 1\) are text generated after that tail had left the window, and
those chunks are looping through turnover 1208.5. The 0/8 result is
not the tail still sitting in the prompt.

P1 (a majority have no confirmed escape) is true at 8/8. That score
is the prediction, stated as a count, not a softened failure. P2
(reasoning tokens 0) and P3 (no empty-completion death relabelled as
escape) match the table. P4 stays closed, which is what was
pre-registered.

---

## Blocking findings

1. **Claim.** §2: "Clock origin is the L0 lock at 0.75 turnover",
   in the same sentence group as \(T_{\min} = 4999168\) tokens
   (1220.5000 turnovers). The caption in
   `artifacts/stage-12/tau_escape/tau_escape.meta.json` says
   "tau_escape on the L0 clock (lock at 0.75 turnover, horizon 12.0)".

   **Problem.** The numbers are absolute generated tokens from the
   first L0 token. `scripts/s12_tau.py` shifts continuation turnovers
   by the L0 horizon 12, and `tests/test_s12_tau_clock.py` expects
   an escape at absolute turnover 12.75 when the lock is at 0.75.
   ADR-0025 defines \(\tau_{\mathrm{escape}}\) as time from the
   confirmed lock. The implementation stores the absolute turnover.
   With every \(\tau\) blank, 0/8 does not flip. The sentence still
   labels 1220.5 as if it were time since the lock. It is 1219.75
   turnovers after the lock (4,996,096 tokens). HANDOFF's operational
   line is the one the code follows: L0 49,152 plus the additional
   tokens.

   **Resolve (reword, no new `run_id`).** In §2 and in the artifact
   caption, one axis sentence: absolute turnovers from L0 token 0;
   lock at 0.75; L0 series ends at 12.0; continuation series is
   joined at 12.25 through 1220.5; censoring time 1220.5 absolute,
   which is 1219.75 after the lock. Delete the claim that the origin
   is the lock. If `scripts/s12_research.py` is re-run, change that
   string in the script in the same edit. A re-run of the script
   restores the false sentence. Do not recompute the flags.

2. **Claim.** §2 and the meta limitations: \(T_{\min}\) is "the
   shortest cell", and a later escape on a longer cell is censored.

   **Problem.** All eight rows have `absolute_tokens=4999168`.
   Nothing in this cohort was observed past another cell, and no cell
   was cut early. Right-censoring is still the correct word for an
   escape time that was not observed by the common stop. The
   "shortest cell" sentence describes a race this cohort did not have.

   **Resolve (reword, no new `run_id`).** Say every cell reached the
   same target, so \(T_{\min}\) equals each cell's length. Keep
   `censored=True`. E2 can stay PASS: one common \(T\) was used.

3. **Claim.** §2's 0/8 sentence, read on its own, and the
   limitations line of `tau_escape.meta.json`.

   **Problem.** §5 names the real alternatives: P1 reprompt rather
   than native sliding attention, F1 as a surface 3-gram flag,
   separate degeneracy runs joined by the turnover clock, no
   re-measurement of provider non-determinism, families not pooled.
   The quotable paragraph and the artifact limitations do not. The
   limitations line says the table is not a last-band \(G_t\) and
   not a permanent lock, then restates censoring and
   `N_confirm=3`. A limitations line that restates the caption is
   not one. It has to name the alternatives this table does not
   exclude. Two further facts the report never states, both required
   before 0/8 is lifted: `physics` and `love` are the F3 domain-order
   picks after every qualifying seed tied at \(\tau_{\mathrm{lock}}=0.75\),
   not a contrast of semantic domains; `s1` and `s2` are two L0
   descendants, each continued with one new draw (`stochastic_seeds:
   [1]`), not two draws of one tail. Text samples are early/middle/late
   of `mb-physics-s1` and `mb-physics-s2` only (`quotes[:6]` in
   `scripts/s12_research.py`). Six cells have no prose in the report.

   **Resolve (reword, no new `run_id`).** Put the scope in the §2
   result sentence and in the meta limitations, in words a paper
   could lift without §5 open beside it:

   - P1 reprompt, `raw_bytes`, local NF4. Native sliding attention
     was not measured.
   - The label is the F1 chunk looping flag. Embedding geometry was
     not run. A surface loop leaves semantic change unmeasured.
   - Eight cells only. Ministral 3 8B Base NF4 and Qwen3 8B Instruct
     NF4, temperature 0.3, \(W=4096\). Families are counted, not
     pooled into a rate.
   - Seeds are the F3 tie-break (`physics`, then the domain-order
     median `love`). Descendants `s1`, `s2`. One new stochastic draw
     per tail.
   - State the per-cell fact the blank \(\tau\) hides: 4834/4834
     continuation chunks looping, max non-looping run 0, minimum
     3-gram repetition 0.9378 on `qi-physics-s1` and at least 0.9528
     on the other seven. Label the printed quotes as Ministral
     physics only, or add one short quote per cell. Do not retune
     the cut.

4. **Claim.** E7's evidence line, "same classifier as the L0
   degeneracy runs", is operationally true and easy to misread as
   three integer windows of \(W\).

   **Problem.** `prefix_lock_escape` counts consecutive chunk rows,
   which is what L0's persistence pass does. Three rows are 0.75\(W\),
   the floor already named in the Stage 9 review. ADR-0023's word
   "turnovers" is that pre-existing name. Here the distinction is
   idle, because the non-looping run is 0, so a 3-chunk rule and a
   3-window rule agree. A reader of the blank \(\tau\) column can
   still think a shorter break was ignored.

   **Resolve (reword, no new `run_id`).** In §2, say the counter is
   the unchanged L0 chunk-row rule, and that the run length of
   non-looping chunks is 0 on every joined series. Do not
   re-aggregate to integer turnovers. Do not change `N_confirm`.

---

## Non-blocking observations

- §4 is the script's template ("the measured escape count is the
  surprise column"). It does not hedge 0/8. Replace it with the
  actual observation: the continuations are flat loops, not
  near-misses at `N_confirm`. Optional once finding 3 is in §2.
- `artifacts/stage-12/degeneracy/` is the last single-run export
  (`qi-love-s2` only). Its 50% post-horizon trajectory rule is the
  degeneracy verdict, not the escape rule. The confirmatory artifact
  is `artifacts/stage-12/tau_escape/`. Do not cite the one-row file
  as the cohort.
- L0 Qwen `physics` s1 and `love` s2 sit closer to the cut than the
  continuations do (L0 minimum 3-gram repetition 0.2697 and 0.6113,
  both still above 0.083, zero non-looping chunks). The long run did
  not walk back toward 0.083. That is descriptive. It is not a new
  estimand.
- Provider non-determinism on this horizon is already named in §5.
  Leave it. Repetition penalty in the resolved configs is null; the
  loop is not a penalty artifact. No need to add a run for that.
- There is no `artifacts/stage-12/INDEX.md`. The gate accepted the
  bundle. Do not invent an index as a condition of this verdict.

---

## Claims I judge supported

- 0/8 confirmed escape through 4,999,168 original tokens, right-censored
  at that common completed horizon, under the unchanged F1 chunk-row
  rule. The phrase *no confirmed escape through \(T\)* is the right
  strength. Do not relitigate the count.
- The join is L0 flags from
  `s11-degeneracy-20260923T051706Z-81df16d2` (Ministral Base) and
  `s9-degeneracy-20260915T052651Z-cde06a72` (Qwen Instruct), plus the
  eight `s12-degeneracy-20261106T*` continuation runs named in
  `tau_escape.meta.json`, shifted by 12 turnovers. One trajectory per
  continuation parquet. No turnover overlap.
- The measurement is in the regime it is applied to: full \(W=4096\)
  tail, every step a 4096-token reprompt, 4,950,016 additional tokens,
  local NF4, temperature 0.3, the same two generators as the source
  locks. Looping holds after the continuation tail has left the window.
- P1 is true (8/8). The negative result is stated plainly. Empty
  completions were not relabelled. L2-persistence-to-lock was not run.
  Families are not fit as one hazard. Spend on the generate is $0.
- F1's 0.083 cut remains the frozen natural-prose calibration at
  chunk size 1024. It is not re-calibrated on 5M loops, and this
  cohort does not require that re-calibration: every continuation
  chunk is far above the cut.

## Claims I judge unsupported or overreaching

- "Clock origin is the L0 lock", as a description of the number
  1220.5. Unsupported until finding 1 is rewritten.
- Differential censoring ("shortest cell", "a later escape on a
  longer cell") for this cohort. Unsupported. All eight lengths match.
- Any reading of 0/8 as native sliding-window attention, as constant
  embeddings, as a pooled family escape rate, as a sample of semantic
  domains, or as a lock that cannot break after \(T\). Those readings
  are unsupported. §5 already refuses several of them; finding 3
  puts the refusal where the number is.
