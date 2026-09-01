# Research plan — Semantic Afterlife

**Working title.** *Semantic Afterlife: Long-Run Dynamics of Large Language
Models Beyond the Context Horizon*

**Target venue.** TMLR (primary) / ICLR; ACL-family as fallback.
Russian mirror of this document: [`research-plan.ru.md`](research-plan.ru.md).

**Status.** `S2` closed PARTIAL (2026-09-01). `S3` is next. Last revised 2026-09-01.

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
> occupies and transitions between a *finite* set of model-specific **metastable**
> semantic states, whose escape times exceed the observation horizon.

*Phrasing note, from literature verification.* Zekri et al. (arXiv:2410.02724)
prove that an LLM with finite context is an ergodic unichain with a **unique**
stationary distribution. H1 must therefore not be read as "several stationary
states" — that would contradict established theory. Metastability is about
timescale separation *on the way* to the stationary distribution: a unichain can
contain long-lived almost-invariant sets whose escape times exceed any feasible
observation window, and that is exactly what an MSM macrostate decomposition
measures. Every claim in the paper is bounded by the observed turnover count.

Subsidiary, individually falsifiable:

- **H2 (semantic half-life).** Measurable information about the seed persists
  well past the context horizon: `T_½ > W`, plausibly `T_½ = c·W` with `c > 1`.
  Stated in the long-horizon-agent literature's terms: does **long-term memory
  emerge from long-context generation alone**, given that we supply no retrieval,
  no scratchpad and no summarisation? Any persistence must come from the model
  re-emitting information faster than the window evicts it.
- **H3 (confinement).** Mean squared displacement in representation space grows
  sublinearly and saturates: `MSD(τ) ∝ τ^α` with `α < 1`, plateauing — the
  signature of a bounded basin rather than free diffusion.
- **H4 (irreversibility).** Transition currents between macrostates are
  non-zero, `J_ij = π_i T_ij − π_j T_ji ≠ 0`: the long-run semantic dynamics
  are genuinely out of equilibrium, not a reversible walk.
- **H5 (temperature transition).** There is a temperature region separating a
  *confinement* regime (low `T`: few states, long dwell times, small `α`) from
  a *diffusion* regime (high `T`: many states, short dwell, `α → 1`).

  *Registered against a real tension.* Two verified adjacent papers disagree
  about temperature in neighbouring regimes: Wang et al. (ACL 2025) find
  paraphrasing limit cycles **robust to increasing temperature**, while Geng et
  al. (arXiv:2603.11228) find higher temperature **lengthens transients** in
  transformation chains. Zekri et al. derive temperature's effect on convergence
  rate theoretically. So H5 is a genuine open question in our regime, not an
  obvious expectation, and we may well be wrong.
- **H6 (window scaling).** `T_½`, mixing time, and macrostate count scale with
  `W` non-trivially — not proportionally.

**We do not claim** to be first to apply attractor language to LLMs, nor first to
track embeddings over generation, nor that temperature controls exploration. All
three are established. The nearest work was verified in full on 2026-08-30; see
[`literature/related-work.md`](literature/related-work.md) for the delta against
each paper.

Our contribution is the specific regime — *unbounded free-running generation
under an **imposed** finite sliding window, past the eviction of the initial
condition* — together with a reproducible benchmark and a dynamics-first
measurement suite. No verified paper occupies that regime: the nearest either
keep the whole history in context (multi-turn attractors), replace the state
entirely at each step under a transformation instruction (successive paraphrasing,
Markovian generation chains), or work analytically in token space without
measuring the semantic approach (LLMs as Markov chains).

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

### S0 — Foundations and feasibility audit `✓ closed 2026-08-30`

**Outcome:** 8 of 10 exit criteria passed, 1 partial, 1 failed-and-fixed. Actual
spend **$0.0128** of a $3 ceiling. Full report:
[`stages/stage-0/REPORT.md`](stages/stage-0/REPORT.md).

Seven findings changed the design: no base models exist on the provider;
`/completions` works everywhere despite not being advertised; three of four
models emit hidden reasoning tokens and one suppression flag lies; provider
pinning raises reproducibility from 20% to 100%; sustained throughput rather than
price is the binding endpoint constraint; the cost model underestimated input by
20.7% until block fill was measured; and four bugs in our own code would each
have produced confident wrong numbers.

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

**Question.** Over 32 window turnovers, is there any structure at all —
seed-dependent separation, recurring regions, non-trivial MSD?

Matrix, fixed by S0's measured prices and split into two configs because a single
factorial cannot give two models different matrices:

