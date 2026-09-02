# Stage 3 review
Reviewer: Cursor Grok 4.6 (scientific supervisor)   Date: 2026-09-01
Gate: **FAIL on this reviewer VM** (`afterlife review --stage s3`, exit 1).
Cause: `runs/s3` is absent. Raw runs are git-ignored; this environment only
has `runs/s0`, `runs/s1`, and a ledger truncated at Stage 1 ($9.0270).
Checks that still PASS on the committed record: `plan.exists`,
`artifacts.bundle` (11/11 with data, captions, limitations),
`budget.reconciled` (stage $0.00 hosted), `report.diagnostics_segmented`,
`report.quotes_text`, `report.scores_predictions`.
SKIPPED: `runs.integrity`, `analysis.degeneracy_labelled`,
`budget.ledger_matches_events`.
WARN: 1 LEAD citation (same leftover as Stage 2).

This review is of the committed PLAN / REPORT / artifacts — the record a
remote reader has. I have not re-hashed generation manifests. Merge still
requires the executor, or a restored snapshot, to show gate exit 0 on a
machine that has `runs/s3` and `runs/s2`.

Verdict: **APPROVED WITH CHANGES**

The stage verdict PARTIAL is the right stage verdict (F6 FAIL as a
validity bar). This review does not upgrade it. It also does not merge.

Do not merge to `main` from this review. The standing instruction is that
the human closes the branch, and only after the blocking findings are
fixed.

---

## Blocking findings

Each names the claim, the problem, and what would resolve it.

### 1. “The reviewer register is instruct-specific” does not follow

**Claim.** REPORT §7: “The reviewer register is instruct-specific. A 1B
base model under the same P1 protocol does not enter it.”

**Problem.** S3.0 is `local-gemma-3-1b-pt` at `W = 256`, 12 turnovers,
local Hugging Face, no chat template. The register it is compared to was
measured on `or-qwen3-8b` instruct at `W = 4096`, hosted, under P1. The
axes that moved at once are: instruction-tuning, family, scale (1B vs
8B), `W` (256 vs 4096), stack (local vs OpenRouter), and chunk size
(256 vs 1024). PLAN §8 already named the `W` transfer risk and F3
forbids reading S3.1 as a base-model result. The *results* paragraph is
careful (“The base model under P1 at this `W` does not become a
reviewer”). The *implication* is a causal isolation the design did not
perform.

**Resolve.** Replace the §7 sentence with the measured object, for
example:

> A 1B pretrained Gemma-3 under P1 at `W = 256` did not enter the
> reviewer register (0/8). That is an existence check on one confound
> axis that is still entangled with family, scale, `W`, and stack.
> Stage 1/2 qwen results stay labelled instruct-under-P1. They are not
> shown to be instruct-*caused*.

Do not put “instruct-specific” in the manuscript from this stage.

### 2. Chapman–Kolmogorov is scored on the 50-state micro-MSM, then read as “the MSM is not Markovian”

**Claim.** F6 FAIL; INDEX / `chapman_kolmogorov.meta.json`: “the MSM is
not Markovian at lag 1 on this sample.” REPORT: “CK fails by a factor of
four to six above the pre-registered 0.15 bar. … That is why F6 is the
gate.”

**Problem.** In `compute_dynamics`, CK is called on k-means
*microstate* assignments with `n_states = K` (50 on the F4 cells, 30 on
glimmer), *before* spectral coarse-graining. There is no CK on the
2–4 macrostate assignment. Methodology §3.5 and the module docstring
say only a coarse-graining that survives CK is a macrostate. The
implemented test never sees that object.

With K = 50 and ~352–359 frames, a cell has ~7 visits. Unvisited rows
are given a self-loop (`T_ii = 1`). The statistic is
`max |T(kτ) − T(τ)^k|`. A single empty-versus-occupied discrepancy
drives the max to 1. Observed values 0.67–1.00 are what a sparse
50-state count matrix produces on a short looping series. They do not
uniquely mean “the process is non-Markov.”

The 0.15 bar is pre-registered (`PLAN` F6, `configs/analysis/dynamics.yaml`)
and not calibrated against a synthetic MSM, a deeptime reference, or
this K / n_frames regime. It is also not scale-aware: the same absolute
threshold is hostile at K = 50 and loose at K = 2. That is a defect
whether or not the result survives it. Here it survives by a wide
margin, so calibration would not flip F6. It still cannot carry the
sentence “not Markovian.”

