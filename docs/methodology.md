# Methodology

Normative document. Code must implement what is written here; if code and this
document disagree, one of them is a bug. Changes require an ADR.

---

## 1. The generative process

Let `V` be the generator's vocabulary, `θ` its fixed parameters, `W` the imposed
sliding-window size in **generator tokens**, `B` the number of tokens requested
per API call (the *block*), and `S` the stride by which the window advances.

### 0. Three axes not to conflate

Following the long-horizon-agent literature, which names this confusion as
endemic, we keep three logically independent properties distinct throughout:

| Axis | Property of | Our variable |
| --- | --- | --- |
| **long-context** | the model — how many tokens it attends to at once | the imposed window `W` |
| **long-horizon** | the process — how many steps it runs for | the turnover count `T/W` |
| **long-term memory** | the system — whether information persists across steps | the object of H2 |

The point of H2 is precisely that we provide **no memory system at all**: no
retrieval, no scratchpad, no summarisation. If seed information survives past the
context horizon, it does so only because the model re-emits it faster than the
window evicts it. "Semantic half-life exceeds `W`" is a statement about long-term
memory *emerging from* long-context generation alone.

### 0.1 `S` is not a constant

`S = B` is the *requested* stride. Measured behaviour (S0.7): models emit a stop
token before filling the block, so the realised stride lies in `[0, B]` and is
model- and context-dependent — mean fill 0.88 with range 0.04–1.00 for
mistral-nemo at `W = 2048`, and fill measured on short prompts badly
underestimates fill inside a trajectory, where the prompt is a full window of
flowing text. Consequences that hold throughout:

- The realised block-fill distribution is **reported per model per stage**, not
  assumed.
- Cost forecasts scale as `1/fill` on the input side (see the cost law below).
- Any claim that depends on a fixed stride must instead be stated in terms of the
  measured distribution, or shown insensitive to it via the Stage 6 stride
  ablation.

State at step `t` is the token sequence held in the model's input:

```
X_t ∈ V^{≤W}
Y_t ~ P_θ( · | X_t ; temperature, top_p, seed_t )        |Y_t| ≤ B
X_{t+1} = Tail_W( X_t ⊕ Y_t )
```

`Tail_W(·)` keeps the last `min(|·|, W)` tokens. The **trajectory** is the
concatenation of all generated blocks, `Y_0 ⊕ Y_1 ⊕ …`, of total length `T`
tokens; the seed prefix is *not* part of it.

Two derived quantities are used everywhere:

- **context horizon** `t_h` — the number of generated tokens after which no seed
  token remains in `X_t`. With a seed of `L_0` tokens and `L_0 < W`,
  `t_h = W − L_0` (the first block whose generation begins with a seed-free
  window is `⌈t_h / B⌉`). Recorded per trajectory, since `L_0` varies by seed.
- **turnover** `R = T / W` — how many times the entire memory has been
  replaced. This, not absolute token count, is the meaningful measure of how
  long we observed the system.

### 1.1 Protocol P1 — re-prompt (primary)

Each step sends `Tail_W` as a fresh prompt. Position IDs restart at 0; there is
no KV-cache carry-over. This is the only protocol implementable over a hosted
API, it realises the recursion above exactly at the token level, and it is what
all reported results use unless stated otherwise.

What it is **not**: a genuine sliding-attention mask with KV eviction, where
positions keep increasing (or are re-indexed by a RoPE scheme) and earlier keys
remain in cache. The two can differ, and the paper says so in its limitations.
Stage 6 attempts a small-`W` local comparison as far as CPU-only hardware
allows.

### 1.2 Protocol P2 — true sliding attention (control, local only)

Single forward-running generation with KV-cache eviction beyond `W` tokens.
Requires local weights. Recorded as a control at small `W` and small `T`; never
mixed with P1 data.

### 1.3 Continuation mechanism

Which API surface is used to "continue text" is a protocol fact, logged per run:

| Mechanism | Surface | Applies to | Notes |
| --- | --- | --- | --- |
| `raw_completion` | `POST /completions` | base models | purest realisation of `P_θ(·|X)`; preferred whenever available |
| `assistant_prefill` | `POST /chat/completions` with a trailing partial assistant message | chat models where the provider supports prefill | no instruction text, so close to unforced |
| `chat_instructed` | `POST /chat/completions` with a fixed minimal continuation instruction | chat models without prefill | the instruction is a *permanent external force* — a separate experimental arm, never pooled with the above |

The `system prompt` condition is orthogonal and explicit: `unforced` (none) or
`fixed` (a recorded string). Stage 0 measures which mechanisms actually work per
model, since provider support is not reliably documented.

### 1.4 Stop events — a declared forcing, and an order parameter

