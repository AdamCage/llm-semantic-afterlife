# ADR-0009: A bounded, measured reasoning budget is admissible; a hidden one is not

Status: accepted
Date: 2026-09-01
Stage: S2
Amends: [ADR-0005](ADR-0005-reasoning-tokens-disqualify.md), [ADR-0008](ADR-0008-stage2-replan-after-convergence.md)

## Context

ADR-0005 set the per-step tolerance for reasoning tokens to zero and required an
ADR to raise it. This is that ADR.

Stage 1 could not assess exit criterion E2: every number rested on one generator,
because muse-glimmer-30b appeared unable to free-run at `W = 4096` and llama and
mistral lost every cell to HTTP 429. A stage whose results rest on one model is a
claim about one model.

Three newer generators were proposed as a remedy. The capability probe (S2.0)
produced four measurements that change the position, and one correction to a
conclusion this project had already drawn.

**The correction first.** The initial probe reported "0 of 18 usable" for
`gpt-oss-120b` and "0 of 11" for `gpt-oss-20b`, and that was read here as *the
models are unusable*. It meant something narrower: every endpoint refuses
`reasoning.enabled=false` with an explicit
`"Reasoning is mandatory for this endpoint and cannot be disabled"`. The probe
had only ever tried to switch reasoning off. With reasoning *allowed*, both
models serve `/completions` normally.

**Reasoning at the real regime is small, and it was four times larger than the
cheap probe suggested.** Measured on a genuine 4096-token window of trajectory
prose at `max_tokens = 1024`:

| model | reasoning tokens | finish_reason | block fill |
| --- | --- | --- | --- |
| gpt-oss-120b | 43, 33 | length, length | 1.00, 1.00 |
| gpt-oss-20b | 0, 0 | length, stop | 1.00, 0.44 |
| gemma-4-31b-it | 0, 0 | stop, stop | 0.78, 0.58 |
| muse-glimmer-30b | 0, 0 | length, length | 1.00, 1.00 |

A 734-character prompt had shown 8–9 reasoning tokens for the 120b; the real
window shows 33–43. Four times more, in the direction of the regime we actually
run. Every tolerance below is set from the window measurement.

**The stride objection does not survive its own evidence.** ADR-0005's strongest
argument was that reasoning makes the block advance by an amount we did not
choose. At 3–4% of the block that effect is real but small — and Stage 1 failed
E7 with block fill decaying from 0.995 to 0.653 **with no reasoning at all**. The
generators that stop early distort the stride an order of magnitude more than the
generator that thinks. Excluding a model that fills every block because it spends
4% of it thinking, while retaining one that delivers 65% of the block for reasons
we cannot control, is not a defensible ordering.

**muse-glimmer-30b was excluded on an over-generalisation.** Three of four cells
died on five consecutive empty completions at `W = 4096`, and `HANDOFF.md`
recorded that as a property of the window. Probed again at a genuine
4096-token window it returned two full 1024-token blocks. The empty completions
are intermittent, not a property of `W`, and four cells were not enough to tell
the difference. This is the sixth regime- or sample-transfer error in this
project and the third that originated in my own notes.

## Decision

1. **`max_reasoning_tokens` may exceed zero when, and only when, the budget is
   bounded and measured in the regime it is applied to.** Set per model from the
   window measurement, at roughly 1.5× the observed maximum: 64 for
   gpt-oss-120b, 32 for gpt-oss-20b, 0 for gemma-4-31b and muse-glimmer-30b,
   which are measured at zero and accept the switch.

2. **The per-step guard is unchanged and remains the authority.** A step above
   tolerance still fails the trajectory. ADR-0005's rule that a configured
   switch is never treated as evidence stands: the guard runs regardless of
   `extra_body`, because a switch was once accepted while being ineffective and
   one model's behaviour varied between identical calls.

3. **The provenance gap is stated rather than closed.** `/completions` reports
   `reasoning_tokens` but does not return the trace text; `/chat/completions`
   does, via `reasoning_details`. We therefore know how many hidden tokens each
   step contained and not what they said. This is a real weakening of the
   logging rule and belongs in the paper's limitations, not in an appendix. It
   is accepted because the quantity is bounded at ~4% of the block and recorded
   per step, which is the difference between a known gap and an unknown one.

4. **Reasoning tokens are reported as an order parameter**, per model and per
   step, alongside block fill and stop rate — not as a nuisance to be minimised
   out of the record.

5. **muse-glimmer-30b is re-admitted**, with its empty-completion rate as a
   measured quantity rather than an assumption. The existing guard fails a
   trajectory after five consecutive empty completions, so the rate is
   observable either way.

6. **Stage 2 gains a model axis** on top of ADR-0008's continuation-mechanism
   axis: qwen3-8b (dense 8B, the Stage 1 baseline), gemma-4-31b (dense 30.7B),
   gpt-oss-20b and gpt-oss-120b (MoE, 3.6B and 5.1B active), muse-glimmer-30b
   (hybrid attention). This spans sparse against dense and a 15× parameter
   range, and it is what E2 needed and never got.

## Alternatives considered

- **Keep the zero tolerance and drop the gpt-oss family.** This was the position
  until the window measurement. It would exclude the only two generators that
  filled every block, on the grounds of a 4% effect, while keeping generators
  whose stride drifts by 35%. Rejected on its own evidence.

- **Use `/chat/completions` to obtain the trace.** It returns the reasoning text
  and would close the provenance gap. Rejected as the default because chat adds
  27–107 template tokens against 1–8 for raw completion, and because a chat
  turn is a different continuation mechanism — methodology §1.3 treats that as a
  separate experimental arm, not a transport detail. Worth doing as a contrast
  arm if the provenance gap turns out to matter.

- **Append the reasoning text to the window.** Faithful in principle, impossible
  in practice on `/completions`, which does not return it. Unchanged from
  ADR-0005.

- **Treat reasoning models as a separate protocol P1-R.** Attractive and still
  open. Rejected for Stage 2 because at 3–4% of the block the difference does not
  warrant splitting the ensemble, and splitting it would halve the power of the
  cross-model comparison that is the whole point. If a model is found whose
  reasoning is a large fraction of its output, this becomes the right answer.

## Consequences

- Stage 2 has five candidate generators where Stage 1 had one. E2 becomes
  answerable.
- Two arms now carry MoE non-determinism. Stage 0 measured 20% exact-match
  reproducibility for the only MoE audited, even pinned. Claims for those arms
  must be distributional, and `audit determinism` measures the rate per model
  before generation rather than after.
- The paper's method section must state: all generators instruction-tuned; two
  of five with a bounded, measured reasoning budget of under 4% of each block,
  whose content is not recoverable from the provider.
- `HANDOFF.md` for Stage 1 contains a wrong statement about glimmer and `W`. It
  is stage-1 history and stays as written; this ADR is the correction.

## Reversal cost

Low. The tolerances are per-model configuration recorded in every manifest, so a
run states exactly which budget produced it, and reverting to zero simply
excludes the two gpt-oss arms without touching anything else.
