# Stage 10 review
Reviewer: Cursor Grok 4.6 (scientific supervisor)   Date: 2026-09-19
Gate: PASS (`afterlife review --stage s10`, exit 0; `.cache/review-s10.json`)
Verdict: **APPROVED WITH CHANGES**

## Close of phrase blockers (same day)

Executor rewords applied 2026-09-19. Both blockers below are
closed by phrase rewrite, no new `run_id`. Checked on disk:
[`REPORT.md`](REPORT.md) lede, P3 observed, DPO `noise` s2 quote;
[`HANDOFF.md`](HANDOFF.md); [`README.md`](README.md);
[`docs/research-plan.md`](../../research-plan.md) S10 line;
[`docs/research-plan.ru.md`](../../research-plan.ru.md) S10 line.
“positive where identified (Base, SFT, RLVR)” and P3 “true on the
point” remain only in this file, as the rejected wording.

Do not merge from this close note. The human may `--no-ff` when
they ask.

Re-ran the gate this review (2026-09-19): exit 0, one WARN
`runs.complete` on
`s10-paperb-olmo-rlvr-int8-20260918T142301Z-7125ccca`
(STATUS=FAILED, 0/10 empty-completion). That is E2 PARTIAL, not a
hole. Everything the gate checks is taken as true.

Do not merge from this review. Do not generate, embed, or recompute
\(G_t\). Do not change F1 or `N_confirm=3`. Do not start S11. Do not
write `paper/main.tex`. Do not rebase. Phrase blockers are applied.
The human may `--no-ff` close when they ask. I do not merge unless
they say so.

The two blockers are phrase rewrites, no new `run_id`.

---

## Answer to the stage question

On the local OLMo 3 7B Instruct line (Base → SFT → DPO → RLVR), P1
`raw_completion` / `serialization: raw_bytes`, `W=4096`, `B=1024`,
`T=49152`, T=0.3, **two estimands**, both confirmatory, not pooled
with S9 Qwen:

1. **Completion (planned sample of 40 NF4 traj / rung).** Empty-
   completion deaths 13 → 21 → 37 → 36 / 40. That is collapse from
   Base through DPO and a **floor** at DPO ≈ RLVR, not a four-step
   monotone descent. INT8 agrees on direction at the ends (Base 5/10
   empty, RLVR 10/10). Failed cells stay in the sample; they are not
   unlocks. Selecting on completers *is* the first estimand's
   sample, and that selection gets stronger down the line.

2. **Persistence among trajectories that enter the lock table**
   (`min_chunks=8`; not identical to 12W completers). Every such
   trajectory is a confirmed early-onset long-lived repetition lock
   (`N_confirm=3`); confirmed escape **0** in both spaces. Almost
   every lock sits on the construct floor \(\tau=0.75\); one RLVR
   `recipe` descendant locks at \(\tau=1.50\) (still not a late
   lock). Last-band \(G_t\) is a late-window measurement of already-
   locked registers / loop families. Base NF4 last-band CIs exclude
   0 in both spaces. SFT excludes 0 only in Qwen-embed. RLVR has a
   positive *point* in both spaces; both CIs include 0; LOO skipped
   (`<3` seeds). DPO last-band is **unidentified** (3 within, 0
   between) — missing identification, not a sign and not a flip.

The executor headline is **accepted after the two rewords below**,
and only as a two-estimand sentence on **this line / this stack**.
It is not accepted as written: “last-band \(G_t\) is positive where
identified (Base, SFT, RLVR)” treats a point estimate whose interval
includes 0 as an established gap, and P3 scored “true on the point”
is the same move. Last-band \(G_t>0\) is not recovered semantics,
not a semantic state, and not absorbing. The lock is not a late
lock.

---

## Answers the executor marked as disputed

### 1. Is “point \(G_t>0\), CI includes 0” (5 traj) enough for P3?

**No.** P3 was pre-registered as “RLVR last-band \(G_t>0\) in both
spaces.” A point of 0.2015 (BGE) / 0.3346 (Qwen) with intervals
\([-0.134, 0.202]\) and \([-0.147, 0.335]\) does not establish
\(G_t>0\). Both upper bounds equal the point (two-seed cluster
bootstrap). LOO is skipped. [`gt_last_band.csv`](../../../artifacts/stage-10/gt_last_band/gt_last_band.csv)
already records `ci_excludes_0=False` and
[`gt_last_band_figure.meta.json`](../../../artifacts/stage-10/gt_last_band_figure/gt_last_band_figure.meta.json)
already says “RLVR CIs include 0 (small-n).”

