# Stage 3 report — no validated macrostates; a base model loops the seed

**Status.** Computations finished 2026-09-01. Overall verdict: **PARTIAL**.
S3.0 answered the base-model question from generated text. S3.1 found no
validated MSM macrostate on the restricted instruct sample. S3.0 embeddings
remain deferred (ADR-0012). OpenRouter was not called. Hosted spend: **$0.00**.

This revision answers the six blocking findings in
[`REVIEW.md`](REVIEW.md) (APPROVED WITH CHANGES). It does not upgrade the
stage verdict.

Branch: `cursor/stage-3-6dce`. Plan: [`PLAN.md`](PLAN.md).

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| F1 | S3.0 generated | **PASS** | 8/8 trajectories COMPLETED, `s3-local-base-20260901T184812Z-cc80633b` |
| F2 | S3.0 surface labelled | **PASS** | [`s30_surface_labels.md`](../../../artifacts/stage-3/surface/s30_surface_labels.md); 0/8 reviewer register at step 1; `last_step` uses the same criterion as last-quarter (`token_lock` ≠ silence) |
| F3 | Confound status explicit | **PASS** | embeddings deferred; every S3.1 sentence below is instruct-under-P1. S3.0 is one 1B Gemma at `W = 256`, not a cause |
| F4 | MSM on the restricted sample | **PASS** | 6 cells with `n_frames ≥ 80` (qwen raw/prefill × 2 spaces, 120b × 2). Glimmer 90 frames, underpowered, not padded. `s3-dynamics-20260901T204521Z-f21d5908`, `s3-dynamics-20260901T204549Z-b7c4d0c9`. S2.1 leftover qwen (2 traj) excluded |
| F5 | Implied timescales scored | **PASS** | [`implied_timescales.meta.json`](../../../artifacts/stage-3/dynamics/implied_timescales.meta.json). Mixed flatness; none validated |
| F6 | Chapman–Kolmogorov < 0.15 | **FAIL** | scored on the **50-state micro-MSM** (pre-registered object). Per-cell max over `k` is 0.73–1.00. Global min over (cell, `k`) is 0.67. Macro CK is a different object and is reported beside it; it is not F6. [`chapman_kolmogorov.meta.json`](../../../artifacts/stage-3/dynamics/chapman_kolmogorov.meta.json) |
| F7 | Macrostate stability or its absence | **PASS** | instability is the result. `k_stability` is a CLI refit over the plan's `K` grid ([`k_stability.md`](../../../artifacts/stage-3/dynamics/k_stability.md)). At fitted `K = 50`, qwen-raw is 2 vs 1 across spaces; 120b needs the `K = 100` row to flip (2 vs 4 / 2 vs 1) |
| F8 | Leiden–MSM ARI with CI | **PASS** | per process × space in [`leiden_msm_agreement.meta.json`](../../../artifacts/stage-3/dynamics/leiden_msm_agreement.meta.json) |
| F9 | Currents signed | **PASS** | reported quantity is microstate `‖J‖_F`, not H4. Prefill / bge-m3 CI excludes 0; other qwen and 120b CIs reach ~0; glimmer n = 2. [`probability_currents.meta.json`](../../../artifacts/stage-3/dynamics/probability_currents.meta.json) |
| F10 | No OpenRouter spend | **PASS** | Stage 3 ledger $0.00 hosted; project $11.57 of $50 in `runs/_ledger/spend.jsonl` on the machine that wrote this report |

F6 failed as a *pre-registered microstate bar*. That is not a diagnosis that
"the process is non-Markov." H1 is unsupported on this sample because 7–8/8
F4 trajectories are degenerate and `n_macro` is unstable. Degeneracy alone
zeros `validated` on qwen-raw and 120b even if micro-CK had passed.

## 2. Results

### S3.0 — `local-gemma-3-1b-pt` at `W = 256`, 12 turnovers