CLI limitations originally said the test is applied to the MSM, not to
the VAMP-reduced model (methodology §3.5 / ADR-0002 require both). The
published caption dropped that sentence and replaced it with the
stronger reading.

**H1 unsupported still follows**, because `validated` is

```
flat AND ck_pass AND n_macro ≥ 2 AND n_degenerate < n_trajectories
```

and 7/8 or 8/8 F4 trajectories are degenerate. On qwen-raw and 120b,
degeneracy alone zeros `validated` even if CK passed. The conclusion
is overdetermined. The *attribution* to CK is the defect.

**Resolve.** Do one of:

- **(preferred)** Compute CK on the spectral-coarse-grained assignment
  (`n_macro` states) and report that number next to the microstate CK.
  Keep F6 as the pre-registered microstate bar if you want, but stop
  calling it a test of semantic-state Markovianity.
- **Or** rewrite F6 / the caption / REPORT §2 to: “the 50-state
  micro-MSM fails the pre-registered max-abs bar, as expected under
  sparsity and loops; H1 remains unsupported because 7–8/8 trajectories
  are degenerate and `n_macro` is unstable.” Name the object. Do not
  write “the MSM is not Markovian.”

Also add, in threats, that 0.15 was pre-registered rather than
calibrated, and that methodology’s VAMP-reduced CK was not run.

### 3. Q7 / F9: one qwen cell’s current CI excludes 0; J is not H4

**Claim.** F9 PASS: “qwen and 120b CIs reach ~0.” Q7 scored **right**:
“qwen currents consistent with 0.” Caption: “Intervals that reach ~0
are consistent with equilibrium-like currents on this sample.”

**Problem.** From `artifacts/stage-3/dynamics/dynamics_scalars.csv`:

| cell | ‖J‖ | 95% trajectory-bootstrap CI | excludes 0? |
| --- | --- | --- | --- |
| qwen raw / bge-m3 | 0.0320 | [6.8e-17, 0.0257] | no (reaches ~0) |
| qwen raw / qwen3-embed-8b | 0.0288 | [3.8e-17, 0.0275] | no |
| **qwen prefill / bge-m3** | **0.0766** | **[0.00816, 0.0712]** | **yes** |
| qwen prefill / qwen3-embed-8b | 0.0308 | [3.6e-16, 0.0308] | no |
| 120b / bge-m3 | 0.0161 | [4.6e-17, 0.0115] | no |
| 120b / qwen3-embed-8b | 0.0234 | [3.0e-16, 0.0172] | no |
| glimmer (both spaces) | ~0.36–0.38 | [0.16, 0.38] | yes (underpowered; named) |

The point estimate sits above the CI upper bound on several cells
(qwen-raw/bge 0.032 > 0.026; prefill/bge 0.077 > 0.071). The figure
limitations name that pathology. The report’s “reach ~0” sentence does
not.

These currents are `‖J‖_F` of the **K × K microstate** matrix, not
`J_ij` between macrostates. H4 is the latter. A sliding loop chopped
into 50 k-means cells can carry a small directed current that has
nothing to do with semantic circulation. F9 as written allows either
“a CI excluding 0” or “consistent with equilibrium.” The report took
the second branch and the tidy table contradicts it on prefill/bge.

**Resolve.** Score Q7 **partial** or **wrong**. Name the prefill/bge
cell. Write that the reported quantity is microstate `‖J‖_F`, not H4.
Do not claim equilibrium on “qwen.” Glimmer’s excluding-0 interval
stays a 2-trajectory non-claim, as already written.

### 4. Reserved words: “textual attractors” and “converges”

**Claim.** REPORT §2: “All three are textual attractors; they are not
the same attractor.” §7: “the base model also converges, by looping
the seed.”

**Problem.** `docs/glossary.md`: “Attractor” only with demonstrated
timescale separation; otherwise *metastable state* or, here, *fixed
point* / *loop*. “Converges” only with a stated criterion and a CI.
S3.0 *does* have a criterion and a rate (8/8 fixed-point, CI [1, 1]
per temperature in `fixed_point_rates`). Calling that an attractor
imports H1 language onto a surface loop. That is how a negative MSM
stage gets rewritten as “we found attractors.”