“5 traj” is **lock-table** \(n\) (`n_traj_lock_table=5`). Last-band
pair counts are 3 within / 3 between — four last-band trajectories,
two seeds (`noise`, `recipe`), matching 12W completers = 4, not 5.
The fifth is a mid-horizon lock-table extra. Either denominator is
too small to identify the sign. Score P3 **not established** (or
partial: point `+`, interval includes 0, LOO absent). Do not score
it true.

SFT is not a P3 cell, but the same sentence in the lede lumps it
with Base: SFT BGE 0.102 \([-0.007, 0.122]\) includes 0; SFT Qwen
excludes 0. Sign of the point agrees. That is not two-space
interval identification.

### 2. Is “completion ladder” too strong when DPO/RLVR have 3 and 4 completers? Sample or selection?

**Not too strong for estimand 2; those 3 and 4 are selection into
estimand 1.** Empty rates 13/40, 21/40, 37/40, 36/40 are counted on
the planned NF4 sample. The rarity of 12W completers *is* the
completion result. Do not hedge the completion headline because the
persistence sample shrank. Do not treat 3 and 4 as an unlucky draw
from a still-large completer population.

Tighten one clause: DPO → RLVR is a **floor** (37 vs 36 empty; 3 vs
4 completers), not a further collapse. Adjacent-edge language in
the PLAN was never a monotone-ladder test
([`adjacent_edges.meta.json`](../../../artifacts/stage-10/adjacent_edges/adjacent_edges.meta.json)).
“Post-training on this line kills completion, not the lock” remains
the right contrast once the last step is named as a floor.

### Lock-table \(n\) versus completer \(n\)

The substitution exists and is **named in REPORT §2**, then reused
in two places that still read as completer counts:

| Cell | 12W completers | lock-table \(n\) (`min_chunks=8`) |
| --- | ---: | ---: |
| Base NF4 | 27 | 27 |
| SFT NF4 | 19 | 20 |
| DPO NF4 | 3 | 5 |
| RLVR NF4 | 4 | 5 |
| Base INT8 | 5 | 6 |

[`adjacent_edges.csv`](../../../artifacts/stage-10/adjacent_edges/adjacent_edges.csv)
`left_n_traj` / `right_n_traj` are lock-table \(n\) (27, 20, 5, 5)
under a caption that says “completer lock saturation.” P3 observed
“5 traj” is the same substitution applied to last-band \(G_t\).
Saturation (lock rate 1, escape 0) holds on **both** denominators.
Do not cite 20 / 5 / 5 as 12W completer \(n\), and do not cite 5 as
the last-band \(G_t\) sample.

### DPO NaN as a sign or a flip

**Not read as either, in the tables that matter.**
[`gt_last_band.csv`](../../../artifacts/stage-10/gt_last_band/gt_last_band.csv)
`sign=unidentified`, `identified=False`, 3 within / 0 between.
[`adjacent_edges.csv`](../../../artifacts/stage-10/adjacent_edges/adjacent_edges.csv)
`right_sign` / `left_sign` = `unidentified`, `sign_flip=False`.
The last-band figure omits DPO. REPORT / P9 say undefined, not a
flip. That reading is supported.

Hazard, not a finding: per-cell `persistence_gt` captions print
`Last-band G=nan [-0.0742, -0.0742]` (BGE) and
`[-0.1309, -0.1309]` (Qwen). Those bounds are the leftover
within-seed interval when between-pairs hit zero
([`persistence_gt_bands.csv`](../../../artifacts/stage-10/persistence/dpo-nf4-local-bge-m3/persistence_gt_bands.csv)
bands 4–13). Do not let a negative degenerate interval leak into
prose. Overlay traces of DPO \(G_t>0\) in bands 1–3 are early-band
geometry while two seed families still have chunks; they are not
last-band identification.

---

## Blocking findings