`run_id`: `s3-local-base-20260901T184812Z-cc80633b`.
8/8 completed. 96 chunks. **$0.00**. Fill ≈ 1.00 in every quarter
([`artifacts/stage-3/protocol/`](../../../artifacts/stage-3/protocol/)).
Stop rate ≤ 1.5%. Fixed-point rate 8/8
([`artifacts/stage-3/rates/`](../../../artifacts/stage-3/rates/));
late-phase shingle Jaccard, CI [1, 1] per temperature.
Degeneracy 8/8, looping fraction 1.0, mean n-gram repetition 0.84–0.98
(`s3-degeneracy-20260901T193542Z-f76d2086`). `max_ngram_repetition` reaches
0.996.

The degeneracy threshold 0.083 was calibrated at 1024-token chunks; these
chunks are 256. A rate ten times the threshold is not a calibration edge
case.

**Step-1 / last-quarter / last-step criterion.** Reviewer register = the
completion self-reviews the prompt ("you've provided", "well-structured",
"comprehensive overview", "thank you for sharing"). Silence = whitespace
or recursion marks as in gemma-4-31b. Verbatim loop = a ≥40-character
span repeats in the same completion. Token lock = a short repeated token
or phrase that is not whitespace/recursion (`I I`, `Is This`, `/1/1`).
Continuation = none of those. `last_step` uses this same rule.

| trajectory | step 1 | last quarter | last step |
| --- | --- | --- | --- |
| T=0.3 physics s1, s2 | continuation (sliding seed-echo) | verbatim loop | continuation (still the seed-echo) |
| T=0.3 surreal s1 | verbatim loop | verbatim loop | verbatim loop |
| T=0.3 surreal s2 | continuation (then locks) | verbatim loop | continuation |
| T=1.0 physics s1 | continuation (already collapsing) | verbatim loop | continuation (`Deformation phase.`) |
| T=1.0 physics s2 | continuation | verbatim loop | continuation (`Is This`) |
| T=1.0 surreal s1 | continuation | verbatim loop | token lock (`I I`) |
| T=1.0 surreal s2 | continuation (already "the meaning of") | verbatim loop | continuation (`/1/1/1`) |

**0/8** open in the reviewer register. **0/8** last-quarter silence.
**8/8** are a loop by the last quarter. The tidy `last_step` for T=1.0
surreal s1 is `token_lock`, not `silence`: "I I" is a token lock, not
gemma-4-31b whitespace / recursion marks.

T=0.3 physics s1 and s2 are **bit-identical** on every degeneracy metric
and on both quotes. Effective independent n at that cell is 1, not 2.
0/8 and 8/8 still hold. Local `temperature = 0.3` can be near-greedy.

Quoted, three points:

T=0.3 physics s1, step 1 and step 96 — the window slides over the seed:

> the choice of update scheme is not a detail but the central practical
> problem. In the deconfined phase the Polyakov loop acquires a nonzero
> expectation value, and the

T=0.3 surreal s1, every step:

> the register of dissent had been sealed inside the lowest octave of the
> expedition, and the register of dissent had been sealed inside the
> lowest octave of the expedition, and

T=1.0 surreal s2, last step:

> /1/1/1/1/1/1/1/1/1/1/1/1/1/1/1/1

The base model under P1 at this `W` does not become a reviewer. It
repeats the seed, or it collapses. That is a different textual fixed
point from qwen's reviewer page and from gemma-4-31b's silence. All
three are textual fixed points / loops; they are not the same loop.

Geometry of S3.0 is **not** reported. Embeddings were not computed.

### S3.1 — MSM on the restricted instruct sample

Instruct-under-P1 only. Source embeddings:
`s2-embed-mechanism-20260901T131051Z-55761049` (qwen both mechanisms),
`s2-embed-model-axis-20260901T125626Z-50d60286` (120b; glimmer `T=0.3`
physics). S2.1 leftover qwen (2 traj, 90 frames) was excluded; S2.2 is
the qwen cell.