**Resolve.** “All three are textual fixed points / loops; they are not
the same loop.” “The base model also reaches a textual fixed point
(8/8, late-phase shingle Jaccard), by looping the seed.” Keep
“semantic state” only in the refusal sentence, which is already
correct.

### 5. Surface table vs Q3: `last_step = silence` on one row

**Claim.** 0/8 produce gemma-4-31b-style silence. Q3 scored **right**.
Criterion: silence = whitespace or recursion marks as in gemma-4-31b.

**Problem.** `s30_surface_labels.csv` row
`local-gemma-3-1b-pt__W256__T1__surreal__s1` has `last_step = silence`
and `last_quote = "I I"`. `last_quarter` is `verbatim_loop`. The
hand table in REPORT §2 calls this an `"I I"` lock, not silence. “I I”
is a token lock, not gemma-4-31b whitespace / recursion marks.

Step-1 reviewer-register 0/8 and last-quarter silence 0/8 hold. The
CSV column contradicts the scored criterion.

**Resolve.** Relabel that `last_step` as `verbatim_loop` / token lock,
or add a sentence that `last_step` used a different rule and Q3 is
scored on last-quarter. Do not leave `silence` in the tidy table next
to a Q3 of “right.”

### 6. F7’s `k_stability` table is not produced by the CLI

**Claim.** F7 PASS: “instability is the result,” citing
`artifacts/stage-3/dynamics/k_stability.md`. n_macro flips across
`K ∈ {50, 100}`.

**Problem.** `afterlife analyze dynamics` fits one K
(`n_microstates = 50`, or the cap) and writes scalars / ITS / CK /
currents / occupancy-parquet / Leiden ARI. There is no `k_stability`
symbol in `src/`. `afterlife report` only rebuilds `INDEX.md`. The
K = 50 rows match `dynamics_scalars`. The K = 100 rows have no other
home. `afterlife reproduce` of
`s3-dynamics-20260901T184826Z-f21d5908` /
`s3-dynamics-20260901T184929Z-b7c4d0c9` will not regenerate that
table.

F7 can still be *pointed at* without K = 100: at the fitted K = 50,
qwen-raw is 2 vs 1 across spaces and qwen-prefill is 4 vs 1. 120b is
2 vs 2 at K = 50, so the K = 100 sweep is what makes 120b unstable on
the count.

**Resolve.** Either wire a K-grid loop that writes `k_stability` as a
first-class artifact and regenerate it from the same embeddings, or
score F7 from the cross-space `n_macro` at the fitted K, mark 120b as
the cell that needs the sweep, and retire the unreproducible table.
Do not leave a headline exit criterion citing a table the supported
entry point cannot build.

---

## Non-blocking observations

1. **H1 unsupported is the right scientific result** on this sample.
   The eligible Stage 2 arms are loops (7–8/8 degenerate). An MSM on a
   looping reviewer page will invent microstates inside the loop. Q4
   predicted that. Scoring it **right** is honest, not hedged.

2. **S3.0 surface result is real and well quoted.** 0/8 reviewer
   register at step 1; 8/8 looping by last quarter; fill 1.00 in
   quarter 4; stop ≤ 1.5%; $0; 8/8 COMPLETED. The three quotes (sliding
   Polyakov seed-echo, “register of dissent” loop, `/1/1` lock) are
   what the metrics say. T = 1.0 replacing a clean seed-echo with a
   shorter token lock is a finding, not a rescue.

3. **T = 0.3 physics s1 and s2 are bit-identical** on every degeneracy
   metric and on both quotes. That is stronger than “the same sliding
   sentence.” Effective independent n at T = 0.3 physics is 1, not 2.
   0/8 and 8/8 still hold. Do not cite “eight independent trajectories”
   for a determinism claim without saying two of them are the same
   string. Local `temperature = 0.3` can be near-greedy; name that.

4. **ADR-0010 sample restriction was respected.** No gemma-silence, no
   20b, no glimmer empty-EOS, no pooled mixed process. S2.1 leftover
   qwen (2 traj) excluded; S2.2 is the qwen cell. Prefill is a contrast
   arm, not the default. Glimmer is labelled underpowered (Q9 right).

5. **Q5 and Q10 scored wrong, on the record.** Leiden–MSM ARI on
   qwen-embed is 0 because `n_macro = 1` against a multi-community
   Leiden partition. Collapse is not agreement. That is the one
   tempting story they refused. Keep the refusal.

