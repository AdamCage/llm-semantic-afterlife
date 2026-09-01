# Stage 3 report — no validated macrostates; a base model loops the seed

**Status.** Computations finished 2026-09-01. Overall verdict: **PARTIAL**.
S3.0 answered the base-model question from generated text. S3.1 found no
validated MSM macrostate on the restricted instruct sample. S3.0 embeddings
remain deferred (ADR-0012). OpenRouter was not called. Hosted spend: **$0.00**.

Branch: `cursor/stage-3-6dce`. Plan: [`PLAN.md`](PLAN.md).

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| F1 | S3.0 generated | **PASS** | 8/8 trajectories COMPLETED, `s3-local-base-20260901T184812Z-cc80633b` |
| F2 | S3.0 surface labelled | **PASS** | [`artifacts/stage-3/surface/s30_surface_labels.md`](../../../artifacts/stage-3/surface/s30_surface_labels.md); 0/8 reviewer register at step 1 |
| F3 | Confound status explicit | **PASS** | embeddings deferred; every S3.1 sentence below is instruct-under-P1 |
| F4 | MSM on the restricted sample | **PASS** | 6 cells with `n_frames ≥ 80` (qwen raw/prefill × 2 spaces, 120b × 2). Glimmer 90 frames, underpowered, not padded. `s3-dynamics-20260901T184826Z-f21d5908`, `s3-dynamics-20260901T184929Z-b7c4d0c9` |
| F5 | Implied timescales scored | **PASS** | [`artifacts/stage-3/dynamics/implied_timescales.meta.json`](../../../artifacts/stage-3/dynamics/implied_timescales.meta.json). Mixed flatness; none validated |
| F6 | Chapman–Kolmogorov < 0.15 | **FAIL** | every eligible cell 0.67–1.00. No MSM is usable. [`chapman_kolmogorov.meta.json`](../../../artifacts/stage-3/dynamics/chapman_kolmogorov.meta.json) |
| F7 | Macrostate stability or its absence | **PASS** | instability is the result: `n_macro` flips across `K ∈ {50, 100}` and across spaces. [`k_stability.md`](../../../artifacts/stage-3/dynamics/k_stability.md) |
| F8 | Leiden–MSM ARI with CI | **PASS** | per process × space in [`leiden_msm_agreement.meta.json`](../../../artifacts/stage-3/dynamics/leiden_msm_agreement.meta.json) |
| F9 | Currents signed | **PASS** | qwen and 120b CIs reach ~0; glimmer's larger `‖J‖` is 2 trajectories. [`probability_currents.meta.json`](../../../artifacts/stage-3/dynamics/probability_currents.meta.json) |
| F10 | No OpenRouter spend | **PASS** | Stage 3 ledger $0.00 hosted; project still $11.57 of $50 |

F6 failed as a *validity* bar. That is the finding, not a missing measurement.
A cell that fails F6 is not given a macrostate interpretation. H1 is
unsupported on this sample.

## 2. Results

### S3.0 — `local-gemma-3-1b-pt` at `W = 256`, 12 turnovers

`run_id`: `s3-local-base-20260901T184812Z-cc80633b`.
8/8 completed. 96 chunks. **$0.00**. Fill ≈ 1.00 in every quarter
([`artifacts/stage-3/protocol/`](../../../artifacts/stage-3/protocol/)).
Stop rate ≤ 1.5%. Fixed-point rate 8/8
([`artifacts/stage-3/rates/`](../../../artifacts/stage-3/rates/)).
Degeneracy 8/8, looping fraction 1.0, n-gram repetition 0.84–0.98
(`s3-degeneracy-20260901T193542Z-f76d2086`).

The degeneracy threshold 0.083 was calibrated at 1024-token chunks; these
chunks are 256. A rate ten times the threshold is not a calibration edge
case.

**Step-1 register (criterion).** Reviewer register = the completion
self-reviews the prompt ("you've provided", "well-structured",
"comprehensive overview", "thank you for sharing"). Silence = whitespace
or recursion marks as in gemma-4-31b. Verbatim loop = a ≥40-character
span repeats in the same completion.

