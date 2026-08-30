# Research plan — Semantic Afterlife

**Working title.** *Semantic Afterlife: Long-Run Dynamics of Large Language
Models Beyond the Context Horizon*

**Target venue.** TMLR (primary) / ICLR; ACL-family as fallback.
Russian mirror of this document: [`research-plan.ru.md`](research-plan.ru.md).

**Status.** `S0` in progress. Last revised 2026-08-30.

---

## 1. The question

A language model with sliding window `W` generates text without end. Its state
is the last `W` tokens:

```
X_t ∈ V^W ,     Y_t ~ P_θ(· | X_t) ,     X_{t+1} = Tail_W(X_t ⊕ Y_t)
```

After roughly `W` generated tokens the initial prompt has physically left the
model's input. Everything that happens after that point is the object of this
paper. We call it the **semantic afterlife** of the seed.

Three outcomes are a priori possible, and they are mutually exclusive enough to
be worth distinguishing carefully:

| | Behaviour | What it would mean |
| --- | --- | --- |
| **A** | trajectories stay separated by seed | self-sustaining semantic memory: the model re-encodes the seed into its own output faster than the window discards it |
| **B** | all seeds converge | model-specific *natural semantic state* reached without external forcing |
| **C** | persistent wandering | a stationary distribution over semantic states, with no single attractor |

We expect the truth to be a mixture — most plausibly **metastability**: a finite
set of model-specific semantic states, long dwell times, and occasional
transitions. The paper's job is to measure which, with uncertainty, and to
characterise the dynamics quantitatively rather than to narrate a picture.

## 2. Central hypothesis (pre-registered)

> **H1.** After the initial context has been fully evicted, a freely generating
> LLM does not perform unbounded random drift through semantic space. It
> occupies and transitions between a *finite* set of model-specific metastable
> semantic states.

Subsidiary, individually falsifiable:

- **H2 (semantic half-life).** Measurable information about the seed persists
  well past the context horizon: `T_½ > W`, plausibly `T_½ = c·W` with `c > 1`.
- **H3 (confinement).** Mean squared displacement in representation space grows
  sublinearly and saturates: `MSD(τ) ∝ τ^α` with `α < 1`, plateauing — the
  signature of a bounded basin rather than free diffusion.
- **H4 (irreversibility).** Transition currents between macrostates are
  non-zero, `J_ij = π_i T_ij − π_j T_ji ≠ 0`: the long-run semantic dynamics
  are genuinely out of equilibrium, not a reversible walk.
- **H5 (temperature transition).** There is a temperature region separating a
  *confinement* regime (low `T`: few states, long dwell times, small `α`) from
  a *diffusion* regime (high `T`: many states, short dwell, `α → 1`).
- **H6 (window scaling).** `T_½`, mixing time, and macrostate count scale with
  `W` non-trivially — not proportionally.

**We do not claim** to be first to apply attractor language to LLMs, nor first
to track embeddings over generation. See
[`literature/related-work.md`](literature/related-work.md). Our contribution is
the specific regime — *unbounded free-running generation under a finite sliding
window, past the eviction of the initial condition* — together with a
reproducible benchmark and a dynamics-first measurement suite.

## 3. What the protocol actually is (and the cost law it implies)

The measurement protocol is defined precisely in
[`methodology.md`](methodology.md). Two facts belong in the plan because they
drive every budget decision.

**Protocol P1 (re-prompt, stride `S`).** At each step we send the last `W`
tokens as the prompt and receive `B` new tokens; the window slides by `S = B`.
This realises `X_{t+1} = Tail_W(X_t ⊕ Y_t)` exactly, over any API, and is our
primary protocol. It is *not* identical to true sliding attention with KV-cache
eviction — positions restart each step. We state this in the paper's
limitations rather than hiding it, and Stage 6 quantifies the gap on a small
local control.

**The cost law.** Because the whole window is re-sent every `S` tokens, input
tokens dominate:

```
input_tokens  ≈  T · W / S            output_tokens  ≈  T
```

For `W = 32k`, `S = 1024`, `T = 512k` that is **16.4M input** tokens for 512k
output — a 32× input amplification. This single relation, more than model
prices, decides what is affordable. Consequences we adopt:

- The pilot's primary window is `W = 8k`, not `32k`: same number of turnovers
  at one quarter the input cost.
- `S` is a first-class protocol parameter with a documented sensitivity check
  (Stage 6), not an implementation detail.
