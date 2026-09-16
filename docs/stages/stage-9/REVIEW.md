# Stage 9 review
Reviewer: Cursor Grok 4.6 (scientific supervisor)   Date: 2026-09-16
Gate: PASS (`afterlife review --stage s9`, exit 0; `.cache/review-s9.json`)
Verdict: **APPROVED WITH CHANGES**

## Close of phrase blockers (same day)

Executor rewords applied 2026-09-16. All three blockers below are
closed by phrase rewrite, no new `run_id`. Checked on disk:
[`REPORT.md`](REPORT.md) lede, P8 observed, §5, §7;
[`PLAN.md`](PLAN.md) P8 observed; [`README.md`](README.md);
[`HANDOFF.md`](HANDOFF.md);
[`docs/research-plan.md`](../../research-plan.md) S9 line;
[`docs/research-plan.ru.md`](../../research-plan.ru.md) S9 line.
“late lock” remains only in this file, as the rejected wording.

Do not merge from this review. Do not generate, embed, or rerun
persistence. Do not change F1 or `N_confirm=3`. Do not start S10.
Do not write `paper/main.tex`. The human may `--no-ff` close when
they ask. I do not merge unless they say so.

---

## Answer to the stage question

On local Qwen3-8B Base vs Instruct, P1 `raw_completion` /
`serialization: raw_bytes`, `W=4096`, `T=49152`, T=0.3, **two
estimands**, not one:

1. **Persistence among completers.** Every completed 12W trajectory
   confirms a long-lived repetition lock at
   \(\tau_{\mathrm{lock}}\in\{0.75,1.00\}\) (Base NF4: 31/31 at the
   `N_confirm=3` floor 0.75; Instruct NF4: 36/38 at 0.75, 2/38 at
   1.00), with **no confirmed escape** through 12W, and last-band
   \(G_t>0\) whose seed-cluster CI excludes 0 in both BGE-M3 and
   hosted Qwen-embed. Last-band signs agree. That is a Base≈Instruct
   finding on the P8 criterion, on **this pair / this stack**.
2. **Completion under this continuation mechanism.** Base NF4 9/40
   empty-completion deaths vs Instruct 2/40; Base `recipe` 0/4
   completed vs Instruct `recipe` 4/4 locked. Failures are missing
   data, not unlocks. Selecting on completers is part of the result.

This is **not** a late-onset afterlife lock. The lock is confirmed
as soon as the construct allows (three 1024-token chunks = 0.75W),
then survives eviction. Last-band \(G_t\) is a late-window
measurement of an already-locked, seed-conditioned register /
loop-family; the quotes (love-s2 “Let me know what you need!”,
surreal-s1 “interior of the interior…”) are what the number is
about. It is not H1, not a semantic state, and not absorbing.

The executor headline is **accepted after the three rewords below**.
It is not accepted as written: “late lock” in §7, P8 as the sole
finding, and an unhedged “positive \(G_t\)” in the lede would let a
reader take the wrong object home.

---

## Blocking findings

1. **Claim.** Lede / P8 / §7: the stage result is Base≈Instruct
   persistence (P8) on completed cells.
   (`REPORT.md` title, lines 7–11, P8 observed, §7 first bullet.)

   **Problem.** That is the right reading of the *completer*
   persistence contrast (locks saturate; NF4 last-band CIs overlap
   in both spaces). It is the wrong reading of the *stage*, because
   the sample that enters \(G_t\) is selected. Base lost 9/40,
   Instruct 2/40; all four Base `recipe` cells died after 7–13
   tokens. P2 is numerically 9/10 vs 10/10 only because `recipe` has
   no completed descendant — “numerically true, dynamically false”
   as an unlock story is correct, and must not be used to retire
   the completion contrast. Threats already say “conditioning on
   completers selects for free-running seeds.” A confound named
   only in §5, while the title and P8 carry the paper, is a buried
   second result. E1/E2 **PARTIAL** is enough for matrix
   completeness. A Heckman-style selection *model* is not required.
   A **named two-estimand sentence** is.

   **Resolve (reword, no new `run_id`).** In the lede, after the
   completed-cell P8 sentence, add a sentence with these facts:
   completion under P1 `raw_completion` is Base worse (NF4 31/40 vs
   38/40; `recipe` 0/4 vs 4/4); failed cells stay in the sample and
   are not unlocks; the persistence contrast is defined on
   completers. In the P8 observed cell, say P8 is the completer
   estimand, not the only estimand. Do not move this solely to
   Threats.

