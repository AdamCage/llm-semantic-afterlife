# Stage 3 — Metastability on a restricted sample, and a local base-model check

**Status.** Opened 2026-09-01 on branch `cursor/stage-3-6dce`, after Stage 2
closed PARTIAL. OpenRouter is empty this opening ([ADR-0012](../../decisions/ADR-0012-stage3-no-openrouter.md)):
no hosted generation, no hosted embedding.

## 1. Question

Stage 2 showed that textual convergence is not universal (absent on
gemma-4-31b, present on qwen3-8b and gpt-oss-120b) and that
`assistant_prefill` is not a lever on the attractor. Two things remain
blocking:

1. **Is the reviewer register / fixed-point an instruction-tuning
   artifact?** Only a true base model under P1 can say. That is S3.0.
2. **Does the after-horizon process have validated metastable semantic
   states, or is "fixed point" just one absorbing textual loop?** That
   is S3.1, and only on arms that actually reached ~12 turnovers.

This stage does not ask whether seed identity survives (Stage 1, qwen
only) and does not sweep temperature × `W` (Stage 4).

## 2. Entry state

From [Stage 2](../stage-2/REPORT.md), [ADR-0010](../../decisions/ADR-0010-stage2-findings-replan-s3.md),
[ADR-0011](../../decisions/ADR-0011-local-base-provider.md):

- Convergence is model-specific. Gemma-4-31b long trajectories continue
  the seed and then write silence. Qwen reprints a reviewer page under
  both mechanisms. gpt-oss-120b almost-`T` is 8/8 at a fixed point.
  gpt-oss-20b produced no long trajectory.
- Prefill vs raw on qwen: register 4/8 vs 6/8 at step 1; fixed-point
  7/8 vs 8/8. Prefill is a different wrapper, not a different attractor.
- Hosted catalogues still have **zero** pretrained generators.
- `api: local` exists. A two-turnover smoke of `gemma-3-1b-pt` at
  `W = 128` completed ($0, fill 1.0, 3.07 s/step). That smoke is not
  S3.0. Gemma 4 E2B loaded and produced a degenerate 16-token probe.
- Both Stage 2 embedding spaces already exist on disk for the eligible
  arms. Re-embedding is not required and is not allowed this opening.

## 3. Experiment matrix

Must match `configs/stages/stage3_local_base.yaml` for S3.0. S3.1 is an
analysis pass over named existing runs, not a new generation config.

| # | Pass | What it decides | Units | Forecast |
| --- | --- | --- | --- | --- |
| S3.0 | Local `gemma-3-1b-pt`, `W = 256`, `T = 3072` (12 turnovers), `B = 32` | does a base model under P1 enter the reviewer register, a loop, or silence? | 8 trajectories, 187,392 in + 24,576 out | **$0.00**, ~40 min CPU |
| S3.1 | VAMP → MSM → PCCA+ and Leiden on existing S2 embeddings | are there validated macrostates, or is H1 unsupported on this sample? | 0 new tokens | **$0** |

**S3.0 factorial.** 1 generator × 2 semantic seeds (`physics`, `surreal`)
× 2 temperatures (0.3, 1.0) × 2 stochastic replicates = 8 trajectories.
`chunk_size = 256` so a chunk is one window. No embedding models in the
config. `max_concurrent = 1` (the 1B checkpoint in float32 is ~4 GB on
a 15 GB CPU box).

Wall-clock from the smoke: 3.07 s per 32-token block at fill 1.0. One
trajectory is 96 blocks ≈ 5 min; eight sequential ≈ 40 min. If fill
collapses the step count rises as `1/fill`; stop and ask above 4 h.

**S3.1 eligible cells** (pre-registered; do not add arms after seeing
scores). A trajectory enters only if it has ≥ 40 chunks (~10 turnovers
at `chunk = 1024`). Processes are never pooled.