The process is *defined* as unbounded, so a stop token is not the end of a
trajectory: we log the `finish_reason`, count it, and continue by re-prompting
with the current `Tail_W`.

**This is a forcing, and it is not a small one.** Measured at `W = 8192`
(S1.0, llama-3.1-8b): block fill is 1.000 while the window is still filling and
collapses to **0.087** once it is full, with a median completion of 48 tokens
against a requested 1024. In other words, conditioned on a full window of its
own output, the model tries to terminate on almost every step, and the process
only continues because we override it.

Three consequences, all binding:

1. **The paper declares it alongside the re-prompt caveat**, in the method
   section rather than the appendix. What we measure is not "a model generating
   freely" but "a model repeatedly restarted from its own tail after each attempt
   to stop". A reader must be able to see that from the method, not infer it.
2. **The stop rate is an order parameter, not a diagnostic.** It is reported as a
   function of `W`, temperature and model, on the same footing as the diffusion
   exponent and the macrostate count. A model that tries to stop after 48 tokens
   at `W = 8192` but runs on at `W = 2048` is telling us something about the
   post-horizon regime, and it is measured rather than mentioned.
3. **No provider-side suppression is used.** A minimum-token floor would change
   the sampled distribution to `P_θ(· | X, no stop)`, a different process. Six
   conventions were tested (`min_tokens`, `min_new_tokens`,
   `provider.min_tokens`, `ignore_eos`, `skip_special_tokens`, and the
   provider-nested form); Groq accepts four silently and honours none. Should a
   floor become available, using it requires its own ADR and a separate arm — it
   would not be a default.

The realised **stride** is therefore the realised block length, and at large `W`
it is far below `B`. See §0.1; the cost law and the turnover accounting both use
the measured stride, never `B`.

### 1.5 Token accounting and the tokenizer round trip

Windows are defined in generator tokens, so each generator's own tokenizer is
loaded locally (tokenizer files only; no weights, no GPU).

We hold text, not token ids, as the authoritative state, because the API
consumes and produces text. Each step:

```
tail_text ← tail_text ⊕ new_text
ids       ← encode(tail_text)
if |ids| > W:  tail_text ← decode(ids[−W:])
prompt    ← tail_text
```

This is exact, `O(W)` per step, and self-consistent: the prompt sent *is* the
detokenisation of the last `W` tokens under our tokenizer. Two facts are logged
every step:

- `tokenizer_roundtrip_ok` — whether `decode(encode(x)) == x` on the tail. For
  byte-level BPE this holds; a failure means the window boundary is not where
  the manifest claims, which invalidates `W` semantics for that trajectory and
  marks it `SUSPECT`.
- `prompt_tokens_local` vs. `prompt_tokens_api` — our count against the
  provider's. A systematic gap indicates a template or special-token difference
  and is reported in the S0 audit.

### 1.6 Chunking for analysis

The analysis unit is a **chunk** of exactly `chunk_size = 1024` generator
tokens, **non-overlapping**, taken over the generated stream only (the seed is
excluded). Chunk boundaries are cut in generator-token space, then the
corresponding raw text is handed to every embedding model. Overlap is forbidden:
it inflates autocorrelation and fabricates metastability.

`chunk_size ∈ {512, 1024, 2048}` sensitivity is a Stage 6 ablation. If a
characteristic timescale is invariant in **tokens** rather than in chunks, that
is a real result about the process.

## 2. Representation

For chunk `k` with raw text `c_k` and embedding model `E`:

```
z_k = E(c_k) ∈ R^d
```

Stored as `float32` in `runs/<run_id>/data/embeddings_<model>.parquet` alongside
`(trajectory_id, chunk_index, token_start, token_end, n_tokens, text_sha256)`.

Conventions:

- Whether the provider L2-normalises is measured in S0 and recorded; we
  additionally store an explicitly L2-normalised copy so that cosine and
  Euclidean geometry are unambiguous.
- Cosine geometry is primary (embedding spaces are trained for it); Euclidean
  results are computed on L2-normalised vectors, where the two are monotonically
  related.
- Embeddings are cached content-addressed by
  `sha256(model_id ‖ normalise(text))`, so re-analysis never re-pays.

## 3. Measurements

Time axis is generated tokens; every figure also annotates `t/W`. Unless stated,
statistics use only the post-horizon segment `t > W`, with sensitivity to
`t > 3W` reported. The independent replicate unit for uncertainty is the
**trajectory**, never the chunk — chunks are autocorrelated by construction, so
bootstrapping over chunks would understate every confidence interval in the
paper.

### 3.1 Geometry of a single trajectory

- **step displacement** `d_k = 1 − cos(z_k, z_{k+1})`, and its Euclidean
  counterpart on normalised vectors — the *semantic velocity*.