6. **Q8 as “partial” is slightly soft.** The prediction was same
   `n_macro` and same “no gap.” `n_macro` is 2 vs 4 and ITS flatness
   disagrees. Unvalidated-vs-unvalidated is not what was predicted.
   Scoring **wrong** would be cleaner. Not blocking: the numbers are
   in the table.

7. **CK range “0.67–1.00”** is the global min over (cell, k), from
   qwen-raw / qwen3-embed k = 2 and glimmer-embed k = 2
   (`chapman_kolmogorov.data.parquet`). The §2 table’s `ck_max_error`
   column (max over k per cell) starts at 0.73. Say which.

8. **n-gram “0.84–0.98”** is `mean_ngram_repetition`; the lowest mean
   is 0.837 (T = 1 surreal s1). `max_ngram_repetition` goes to 0.996.
   Ten times the 0.083 threshold either way. The 1024-vs-256
   calibration mismatch cannot flip 8/8 looping. Named in threats.

9. **Cross-space MSM ARI = 0 on qwen-raw** is in the Leiden figure
   limitations and the report, not in a tidy frame. When one side is a
   single label, ARI is identically 0. That is arithmetic, not a
   robustness result. Fine as Q10 **wrong**; do not cite it as a
   measured disagreement between two rich partitions.

10. **Occupancy vs turnover** was promised in PLAN §4 item 5.
    `compute_dynamics` builds the frame and the CLI writes
    `dynamics_occupancy.parquet` into the *run*. No stage figure.
    Not an exit criterion. Either add the figure or strike the promise
    in the same commit as the report.

11. **Methodology debt, all the same direction (missing, not
    inverted).** Name in threats, do not silently carry:
    - VAMP-2 / VAMP-E out-of-sample CV for `n_pca`, `n_vamp`, `K` is
      not run. Grids exist in `dynamics.yaml`; `compute_dynamics` uses
      defaults (`n_pca = 128`, `n_vamp = 10`, `K = 50`) and records
      `split: "full"`.
    - tICA *is* fit; `vamp_tica_angle` is 0.47–0.71 rad on F4 cells
      and ~1.35 on glimmer. ADR-0002 says that discrepancy is a
      reported irreversibility diagnostic. It is a CSV column, not a
      REPORT sentence.
    - Leiden resolution is not swept (`leiden_resolution = 1.0`).
    - “PCCA+” in the plan is k-means on leading right eigenvectors of
      `T`. Acceptable as spectral coarse-graining; do not cite Röblitz
      / Weber PCCA+ as the estimator that was run.
    - `mean_dwell_chunks` of 6e13–1e14 is the mean of
      `1 / max(1 − T_ii, 1e-15)` including unvisited self-loops. The
      report does not quote it. The tidy table should not either, or
      should drop unused states first.
    - No unit test calls `chapman_kolmogorov` on a short looping
      series. The file header says that is why the tests exist.

12. **Master plan still says `S3 is next` / `← current`.** PLAN’s
    definition of done asked only for consistency with ADR-0012, which
    is there (embeddings deferred, no OpenRouter). Stage-close still
    needs the research plan to record S3 PARTIAL and point at S4, with
    S3.0 embeddings remaining the open confound. Do that in the same
    commit as the prose fixes, with no new ADR beyond a one-line
    amendment if the plan’s S3 exit-criteria block is updated to match
    what was actually measured.

13. **Project spend “$11.57 of $50”** is inherited from Stage 2 close.
    This VM’s ledger is $9.0270 (s0 + s1 only). I cannot reconcile
    F10’s project total here. Stage 3 hosted $0.00 I *can* see (no
    `s3-*` ledger rows). Keep F10; do not let the project total drift
    between reports without a ledger citation that exists on the
    machine that writes the report.

14. **Frozen-label Leiden–MSM ARI bootstrap** is named. Good. Do not
    upgrade it to a refit CI in later prose.

15. **S3.0 has no embeddings.** Geometry, MSD, seed-separation, and
    any MSM of the base-model loop are not this stage. F3 PASS is
    correct as long as §7 does not sneak a geometric claim through
    “instruct-specific.”

16. **One LEAD citation** remains in `docs/literature/related-work.md`.
    Same Stage 2 leftover. Fine while `paper/main.tex` is empty.