| trajectory | step 1 | last quarter |
| --- | --- | --- |
| T=0.3 physics s1, s2 | continuation (sliding seed-echo) | verbatim loop |
| T=0.3 surreal s1 | verbatim loop | verbatim loop |
| T=0.3 surreal s2 | continuation (then locks) | verbatim loop |
| T=1.0 physics s1 | continuation (already collapsing) | "Deformation phase." lock |
| T=1.0 physics s2 | continuation | "Is This" lock |
| T=1.0 surreal s1 | continuation | "I I" |
| T=1.0 surreal s2 | continuation (already "the meaning of") | `/1/1/1` lock |

**0/8** open in the reviewer register. **0/8** produce gemma-4-31b
silence. **8/8** are a loop by the last quarter.

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
repeats the seed, or it collapses. That is a different fixed point from
qwen's reviewer page and from gemma-4-31b's silence. All three are
textual attractors; they are not the same attractor.

Geometry of S3.0 is **not** reported. Embeddings were not computed.

### S3.1 — MSM on the restricted instruct sample

Instruct-under-P1 only. Source embeddings:
`s2-embed-mechanism-20260901T131051Z-55761049` (qwen both mechanisms),
`s2-embed-model-axis-20260901T125626Z-50d60286` (120b; glimmer `T=0.3`
physics). S2.1 leftover qwen (2 traj, 90 frames) was excluded; S2.2 is
the qwen cell.

| process | space | n_traj | n_frames | degenerate | n_macro | ITS flat | CK max err | validated | ARI(Leiden, MSM) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen raw | bge-m3 | 8 | 359 | 8 | 2 | yes | 0.90 | no | 0.068 [0.00, 0.42] |
| qwen raw | qwen3-embed-8b | 8 | 359 | 8 | 1 | no | 0.89 | no | 0.00 |
| qwen prefill | bge-m3 | 8 | 359 | 7 | 4 | no | 0.97 | no | 0.49 [0.37, 0.90] |
| qwen prefill | qwen3-embed-8b | 8 | 359 | 7 | 1 | no | 1.00 | no | 0.00 |
| gpt-oss-120b | bge-m3 | 8 | 352 | 8 | 2 | yes | 0.75 | no | 0.048 [0.00, 0.37] |
| gpt-oss-120b | qwen3-embed-8b | 8 | 352 | 8 | 2 | no | 0.90 | no | 0.050 [0.00, 0.36] |
| glimmer T=0.3 physics | bge-m3 | 2 | 90 | 2 | 3 | no | 0.73 | no | 0.54 [−0.02, 0.54] |
| glimmer T=0.3 physics | qwen3-embed-8b | 2 | 90 | 2 | 4 | no | 0.80 | no | 0.65 [0.00, 0.65] |

`validated_macrostates = 0` on every cell. CK fails by a factor of four
to six above the pre-registered 0.15 bar. `n_macro` at `K=50` vs `K=100`
does not agree on any process × space
([`k_stability.md`](../../../artifacts/stage-3/dynamics/k_stability.md)).
Cross-space ARI of MSM labels on qwen is **0** (one space chose
`n_macro=1`).

Almost every trajectory in the F4 cells is degenerate. An MSM on a
looping reviewer page will invent microstates inside the loop. That is
why Q4 predicted no gap and why F6 is the gate.

`‖J‖` on qwen-raw / bge-m3 is 0.032 with a trajectory-bootstrap interval
that reaches machine epsilon. We cannot reject `J = 0`. Glimmer's
`‖J‖ ≈ 0.36` is two trajectories and is not a circulation claim.

## 3. Prediction vs outcome