| process | source run | n trajectories (expected) | notes |
| --- | --- | --- | --- |
| `or-qwen3-8b` raw | `s2-embed-mechanism-20260901T131051Z-55761049` | 8 | 47–48 chunks |
| `or-qwen3-8b-prefill` | same | 8 | 47–48 chunks |
| `or-gpt-oss-120b` | `s2-embed-model-axis-20260901T125626Z-50d60286` | 8 | 47 chunks, almost-`T` |
| `or-muse-glimmer-30b` `T = 0.3` physics | same | 2 | underpowered by construction; run, do not interpret as a macrostate count |

Both `bge-m3` and `qwen3-embed-8b`. Gemma-4-31b, gpt-oss-20b, and
glimmer empty-EOS deaths stay out (ADR-0010).

**Sample-size rule, written before the fit.** `n_pca = min(128, n_frames − 2, d)`.
`K ∈ {50, 100, 200, 400}` is attempted only when `K ≤ n_frames / 3`.
`τ ∈ {1, 2, 4, 8}` (chunks); a lag with fewer than 20 pairs is skipped.
Primary grouping is `(generator, embedding)`, pooling temperature and
seeds of the *same* process so that qwen-raw at one temperature is not
asked to support `K = 50` on 80 frames. Per-temperature models are
attempted and marked underpowered if `n_frames < 120`. That is a
declared deviation from methodology §3.5's "per temperature" split,
forced by the Stage 2 replicate count, not a finding.

## 4. Computations

1. `afterlife generate --config configs/stages/stage3_local_base.yaml --yes`
   — S3.0 trajectories. Artifact: `runs/s3/<run_id>/`.
2. `afterlife analyze degeneracy --run <s3.0>` then `analyze rates` and
   `analyze protocol`. Artifacts under `artifacts/stage-3/`.
3. Hand count of S3.0 step-1 and last-quarter register / silence /
   continuation, ≥ 8 trajectories, criterion stated in the report.
4. `afterlife analyze dynamics --run s2-embed-mechanism-…` and
   `--run s2-embed-model-axis-…`, both embedding spaces. Degeneracy
   labels joined from the source generation run before any confinement
   or timescale is read.
5. Figures: implied timescales vs `τ`, Chapman–Kolmogorov error
   (micro and macro assignments labelled), microstate current norm,
   occupancy vs turnover, Leiden–MSM ARI table, and `k_stability` from
   the CLI K-grid. UMAP if drawn is an illustration and is labelled as such.

No `afterlife embed` this opening. No OpenRouter.

## 5. Exit criteria

Falsifiable, quantitative, fixed before any Stage 3 number exists.

| # | Criterion | Threshold |
| --- | --- | --- |
| F1 | **S3.0 generated** | 8/8 planned trajectories exist with a manifest, or each missing one is declared with cause |
| F2 | **S3.0 surface labelled** | reviewer-register / loop / silence / continuation counted on step 1 and on the last quarter, over all completed S3.0 trajectories, criterion written in the report |
| F3 | **Confound status explicit** | S3.0 embeddings are deferred; every S3.1 claim is labelled instruct-under-P1. F3 does not pass if the report reads S3.1 as a base-model result |
| F4 | **MSM attempted on the restricted sample** | a fit is reported for ≥ 3 of {qwen-raw, qwen-prefill, 120b} × {bge-m3, qwen3-embed-8b} with `n_frames ≥ 80`. Glimmer may fail this bar; that is recorded, not padded |
| F5 | **Implied timescales scored** | `t_i(τ)` plotted for every cell in F4. "Flat" means the slowest real timescale changes by < 50% across adjacent valid `τ`. Otherwise the cell is "not flat" — that is a result |
| F6 | **Chapman–Kolmogorov scored** | for the primary lag, `max |T(kτ) − T(τ)^k|` reported at `k ∈ {2, 3}`. Pass if that maximum is < 0.15; otherwise "CK failed" |
| F7 | **Macrostate stability or its absence** | `n_macro` is the same across valid `K` and both embedding spaces of one process, with assignment ARI > 0.5, **or** instability is the reported result. A single `K` does not count as stable |
| F8 | **Leiden–MSM agreement** | ARI(Leiden, MSM) with a trajectory-bootstrap CI, per process × embedding that entered F4 |
| F9 | **Currents signed** | `J_ij` reported; either at least one pair has a bootstrap CI excluding 0, or the report says currents are consistent with equilibrium |
| F10 | **No OpenRouter spend** | Stage 3 ledger entries sum to $0.00 of hosted API. Local generation may appear at $0 |