---

## Claims I judge supported

- **On this restricted instruct-under-P1 sample, H1 has no validated
  macrostate.** `validated_macrostates = 0` on all eight process ×
  space cells. 7–8/8 F4 trajectories are degenerate. `n_macro` at the
  fitted K already disagrees across spaces on qwen. Do not name MSM
  cells “semantic states” from this sample. This is a successful
  negative stage on the dynamics branch.

- **Qwen (both mechanisms) and gpt-oss-120b look like one absorbing
  textual loop, not a multi-state MSM.** That is Q4 and Q6, scored
  right. Prefill vs raw agree on “unvalidated,” which is the part of
  Q8 that holds.

- **`local-gemma-3-1b-pt` at `W = 256`, 12 turnovers, does not open in
  the reviewer register (0/8) and is a loop by the last quarter
  (8/8).** Q1, Q2 right. Fill 1.00 in Q4 is a property of this base
  model, not of P1 (instruct qwen’s fill decay does not appear). $0.
  Run `s3-local-base-20260901T184812Z-cc80633b`.

- **S3.0’s late-run collapse is seed-echo or token lock, not
  gemma-4-31b silence, on the last-quarter criterion.** Q3 right once
  finding 5 is cleaned. “I I”, “Is This”, `/1/1`, “Deformation phase.”
  are not whitespace / recursion marks.

- **T = 1.0 is not a diffusion regime for this 1B base model at
  `W = 256`.** It is a different degeneracy. Do not take H5 from
  Stage 3. The report already says so.

- **Glimmer’s 2-trajectory MSM is underpowered and is not a
  macrostate or circulation claim.** Q9 right. `‖J‖ ≈ 0.36` with
  n = 2 stays parked.

- **No OpenRouter / RouterAI spend this opening.** ADR-0012 held.
  Stage ledger $0.00.

- **The estimator is not the thing that failed H1.** Tests recover a
  two-state HMM and a driven cycle; a reversible chain has `J ≈ 0`.
  That sentence in §7 is supported as far as the synthetic tests go.
  It does not license reading the real-series CK numbers as a clean
  non-Markov test (finding 2).

---

## Claims I judge unsupported or overreaching

- **Any sentence whose subject is “instruction tuning” as the cause
  of the reviewer register.** One 1B Gemma at `W = 256` did not enter
  it. That is not a cause.

- **“The MSM is not Markovian at lag 1.”** The 50-state micro-MSM
  failed an uncalibrated max-abs bar. That is the sentence.

- **H4 (macrostate currents ≠ 0), or its negation, from this sample.**
  The reported `‖J‖` is microstate. Prefill/bge’s CI excludes 0.
  Equilibrium-like on “qwen” is not a claim the table supports.

- **A validated timescale, dwell time, entropy rate, or occupancy
  curve.** `mean_dwell_chunks` is an unused-state artifact.
  Occupancy-vs-turnover was not published. Entropy rate on glimmer
  bge is `-0`.

- **Cross-space robustness of a state decomposition.** Q10 is 0
  because one space chose `n_macro = 1`. That is not ARI between two
  partitions.

- **Class-level statements about base models, or transfer of the
  S3.0 loop to `W = 4096`.** Threats name this. §7 must keep it.

- **Determinism of hosted APIs.** The bit-identical T = 0.3 physics
  pair is a local-sampler observation. ADR-0010 still: no arm except
  glimmer may claim seeded determinism on the hosted stack.

---

## The seven questions

1. **Does the conclusion follow?** The conclusions the report *should*
   be judged on — “H1 unsupported on this degenerate instruct sample”
   and “this 1B base model at `W = 256` loops the seed and does not
   become a reviewer” — follow from the tidy tables and the quoted
   text. The conclusions in §7 that isolate instruction-tuning, and
   the CK caption that declares non-Markovianity, do not. Finding 1
   and 2 are those two sentences.

2. **Thresholds calibrated?** Degeneracy 0.083 is the Stage 1
   calibration, reused at 256-token chunks with the mismatch named;
   raw rates (0.84–0.98) are not near the edge. Fixed-point is the
   Stage 1/2 late-phase shingle Jaccard, in-regime for S3.1, applied
   to S3.0 with the same named chunk-size caveat. CK 0.15 is
   pre-registered and not calibrated; it is the defect in finding 2.
   ITS “flat” = < 50% relative change across adjacent `τ` is a
   heuristic; mixed results are reported, not used to validate.
   Spectral-gap ratio 2.0 and `n_macro_max = 4` are heuristics;
   instability across K is the F7 result, so they did not quietly
   pick a pretty `n_macro`.