CK micro = max over `k ∈ {2, 3}` of `|T(kτ) − T(τ)^k|` on the k-means
assignment (F6). CK macro = the same statistic on the spectral
coarse-graining (not F6).

| process | space | n_traj | n_frames | degenerate | n_macro | ITS flat | CK micro | CK macro | validated | ARI(Leiden, MSM) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen raw | bge-m3 | 8 | 359 | 8 | 2 | yes | 0.90 | 0.022 | no | 0.068 [0.00, 0.42] |
| qwen raw | qwen3-embed-8b | 8 | 359 | 8 | 1 | no | 0.89 | — | no | 0.00 |
| qwen prefill | bge-m3 | 8 | 359 | 7 | 4 | no | 0.97 | 0.042 | no | 0.49 [0.37, 0.90] |
| qwen prefill | qwen3-embed-8b | 8 | 359 | 7 | 1 | no | 1.00 | — | no | 0.00 |
| gpt-oss-120b | bge-m3 | 8 | 352 | 8 | 2 | yes | 0.75 | 0.00 | no | 0.048 [0.00, 0.37] |
| gpt-oss-120b | qwen3-embed-8b | 8 | 352 | 8 | 2 | no | 0.90 | 0.00 | no | 0.050 [0.00, 0.36] |
| glimmer T=0.3 physics | bge-m3 | 2 | 90 | 2 | 3 | no | 0.73 | 0.24 | no | 0.52 [0.00, 0.52] |
| glimmer T=0.3 physics | qwen3-embed-8b | 2 | 90 | 2 | 4 | no | 0.80 | 0.61 | no | 0.65 [0.00, 0.65] |

`validated_macrostates = 0` on every cell. The 50-state micro-MSM fails
the pre-registered 0.15 bar, as expected under sparsity and loops (an
unvisited self-loop versus an occupied row drives the max toward 1; a
unit test recovers CK = 0 on an exact two-state alternation and CK > 0.9
on that discrepancy). Several F4 cells *pass* 0.15 after coarse-graining
(qwen/120b on bge-m3: 0.00–0.04). That is a 2–4 state partition of a
loop, not a validated semantic-state model. H1 remains unsupported
because 7–8/8 trajectories are degenerate and `n_macro` is unstable.

`n_macro` at `K = 50` vs `K = 100` does not agree on any F4 process ×
space ([`k_stability.md`](../../../artifacts/stage-3/dynamics/k_stability.md),
produced by `afterlife analyze dynamics`). At the fitted `K = 50`,
qwen-raw is already 2 vs 1 across spaces; 120b is 2 vs 2 and only flips
when the sweep is included. Cross-space ARI of MSM labels on qwen is
**0** because one space chose `n_macro = 1`. That is arithmetic, not a
robustness result between two rich partitions.

tICA / VAMP principal angle on F4 cells is 0.47–0.71 rad; glimmer is
~1.35 rad. That discrepancy is the irreversibility diagnostic ADR-0002
asked for; it is not a validated current.

Almost every trajectory in the F4 cells is degenerate. An MSM on a
looping reviewer page will invent microstates inside the loop. That is
why Q4 predicted no validated gap.

Reported currents are **microstate** `‖J‖_F`, not H4 (`J_ij` between
macrostates):

| cell | ‖J‖_F | 95% trajectory-bootstrap CI | excludes 0? |
| --- | --- | --- | --- |
| qwen raw / bge-m3 | 0.0320 | [6.8e-17, 0.0257] | no (reaches ~0) |
| qwen raw / qwen3-embed-8b | 0.0288 | [3.8e-17, 0.0275] | no |
| **qwen prefill / bge-m3** | **0.0766** | **[0.00816, 0.0712]** | **yes** |
| qwen prefill / qwen3-embed-8b | 0.0308 | [3.6e-16, 0.0308] | no |
| 120b / bge-m3 | 0.0161 | [4.6e-17, 0.0115] | no |
| 120b / qwen3-embed-8b | 0.0234 | [3.0e-16, 0.0172] | no |
| glimmer (both spaces) | ~0.36–0.38 | [0.16, 0.38] | yes (n = 2; not a claim) |