- **semantic acceleration** — first difference of displacement.
- **distance from seed** `1 − cos(z_k, z_seed)` where `z_seed = E(seed text)`.
- **distance from trajectory origin** `1 − cos(z_k, z_0)`.
- **autocorrelation** of the displacement series and of the leading VAMP
  coordinates, with an integrated autocorrelation time.
- **recurrence matrix** `R_ij = 1[ ‖z_i − z_j‖ < ε ]`, with `ε` chosen as a
  fixed quantile of the pairwise distance distribution (reported, and swept).
  From it: recurrence rate, determinism, mean diagonal line length, trapping
  time — the standard RQA quantities.

### 3.2 Inter-trajectory geometry

- `D_between(t)` — distance between trajectories from *different* semantic
  seeds at matched `t`.
- `D_within(t)` — distance between trajectories from the *same* seed with
  different stochastic seeds. This is the control that makes `D_between`
  interpretable: seed identity persists only if `D_between > D_within`.
- **twin-seed** `D(t) = ‖z_t^A − z_t^B‖` for minimally-different seed pairs,
  classified as divergent / convergent / metastable against the `D_within`
  baseline.

### 3.3 Diffusion

```
MSD(τ) = E_t [ ‖ z_{t+τ} − z_t ‖² ]          on L2-normalised embeddings
MSD(τ) ∝ τ^α
```

`α` is fitted by weighted least squares on `log MSD` vs. `log τ`, over a `τ`
range chosen *before* fitting (`τ ≤ T/4`, so that each lag has enough
independent pairs), with a bootstrap CI over trajectories. Reported alongside:
the plateau value if one exists, and the confinement radius implied by it.
`α ≈ 1` free diffusion, `α < 1` subdiffusion/confinement, `α > 1` directed
drift. A fit is only reported with its residual diagnostic figure.

### 3.4 Semantic memory: the half-life

Train a probe `f(z) → seed_id` (multinomial logistic regression, and kNN as a
non-parametric check) on chunks from a *training* set of trajectories, evaluate
on *held-out* trajectories, as a function of the chunk's position `t`:

```
acc(t) = P( f(z_t) = seed(t) )        on held-out trajectories
```

Guardrails that matter:

- Split by trajectory, never by chunk. Chunks from one trajectory in both train
  and test would leak and inflate `acc` catastrophically.
- Baselines: label-shuffled probe, and a probe on time-shuffled chunks. Report
  `acc` against the *empirical* chance level, not against `1/n_seeds`.
- Define, with `acc_0` measured in the first post-horizon window and `acc_∞` the
  empirical chance level:

```
T_½ = min { t : acc(t) − acc_∞ ≤ ½ ( acc_0 − acc_∞ ) }
```

  reported in tokens **and** in units of `W`. Also fit an exponential decay to
  `acc(t) − acc_∞` and report both estimates; if they disagree materially, the
  decay is not exponential and we say so instead of picking the prettier number.
- The headline comparison is `T_½` vs. `W`. `T_½ ≫ W` is the interesting
  outcome: memory sustained by the model's own output, not by its context.

### 3.5 Dynamics: VAMP → microstates → non-reversible MSM

Ordered pipeline, per (model, `W`, temperature, embedding space):

1. **PCA** to `n_pca ∈ {128, 256, 512}` (default 256), projection only, **no
   whitening** — VAMP performs its own covariance normalisation.
2. **VAMP** at lag `τ`, keeping `n_vamp ∈ [5, 20]` coordinates.
   VAMP rather than tICA because tICA presumes stationary, reversible dynamics
   with detailed balance, and autoregressive generation has an arrow of time:
   `A → B` need not be as likely as `B → A`. tICA is run as an ablation, and the
   VAMP/tICA discrepancy is itself a reported measure of irreversibility.
3. **k-means microstates**, `K ∈ {50, 100, 200, 400}`, seeded and recorded.
   k-means, not HDBSCAN, at this step: MSM estimation needs every frame assigned,
   and HDBSCAN's `noise` label has no defensible transition semantics.
4. **MSM** estimation of `T_ij(τ) = P(S_{t+τ}=j | S_t=i)` **without imposing
   detailed balance**. Reversibility is a hypothesis to test, not a constraint
   to assume.
5. **Macrostates** via PCCA+ / spectral coarse-graining. Only these are called
   *semantic states*, and only after validation. Labels are assigned post hoc by
   reading representative chunks, and the assignment procedure is recorded.

Validation, all mandatory before any macrostate is interpreted:

- **VAMP-E / VAMP-2 score**, cross-validated out-of-sample, to choose `n_pca`,
  `n_vamp` and `K`. **Used for model selection only.** VAMP works with singular
  values of the Koopman operator rather than eigenvalues of a reversible transfer
  operator, and those singular values cannot in general be read as relaxation
  timescales — the price of its generality. Reading a timescale off a VAMP
  singular value would be a category error.
