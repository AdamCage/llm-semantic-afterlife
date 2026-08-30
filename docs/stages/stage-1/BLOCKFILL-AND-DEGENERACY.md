# S1.0b — block fill and degeneracy across four generator families

Same window (`W = 8192`), same temperature (1.0), same seed (`physics`), same
mechanism (`raw_completion`), same target (`T = 12288`). Only the generator
differs, so the numbers are directly comparable.

Reference row is 237 chunks of public-domain English prose (Carroll and Darwin),
cut by the same tokenizer at the same 1024-token size
(`scripts/calibrate_degeneracy.py`).

| Generator | Endpoint | Quant. | Block fill (mean / min) | Stop rate | Repetition | × natural | Type-token | Entropy | Prompt Δ | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| *natural prose* | — | — | — | — | **0.034** | 1.0× | 0.41 | 7.40 | — | reference |
| **muse-glimmer-30b** | `parasail/bf16` | bf16 | **0.949** / 0.544 | **0.111** | **0.028** | **0.82×** | 0.45 | 7.34 | **1** | FAILED (empties) |
| **qwen3-8b** | `alibaba` | unknown | **0.928** / 0.659 | 0.462 | **0.041** | 1.2× | **0.50** | **7.65** | 12 | COMPLETED |
| mistral-nemo-12b | `io-net/fp16` | fp16 | 0.131 / 0.008 | 0.990 | 0.220 | 6.5× | 0.34 | 6.99 | 3 | COMPLETED |
| llama-3.1-8b-instruct | `groq` | unknown | 0.248 / 0.009 | 0.915 | 0.360 | 10.6× | 0.28 | 6.81 | 35 | COMPLETED |

## What this settles

**The collapse is not a property of the regime.** Two of four families sustain
near-full blocks *and* produce text statistically indistinguishable from human
prose under the same protocol. The stop-token collapse and the repetition
collapse are the same defect and they belong to specific models, not to
free-running generation under a finite window. The S1.0 conclusion drawn from
llama alone was wrong, and it was wrong because it generalised from one
generator.

**The two failure modes coincide exactly.** Fill 0.93–0.95 goes with repetition
at or below natural prose; fill 0.13–0.25 goes with 6–11× natural repetition.
That is not a coincidence: a model that has fallen into a loop also emits its
stop token early, because it has run out of things to say. Block fill is
therefore a *cheap online proxy* for degeneracy — measurable from `usage`
without embedding anything — and Stage 1 should monitor it per step as an early
warning rather than discovering collapse in post-analysis.

**Glimmer writes better than the reference corpus.** Repetition 0.028 against
0.034 for Carroll and Darwin, with the cleanest prompt overhead of any endpoint
(1 token) and a known bf16 quantization. It is the most attractive generator on
every quality axis.

## Two problems that need resolving before Stage 1 locks

**Glimmer returns empty completions.** It failed after five consecutive empty
responses at 8,742 of 12,288 tokens. The guard behaved correctly — five empties
in a row is not free-running — but the cause is unknown. If it is transient
provider behaviour it can be retried through; if the model genuinely stops
producing visible content once conditioned on a full window, that is the same
family of finding as the stop-token collapse and disqualifies it. Cheap to test:
re-run with a longer empty tolerance and inspect the raw responses.

**Mistral produced a tokenizer round-trip failure** at step 100. One event in
104, but a round-trip failure means the window boundary was not where the
manifest claims, so `W` is not `W` for that trajectory. Mistral is already
disqualified on degeneracy; this is recorded because the same check must stay
green on whichever generator is chosen.

## Consequence for the Stage 1 matrix

qwen3-8b becomes the primary generator: it completed cleanly, sustains fill
0.928, and its type-token ratio (0.50) and entropy (7.65) exceed the natural
reference. Its drawback is that its single endpoint reports `unknown`
quantization, which is a provenance limitation to state rather than one we can
design away.

Glimmer becomes the replication arm if the empty-completion behaviour proves
transient — it would also bring the hybrid local/global attention axis that makes
it interesting in its own right. Otherwise the replication arm needs a fifth
candidate, since mistral and llama are both disqualified on output quality.
