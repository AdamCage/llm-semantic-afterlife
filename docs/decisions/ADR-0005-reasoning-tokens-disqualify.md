# ADR-0005: Hidden reasoning tokens disqualify a step; the invariant is asserted, not configured

Status: accepted
Date: 2026-08-30
Stage: S0

## Context

Stage 0's continuation audit (S0.3) found that three of the four available
generators emit *hidden reasoning tokens*. The measured facts:

| Model | Mechanism | reasoning_tokens | completion_tokens (max_tokens=160) | visible text |
| --- | --- | --- | --- | --- |
| qwen3-8b | `/completions` | 672 | 781 | 702 chars |
| muse-glimmer-30b | `/chat/completions` | 232 | 160 | **empty** |
| deepseek-v4-flash | `/completions` | 160 | 160 | **empty** |
| mistral-nemo-12b | any | 0 | 96 | 583 chars |

This breaks the experiment in three independent ways.

1. **The recursion is not the model's own.** We implement
   `X_{t+1} = Tail_W(X_t ⊕ Y_t)` where `Y_t` is what the model generated. If the
   model generates reasoning and returns only the visible remainder, the block we
   append is a *filtered* `Y_t`. The process we measure is then not the process
   we describe, and no amount of downstream care repairs that.
2. **`max_tokens` stops bounding the block.** Reasoning tokens are not always
   charged against it: qwen3-8b returned 956 tokens for a 96-token request, a
   9.96x overshoot. The window would then advance by a stride we did not choose,
   so `S` — and with it the cost law, the step/chunk alignment, and the reported
   turnover count — is not what the manifest claims.
3. **The reasoning text is a different semantic regime.** The observed traces are
   meta-commentary about the task ("We need answer continuation only. Need
   continue text. Need obey: no comment etc."). That is exactly the
   meta-textual attractor we must be able to distinguish from free continuation,
   so silently discarding it would contaminate the object of study.

The suppression audit (S0.3b) then found something worse than the reasoning
itself. Of seven candidate switches:

- `reasoning_effort: "none"` (and `reasoning: {effort: none}`) genuinely
  suppresses generation — accepted by qwen3-8b, mistral-nemo and deepseek,
  **rejected** by muse-glimmer.
- `include_reasoning: false` **only hides the trace**. qwen3-8b still produced
  508 reasoning tokens with it set. A parameter that looks like it disables
  reasoning while the model keeps generating it is precisely the kind of silent
  corruption that would have survived into the paper.
- deepseek-v4-flash reasons *intermittently*: identical-shaped probes gave 160
  reasoning tokens on one call and 0 on another. Intermittent is worse than
  consistent, because it corrupts individual blocks mid-trajectory rather than
  failing visibly at the start.

Neither behaviour is documented: RouterAI's parameter reference does not mention
`reasoning` at all, though endpoints advertise it in `supported_parameters`.

## Decision

1. **Zero reasoning tokens is a per-step protocol invariant**, checked against
   the provider's own `usage.completion_tokens_details.reasoning_tokens` on every
   step. A violation raises and marks the trajectory `FAILED` with the reasoning
   head logged. Default tolerance is 0, configurable per model via
   `max_reasoning_tokens` but never raised without an ADR.
2. **Block overshoot is likewise a per-step invariant.** A completion exceeding
   `1.10 x max_tokens` fails the trajectory, because the stride would not be `S`.
3. **The reasoning switch is per-model configuration** (`extra_body` in the
   generator definition), recorded in every manifest as part of the protocol.
   The measured values are in `configs/models/generators.yaml`.
4. **A configured switch is never treated as evidence.** The guard runs
   regardless of what `extra_body` contains — because `include_reasoning: false`
   demonstrated that a switch can be accepted and still not work, and because
   deepseek demonstrated that behaviour can vary between calls.
5. **`raw_completion` becomes the primary continuation mechanism** for all
   models, superseding the `chat_instructed` defaults. It is available on every
   model despite not being advertised, adds far fewer template tokens (1-8
   against 27-107), and for muse-glimmer it is the *only* mechanism that avoids
   reasoning entirely.

## Alternatives considered

- **Append the reasoning text to the window as well.** Faithful to "everything
  the model generated", but the provider does not always return the trace, its
  token boundaries are unknown to us, and it would make the trajectory a mixture
  of two registers. Rejected.
- **Accept reasoning and treat it as part of the generator's character.** Then
  block size is uncontrolled and cross-model comparison at fixed `S` becomes
  impossible. Rejected.
- **Drop every reasoning-capable model.** That would leave one model
  (mistral-nemo), destroying the cross-family comparison that the paper's
  main claim requires. Rejected in favour of suppression plus verification.
- **Trust the switch and skip the guard.** Rejected on direct evidence: one
  switch is accepted while being ineffective, and one model's behaviour varies
  between identical calls.

## Consequences

- Every generator config now carries a measured `extra_body`, and the manifest
  records it, so a run states exactly which protocol produced it.
- Trajectories can fail for a *methodological* reason rather than a transport
  one. That is intended: a failed trajectory recorded as missing data is far
  better than a silently filtered one.
- Cost forecasts become trustworthy only because overshoot is now caught; without
  the guard, qwen3-8b would have cost roughly ten times its estimate.
- Stage 1 must report the reasoning-guard failure rate per model alongside its
  results, and the paper's limitations must state that all generators are
  instruct-tuned models with reasoning suppressed rather than base models.

## Reversal cost

Low in code. High in data: any trajectory generated before this guard existed
would have to be discarded, since there would be no record of whether its blocks
were complete.