- **Implied timescales** `t_i = −τ / ln|λ_i|`, computed from the **MSM
  transition-matrix eigenvalues**, plotted against `τ`; a usable model requires a
  region where they are flat. For a non-reversible transition matrix these
  eigenvalues may be complex: the timescale comes from `|λ_i|`, and any
  rotational component (non-zero imaginary part) is itself evidence of
  circulation and is reported rather than discarded.
- **Chapman–Kolmogorov**: `T(kτ) ≈ T(τ)^k` within error, for several `k`, applied
  both to the MSM and — following the non-equilibrium VAMP literature — to the
  VAMP-reduced model itself.
- **Stability**: macrostate count and assignment stable across `K`, `n_pca`, and
  across both embedding spaces (ARI).

If clustering is performed in VAMP coordinates, `scaling="kinetic_map"` is used
so that Euclidean distances in the projected space approximate kinetic distances;
the choice is recorded, since it changes what k-means is minimising.

Derived quantities: stationary distribution `π`, dwell/residence times,
mean first-passage times, entropy rate, and

```
J_ij = π_i T_ij − π_j T_ji
```

the **probability currents**. `J ≠ 0` establishes genuine non-equilibrium
semantic circulation; `J → 0` at long times would mean the system approaches an
equilibrium-like regime. Either is a result; both need a CI.

`τ` is swept over `{1, 2, 4, 8, 16, 32}` chunks (`1k`–`32k` tokens), plus `2W`,
so that the probed timescales run from a fraction of the window to beyond it.

### 3.6 Geometry branch: Leiden (deliberately time-blind)

```
E → PCA(50–100) → mutual-kNN (k ≈ 30, cosine) → Leiden
```

Run on raw embeddings, **not** on VAMP coordinates, so that this branch shares
no temporal projection with the dynamics branch. Resolution parameter swept;
partition stability assessed by bootstrap.

The robustness argument is the agreement matrix: `ARI`/`NMI` between
{Leiden, MSM} × {Qwen3-Embedding, BGE-M3}. High agreement across a time-blind
geometric method and a time-based dynamical method, in two architecturally
different representation spaces, is much stronger evidence than any single
pipeline's output.

### 3.7 Degeneracy diagnostics

Reported for every trajectory, because they qualify every other measurement:

- **repetition-loop detection** — exact and near-exact n-gram recurrence at
  multiple scales; a trajectory can collapse into a cycle, which is a genuine
  dynamical state, not an artifact to drop.
- **distinct-token entropy** per chunk and its trend.
- **compression ratio** per chunk as a cheap redundancy proxy.
- **self-similarity spike detection** — `cos(z_k, z_{k−1}) → 1`.

Degenerate trajectories are kept, labelled, and counted. Their rate is an order
parameter in the temperature sweep, not a data-cleaning step.

## 4. Statistics

- Uncertainty by bootstrap over trajectories (`n_boot = 2000` default), reported
  as 95% percentile intervals. Every aggregate states its `n`.
- Multiple comparisons across the matrix: Benjamini–Hochberg within a stage's
  declared family of tests, with the family declared in the stage plan *before*
  execution.
- Effect sizes always alongside p-values. A significant difference of no
  practical size is reported as such.
- No estimator is used on real data before it has recovered the truth on a
  synthetic process with a known answer (see `.cursor/skills/add-analysis`).

## 5. Reproducibility levels

| Level | Meaning |
| --- | --- |
| **L3** | bit-exact replay from the response cache |
| **L2** | analysis re-run on stored trajectories gives identical numbers |
| **L1** | fresh generation reproduces the conclusion within CI |

Every published claim reaches at least **L2**; headline results report a
measured **L1** agreement. LLM API determinism is not assumed anywhere — it is
measured in S0 and reported as a rate.

## 6. Known threats, and where each is addressed

| Threat | Where addressed |
| --- | --- |
| Attractors are artifacts of one embedding space | two architecturally different primary spaces, third in S6; ARI reported |
| 2-D projections mistaken for evidence | all statistics in full space; UMAP labelled illustration-only |
| A permanent system prompt keeps forcing the system | `unforced` vs. `fixed` as separate arms |
| Re-prompt ≠ sliding attention | stated in §1.1, local P2 control in S6, named in the paper's limitations |
| Overlapping chunks manufacture metastability | non-overlapping by construction; enforced by tests |
| Microstates over-interpreted | only validated macrostates are interpreted, labelled post hoc |
| Provider drift / unknown quantization | provider pinning + `allow_fallbacks=false`, recorded quantization, determinism audit |
| Probe leakage inflates memory estimates | trajectory-level splits, shuffled baselines, empirical chance level |
| Bootstrapping over autocorrelated chunks | replicate unit is the trajectory, everywhere |