The point estimate sits above the CI upper bound on several cells
(qwen-raw/bge 0.032 > 0.026; prefill/bge 0.077 > 0.071). The figure
limitations name that pathology. We do not claim equilibrium on "qwen."
Glimmer's excluding-0 interval stays a 2-trajectory non-claim.

Occupancy versus turnover is in
[`occupancy_vs_turnover`](../../../artifacts/stage-3/dynamics/occupancy_vs_turnover.meta.json).
It is a partition of the loop. Do not read a dwell or a basin from it.

## 3. Prediction vs outcome

| # | Prediction | Confidence | Observed | Score |
| --- | --- | --- | --- | --- |
| Q1 | gemma-3-1b-pt does not open in the reviewer register | 0.70 | 0/8 | **right** |
| Q2 | ≥ half of S3.0 degenerate by the last quarter | 0.75 | 8/8, looping fraction 1.0 | **right** |
| Q3 | S3.0 does not produce gemma-4-31b silence | 0.50 | last-quarter collapse is seed-echo or token lock (`Is This`, `/1/1`, `I I`), not whitespace/recursion | **right** |
| Q4 | qwen MSM has no validated timescale gap | 0.65 | validated=0 both mechanisms both spaces; 7–8/8 degenerate | **right** |
| Q5 | Leiden–MSM ARI on qwen > 0.4 | 0.55 | raw/bge 0.068; prefill/bge 0.49; embed spaces 0.00 | **wrong** |
| Q6 | 120b looks like qwen on F5–F7 | 0.60 | validated=0, micro-CK fail, n_macro unstable | **right** |
| Q7 | qwen currents consistent with 0 | 0.60 | 3/4 qwen cells reach ~0; prefill/bge CI excludes 0; quantity is microstate `‖J‖_F`, not H4 | **partial** |
| Q8 | prefill vs raw agree on F5/F7 verdict | 0.70 | both unvalidated, but n_macro 2 vs 4 and ITS flatness disagree — that is not the predicted agreement | **wrong** |
| Q9 | glimmer MSM is underpowered | 0.85 | 2 traj, 90 frames, labelled underpowered | **right** |
| Q10 | cross-space MSM ARI on qwen-raw > 0.3 | 0.50 | 0.00 because one space chose n_macro=1 | **wrong** |

Q5 was the tempting one: if both methods collapse to one region, ARI
should be high. On qwen-embed `n_macro=1` against a multi-community
Leiden partition, ARI is zero. Collapse is not the same thing as
agreement.

## 4. Surprises

- **The base model fills every block.** Fill 1.00 ± 0.00 in quarter 4.
  Instruct qwen's fill decay is not a property of P1. It is a property
  of that model trying to stop. S3.0 stop is ~0, so the Stage 2
  forced-continuation confound is *absent* here.
- **T=0.3 physics s1 and s2 are bit-identical.** Seeded local
  generation at `temperature=0.3` reproduced the same string. That is a
  local-sampler observation, not a claim about hosted APIs.
- **T=1.0 does not rescue the process.** It replaces a clean seed-echo
  with a shorter token lock. Higher temperature here is a different
  degeneracy, not diffusion.
- **Macro CK can pass while micro CK fails.** qwen/120b on bge-m3 have
  macro max-abs 0.00–0.04 against micro 0.75–0.97. The 50-state bar is
  hostile under sparsity; a 2-state partition of a loop is not H1.

## 5. Threats to validity

- **`W = 256` is not `W = 4096`.** S3.0 is an existence check at reduced
  `W`. The seed-echo may be easier at a window the size of one chunk.
  Do not transfer the loop to Stage 2's regime without a measurement
  there.
- **S3.0 chunks are 256 tokens.** Degeneracy calibration was at 1024.
  Named above; the raw rates are far past the threshold.
- **S3.0 has no embeddings.** We know what the text does. We do not
  know its path in either representation space.