- Cheap models carry the wide matrix; expensive models are used where their
  architecture is the point (Glimmer's hybrid local/global attention).
- RouterAI `service_tier: flex` where available (≈2× cheaper), recorded per run.

## 4. Stages

Each stage has its own `PLAN.md` (written before execution) and `REPORT.md`
(after), under `docs/stages/stage-N/`. Budgets are indicative ceilings that
trigger a stop-and-ask, not targets.

### S0 — Foundations and feasibility audit `← current`

**Question.** Can this experiment be run reproducibly at all, on this
infrastructure, at a cost that permits the full plan? What are the *measured*
facts about our providers, rather than the documented ones?

No scientific claims are made in S0. Its outputs are infrastructure and an
honest capability audit.

- Repository, agent harness, library, CLI, logging, provenance, cost ledger.
- **Provider capability audit** — for each candidate model: availability,
  endpoints, provider slugs, `quantization`, `context_length`,
  `max_completion_tokens`, `supported_parameters`, real prices in RUB→USD.
- **Continuation-mechanism audit** — which of `/completions` (raw), assistant
  prefill, or instruction-framed chat actually works per model. This determines
  whether a "pure" base-model regime is available to us at all.
- **Determinism audit** — repeat identical seeded requests, measure exact-match
  and near-match rates per model/provider. Establishes what reproducibility
  level our claims can honestly assert.
- **Embedding audit** — dimensions, batch limits, cost, whether returned
  vectors are L2-normalised.
- **End-to-end micro-trajectory** — `W = 2048`, `T ≈ 16k`, 2 seeds, 1 model:
  the full pipeline from generation through embedding, geometry, figures, and a
  stage report.
- **Cost model calibration** — predicted vs. actual tokens and USD, and a
  forecast for S1.

**Exit criteria.** (i) ≥3 candidate generators pass the continuation audit;
(ii) ≥2 embedding models usable; (iii) a micro-trajectory completes and
regenerates bit-identically in `replay` mode; (iv) measured determinism rate
reported per model; (v) S1 cost forecast within the $50 pilot budget;
(vi) `afterlife doctor|audit|generate|embed|analyze|report` all green.

**Budget.** ≤ $3.

### S1 — Pilot: does the phenomenon exist?

**Question.** Over ~16–32 window turnovers, is there any structure at all —
seed-dependent separation, recurring regions, non-trivial MSD?

Indicative matrix (final numbers come from S0's audit and cost model):
4 models × `W ∈ {8k}` (plus a `32k` arm on 1–2 models) × `T ∈ {0.3, 1.0}` ×
8 semantic seeds × 3 stochastic repetitions, `T = 256k`, `chunk = 1024`.

Passes: generation → embedding (both spaces) → geometry (displacement,
distance-from-seed, inter-trajectory distance, autocorrelation, recurrence) →
first-look MSD → degeneracy diagnostics (repetition-loop detection, entropy
collapse).

**Exit criteria.** Seed-identity signal measurably above a shuffled baseline
past `t = W` on ≥2 models; MSD exponent estimable with bootstrap CI narrower
than 0.2; <20% of trajectories degenerate into repetition loops (if more,
the sampling configuration is revised before proceeding).

**Budget.** ≤ $25.

### S2 — Semantic memory decay and diffusion

Seed-identity probes (linear + kNN on held-out trajectories) as a function of
generated tokens ⇒ **semantic half-life** `T_½` and its ratio to `W`.
MSD scaling with fitted `α` and CI, confinement radius, velocity and
acceleration statistics, autocorrelation times, recurrence quantification.

**Exit criteria.** `T_½` with CI on ≥3 models; the `T_½` vs `W` relation
estimated on ≥2 windows; `α` distinguishable from 1.0 at 95% or explicitly
reported as indistinguishable.

**Budget.** ≤ $40 (mostly the `W`-sweep generation).

### S3 — Metastability, Markov state models, and representation robustness

Dynamics branch: `PCA → VAMP → k-means microstates → non-reversible MSM →
macrostates (PCCA+)`, with full MSM validation — VAMP score cross-validation
over `K`, implied timescales vs. `τ`, Chapman–Kolmogorov test. Then dwell
times, first-passage times, entropy rate, and **probability currents** `J_ij`.

Independent geometry branch: `PCA → mutual-kNN → Leiden`, deliberately using no
temporal information. Agreement between branches (ARI/NMI) and across both
embedding spaces is the robustness argument. tICA is run as an ablation, and the
tICA/VAMP discrepancy is itself reported as a measure of irreversibility.

**Exit criteria.** Macrostate count stable across `K` and across both
embedding spaces; implied timescales flat over a `τ` range; CK test passed;
ARI(Leiden, MSM) reported per model/embedding with a bootstrap CI.

**Budget.** ≤ $10 (compute-bound, not API-bound).

### S4 — Control parameters: the `temperature × W` phase portrait

Sweep `T ∈ {0.0, 0.2, 0.5, 0.7, 1.0, 1.2, 1.5}` × `W ∈ {4k, 8k, 16k, 32k}` on
2–3 models; locate any transition between confinement and diffusion using
`α`, macrostate count, dwell time, and entropy rate as order parameters.
For Glimmer, test specifically whether a characteristic scale appears near its
2048-token local-attention window.

**Exit criteria.** Order-parameter curves with CI across the full sweep; a
transition region either localised or explicitly reported as absent.

**Budget.** ≤ $120 (requires approval; the largest generation stage).

### S5 — Basins of attraction and sensitivity to initial conditions

Many seeds (target 200+ per model) at the best-characterised operating point ⇒
empirical basin occupancy, compared across model families ("semantic phase
portraits"). Twin-seed experiment: minimally different seeds (*Napoleon won* vs.
*lost at Waterloo*), tracking `D(t) = ‖z_t^A − z_t^B‖` for divergence,
convergence, or metastable switching.

**Exit criteria.** Basin occupancy with CI per model; twin-seed divergence
classified with a stated statistical criterion against a same-seed
different-stochastic-seed control.

**Budget.** ≤ $120 (requires approval).

### S6 — Robustness, ablations, independent replication

Third embedding space as a sanity check; `chunk ∈ {512, 1024, 2048}`;
PCA dimension sensitivity; stride `S` sensitivity; `system prompt` present vs.
absent (*forced* vs. *unforced*); cross-provider replication of headline results
(RouterAI vs. OpenRouter); a small local CPU control run to show the effect
does not depend on router infrastructure; and the re-prompt vs. true-sliding
comparison at small `W` insofar as hardware allows.

**Exit criteria.** Every headline result reproduced under at least two
representation spaces and one alternative provider, or the failure documented as
a limitation with its scope stated.

**Budget.** ≤ $40.

### S7 — Manuscript

Written from artifacts only, per `.cursor/rules/50-paper.mdc`. Deliverables:
manuscript, reproducibility appendix, artifact release (figures with tidy data,
response cache for headline figures, trajectory bundles with provenance).

**Budget.** $0 API.

## 5. Models

The final list is decided by S0's audit, not by this table. Candidates and
their role:

| Model | Native context | Role |
| --- | --- | --- |
| Llama 3 8B **Base** | 8K | pure autoregressive control — no chat template, no RLHF policy |
| Qwen3 8B | 32K (→131K YaRN) | modern compact dense transformer |
| Mistral Nemo 12B | 131K | very cheap architecturally independent baseline; carries the wide matrix |
| Muse Glimmer 30B | 131K | modern open-weight model with hybrid local/global attention (2048-token local window) — its own research axis |
| DeepSeek V4 Flash | ~1M | frontier MoE control: answers "your effect is an artifact of small models" |

`W` is always **imposed by us**, never taken as the model's native context.
That is what turns "compare five models" into "hold `θ` fixed and vary memory".

Base models give the physically clean process (`continue this text forever`);
instruct models give the production-relevant regime but introduce EOS, turn
structure, and RLHF policy as confounds. Both are run, labelled, and never
pooled.

## 6. Representation spaces

| | Qwen3-Embedding-8B | BGE-M3 | Gemini Embedding 001 |
| --- | --- | --- | --- |
| Architecture | causal decoder (`Qwen3ForCausalLM`) | bidirectional encoder (XLM-RoBERTa) | closed |
| Dimension | 4096 | 1024 | — |
| Role | primary | primary (independent architecture) | S6 sanity check |

The two primary spaces are architecturally *different in kind*, which is what
makes cross-space agreement evidence about the generator rather than about
embedding models. Chunk boundaries are defined in **generator** tokens; each
embedding model tokenises the same raw text its own way, and that is fine.

## 7. Standing methodological commitments

These come from the traps identified during project scoping and are enforced by
`.cursor/rules/`:

1. **Never one embedding space.** Attractors claimed in one representation are
   not claimed at all. Report cross-space ARI/NMI.
2. **UMAP/t-SNE are illustrations.** All statistics in the full space, always.
3. **System prompt is an experimental condition.** A permanent
   "You are a helpful assistant" is a permanent external force; `unforced` and
   `fixed-system-prompt` are separate arms, never merged.
4. **The window mechanism is stated explicitly.** Re-prompt is not sliding
   attention. Position IDs, RoPE, and KV-cache handling are protocol facts, not
   details.
5. **Non-overlapping chunks.** Overlap manufactures autocorrelation and
   therefore fake metastability.
6. **Microstates are not semantic states.** Only validated MSM macrostates get
   interpreted, and their labels are assigned post hoc.
7. **Degeneracy is measured, not discarded.** Repetition loops and entropy
   collapse are findings about the dynamics; they are reported, not filtered
   out of the sample.

## 8. Budget and risk summary

Cumulative ceiling for S0–S3 is **$78**, within the approved $50 pilot only if
S2's window sweep is trimmed — so S2's matrix is finalised from S1's actual
cost data, and S4/S5 require explicit approval before launch. Full risk register
with mitigations: [`risks.md`](risks.md).

The three risks that would most change the project:

- **Instruct models refuse to free-run** (EOS storms, meta-commentary). Mitigation:
  base models as the primary arm; S0's continuation audit decides this early.
- **Degenerate repetition dominates at low temperature.** Mitigation: treat as a
  measured phase, not a bug; report the repetition-loop rate as an order
  parameter.
- **Input-token amplification makes large `W` unaffordable.** Mitigation: the
  cost law above, small primary `W`, stride sensitivity instead of brute force.

## 9. How to work on this

Read `AGENTS.md`. Stage discipline is the point: plan, execute, produce
artifacts, report, re-plan. A stage that falsifies its own hypothesis and says
so is a stage well spent.