| Arm | Config | Model | Matrix | Trajectories | Forecast |
| --- | --- | --- | --- | --- | --- |
| core | `stage1_pilot_core.yaml` | mistral-nemo-12b | `W=8192`, `T=262144`, 2 temperatures × 8 semantic seeds × 3 stochastic | 48 | $9.68 |
| replication | `stage1_pilot_replication.yaml` | qwen3-8b | same window and length, 1 temperature × 8 semantic seeds × 2 stochastic | 16 | $8.02 |

Both at `chunk = 1024`, giving 32 turnovers and 256 chunk observations per
trajectory. The replication arm gives up the temperature contrast — mapping
temperature is S4's job; the pilot only needs to know whether the effect appears
in a second architecture at all.

Passes: generation → embedding (both spaces) → geometry (displacement,
distance-from-seed, inter-trajectory distance, autocorrelation, recurrence) →
first-look MSD → degeneracy diagnostics (repetition-loop detection, entropy
collapse).

Passes: generation → embedding (both spaces) → geometry (displacement,
distance-from-seed, inter-trajectory distance, autocorrelation, recurrence) →
first-look MSD → degeneracy diagnostics.

**Exit criteria.** Seed-identity signal measurably above a shuffled baseline
past `t = W` on both models; MSD exponent estimable with bootstrap CI narrower
than 0.2; <20% of trajectories degenerate into repetition loops (if more, the
sampling configuration is revised before proceeding).

**Additionally required by S0's findings**, as protocol diagnostics rather than
incidentals: realised block-fill distribution per model, stop-event rate per
model, reasoning-guard failure rate, and the rate of trajectories lost to
provider throttling.

**Budget.** ≤ $22 declared across the two arms; $17.70 forecast.

### S2 — Is the convergence a property of the model, or of the protocol?

**Closed PARTIAL, 2026-09-01.** Plan:
[`docs/stages/stage-2/PLAN.md`](stages/stage-2/PLAN.md). Report:
[`docs/stages/stage-2/REPORT.md`](stages/stage-2/REPORT.md). Re-plan:
[ADR-0008](decisions/ADR-0008-stage2-replan-after-convergence.md),
[ADR-0009](decisions/ADR-0009-bounded-reasoning-and-the-stage2-model-axis.md),
[ADR-0010](decisions/ADR-0010-stage2-findings-replan-s3.md).

What actually ran (not the ADR-0008 sketch): S2.3 determinism on all five
generators; S2.1 model axis 5 × 2 × 2 × 2 = 40 trajectories at `W = 4096`,
12 turnovers; S2.2 mechanism axis, qwen3-8b only, `raw_completion` vs
`assistant_prefill`, 16 trajectories. The local base-model arm of ADR-0008
was not implemented.

Headline measurements:

- Convergence is **not universal**. Long-trajectory fixed-point rate is 0/8
  on gemma-4-31b (CI 0–0; the process dies into silence glyphs) and 8/8 on
  gpt-oss-120b almost-`T` (CI 1–1). Qwen3-8b is 8/8 under both mechanisms.
  gpt-oss-20b produced no long trajectory (empty EOS). Glimmer: 2/8 reached
  `T`, both fixed points, both `T = 0.3` physics.
- Prefill does **not** remove the reviewer register (matched 4/8 vs 6/8 at
  step 1; surreal prefill falls into the register later) and does **not**
  change the qwen fixed-point rate (7/8 vs 8/8, difference CI [−0.375, 0.0]).
- Exact-match determinism: glimmer 100%, qwen 60%, gemma 20%, both gpt-oss
  20%. Q6's >90% on gemma was false.
- S2.1 completion 11/40. F8 failed. Spend **$2.54 / $6**. Embeddings and
  geometry charged $0 (cache).
- MSD on long trajectories is subdiffusive in both embedding spaces.
  Degenerate rows (120b, qwen, glimmer-physics, gemma-physics) do not
  support a confinement claim. Gemma surreal is subdiffusive *and*
  non-degenerate while writing silence glyphs.
- On qwen3-8b (S2.2) the seed-separation gap stays positive through 12
  turnovers in both spaces (band-12 CI excludes 0). S2.1 separation is
  mixed-generator and is not a half-life.

The Stage 1 reading survives as a claim about qwen3-8b under P1, not about
language models.

**Budget.** ≤ $6 declared; $2.8 forecast; **$2.54** actual.

### S3 — Metastability, Markov state models, and representation robustness `← current`

**Re-planned after Stage 2** ([ADR-0010](decisions/ADR-0010-stage2-findings-replan-s3.md)).
Do not default to prefill. Do not pool gemma-silence, qwen-reviewer,
glimmer-physics and 20b-fragments into one MSM.

