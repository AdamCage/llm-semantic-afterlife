# Stage 4 review
Reviewer: scientific supervisor   Date: 2026-09-05
Gate: **FAIL on this reviewer VM** (`afterlife review --stage s4`).
Cause: `runs/s4` is absent. Raw runs are git-ignored. Artifact bundles
on the committed record: 60/60 PASS. Last CI on `cursor/stage-4-6dce`
is green. Generate manifests were not re-hashed here. The executor
previously showed gate exit 0 on a machine that has `runs/s4`.

Verdict: **APPROVED**

Do not merge from this review. Do not regenerate S2.2 or Stage 4
generate. Do not open S5 generate.

---

## Answer to the stage question

On `or-qwen3-8b` under P1 `raw_completion`, temperature moves the
looping rate only at T=1.5. T=1.0 is a lock (4/4 degenerate) at both
`W ∈ {4096, 8192}`. The same holds for T=0.3 and T=0.7. `W` does not
unlock the lock rate at T≤1.0. T=1.5 is the only cell with a defined
clean-`α`; the exponent is subdiffusive in both spaces and is not
diffusion. H5 is absent on this grid because there is no low-T cell
without loops.

Numbers in [`artifacts/stage-4/grid/`](../../../artifacts/stage-4/grid/)
match the report: 24/24 degenerate at T≤1.0; T=1.5 `W=4096` 0/4;
T=1.5 `W=8192` 2/4, CI [0, 1]. Clean-`α` only at T=1.5; all four CIs
exclude `α = 1`.

---

## Blocking findings

None.

---

## Non-blocking observations

1. **The 4/4 lock at T≤1.0 rests on the joint 24/24, not on the
   bootstrap CI [1, 1].** Four identical Bernoulli outcomes collapse
   that interval. Do not carry `[1, 1]` into the manuscript as
   uncertainty.

2. **H5 absent is the F6 “comparison undefined” branch**, not “we
   measured two clean-`α`s and they overlapped.” Do not write “we
   measured H5 and it is absent.”

3. **0.083 is calibrated and in-regime.** It is the p99 of 237
   1024-token chunks (Carroll+Darwin), the same `chunk_size` as S4.
   The threshold was not moved. At T≤1.0 it is not load-bearing:
   several rows are mode 2 (Jaccard ≥ 0.0122), including T=0.7
   physics s1 at `looping_fraction = 0.0465`. Shifting 0.083 to 0.05
   or 0.15 does not flip those cells. Residual gap: calibration
   tokenizer (Llama vs Qwen). Not a reason to move the bar.

4. **Fill at `W=8192` was measured, not imported from 4096.** Q4 is
   wrong at T=1.0 (Δ = 0.311: 0.745 vs 0.434). S3.0 `W=256` was not
   transferred here. S2.2 reuse is the same protocol, a different
   day.

5. **The two T=1.0 locks are not one mechanism.** At `W=4096` Q4
   stop is 0.954; at `W=8192` it is 0.450. Do not identify them.

6. **T=1.5 clean ≠ left the register is an existence proof**, not a
   band-level claim. The quoted `W=8192` T=1.5 physics s1 chunk is
   still an assistant / toolkit pitch. “The whole T=1.5 residual is
   reviewer register” is early for the manuscript: one of six clean
   trajectories is quoted. Observation, not a blocker.

7. **Thin, non-flipping confounds already on the record:**
   `continuation_instruction`, the open instruct-confound, register
   judged from one quote, CLI ensemble MSD on the mixed sixteen
   (`α = 0.205` in `INDEX.md` — the Stage 1.0 trap; the report does
   not cite it). Also named: degeneracy as surface form, P1 vs true
   sliding attention, n=4 / n=2, fill collapse as a trajectory,
   stop-forced continuation, two tokenizer round-trip fails,
   provider, dirty embed tree.

---

## Claims I judge supported

- **On `or-qwen3-8b` under P1, T≤1.0 is a lock at both W.** 24/24
  degenerate. Every sentence that names this names that one process.

- **T=1.5 is the only defined clean-`α`, and it is not diffusion.**
  From [`clean_alpha_by_cell.csv`](../../../artifacts/stage-4/grid/clean_alpha_by_cell.csv).
  Both spaces, both windows: CIs exclude `α = 1`.

- **H5 is absent on this grid** because the low-T comparison arm is
  undefined. F6’s absent branch.

- **Q4 and Q6 scored wrong, on the record.** Fill does not transfer
  at T=1.0. Both T=1.5 cells have `n_clean ≥ 2`.

- **Q7 last-band gap at `W=8192` T=0.3 excludes 0 in both spaces**,
  under same-(W, T) pairing only.

- **ADR-0015 follows from the grid.** S5 must not open at T=1.0 as a
  semantic operating point. Pick (a) lock occupancy vs seed or
  (b) the T=1.5 residual before any generate.

- **One process is not a class.** Stage 2 already showed gemma-4-31b
  and gpt-oss-120b disagree with qwen.

---

## Claims I judge unsupported or overreaching

- **“We measured H5 and it is absent.”** There is no low-T clean-`α`
  to compare.

- **T=1.5 as diffusion, or as having left the register.** Clean-`α`
  is subdiffusive; the quoted clean text is still the assistant
  register. Band-level register claims wait for more quotes.

- **The two T=1.0 locks as one mechanism.** Stop rates differ across
  W (0.954 vs 0.450 in quarter 4).

- **A W-effect on lock rate at T≤1.0.** Looping CIs overlap; the
  4/4 lock is the result.

- **`n_macro` as an order parameter.** Not in this report.

- **Class-level temperature or window claims.** One generator, one
  protocol, one pin.

---

## The seven questions

1. **Does the conclusion follow?** Yes. “T≤1.0 is a lock at both W”
   from the joint 24/24. “T=1.5 is the only clean-`α`, not
   diffusion” from `clean_alpha_by_cell.csv`. “H5 is absent” is the
   undefined-comparison branch.

2. **Thresholds calibrated?** 0.083 is calibrated in-regime (p99 of
   237 × 1024-token Carroll+Darwin chunks). Not moved. Not
   load-bearing at T≤1.0 (mode 2 / Jaccard). Residual tokenizer
   mismatch is named.

3. **Regime?** Fill at `W=8192` was measured in that regime. Q4
   failed the transfer we have been wrong about before. S3.0
   `W=256` was not imported. S2.2 reuse is the same protocol.

4. **One instance?** Every thesis is `or-qwen3-8b` / P1 / Alibaba.
   Not generalised.

5. **Confounds named?** Degeneracy as surface form, P1 vs sliding
   attention, n=4 / n=2, fill collapse as a trajectory, stop-forced
   continuation (Q4 stop 0.954 at `W=4096` T=1.0), two round-trip
   fails, provider, dirty embed tree. Thin leftovers listed above
   do not flip the headlines.

6. **Do the artifacts state what they cannot?** Grid captions and
   the report’s threats name the alternatives. Do not read the S4.2
   CLI `separation_per_band` as Q7. Do not cite the mixed-16
   ensemble MSD in `INDEX.md` as confinement.

7. **Negative result softened?** No. Q4 and Q6 are **Wrong** in the
   open. Clean ≠ left-the-register is quoted, not hedged.

---

## Sign-off

APPROVED. The stage question is answered on this one process. Merge
is withheld. S5 stays closed until a PLAN picks object (a) or (b)
and a generate-yes exists (ADR-0015).