2. **Claim.** §7: “post-training reshaping the **late lock** on
   completed cells.” PLAN question language (“late-regime
   persistence”) applied to lock *onset*.
   (`REPORT.md` §4 surprise 1 already knows this; §7 forgets it.)

   **Problem.** Unique \(\tau_{\mathrm{lock}}\) values are 0.75 and
   1.00. 0.75 is the floor of the construct (`N_confirm=3` × chunk
   1024 / `W=4096`). Base NF4 is 31/31 at 0.75; Instruct NF4 is
   36/38 at 0.75. [`gt_bands_all`](../../../artifacts/stage-9/gt_bands_all/gt_bands_all.csv)
   is already \(G_t>0\) in the first integer band and stays flat
   through 12W. Last-band \(G_t\) does not discover a post-horizon
   attractor. “Late-regime” may name the *measurement time* of
   \(G_t\). It may not name the lock. “Late lock” does not follow.

   **Resolve (reword, no new `run_id`).** Replace “late lock” in §7
   with “early-onset long-lived repetition lock that persists
   through 12W.” Scope that sentence to **this Qwen3-8B pair, P1
   `raw_bytes`, NF4, T=0.3** — not “post-training” as a tested
   class. Last-band \(G_t\) may remain “late-window \(G_t\).”

3. **Claim.** Lede: “positive last-band \(G_t\) in both embedding
   spaces” as the second half of P8, without saying what the quotes
   are.
   (`REPORT.md` lines 7–11 vs §2 “What the completed text actually
   is” and §5 “same loop family stays nearer.”)

   **Problem.** Every completed trajectory in
   [`degeneracy_verdicts.csv`](../../../artifacts/stage-9/degeneracy/degeneracy_verdicts.csv)
   is F1-degenerate (the single `degenerate=false` row is Instruct
   `programming` s2: one chunk, FAILED empty completion).
   looping_fraction is 1.0 on completed Base and on 37/38 completed
   Instruct NF4. Love-s2 and surreal-s1 are loops. The body says
   this. The headline a reader will quote does not. ADR-0026
   already forbids reading a one-text-per-domain bank as identified
   semantics. A limitations line that only says “not semantic-domain
   memory” on the table, while the lede is silent, is not loud
   enough for this stage.

   **Resolve (reword, no new `run_id`).** One clause in the lede
   (not only §2/§5): last-band \(G_t>0\) is seed-conditioned
   separation of these late registers / loop families, not recovered
   prompt memory and not a metastable semantic state.

---

## Non-blocking observations

- **Fingerprint agreement.** Third name in the PLAN / ADR-0023 F4 /
  ADR-0025 confirmatory order. Not computed. E6 correctly forbids
  using the exact-cycle hash as the *lock*. That is not permission
  to treat F4 item 3 as delivered. This is an **allowed E6 choice
  for the lock construct** and a **named drop of L0 confirmatory
  #3**, not a hole in E5 (E5 does not require the hash). Do not
  invent a fingerprint table. S10 must not inherit “Qwen
  fingerprints agree.” One sentence in Threats already says this;
  keep it.
- **Lock-rate half of P8 is a ceiling.** 31/31 vs 38/38 is “both
  saturate F1 + `N_confirm=3`,” not a precise match of lock
  dynamics. The informative Base≈Instruct evidence is last-band
  \(G_t\) *sign* (and the overlapping NF4 CIs, which the REPORT
  correctly does not promote to a magnitude test).
- **INT8 CIs that include 0.** Wording is already tight:
  concordance (P7), not a third headline; small-n / 3–4 within-seed
  pairs; not a sign flip. Leave it.
- **Qwen-embed magnitude.** Surprise 4 is correct: larger last-band
  \(G_t\) (~0.23–0.30 vs ~0.15) is a scale difference between
  spaces, not a “Qwen-embed is stronger” claim. Hosted embed $0 is
  recorded; do not treat that price as permanent (ADR-0027).