**S3.0 (opened 2026-09-01; embeddings deferred).** A local 1–3B *base*
model at reduced `W` and a matched turnover count. The harness has
`api: local` ([ADR-0011](decisions/ADR-0011-local-base-provider.md));
the object is `google/gemma-3-1b-pt` at `W = 256`, `T = 12W`
([ADR-0012](decisions/ADR-0012-stage3-no-openrouter.md)). This opening
does **not** call OpenRouter: S3.0 is generation + surface diagnostics
only. Geometry of the base model waits for an embedding balance. Until
then every S3.1 sentence is instruct-under-P1. Gemma 4 E2B stays out.
A two-turnover smoke is not S3.0.

**S3.1 Dynamics, restricted sample.** `PCA → VAMP → k-means microstates →
non-reversible MSM → macrostates (PCCA+)`, with full MSM validation — VAMP
score cross-validation over `K`, implied timescales vs. `τ`, Chapman–Kolmogorov
test. Then dwell times, first-passage times, entropy rate, and **probability
currents** `J_ij`. Eligible arms: qwen3-8b (both mechanisms), glimmer
`T = 0.3` physics, gpt-oss-120b almost-complete. Fixed-point, looping and
silence remain three labels.

Independent geometry branch: `PCA → mutual-kNN → Leiden`, deliberately using no
temporal information. Agreement between branches (ARI/NMI) and across both
embedding spaces is the robustness argument. tICA is run as an ablation, and the
tICA/VAMP discrepancy is itself reported as a measure of irreversibility.

**Exit criteria.** Base-model comparison present or explicitly open; macrostate
count stable across `K` and across both embedding spaces **on the restricted
sample**; implied timescales flat over a `τ` range; CK test passed;
ARI(Leiden, MSM) reported per model/embedding with a bootstrap CI.

**Budget.** ≤ $10 (compute-bound once S3.0 is local; S3.0 itself must be
estimated before any spend).

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

## 5. Models — as measured in S0, not as hoped

**Revised 2026-08-30 after S0's provider audit.** The original table listed
Llama 3 8B *Base* as the primary arm. RouterAI carries **no base models at all**
— 468 catalogue entries, zero — and that slug returns `400 Model not found`. The
base arm is dropped ([ADR-0006](decisions/ADR-0006-no-base-models-available.md)).

| Model | Endpoint pinned | Quant. | USD/M in · out | Role |
| --- | --- | --- | --- | --- |
| Mistral Nemo 12B | Io Net | fp16 | 0.061 · 0.223 | **wide arm.** Only candidate with no reasoning at all. Chosen over the cheaper Parasail endpoint, which throttles after ~4 steps |
| Qwen3 8B | Alibaba | unknown | 0.163 · 0.633 | **replication arm.** Second architecture; needs `reasoning_effort: none` (9.96× block overshoot without it) |
| Muse Glimmer 30B | Parasail | bf16 | 0.417 · 1.530 | hybrid local/global attention, 2048-token local window — its own research axis (S4) |
| DeepSeek V4 Flash | DeepInfra | fp8 | 0.138 · 0.275 | frontier MoE control (S5/S6). Intrinsically non-deterministic even when pinned |
| ~~Llama 3 8B Base~~ | — | — | — | **unavailable.** Retained in config so audits keep reporting its absence |

`W` is always **imposed by us**, never taken as the model's native context.
That is what turns "compare five models" into "hold `θ` fixed and vary memory".

Every generator runs through **`raw_completion`** (`POST /completions`), which S0
found works on all four despite no endpoint advertising it, and which adds 1–8
template tokens against 27–107 for chat. `forcing = unforced` throughout: no
system prompt, no instruction text. The `chat_instructed` variant is retained as
a Stage 6 contrast condition, never pooled with unforced data.

Two protocol facts follow from S0 and apply to every model:

- **Reasoning is suppressed per model and verified per step.** Three of four
  models emit hidden reasoning tokens, and one suppression flag
  (`include_reasoning: false`) is accepted while doing nothing. A step with
  non-zero reasoning tokens fails the trajectory
  ([ADR-0005](decisions/ADR-0005-reasoning-tokens-disqualify.md)).
- **The stride `S` is not constant.** Models emit a stop token before filling the
  block: measured fill 0.88 mean, 0.04–1.00 range. `S` is model-determined within
  `[0, B]`, its distribution is reported, and the cost model is calibrated on it.

We do not claim to have measured base language models. That limitation belongs in
the method section, not the appendix.

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
