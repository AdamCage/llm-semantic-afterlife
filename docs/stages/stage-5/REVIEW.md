# Stage 5 review
Reviewer: Cursor Grok 4.6 (scientific supervisor)   Date: 2026-09-06
Gate: **FAIL on this reviewer VM** (`afterlife review --stage s5`, exit 1).
Cause: `runs/s5` is absent. Raw runs are git-ignored. Artifact bundles
on the committed record: 43/43 PASS (`artifacts.bundle`). Last CI on
`91348b4` is 6/6 green
([run 34009174537](https://github.com/AdamCage/llm-semantic-afterlife/actions/runs/34009174537)).
Generate manifests, spend, and F1/F2/F8/F10 were not re-derived here.
The executor previously showed gate exit 0 on a machine that has
`runs/s5`. Literature WARN (1 LEAD citation) is not a blocker: this
stage does not write `paper/main.tex`.

Verdict: **APPROVED WITH CHANGES**

Do not merge from this review. Do not regenerate, re-embed, retune
0.083 / 0.0122, drop degenerate rows, headline `α` or `n_macro`, call
a lock a basin, or open T=1.0 / T=1.5 / `W=8192` / 200 seeds / Gemma.
Stage close is `--no-ff` into `main` only after the human says close.

---

## Answer to the stage question

On `or-qwen3-8b` under P1 `raw_completion`, at the S4 lock
(`W=4096`, T=0.3, 12 turnovers), the ten `seed_bank_v1` domain seeds
are **ensemble-distinguishable** at the last band: occupancy-assemble
`D_between − D_within` excludes 0 in both embedding spaces. That is
F4. It is not recovered semantic memory, not H1, and not a basin.

The two one-fact twin pairs are **not last-band divergent** under the
pre-registered F6 rule (CI excludes 0 from above, else collapsed).
That scoring is Right against the PLAN. It does **not** establish that
the twins occupy one lock, and it does **not** establish that
waterloo’s contrast vanished. Waterloo’s last-band point Δ is the
same size as its band-0 Δ, where the CI *did* exclude 0; what grew is
the interval. Reactor never excluded 0, including while the seed was
still in the window.

Object under review is lock occupancy vs seed at this operating
point, one generator.

---

## Blocking findings

1. **Claim.** Title and Q4 reading: “twins collapse to the control”;
   REPORT §3 “a one-fact flip does not occupy a distinguishable lock”;
   implications “a one-fact flip does not stay apart from the
   stochastic control”; F6 source table
   [`twin_last_band.meta.json`](../../../artifacts/stage-5/occupancy/twin_last_band.meta.json)
   limitations “n=4. Not an MSM macrostate.”

   **Problem.** Last-band F6 is an NHST default: divergent iff the CI
   excludes 0 from above, else collapsed. Scoring Q4 **Right** against
   that rule is correct. The dynamical sentence is not. In
   [`twin_per_band.csv`](../../../artifacts/stage-5/occupancy/twin_per_band.csv)
   waterloo `bge-m3` Δ is 0.048 at band 0 (CI [0.021, 0.075],
   divergent, seed still in the window) and 0.049 at band 12 (CI
   [−0.394, 0.491], collapsed). The point did not go to 0; the CI
   widened until it covered a Δ larger than the F4 domain gap (0.201).
   `qwen3-embed-8b` waterloo is the same shape (divergent at bands 0–4;
   last-band CI [−0.688, 0.671] with point −0.009). Reactor is a
   different family: last-band [−0.077, 0.092] on `bge-m3`, and it
   never excluded 0, including at band 0. Pooling them as “twins
   collapse” sells a precision-limited null as occupancy of one lock.
   The F6 table’s limitations line restates F9 (`n_macro`) and does
   not name the alternative the figure fails to exclude.

   **Resolve (reword, no new arm).** Keep F6’s operational last-band
   scoring. Change the title and any sentence a reader would take as
   “the twins occupy the same lock” or “the one-fact contrast died.”
   Split families: reactor was never last-band (or band-0) divergent;
   waterloo was divergent while the seed was in context and is
   underpowered at the last band. Rewrite
   `twin_last_band.meta.json` `limitations` to name that alternative
   (stable Δ≈0.05 with a CI that grew to include 0 and a domain-sized
   gap; n=2 last-band pairs per family). Extra replicates would be
   required to *claim sameness*; they are not required to close this
   stage once the prose matches the interval.

---

## Non-blocking observations

1. **F4 is an ensemble, not ten tight point attractors.** Last-band
   `D_within` rose from 0.170 (band 0) to 0.288 (band 12) in `bge-m3`
   while `D_between` stayed ~0.49
   ([`domain_separation_per_band.csv`](../../../artifacts/stage-5/occupancy/domain_separation_per_band.csv)).
   Same-seed loops collapsing `D_within` is therefore not the
   last-band mechanism; the gap survives because `D_between` stays
   high. Per-seed: philosophy / recipe / finance are tight; war
   within 0.477 exceeds war–surreal 0.389 and war–love 0.353. Do not
   write that each of the ten seeds sits on its own point lock.

2. **physics s1 drops out of last-band `D_within`.** Reused S2.2
   `or-qwen3-8b__W4096__T0p3__physics__s1` has 47 chunks vs 48 on its
   pair. Last-band matrix diagonal is NaN, `n_chunk_pairs=0`; F4
   `n_within_pairs=9`, `n_between_pairs=162` (19 last chunks). Named
   in the tidy matrix, not in REPORT §2. Unlikely to flip CI
   [0.065, 0.332]. Name the missing last-band chunk. Do not regenerate
   S2.2.

3. **love s1 is the right row to keep, and it is stop-forced.**
   looping 0.477 and late Jaccard 0.010 miss both calibrated bars;
   the bars were not moved. love within 0.240 is not the F4 gap.
   Unnamed: love Q3 stop = 1.0, Q4 stop = 0.907
   ([`protocol_by_seed_quarter.md`](../../../artifacts/stage-5/occupancy/protocol_by_seed_quarter.md)).
   The only clean S5.1 row is a high-stop assistant register, not an
   escape from the lock. Name that next to the 1/2. Do not drop the
   row and do not move 0.083 / 0.0122.

4. **Q7 fill transferred as a cell mean, not per seed.** domain_20 Q4
   0.853 vs S4 0.903 (Δ=0.050) is the scored object. war Q4 0.479 and
   waterloo-lost Q4 0.586 (s1 run-mean fill 0.158) are named. Physics
   / surreal are S2.2 reuse, different day, same protocol — named as
   reuse. The motivating S4 last-band gap was `W=8192` T=0.3, two
   seeds; this measurement is `W=4096` T=0.3, ten seeds, not an
   imported number. Fine.

5. **`artifacts/stage-5/INDEX.md` is the CLI geometry bundle**, not
   the occupancy assemble. F4/F5/F6 live under
   `artifacts/stage-5/occupancy/`. Do not quote INDEX MSD α (0.347 /
   0.398 on the mixed 24) as confinement. The report already refuses
   to headline α.

6. **CLI vs assemble is named and is prior law for this stage.** Do
   not quote CLI `analyze separation` on the S5.1 embed as F4. Do not
   quote CLI twins `scope=all` as F6. First CLI twins pair
   `s5-twins-*-20260906T031918Z-*` is SUPERSEDED.

7. **Thin leftovers, already on the record:** P1 vs true sliding
   attention; two tokenizer round-trip fails (war s1 step 36, love s1
   step 44 — love s1 is also the clean row); eight `ep_poll` stalls
   on one `run_id`; family-scope bug then `twins.family_name`;
   embedding-space gap *level* 0.20 vs 0.39 with sign agreement;
   `uv.lock` dirty on analysis runs; trajectory-bootstrap is the
   resample unit (captions). Ensemble Q4 stop 0.329 is not S4’s T=1.0
   stop 0.954; some seeds still hit stop-forced continuation (love,
   war). Provider pin Alibaba, `reasoning_effort: none`.

---

## Claims I judge supported

- **F4 on this process, this lock, ten domain seeds, both spaces.**
  Occupancy assemble last-band gap 0.201 [0.065, 0.332] (`bge-m3`) and
  0.390 [0.151, 0.593] (`qwen3-embed-8b`). Distinguishable ≠
  recoverable semantic memory. The vs-turnover limitations line
  already says that.

- **F5 as k/n.** Domain traj 19/20; seeds with ≥1 lock 10/10; love
  1/2. No `[1, 1]` carried as uncertainty. Thresholds 0.083 and late
  Jaccard 0.0122 are S4-calibrated and were not moved. Degenerate
  rows kept; love s1 kept. Mode-2 rows (philosophy s1, programming s2,
  reactor-unstable s2) are the same OR as S4.

- **F6 operational last-band scoring.** Every last-band Δ CI includes
  0, per family and pooled, both spaces. Q4 as the pre-registered
  “interesting wrong is divergent” branch: that wrong did not happen
  *at the last band*.

- **Q1, Q2, Q3, Q6 (verdict sign), Q7 cell mean, Q8.** noise 2/2
  mode 2. Register quotes are still the assistant, including recipe
  staying culinary and still 2/2 locked. One generator, named.

- **F9.** No basin, no `n_macro` as order parameter, no H1.

- **ADR-0015 / ADR-0016 still hold.** This opening is object (a) at
  T=0.3 `W=4096` on `seed_bank_v1`. Do not open the parked arms.

---

## Claims I judge unsupported or overreaching

- **“Twins collapse to the control” as a dynamical claim**, or “a
  one-fact flip does not occupy a distinguishable lock” as sameness.
  Last-band non-rejection is not occupancy of one lock. Waterloo’s
  point Δ did not collapse.

- **Q5 as “the two families did the same thing.”** They share the
  last-band operational verdict. Reactor was never apart. Waterloo
  was apart early and is underpowered late.

- **Each of the ten domain seeds occupies its own tight lock.**
  Ensemble F4 holds; war / biology last-band within is not small.

- **Recovered semantic memory, language models as a class, a basin,
  `n_macro`, α as the headline, T=1.0 as this lock.** Not in this
  report, and they must stay out.

- **CLI separation on the S5.1 embed as F4, or superseded twins
  `run_id`s as F6.**

---

## The seven questions

1. **Does the conclusion follow?** F4: yes, as an *ensemble*
   last-band gap. A positive gap here is not “loops collapsed
   `D_within`”: within *rose*. Different seeds still sit farther
   apart than same-seed pairs on average. F6: the operational
   last-band verdict follows; “collapse” as the contrast going away
   does not (blocking finding 1). Waterloo [−0.394, 0.491] is
   underpowered, not a demonstration of sameness.

2. **Thresholds calibrated?** 0.083 and late Jaccard 0.0122 are
   S4-calibrated (p99 of 1024-token Carroll+Darwin; S4 REVIEW). Not
   moved. love s1 misses both and stays in the tables: right
   treatment; dropping it would change F4 into “locks only,” which
   is not the PLAN. F6 “divergent iff CI excludes 0 from above” is a
   default NHST rule, not a calibrated minimum Δ. Acceptable as the
   *divergent* test; not acceptable as an equivalence test. Residual:
   calibration tokenizer (Llama vs Qwen), already S4 law.

3. **Regime?** Occupancy was *measured* at `W=4096` T=0.3, ten
   seeds, not imported from S4 Q7 at `W=8192` two seeds. Q7 fill is
   scored as the cell mean and named as not per-seed. S2.2 physics /
   surreal: same protocol, different day, cited not regenerated.
   physics s1 last-band dropout is the reuse scar (observation 2).

4. **One instance?** One generator, one T, one W, one provider
   (Alibaba), two embedding spaces, n=2 per seed. Every thesis
   sentence names that process. No leak to “language models” or
   “semantic memory recovered”; the report forbids the latter for S6.

5. **Confounds named?** Degeneracy as surface form, P1, round-trip
   fails, `ep_poll`, family-scope bug, CLI vs assemble, embedding
   level disagreement, dirty `uv.lock`, n=2, provider. Unnamed but
   not flipping: physics last-band missing chunk; love’s clean row
   is Q4 stop 0.907; seed-level stop-forced continuation under an
   ensemble Q4 stop of 0.329. Trajectory-bootstrap is in the F4/F6
   captions (right unit for autocorrelated chunks).

6. **Do the artifacts state what they cannot?**
   `domain_separation_last_band.meta.json`: a positive gap is not
   recovered semantics — that is a real limitation.
   `domain_separation_vs_turnover.meta.json` is stronger (seed shapes
   the lock; not the prompt; not a basin).
   `twin_last_band.meta.json`: “n=4. Not an MSM macrostate.” is a
   caption restatement of F9, not the alternative the figure fails
   to exclude (blocking finding 1).
   PCA panels: illustration only, distances in-plane are not F4.

7. **Negative result softened?** Q4 collapsed was the pre-registered
   prediction, not a failed H1. The interesting wrong (divergent
   last-band twins) did not happen. That is stated. What is sold too
   hard is the *null* as “collapse to the control.” The twin section
   already has “not a precision claim”; the title and §3 last
   sentence do not. Not hedging a failure — overselling a
   precision-limited null. Same fix as finding 1.

---

## Sign-off

**APPROVED WITH CHANGES.** F4 stands. F5 stands. F6’s last-band
operational score stands. The occupancy object is lock vs seed on
this one process, not H1 and not a basin. Close is withheld until
the F6 prose and `twin_last_band` limitations line match the
interval. Then the human closes `--no-ff` into `main`.
