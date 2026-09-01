# ADR-0010: Stage 2 findings — do not default to prefill; do not MSM a mixed process

Status: accepted
Date: 2026-09-01
Stage: S2
Amends: [ADR-0008](ADR-0008-stage2-replan-after-convergence.md)

## Context

Stage 2 asked whether Stage 1's convergence was a property of the model or of
the protocol / reviewer register. The measurements, from
`s2-model-axis-20260901T015457Z-ab59afc8` and
`s2-mechanism-20260901T071519Z-dfbb173a`:

- Long-trajectory fixed-point rate is 0/8 on gemma-4-31b (CI 0–0) and 8/8 on
  gpt-oss-120b almost-`T` (CI 1–1). Qwen3-8b is 8/8 under both mechanisms.
  gpt-oss-20b produced no long trajectory. Glimmer produced two, both fixed
  points, both `T = 0.3` physics.
- Matched qwen `assistant_prefill` vs `raw_completion`: register at step 1 is
  4/8 vs 6/8; fixed-point rate is 7/8 vs 8/8 (difference CI [−0.375, 0.0]).
  Prefill surreal cells that *open* as continuation fall into the reviewer
  register by mid-run.
- Gemma's long trajectories do not reprint a reviewer page. They continue the
  seed and then write silence / recursion marks.
- Exact-match determinism is 20% on gemma, not the >90% Q6 predicted.

ADR-0008 had parked a local base-model check as S2.2 and treated prefill as
the cheap lever on the register. Prefill was measured; the lever did not
move. The base-model check was not implemented.

## Decision

1. **Do not make `assistant_prefill` the default protocol.** It is a
   different wrapper with better block fill on qwen, not a different
   attractor. P1 `raw_completion` remains the headline protocol. Prefill
   stays a contrast arm.
2. **The base-model existence check of ADR-0008 §S2.2 is the highest-priority
   unexecuted pass.** It was not dropped; it was not done. Stage 3 must
   either run it first (local 1–3B, reduced `W`, matched turnover count) or
   state that the instruction-tuning confound remains open and that every
   MSM / half-life / basin claim is still a claim about instruct models
   under P1.
3. **Stage 3 MSM / Leiden is restricted to arms that reached ~12 turnovers
   and is reported per process, not pooled.** Qwen (both mechanisms),
   glimmer `T = 0.3` physics, and gpt-oss-120b almost-complete may enter.
   Gemma silence, 20b empty-EOS fragments, and glimmer empty-EOS deaths do
   not enter the same state model. Fixed-point, looping, and silence stay
   three labels.
4. **Do not change `W`, `T`, or sampling to convert 120b almost-complete
   into `COMPLETED`.** The last-short-block empty-text interaction is
   harness work for `main`. The 47-chunk sample is usable for rates with
   that limitation stated.
5. **No arm except glimmer may claim seeded determinism.** Gemma is 20%.

## Alternatives considered

- **Adopt prefill as default because fill is healthier.** Rejected: Q3
  failed, Q4 held, and prefill surreal falls into the register later. A
  cleaner request is not a different dynamical system.
- **Drop MSM and spend Stage 3 entirely on a base model.** Tempting, and
  the confound is real. Rejected as a *replacement*: the dynamics branch
  is still the paper's method, but only on processes that exist. The base
  model is a gate on interpretation, not a substitute for the measurement.
- **Treat 120b as failed like 20b.** Rejected: they are different
  outcomes. 20b never entered the 12-turnover regime. 120b almost did.

## Consequences

- `docs/research-plan.md` Stage 3 opens with a base-model check or an
  explicit open confound, and names the restricted MSM sample.
- A follow-up harness ADR may change last-step `max_tokens` or the
  empty-text definition; it does not rewrite Stage 2's `T`.
- The manuscript's E2 sentence is: convergence is not universal; it is
  attested on qwen3-8b and gpt-oss-120b and absent on gemma-4-31b under
  this protocol.

## Reversal cost

Low for (1) and (5): they are refusals. (3) is a sample restriction; lifting
it would require a new measurement showing the mixed ensemble is one
process. (2) is costly to skip: every later stage inherits an unnamed
confound.