| # | Prediction | Confidence | Observed | Score |
| --- | --- | --- | --- | --- |
| Q1 | gemma-3-1b-pt does not open in the reviewer register | 0.70 | 0/8 | **right** |
| Q2 | ≥ half of S3.0 degenerate by the last quarter | 0.75 | 8/8, looping fraction 1.0 | **right** |
| Q3 | S3.0 does not produce gemma-4-31b silence | 0.50 | collapse is seed-echo or token lock (`Is This`, `/1/1`), not whitespace/recursion | **right** |
| Q4 | qwen MSM has no validated timescale gap | 0.65 | validated=0 both mechanisms both spaces; CK 0.67–1.00 | **right** |
| Q5 | Leiden–MSM ARI on qwen > 0.4 | 0.55 | raw/bge 0.068; prefill/bge 0.49; embed spaces 0.00 | **wrong** |
| Q6 | 120b looks like qwen on F5–F7 | 0.60 | validated=0, CK fail, n_macro unstable | **right** |
| Q7 | qwen currents consistent with 0 | 0.60 | CIs reach ~0 | **right** |
| Q8 | prefill vs raw agree on F5/F7 verdict | 0.70 | both unvalidated; n_macro 2 vs 4 and ITS flatness disagree | **partial** |
| Q9 | glimmer MSM is underpowered | 0.85 | 2 traj, 90 frames, labelled underpowered | **right** |
| Q10 | cross-space MSM ARI on qwen-raw > 0.3 | 0.50 | 0.00 | **wrong** |

Q5 was the tempting one: if both methods collapse to one region, ARI
should be high. On qwen-embed `n_macro=1` against a multi-community
Leiden partition, ARI is zero. Collapse is not the same thing as
agreement.

## 4. Surprises

- **The base model fills every block.** Fill 1.00 ± 0.00 in quarter 4.
  Instruct qwen's fill decay is not a property of P1. It is a property
  of that model trying to stop.
- **T=0.3 physics s1 and s2 are the same sliding sentence.** Seeded
  local generation, `temperature=0.3`, reproduced the identical
  seed-echo. That is closer to determinism than any hosted arm in
  Stage 2.
- **T=1.0 does not rescue the process.** It replaces a clean seed-echo
  with a shorter token lock. Higher temperature here is a different
  degeneracy, not diffusion.
- **CK errors of 0.7–1.0.** Not a near miss. The lag-1 MSM is not a
  model of these series.

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
  MSM on degenerate embeddings tests the estimator on a loop, which is
  what F6/Q4 were for. It does not test H1 on a non-degenerate
  after-horizon process, because Stage 2 did not produce one in the
  eligible set.
- **Pooling temperatures** inside a process was declared in the plan.
  Per-temperature models were not the primary claim.
- **Leiden–MSM ARI CI is a frozen-label trajectory bootstrap**, not a
  refit CI. Stated on the figure.
- **Provider identity.** S3.0 is local weights, not a router. That is
  the point of the check. It is also a different stack from Stage 2.

## 6. Cost actuals

| | Forecast | Actual |
| --- | --- | --- |
| S3.0 generation | $0.00 | $0.00 (`s3-local-base-20260901T184812Z-cc80633b`) |
| S3.1 analysis | $0.00 | $0.00 |
| Hosted API | $0.00 | $0.00 |
| Project to date | — | $11.57 of $50.00 |

Wall clock: S3.0 ≈ 46 min (18:48–19:34 UTC). S3.1 ≈ 2 min per embedding
run.

## 7. Implications for the plan

- **The reviewer register is instruct-specific.** A 1B base model under
  the same P1 protocol does not enter it. Stage 1/2 qwen results stay
  labelled instruct-under-P1 for that surface. They do not stay
  labelled as "the only kind of fixed point": the base model also
  converges, by looping the seed.
- **H1 is unsupported on the Stage 2 eligible sample.** Not because we
  lacked an estimator — the estimator recovered a two-state HMM and a
  driven cycle on synthetic data — but because the real series fail CK
  and are degenerate. Do not name MSM cells "semantic states" in the
  paper from this sample.
- **S3.0 embeddings** wait for an OpenRouter balance (ADR-0012). Until
  then there is no geometry of the base-model loop.
- **Stage 4** still needs a temperature × `W` sweep, but S3.0 already
  says T=1.0 is not a diffusion regime for this base model at `W=256`.
  Do not assume H5 from Stage 3.
- No change to the non-negotiables. No ADR beyond ADR-0012.
