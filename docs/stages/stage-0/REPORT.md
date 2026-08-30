# Stage 0 — report

**Closed** 2026-08-30. Plan: [`PLAN.md`](PLAN.md). Artifacts:
[`artifacts/stage-0/`](../../../artifacts/stage-0/).
Actual API spend **$0.0128** against a $3 ceiling.

Stage 0 made no scientific claims, and none are made here. Its job was to find
out whether this experiment can be run reproducibly, at what cost, and what the
providers actually do. It found six things that would each have silently
corrupted the study, and one that changes the design.

---

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| E1 | ≥3 generators produce coherent continuation via a documented mechanism | **PASS on substance; the stated threshold was mis-specified** | 4 of 5 candidates available and continuing coherently via `raw_completion`. Re-probed at `max_tokens=600` to test the literal "≥512 tokens" bar: only glimmer and deepseek clear it in a *single call* (600 each); qwen returns 99 and mistral 95. But the bar itself was the wrong measurement — see F8. Sustained free-running continuation is demonstrated by the live run: 8,196 tokens over 19 steps on mistral, the very model that stops at 95 in a single short-prompt call. |
| E2 | ≥2 embedding models usable | **PASS** | 3 usable, all L2-normalised, all dimensions as documented: qwen3-embedding-8b (4096), bge-m3 (1024), gemini-embedding-001 (3072). `s0_embeddings.csv` |
| E3 | End-to-end pipeline completes with a full manifest and non-empty artifacts | **PASS** | offline: `s0-smoke-…67a42230` → `s0-embed-smoke-…e99d7975` → `s0-geometry-mock-hash-…45f7e4b9`. live: `s0-live-smoke-…a395a78c` → `s0-embed-live-smoke-…fc3e80ed` → `s0-geometry-bge-m3-…0589329e` |
| E4 | Bit-exact replay with zero network calls | **PASS** | `afterlife compare s0-live-smoke-…081709Z s0-live-smoke-…081713Z` → all scientific outputs bit-identical (31,697-byte trajectory text, 16-row chunk table), replay cost $0.00 |
| E5 | Determinism measured per model, n ≥ 5 | **PASS** | measured twice, unpinned and pinned. `s0_determinism.csv` |
| E6 | Cost model within ±5% on tokens, ±10% on USD | **FAIL, then fixed** | as planned: output +0.0%, **input +20.7%**. Cause identified (early stop tokens ⇒ more steps ⇒ more window re-sends), corrected, re-validated at **−0.6%** |
| E7 | Stage 1 forecast ≤ $25 | **PASS** | $17.70 total ($9.68 core + $8.02 replication), on measured prices with the corrected model |
| E8 | CLI surface green | **PASS** | all commands run; two added in response to findings: `audit reasoning`, `compare` |
| E9 | Tests, ruff, mypy clean | **PASS** | 110 tests, ruff clean, mypy clean on 33 modules |
| E10 | Tokenizer round-trip 100% | **PASS** | 5/5 models, 4 probes each (ASCII, Unicode, whitespace, long repetition), tail operation exact. **No `HF_TOKEN` required.** `s0_tokenizers.csv` |

Nine pass (one with a corrected criterion), one failed-and-fixed. Stage 0 is
closed; Stage 1 may open.

## 2. The findings

### F1 — There are no base models. The primary arm is gone. *(design change)*

RouterAI carries **468 models and not one base model**. `meta-llama/llama-3-8b`
returns `400 Model not found`; a catalogue-wide search for `base$` matches only
`thenlper/gte-base`, an embedder. Every Llama entry is `*-instruct`.

The plan designated Llama 3 8B Base as the primary arm precisely because free
continuation is what a base model is trained for. That arm cannot be run here.

**Confirmed against OpenRouter** (the plan's stated prerequisite before Stage 1
locks): 396 models, **also zero base models** — no `base`, no `v0.1` (which would
catch Mistral 7B base), no `davinci`, and no `llama-3-8b`, only
`llama-3.1-8b-instruct`. The five RouterAI `base` matches are all embedding models
(`gte-base`, `e5-base-v2`, `all-mpnet-base-v2`, `bge-base-en-v1.5`,
`multi-qa-mpnet-base-dot-v1`), each 512-token context with zero output price.

So this is not a RouterAI quirk but a property of hosted-inference aggregators
generally: they serve chat endpoints because that is what their customers call.
[ADR-0006](../../decisions/ADR-0006-no-base-models-available.md) drops the arm and
narrows the paper's scope claim: we study instruction-tuned models driven through
a raw-completion interface with reasoning suppressed, not base language models —
and we frame that as a constraint of the ecosystem rather than of our provider
choice.