1. **Claim.** Lede / P3 / HANDOFF: last-band \(G_t\) “is positive
   where it is identified (Base, SFT, RLVR)” in both spaces; P3
   scored **true on the point**.
   ([`REPORT.md`](REPORT.md) title block lines 20–23; §3 P3;
   [`HANDOFF.md`](HANDOFF.md) “Last-band \(G_t>0\) where
   identified.”)

   **Problem.** “Identified” in that sentence means “a number
   exists” (`identified=True` in
   [`gt_last_band.csv`](../../../artifacts/stage-10/gt_last_band/gt_last_band.csv)).
   E5 identification is last-band \(G_t\) + seed-cluster interval +
   LOO. RLVR fails the interval (both CIs include 0) and fails LOO
   (`<3` seeds). SFT fails the BGE interval. Scoring P3 true
   because the point is positive is accepting a trend in place of
   an interval — the move this project has already paid for. The
   body and the figure limitations already know this. The sentence
   a reader will quote does not.

   **Resolve (reword, no new `run_id`).** In the lede, replace the
   “positive where identified (Base, SFT, RLVR)” sentence with
   facts, not a gloss: Base NF4 last-band CIs exclude 0 in both
   spaces (BGE 0.0944 [0.029, 0.108]; Qwen 0.189 [0.086, 0.221]);
   SFT BGE includes 0, SFT Qwen excludes 0; RLVR point `+` in both
   spaces, both CIs include 0, LOO skipped; DPO last-band
   unidentified (3 within, 0 between), not a flip. Keep the
   register / loop-family clause. Score P3 **not established**
   (point `+`; interval includes 0; two seeds; lock-table \(n=5\)
   is not last-band \(n\)). Same sentence in
   [`HANDOFF.md`](HANDOFF.md). Do not move this solely to Threats.
   Do not change F1. Do not rerun persistence.

2. **Claim.** §2 “What the completed text actually is” quotes DPO
   NF4 `finance` s1 as completed-window text.
   ([`REPORT.md`](REPORT.md) lines 190–196.)

   **Problem.** That trajectory is in
   [`empty_completions.csv`](../../../artifacts/stage-10/empty_completions/empty_completions.csv)
   (FAILED, 16 297 tokens) and in the lock table
   ([`persistence_locks_all.csv`](../../../artifacts/stage-10/locks/persistence_locks_all.csv),
   \(\tau=0.75\)). It is one of the two DPO extras that died after
   eight chunks and before \(T=49152\). The three 12W DPO
   completers are the `noise` family — the reason last-band \(G_t\)
   is unidentified. Quoting a mid-horizon death under a
   “completed text” heading substitutes lock-table \(n\) for
   completer \(n\) in the only place a reader sees the object
   \(G_t\) is about.

   **Resolve (reword, no new `run_id`).** Relabel that quote as a
   lock-table / mid-horizon death, not a 12W completer, **or**
   replace it with a last-band `noise` excerpt from a STATUS=
   COMPLETED DPO trajectory. Do not generate a new sample.

---

## Non-blocking observations

- **Completion floor.** 13 → 21 → 37 → 36 already lets a reader see
  DPO ≈ RLVR. Add the word “floor” in the lede if the P3 rewrite
  touches that sentence; not a third blocker.
- **`adjacent_edges` caption** says “completer lock saturation”
  while \(n\) is lock-table \(n\). Limitations already warn
  “few completers; rates are not Bernoulli-on-40.” Optional
  caption: “lock-table (\(min\_chunks=8\)) lock saturation.”
- **Overlay limitations** paraphrase the caption. The last-band
  figure names DPO unidentified and RLVR CIs including 0; the
  overlays do not. Early DPO traces (bands 1–3, then gone) are
  easy to misread as last-band positivity. Illustration-only is
  already labelled.
- **RLVR \(\tau_{\mathrm{lock}}=1.50\)** on `recipe` s3, both
  spaces. Still early relative to 12W; still not a late lock.
  “Confirmed at the floor” is false for that one row.
- **Empty deaths are not all Q1.** Base `recipe` dies at 22–27
  tokens; SFT `love` s3 at 35 171; DPO `finance` s1 at 16 297;
  RLVR `noise` s2 at 14 411. DPO/RLVR Q3–Q4 fill/stop collapse
  among survivors
  ([`protocol_by_quarter.csv`](../../../artifacts/stage-10/protocol_by_quarter/protocol_by_quarter.csv)).
  The operational definition (five consecutive empty completions)
  is one mechanism name over two timescales. Do not retune it.
- **P1 re-prompt ≠ sliding attention.** Named. Native-chat still
  deferred. A lock or an empty under `raw_completion` can be a
  continuation-mechanism artifact.
- **Fingerprint agreement.** Confirmatory #3 in ADR-0023 F4 /
  ADR-0025; not an S10 exit (same allowed E6 choice as S9). Do
  not invent a fingerprint table. Do not inherit “Qwen
  fingerprints agree.”
- **INT8.** Base same-sign concordance only; both INT8 CIs include
  0. RLVR INT8 0/10. P7 partial is the right score. Not a third
  headline.
- **Hosted Qwen-embed $0.00** under the $5 cap (ADR-0028). Scale
  difference vs BGE is not “Qwen-embed is stronger.”
- **One generator family, one temperature, P1 `raw_bytes`, NF4
  headline.** Opposite of S9 Qwen (completion worse on Base there)
  is a contrast, not a pool. E11 holds.