- **Protocol Q3 on Base NF4.**
  [`protocol_by_quarter.csv`](../../../artifacts/stage-9/protocol_by_quarter/protocol_by_quarter.csv)
  has Q2=31, Q3=33, Q4=31 trajectories, Q3 min fill 0.004, stop
  0.120. The “Q1 deaths, not a late-regime collapse” sentence is
  the main story; Q3 is not a clean completed-only quarter. Do not
  claim Q2–Q4 are completers only without explaining n=33.
- **`gt_last_band_figure` limitations** name UMAP and INT8, not the
  loop-family alternative. The table meta and REPORT body do. Optional
  one-line meta edit; not required for close.
- Native-chat remains deferred. Hosted `or-qwen3-8b` was not used.
  Thinking tokens 0. Served provider `local`. Kaleido/Chrome missing
  is named. Thresholds were not retuned after 86/86 locks.

---

## Claims I judge supported

- Instruct NF4: 10/10 domain seeds have ≥1 confirmed lock (P1).
- Instruct last-band \(G_t>0\) in both spaces; CIs exclude 0 (P3).
  BGE-M3 0.1514 [0.0871, 0.1590]; Qwen-embed 0.3046 [0.1917, 0.3152]
  ([`gt_last_band.csv`](../../../artifacts/stage-9/gt_last_band/gt_last_band.csv)).
- Sign of Instruct last-band \(G_t\) agrees across spaces (P4).
- Thinking tokens = 0 on completed NF4 steps (P5).
- Run-level NF4 fill ≥ 0.95, with Base Q1 0.773 named as
  empty-completion deaths (P6). Final-quarter Base fill 0.975.
- INT8 vs NF4, Instruct, F2 seeds: same *sign* of last-band \(G_t\)
  in both spaces (P7). BGE INT8 CI includes 0.
- On **completed** NF4 cells: lock 31/31 vs 38/38; last-band sign
  +/+ in both spaces; LOO-by-seed does not flip last-band \(G_t\)
  to ≤ 0 on the NF4 cells
  ([`persistence_loo_all.csv`](../../../artifacts/stage-9/loo/persistence_loo_all.csv)).
  That is P8 on the completer estimand.
- Confirmed escape 0/86 completed trajectories. Language “no
  confirmed escape through \(T\)” / “long-lived repetition lock”
  is the allowed E6 wording. Not absorbing.
- Empty-completion cells named and kept; absence from \(G_t\) is
  missing data ([`empty_completions.csv`](../../../artifacts/stage-9/empty_completions/empty_completions.csv)).
- Degeneracy ran before published \(G_t\). Local generate; no
  hosted Instruct cell. Hosted Qwen-embed ledger increment $0.00.
- Native-chat not silently rerun as `raw_bytes` (E3).
- One-family, one temperature, P1 `raw_bytes`, NF4 headline: the
  REPORT does not, except for the §7 “late lock” slip, speak of
  post-training as a tested class. OLMo stays unpooled.

---

## Claims I judge unsupported or overreaching

- **“Late lock” / late-onset afterlife lock.** Unsupported. Onset
  is at the confirmation floor, then survival through 12W.
- **P8 as the only stage finding.** Overreaching. Completion is a
  Base-worse-than-Instruct protocol contrast on the same matrix.
- **Positive last-band \(G_t\) as recovered seed semantics or a
  metastable semantic state.** Unsupported. The measurement is
  loop-family / register separation in two embedding spaces.
- **Fingerprint agreement.** Not computed; must not be treated as
  shown.
- **INT8 last-band \(G_t\) significantly > 0.** Unsupported where
  the CI includes 0 (both BGE INT8 cells; Base INT8 Qwen-embed).
  Sign concordance only.
- **Qwen-embed is a stronger scientific space.** Unsupported.
  Magnitude is not a claim; sign agreement is.
- **Post-training in general, or other families, or native-chat, or
  true `Tail_W` sliding attention.** Unsupported. This is one
  Instruct pair on P1 `raw_completion` / `raw_bytes` / NF4 / T=0.3.
- **Paper A 19/20 lock as this Instruct cell.** Unsupported; already
  refused in the REPORT.
- **H1.** Not asked; not supported.