3. **Regime?** S3.1 is the Stage 2 eligible regime (`W = 4096`,
   ~12 turnovers, both temperatures, both spaces) and is labelled
   instruct-under-P1. S3.0 is a different regime (`W = 256`, 1B,
   local, base). F3 is correct only if §7 does not export S3.0 into
   the Stage 2 sentence. Degeneracy labels were joined before
   `validated` is set. Prefill was not imported from the 28-token
   probe. Good. Microstate CK and microstate J are the wrong object
   for “semantic state” / H4 (findings 2 and 3).

4. **One instance?** S3.0 is one generator, one `W`, two seeds, two
   temperatures, two stochastic ids (one pair bit-identical). The
   supported claim is about that instance. S3.1 is three processes ×
   two spaces, never pooled — the one generalisation the design
   allows is “not on this restricted instruct sample,” and that is
   what Q4/Q6 say. “Instruct-specific” generalises off one instance
   on the wrong axes.

5. **Confounds named?** Degeneracy, `W = 256`, chunk 256 vs 1024,
   deferred embeddings, instruct-under-P1, temperature pooling
   (declared), frozen-label ARI bootstrap, last-short-block / almost-`T`
   on 120b (inherited), local vs router stack, forced continuation
   (S3.0 stop is ~0, so that particular Stage 2 confound is *absent*
   here — a finding). Unnamed in the report, named here: CK object
   (micro vs macro), J object (micro vs H4), VAMP CV not run,
   tICA angle not discussed, `k_stability` not in the CLI,
   bit-identical T = 0.3 physics pair as a collapsed replicate.

6. **Do the artifacts state what they cannot?** Gate: 11/11 have a
   limitations line that is not a caption restatement. Geometry
   scalars are not claimed. PCA/UMAP are not used for a number.
   Degeneracy-on-loops is in the ITS and dynamics-scalars
   limitations. The CK limitations line is the one that overreaches
   (“not Markovian”) relative to what the test can exclude. Surface
   limitations correctly refuse transfer to `W = 4096`.

7. **Negative result softened?** No, on the predictions that matter.
   Q4, Q5, Q6, Q10 are scored plainly. F6 is FAIL and is called the
   finding. “H1 is unsupported on this sample” is the right sentence.
   Softening, where it exists, is the *upgrade* of that negative
   into “textual attractors” and “instruct-specific” — findings 1
   and 4. That is the opposite of burying a negative; it is
   converting a negative into a mechanism.

---

## What would make this APPROVED

Executor-only. I am not rewriting the code in this review.

1. Reword REPORT §7 (finding 1) and the attractor / converges
   sentences (finding 4).
2. Reword F6 / CK caption / §2 attribution, or add macrostate CK
   (finding 2).
3. Rescore Q7; name prefill/bge; name the J object (finding 3).
4. Fix the `last_step = silence` row (finding 5).
5. Either reproduce `k_stability` from the CLI or retire it and
   score F7 from the fitted-K cross-space counts (finding 6).
6. On a machine that has `runs/s3`, `afterlife review --stage s3`
   must exit 0.

Optional in the same commit, not blocking for a second look:
occupancy figure or a struck PLAN line; tICA angle in one REPORT
sentence; VAMP-CV / VAMP-CK named as not-run; research-plan status
line set to S3 PARTIAL / S4 next; Q8 scored wrong.

---

## Sign-off

The mechanical gate cannot pass on this VM. The committed artifact
bundles are self-contained, the predictions are scored, hosted spend
is $0, and the scientific *payload* — no validated macrostate on the
restricted instruct sample; a 1B base model at `W = 256` loops the
seed and does not become a reviewer — is supported by the tables and
the quotes.

The sentences that convert that payload into a cause (instruction
tuning) or a dynamical diagnosis (non-Markov MSM, equilibrium
currents on qwen, “attractors”) are not supported. Those are the
changes. After they land, this is an APPROVED PARTIAL stage: a
negative result, stated as one, with the instruct-under-P1 confound
still open for geometry and for any later H1 / H4 claim.
