# ADR-0006: The base-model arm is unavailable; the paper studies instruct models with suppressed reasoning

Status: accepted
Date: 2026-08-30
Stage: S0

## Context

The research plan designated Llama 3 8B **Base** as the primary arm, on the
grounds that free continuation (`continue this text forever`) is exactly what a
base language model is trained to do, whereas instruct models introduce EOS
behaviour, turn structure and an RLHF policy as confounds.

Stage 0's provider audit measured the following:

- `meta-llama/llama-3-8b` returns `400 Model not found` on RouterAI.
- The full catalogue holds **468 models and not a single base model**. A regex
  search for `base$` matches exactly one entry, `thenlper/gte-base`, which is an
  embedding model. Every Llama entry is `*-instruct`; the same holds for the
  other families.

This is a property of the aggregator's product, not of our configuration:
routers serve chat endpoints because that is what their customers call.

Two consolations came out of the same audit, and they change the severity:

- **`/completions` works on every available model**, despite no endpoint
  advertising it. Raw text completion adds only 1–8 template tokens against
  27–107 for chat, so we can drive instruct models through a near-pure
  continuation interface rather than a conversational one.
- Reasoning can be suppressed and, more importantly, *verified* suppressed
  (ADR-0005), removing the largest instruct-specific contaminant.

## Decision

1. **Drop the base-model arm from the experimental design.** The entry stays in
   `configs/models/generators.yaml` marked unavailable so that the audit table
   keeps reporting its absence rather than quietly omitting it.
2. **All generators run through `raw_completion`** (`POST /completions`), the
   closest available approximation to unforced continuation.
3. **`forcing = unforced` everywhere**: no system prompt, no instruction text.
   The `chat_instructed` arm is retained in the code as a *contrast condition*
   for Stage 6, not as the default, and is never pooled with unforced data.
4. **The limitation is stated in the paper's method section**, not the appendix:
   every generator is an instruction-tuned model driven through a raw-completion
   interface with reasoning suppressed. We do not claim to have measured base
   language models.
5. **Local inference is the escalation path** if a reviewer requires a true base
   model. A small base model (1–3B) on CPU at small `W` is feasible on the
   available hardware and would serve as an existence check rather than a full
   arm. Logged in `backlog.md`.

## Alternatives considered

- **Find a base model elsewhere.** OpenRouter historically carried
  `meta-llama/llama-3-8b`; if the OpenRouter key materialises, S0's audit should
  be re-run there before Stage 1 locks its matrix. Worth one cheap check, and it
  would restore the arm outright — so this ADR is explicitly provisional on
  that.
- **Run a base model locally for the whole experiment.** CPU-only, 4 cores. A
  256k-token trajectory would take days per trajectory. Infeasible as an arm.
- **Proceed as if instruct models were base models.** Rejected: the confounds
  are real and a reviewer would find them.
- **Abandon the project.** Disproportionate: the central question — what happens
  past the context horizon — is unchanged, and instruct models driven through a
  completion interface with reasoning off are a legitimate object of study. They
  are also, arguably, the deployment-relevant one.

## Consequences

- The `is_base_model` flag is now `false` for every generator actually used, and
  Stage 1 reports the stop-event rate per model to quantify how much EOS
  behaviour remains under raw completion.
- The novelty claim is unaffected — it was never about base models — but the
  *scope* claim narrows: "free-running generation" means "free-running through a
  raw-completion interface on an instruction-tuned model".
- Cross-family comparison survives with four models (qwen3-8b, mistral-nemo-12b,
  muse-glimmer-30b, deepseek-v4-flash), which is enough for the model-specificity
  claim in H1.
- The research plan's model table and the "base vs instruct" framing in
  `research-plan.md` §5 need amending in the same commit as this ADR.

## Reversal cost

Low. If a base model becomes reachable (OpenRouter, or rented GPU), it is added
as one more generator config; nothing already collected is invalidated, and the
comparison becomes strictly stronger.