- Thresholds were not retuned after seeing locks. Degeneracy ran
  before published \(G_t\). Thinking tokens 0. Served provider
  `local`. Hybrid attention at imposed `W=4096` is not an
  architecture contrast.

---

## Claims I judge supported

- NF4 empty-completion deaths 13 / 21 / 37 / 36 of 40; INT8 Base
  5/10, RLVR 10/10. Same reason on every missing cell
  ([`empty_completions.csv`](../../../artifacts/stage-10/empty_completions/empty_completions.csv);
  [`generate_status.csv`](../../../artifacts/stage-10/generate_status/generate_status.csv)).
  E1/E2 PARTIAL is the right completeness verdict.
- P1 **false**: RLVR 2/10 domain seeds (`noise`, `recipe`). The
  other eight never produce a lock-table descendant.
- P2 **false**: Base empty 13/40 vs RLVR 36/40. Opposite of S9
  Qwen. Stated plainly.
- P4: RLVR last-band *point* sign `+` / `+`. That is sign
  agreement, not interval identification.
- P5: thinking tokens 0 on completed NF4 steps.
- P6: completed 12W NF4 steps fill 1.000 / stop 0.000. Cell-level
  Q4 means include dying trajectories; the REPORT says so.
- P7 **partial**: Base INT8 vs NF4 same sign in both spaces; RLVR
  INT8 has 0 completers.
- P8 antecedent is not met (DPO last-band unidentified). Locks
  saturate where a lock table exists; completion collapse is the
  ladder. That scoring is honest.
- P9 **not falsified**: Base–SFT `+`/`+` in both spaces; edges
  that touch DPO cannot flip a sign that was never identified.
- P10 **true**: Base `recipe` 3/4 empty-completion FAILED.
- Lock table: confirmed lock on every admitted trajectory;
  confirmed escape 0 / 126 lock-table rows (63 traj × 2 spaces).
  Language “early-onset long-lived repetition lock” / “no
  confirmed escape through \(T\)” is the allowed E6 wording. Not
  absorbing. Not a semantic state.
- DPO last-band unidentified in both spaces, not a flip, not a
  zero.
- Base NF4 last-band \(G_t>0\) with CIs excluding 0 in both
  spaces. LOO-by-seed stays positive on Base and SFT
  ([`persistence_loo_all.csv`](../../../artifacts/stage-10/loo/persistence_loo_all.csv)).
- Last-band \(G_t>0\), where the interval excludes 0, is seed-
  conditioned separation of late registers / loop families. The
  quotes that are actually 12W completers (Base `physics` lattice
  reprint; SFT `love` assistant loop; RLVR `noise` ordinal loop;
  Base INT8 `surreal` lexical cycle) are what that number is
  about.
- Degeneracy before \(G_t\). Local generate; no hosted OLMo cell.
  Hosted Qwen-embed ledger increment $0.00. Native-chat not
  silently rerun. One family, unpooled with S9 Qwen.

---

## Claims I judge unsupported or overreaching

- **P3 as true / “last-band \(G_t\) is positive” on RLVR (and on
  SFT in BGE).** Unsupported. Point `+`, interval includes 0.
- **Four-step monotone completion ladder** that treats DPO → RLVR
  as a further collapse. Overreaching. The floor is 37 vs 36.
- **Lock-table \(n\) as 12W completer \(n\), or as last-band
  \(G_t\) \(n\).** Unsupported as a substitution, even when lock
  *rate* agrees.
- **DPO last-band sign, DPO last-band zero, or DPO–RLVR sign
  flip.** Unsupported. NaN is missing identification. The
  degenerate negative `G_lo=G_hi` is not a minus sign.
- **DPO `finance` s1 as completed 12W text.** Unsupported. It is a
  FAILED lock-table extra.
- **Late lock / absorbing lock / semantic state / recovered prompt
  memory / H1.** Unsupported. Not asked; not shown.
- **Fingerprint agreement.** Not computed; must not be treated as
  shown.
- **INT8 last-band \(G_t\) significantly \(>0\), or RLVR INT8
  concordance.** Unsupported where the CI includes 0 or \(n=0\).
- **Post-training in general, other families, native-chat, or true
  `Tail_W` sliding attention.** Unsupported. This is one OLMo 3 7B
  Instruct line, P1 `raw_bytes`, NF4 headline, T=0.3.
- **Pooled OLMo+Qwen law.** Unsupported. The S9 contrast (Base
  worse at completing) is the reason not to pool, not a joint
  estimate.