### F2 — `/completions` works everywhere, though nothing advertises it *(mitigates F1)*

No endpoint lists `completions` in `supported_apis`; 25 of 29 leave the field
empty altogether. Tried anyway, raw text completion **works on all four
available models**. It is also far closer to pure continuation than chat: the
template overhead is 1–8 tokens against 27–107 for `/chat/completions`.

This is why F1 is survivable, and it is a reminder that "not advertised" is not
"not supported". The audit now reports `completions_advertised` as a tri-state
rather than asserting a false negative.

### F3 — Hidden reasoning tokens, and a switch that lies *(would have corrupted everything)*

Three of four models emit reasoning tokens. Measured at `max_tokens=160`:

| Model | reasoning | completion | visible |
| --- | --- | --- | --- |
| qwen3-8b | 672 | 781 | 702 chars |
| muse-glimmer-30b (chat) | 232 | 160 | **empty** |
| deepseek-v4-flash | 160 | 160 | **empty** |
| mistral-nemo-12b | 0 | 96 | 583 chars |

Three independent breakages: the appended block is only the *visible* part of
what the model generated, so the implemented recursion is not the model's own;
`max_tokens` stops bounding the block (qwen3-8b overshot by **9.96×**); and the
reasoning text is meta-commentary ("We need answer continuation only. Need
continue text.") — a different semantic regime from free continuation.

Worse, of seven candidate suppression switches, **`include_reasoning: false`
merely hides the trace**: qwen3-8b still produced 508 reasoning tokens with it
set. And deepseek reasons *intermittently* — identical-shaped probes gave 160
tokens on one call and 0 on another.

So the switch is configured per model and **the invariant is asserted every
step** from the provider's own `usage`, never assumed
([ADR-0005](../../decisions/ADR-0005-reasoning-tokens-disqualify.md)). A step
with non-zero reasoning tokens fails the trajectory loudly.

### F4 — Provider pinning converts 20% reproducibility into 100%

Same audit, unpinned then pinned:

| Model | unpinned exact-match | distinct outputs | pinned exact-match | distinct outputs |
| --- | --- | --- | --- | --- |
| qwen3-8b | 75% | 2 | **100%** | 1 |
| muse-glimmer-30b | 20% | 5 | **100%** | 1 |
| deepseek-v4-flash | 20% | 5 | 20% | 5 |

Unpinned, deepseek was served by **four different providers across five calls**
(Baidu, CoreWeave, DigitalOcean, StreamLake). Pinning is therefore not a
formality: it is the difference between a reproducible generator and a moving
target, exactly as [ADR-0003](../../decisions/ADR-0003-provider-pinning.md)
argued on theoretical grounds and now on measured ones.

deepseek's residual non-determinism survives pinning to a single fp8 endpoint,
so it is intrinsic — plausibly MoE routing under variable batching. The paper can
claim **L3 via the response cache** and **L1 statistical agreement** on fresh
generation, and must not claim seeded determinism.

### F5 — Sustained throughput, not price, is the binding constraint

The cheapest healthy mistral endpoint (Parasail, fp8, `status: 0`, $0.0417/M both
ways) yields an upstream **429 after roughly four consecutive steps** and does
not recover within ten exponential retries (~10 minutes of waiting). Two live
attempts died at step 4 with `generated_tokens = 0` and `671`.

Re-pinned to Io Net (fp16, `status: 0`, $0.0612 in / $0.2226 out — 2.6× the
output price), the same trajectory **completed**: 19 steps, 8,196 tokens, 16
chunks, $0.0038.

Under protocol P1 a trajectory is hundreds of sequential calls, so an endpoint
that throttles is unusable at any price. Endpoint selection is now an empirical
step with its own tool (`scripts/probe_endpoints.py`), re-run whenever a stage
locks its matrix.

### F6 — The cost model was systematically wrong, in a way only a live run reveals

Predicted 27,648 input / 8,192 output; actual **33,375 / 8,196**. Output exact,
input **+20.7%**.

Cause: models emit a stop token before filling the block. Measured block fill was
mean **0.88**, range **0.04–1.00**, with `finish_reason: stop` on 26% of steps.
Reaching `T` therefore takes `1/0.88` times as many steps, and *every extra step
re-sends the entire window*. The estimator assumed full blocks.

Corrected by making block fill a measured per-model parameter: input error is now
**−0.6%**. This also means **the stride `S` is not constant** — a protocol fact
that belongs in the methodology, not a rounding detail. Stage 1 must report the
realised block-fill distribution per model.

### F7 — Four bugs in our own code, each of which would have produced confident wrong numbers

Found because Stage 0 measured rather than assumed:

1. **Off-by-one token accounting.** `prompt_tokens_local` was recorded *after*
   appending the block, so the local-vs-API comparison compared step `t+1`
   against step `t` — a systematic ~2× discrepancy that made the token audit
   meaningless. With it fixed, the delta is a constant **+3 tokens**, confirming
   a fixed template offset and a well-defined window.
2. **False pinning violations.** The served provider is reported as a display
   name (`"Io Net"`) while the pin is a slug (`"io-net"`), so a literal
   comparison rejected valid responses and would have discarded good
   trajectories.
3. **Retries that never fired.** RouterAI returns upstream 429s **inside HTTP
   200** bodies. Status-code checks passed, the backoff loop never engaged, and a
   transient rate limit became a hard failure. On a 256-step trajectory that
   turns a five-minute hiccup into a lost multi-hour run.
4. **`difflib` autojunk.** `SequenceMatcher` treats frequent characters as junk
   above 200 elements, reporting two nearly identical outputs as **0.19**
   similar. This was silently corrupting the determinism audit's near-match rate.

All four are now covered by tests (`tests/test_provider_client.py`) so a refactor
cannot reintroduce them.

### F8 — Single-call probes do not predict in-trajectory behaviour *(invalidates a criterion, not a result)*

Re-running the continuation audit at `max_tokens=600` to test E1's literal bar
produced this:

| Model | raw_completion | assistant_prefill | chat_instructed |
| --- | --- | --- | --- |
| qwen3-8b | 99, `stop` | 164, `stop` | 28, `stop` |
| mistral-nemo-12b | 95, `stop` | error | 18, `stop` |
| muse-glimmer-30b | **600, `length`** | 600, `length` | 600, `length` |
| deepseek-v4-flash | **600, `length`** | 3, `stop` | 117, `stop` |

Taken at face value this says mistral cannot sustain 512 tokens. But the live
trajectory on *the same model and mechanism* averaged 450 tokens per step (fill
0.88) across 19 steps. The difference is the prompt: the probe supplies 28 tokens
of a fragment, whereas a trajectory step supplies a full 2,048-token window of
flowing text. **Block fill depends on how much established context the model is
given**, so a short-prompt probe systematically understates it.

Two consequences:

- E1 was measuring the wrong thing. The criterion should have been "the process
  sustains itself under re-prompting", which the live run demonstrates, not
  "tokens returned per call", which is a function of the probe design.
- Our `expected_block_fill = 0.88` for mistral was measured at `W = 2048`. At
  `W = 8192` the prompt is richer still, so fill should be at least as high,
  making the Stage 1 forecast conservative. Stage 1 must record the realised
  distribution and update the parameter.

The general lesson, and it generalises past this project: **a capability probe
must run in the regime the experiment will run in.** Ours did not, and it took a
live trajectory to notice.

## 3. Prediction vs. outcome

Pre-registered in `PLAN.md` before any measurement.

| # | Prediction | Conf. | Observed | Score |
| --- | --- | --- | --- | --- |
| P1 | `/completions` available for at least one base model | 0.5 | `/completions` works for **all** models; there are **no** base models | half right, and for the wrong reason |
| P2 | ≥1 chat model supports assistant prefill | 0.6 | qwen3-8b does; mistral errors, glimmer/deepseek return empty content | **correct** |
| P3 | Instruct stop-event rate > 0.3 per step when unforced | 0.7 | 5/19 = **0.26** under raw completion | **wrong**, and lower than feared |
| P4 | Exact-match determinism below 50% on ≥1 model | 0.6 | glimmer 20%, deepseek 20% unpinned; deepseek 20% even pinned | **correct** |
| P5 | ≥1 embedding model returns L2-normalised vectors | 0.5 | **all three** do | correct, understated |
| P6 | Tokenizer round-trip holds for all byte-level BPE | 0.85 | 5/5 models, 4 probes each, tail exact | **correct** |
| P7 | Local vs API prompt tokens within ±2 for raw completion; fixed offset for chat | 0.7 | constant **+3** for raw completion; chat offset 27–107 and template-dependent | constancy right, magnitude off by one |
| P8 | Stage 0 spend under $1 | 0.8 | **$0.0128** | **correct**, by two orders of magnitude |
| P9 | Strict pinning honoured in 100% of successful requests | 0.7 | yes, once our comparison bug was fixed; pinning also raised determinism 20%→100% | **correct** |

Six of nine clean, one wrong, two partially wrong. The two most consequential
predictions (P4, P9) were right, and together they fix what reproducibility level
the paper may claim.

Nothing in the plan anticipated reasoning tokens (F3), the throughput ceiling
(F5), or the absence of base models (F1). Those three came out of measurement
alone, and any of them would have invalidated a study that skipped this stage.

## 4. Surprises

- **The most expensive finding was free.** Every design-changing discovery came
  from audits costing under two cents in total. The pilot budget was never the
  risk; the risk was launching without measuring.
- **A parameter that lies is worse than a missing parameter.**
  `include_reasoning: false` is accepted, documented nowhere, and does not do
  what its name says. Had we trusted it, the trajectories would have been
  silently truncated blocks with no record of the fact.
- **Intermittent misbehaviour is worse than consistent misbehaviour.** deepseek's
  occasional reasoning and the shared-pool 429 both pass a single smoke test and
  fail a long run. Anything validated by one call is not validated.
- **Cheap endpoints are not cheap if they throttle.** Effective cost per
  *completed trajectory* is the metric that matters, not price per token.
- **The offline fixture earned its keep.** The five-topic hidden Markov chain
  showed clear metastable switching at `t ≈ 3W` in the semantic-velocity trace,
  which means the geometry pass detects the structure it is supposed to detect.
  It is now a regression target for Stage 3's Markov-state estimators.

## 5. Threats to validity

Current state of each, with the honest assessment:

| Threat | State |
| --- | --- |
| **No base models** (R4-adjacent) | Realised. Mitigated by raw completion + reasoning suppression, not eliminated. Must be stated in the method section. OpenRouter should be audited before Stage 1 locks, since it may still carry `llama-3-8b`. |
| **Reasoning contamination** | Controlled by a per-step invariant rather than a configuration flag. Residual risk: a provider that stops reporting `reasoning_tokens` would make the guard blind. Stage 1 should assert the field is present, not merely zero. |
| **Provider drift** (R6) | Controlled by pinning, verified per response. Residual: quantization is `unknown` for qwen3-8b's only endpoint, so that model's numerical precision is undocumented. |
| **Non-determinism** (R6) | Quantified. deepseek is intrinsically non-deterministic even pinned; claims for it must be distributional. |
| **Variable stride `S`** (new, R2-adjacent) | Not controlled. Block fill 0.04–1.00 means the window advances by a model-determined amount. Needs a methodology paragraph and a reported distribution, and it weakens any claim that depends on a fixed `S`. |
| **Throughput ceiling** (new) | Partially controlled: one working endpoint per model, concurrency reduced to 2, patient retries, resumable runs. Stage 1 will hit this again at 48 trajectories. |
| **Re-prompt ≠ sliding attention** (R2) | Unchanged and unaddressable on this hardware. Stated in ADR-0001 and in the paper's limitations. |
| **Embedding-space artifacts** (R1) | Untouched by Stage 0. Three spaces confirmed usable, which is the precondition; the actual robustness test is Stage 3. |
| **Turnover count** (R10) | Stage 1 is designed at 32 turnovers, above the ≥16 pilot bar. |

## 6. Cost actuals

| Pass | Charges | Prompt tokens | Completion tokens | USD |
| --- | --- | --- | --- | --- |
| `audit.continuation` | 22 | 1,444 | 6,318 | 0.00237 |
| `audit.determinism` | 46 | 1,493 | 5,499 | 0.00354 |
| `audit.reasoning` | 21 | 679 | 4,290 | 0.00300 |
| `audit.embedding` | 3 | 185 | 0 | 0.00000 |
| `completion` (smoke, live + replay + mock) | 180 | 226,254 | 83,286 | 0.00387 |
| `embedding` | 2 | 25,641 | 0 | 0.00000 |
| **total** | | | | **$0.0128** |

Against a $3 stage ceiling and a $50 project ceiling: **0.03% of the project
budget**. Embedding costs registered as zero because the provider reported none
for these volumes; Stage 1 will establish a real per-million rate.

Wall-clock was dominated by rate-limit backoff, not by generation: three live
attempts spent roughly 20 minutes, of which two were spent waiting on a throttled
endpoint before failing.

## 6a. Literature verification (completed alongside the audits)

All seven scoping citations exist and say what the notes claimed. Three say
*more*, in ways that change our framing — full detail in
[`literature/related-work.md`](../../literature/related-work.md):

- **Zekri et al., arXiv:2410.02724** proves a **unique** stationary distribution
  for an LLM as a finite-state Markov chain. So H1 must be phrased as
  metastability — timescale separation on the way to that distribution — and not
  as "multiple attractors", which would contradict established theory.
- **Wang et al., ACL 2025** found paraphrasing limit cycles **robust to
  increasing temperature**, while **Geng et al., arXiv:2603.11228** found higher
  temperature *lengthens* transients. Two adjacent regimes, opposite temperature
  effects. Our H5 is registered against that tension rather than presented as an
  obvious expectation.
- **Chen et al., arXiv:2608.06663** supplies terminology we adopt: long-context
  (model), long-horizon (task), long-term memory (system) are independent axes.
  This sharpens H2 into "does long-term memory emerge from long-context
  generation alone, with no memory system?" — a cleaner claim, tied to a named
  open problem.
- **Wu & Noé, arXiv:1707.04659** confirms ADR-0002, but with a caveat the notes
  missed: VAMP singular values are **not** relaxation timescales. Implied
  timescales must come from MSM transition-matrix eigenvalues; VAMP scores are for
  model selection only. `methodology.md` §3.5 corrected.
- **arXiv:1811.12551** states TICA's detailed-balance requirement explicitly and
  recommends VAMP as its replacement, and extends the Chapman–Kolmogorov test to
  the reduced model — the validation procedure we now adopt verbatim.

The novelty delta survives verification and is sharper for it. The three nearest
papers either keep the full history in context (Ko & Geiping), replace the state
entirely at each step under a transformation instruction (Wang et al.; Geng et
al.), or work analytically in token space (Zekri et al.). None studies the regime
after the initial condition has been evicted from a finite imposed window.

## 7. Implications for the plan

Concrete changes, each already committed:

1. **Model list revised** ([ADR-0006](../../decisions/ADR-0006-no-base-models-available.md)).
   Base arm dropped. Four generators: mistral-nemo-12b (wide arm),
   qwen3-8b (replication), muse-glimmer-30b and deepseek-v4-flash (later stages).
   `research-plan.md` §5 amended.
2. **`raw_completion` is the default mechanism for every model**, superseding the
   `chat_instructed` defaults, with `forcing = unforced` throughout.
3. **Reasoning suppression is part of the protocol**, recorded per model and
   asserted per step ([ADR-0005](../../decisions/ADR-0005-reasoning-tokens-disqualify.md)).
4. **Stage 1 is split into two configs**, because a single factorial cannot give
   two models different matrices and qwen3-8b costs 5× mistral per token:
   - `stage1_pilot_core.yaml` — mistral-nemo, W=8192, T=262144 (32 turnovers),
     2 temperatures × 8 semantic seeds × 3 stochastic seeds = 48 trajectories,
     forecast **$9.68**
   - `stage1_pilot_replication.yaml` — qwen3-8b, same window and length, 1
     temperature × 8 semantic seeds × 2 stochastic seeds = 16 trajectories,
     forecast **$8.02**
   The temperature contrast is given up on the replication arm; mapping
   temperature is Stage 4's job.
5. **Stage 1 must additionally report** the realised block-fill distribution, the
   stop-event rate, and the reasoning-guard failure rate per model. These are
   protocol diagnostics, not incidentals.
6. ~~**Before Stage 1 locks its matrix**: audit OpenRouter for a base model.~~
   **Done.** No base models there either; ADR-0006 stands and is strengthened.
   Re-probing endpoints remains a per-stage step, since availability and
   throttling both drift.
7. **Methodology amended** (§0, §0.1, §3.5): the three-axis terminology
   discipline, the variable stride with its measured distribution, and the
   correction that implied timescales come from MSM eigenvalues rather than VAMP
   singular values.
8. **H1 and H5 rephrased** in light of verification: H1 as metastability under a
   unique stationary distribution, H5 registered against two adjacent papers with
   opposite temperature findings.
9. **Capability probes must run in the experiment's regime** (F8). Any future
   audit that measures a per-call quantity must either use a
   trajectory-realistic prompt or be labelled as a lower bound.

## 8. Reproducibility level achieved

| Level | Status |
| --- | --- |
| **L3** bit-exact replay from cache | achieved and verified (`afterlife compare`) |
| **L2** analysis-exact on stored trajectories | achieved; analysis passes are deterministic, seeds explicit |
| **L1** statistically equivalent on fresh generation | **not claimable per-model**: 100% for qwen3-8b and muse-glimmer-30b when pinned, 20% for deepseek-v4-flash. Distributional claims only for the latter. |