A cell that fails F5 or F6 is not given a macrostate interpretation.
Failing H1 on this sample is a successful stage.

## 6. Pre-registered predictions

| # | Prediction | Confidence | Observed |
| --- | --- | --- | --- |
| Q1 | `gemma-3-1b-pt` does **not** open in the reviewer register at step 1 | 0.70 | |
| Q2 | At least half of S3.0 trajectories are degenerate (loop / n-gram collapse) by the last quarter — the two-turnover smoke already looped | 0.75 | |
| Q3 | S3.0 does **not** produce gemma-4-31b-style silence (whitespace / recursion marks as the late-run register) | 0.50 | |
| Q4 | Qwen MSM, both mechanisms, has **no** validated timescale gap: the process is a textual fixed point, which is one absorbing-like state, not a multi-state MSM. H1 is unsupported on this sample | 0.65 | |
| Q5 | Leiden–MSM ARI on qwen is > 0.4 because both methods collapse to one region, not because they discovered the same rich dynamics | 0.55 | |
| Q6 | gpt-oss-120b looks like qwen on F5–F7 (no gap, one coarse state) | 0.60 | |
| Q7 | Probability currents on qwen are consistent with 0 (no circulation if the chain is stuck) | 0.60 | |
| Q8 | Prefill vs raw qwen agree on the F5/F7 verdict (same `n_macro`, same "no gap"), not on a shared assignment | 0.70 | |
| Q9 | Glimmer's 2-trajectory MSM is marked underpowered and does not support a macrostate claim | 0.85 | |
| Q10 | Cross-space ARI of MSM labels (bge-m3 vs qwen3-embed-8b) on qwen-raw is > 0.3 | 0.50 | |

Q4 is the one that matters. If a looping reviewer page produces a
beautiful MSM with three named semantic states, the estimator is
reading a repetition artifact. Degeneracy labels are joined first.

## 7. Budget and wall clock

- **USD:** $0 forecast, $0 declared. Project spend to date is the Stage 2
  close (~$11.57 of $50). This opening does not spend the Stage 3 $10
  ceiling. Stop and ask before any OpenRouter or RouterAI call.
- **Wall clock:** S3.0 ≈ 40 min if fill stays 1.0; S3.1 is CPU minutes
  per embedding space. Stop and ask if S3.0 exceeds 4 hours.
- **Memory:** 1B float32 + activations on 15 GB. `max_concurrent = 1`.

## 8. Stage-specific risks

| Risk | Mitigation |
| --- | --- |
| Reading a looping trajectory as a macrostate | degeneracy joined before MSM; Q4 predicts no gap; F5/F6 gate interpretation |
| `K = 400` on 176 frames | `K ≤ n_frames / 3`, written above |
| Pooling temperatures hides a T-effect | per-temperature fits are run and marked underpowered; primary claim is pooled-same-process |
| S3.0 `W = 256` does not transfer to `W = 4096` | stated; F3 forbids treating S3.0 as the Stage 2 regime |
| Degeneracy threshold was calibrated at 1024-token chunks | S3.0 uses 256-token chunks; report raw rates and apply the same threshold with that limitation named |
| OpenRouter comes back mid-stage and someone embeds S3.0 quietly | ADR-0012: that is a follow-up pass with its own run_id, not a rewrite of this opening |
| Glimmer's two trajectories get a confident `n_macro` | Q9; F4's `n_frames ≥ 80` bar on the three real cells |

## 9. Definition of done

- [ ] S3.0 generated, surface-labelled, embeddings explicitly deferred
- [ ] S3.1 dynamics + Leiden on the restricted sample, both spaces
- [ ] `artifacts/stage-3/` populated with figures, tidy data, captions
- [ ] `REPORT.md` with a verdict per exit criterion and the prediction
      table scored, quoting S3.0 text from at least three points
- [ ] `afterlife review --stage 3` exits 0
- [ ] Master plan left consistent with ADR-0012
- [ ] Spend reconciled at $0 hosted