- **S3.1 is instruct-under-P1, and almost every frame is a loop.** An
  MSM on degenerate embeddings tests the estimator on a loop. It does
  not test H1 on a non-degenerate after-horizon process, because Stage 2
  did not produce one in the eligible set.
- **CK 0.15 is pre-registered, not calibrated** against a synthetic MSM,
  a deeptime reference, or this `K` / `n_frames` regime. It is not
  scale-aware. Methodology's VAMP-reduced CK was not run. F6 names the
  micro-MSM object.
- **VAMP-2 / VAMP-E out-of-sample CV** for `n_pca`, `n_vamp`, `K` is not
  run. Grids exist in `dynamics.yaml`; the fit uses defaults and records
  `split: "full"`.
- **Spectral coarse-graining is k-means on leading right eigenvectors
  of `T`.** Acceptable as the methodology's PCCA-like step; this is not
  Röblitz / Weber PCCA+.
- **Leiden resolution is not swept** (`leiden_resolution = 1.0`).
- **Pooling temperatures** inside a process was declared in the plan.
  Per-temperature models were not the primary claim.
- **Leiden–MSM ARI CI is a frozen-label trajectory bootstrap**, not a
  refit CI. Stated on the figure.
- **Provider identity.** S3.0 is local weights, not a router. That is
  the point of the check. It is also a different stack from Stage 2.
- **Instruction-tuning is not isolated.** S3.0 moves family, scale, `W`,
  stack, and chunk size at once. One 1B Gemma at `W = 256` did not enter
  the reviewer register. That is not a cause.

## 6. Cost actuals

| | Forecast | Actual |
| --- | --- | --- |
| S3.0 generation | $0.00 | $0.00 (`s3-local-base-20260901T184812Z-cc80633b`) |
| S3.1 analysis | $0.00 | $0.00 (`s3-dynamics-20260901T204521Z-f21d5908`, `s3-dynamics-20260901T204549Z-b7c4d0c9`) |
| Hosted API | $0.00 | $0.00 |
| Project to date | — | $11.57 of $50.00 (`runs/_ledger/spend.jsonl`) |

Wall clock: S3.0 ≈ 46 min (18:48–19:34 UTC). S3.1 refit with K-grid ≈ 1 min.

## 7. Implications for the plan

- **A 1B pretrained Gemma-3 under P1 at `W = 256` did not enter the
  reviewer register (0/8).** That is an existence check on one confound
  axis that is still entangled with family, scale, `W`, and stack.
  Stage 1/2 qwen results stay labelled instruct-under-P1. They are not
  shown to be instruct-*caused*. Do not put "instruct-specific" in the
  manuscript from this stage.
- **The base model also reaches a textual fixed point** (8/8, late-phase
  shingle Jaccard), by looping the seed. Keep "semantic state" only as a
  refusal: do not name MSM cells semantic states from this sample.
- **H1 is unsupported on the Stage 2 eligible sample.** Not because we
  lacked an estimator — the estimator recovered a two-state HMM and a
  driven cycle on synthetic data, and a unit test recovers CK = 0 on an
  exact two-state alternation — but because the real series are
  degenerate and `n_macro` is unstable. The 50-state micro-MSM failed an
  uncalibrated max-abs bar; that sentence is F6, not "the MSM is not
  Markovian."
- **H4 is not answered.** Reported `‖J‖` is microstate. Prefill/bge's CI
  excludes 0. Equilibrium-like on "qwen" is not a claim the table
  supports.
- **S3.0 embeddings** wait for an embedding balance (configured API is
  RouterAI; OpenRouter is still empty). Until then there is no geometry
  of the base-model loop. That is a follow-up run_id, not a rewrite of
  this opening (ADR-0012).
- **Stage 4** still needs a temperature × `W` sweep, but S3.0 already
  says T=1.0 is not a diffusion regime for this base model at `W=256`.
  Do not assume H5 from Stage 3.
- No change to the non-negotiables. No ADR beyond ADR-0012.
