# ADR-0014: Stage 4 is a reduced temperature × W grid on qwen3-8b

Status: accepted
Date: 2026-09-03
Stage: S4
Amends: [ADR-0010](ADR-0010-stage2-findings-replan-s3.md),
[ADR-0013](ADR-0013-project-ceiling-200.md)

## Context

The master-plan sketch for Stage 4 was a 7 × 4 temperature × window
sweep on 2–3 models, budget ≤ $120, with `α`, macrostate count, dwell
time and entropy rate as order parameters. Three things make that
sketch the wrong next experiment:

1. **H1 is unsupported** on the Stage 2/3 instruct sample
   (`validated_macrostates = 0`). `n_macro` is not an order parameter.
2. **T = 1.0 is not a diffusion regime** on the 1B base model at
   `W = 256` (token lock) and is still an 8/8 textual fixed point on
   instruct qwen at `W = 4096` (S2.2). H5 cannot be taken from Stage 3.
3. **Cost.** Input tokens scale as `T · W / S`. `W ∈ {16k, 32k}` on
   several models exceeds the OpenRouter monthly key remainder (~$47)
   and is larger than a first look at H5 needs. The $200 project
   ceiling (ADR-0013) is not a generate-yes for the $120 sketch.

The only process we can already measure at 12 turnovers in both
spaces is `or-qwen3-8b` under P1 `raw_completion`. S2.2 already paid
for that process at `W = 4096`, T ∈ {0.3, 1.0}.

## Decision

1. **One generator:** `or-qwen3-8b` (OpenRouter, Alibaba, pinned,
   `reasoning_effort: none`). No gemma, glimmer, gpt-oss, coder, or
   local base in this opening.
2. **Windows:** `W ∈ {4096, 8192}` only. 16k / 32k and Glimmer's 2048
   local-attention axis stay in the backlog.
3. **Temperatures:** `{0.3, 0.7, 1.0, 1.5}`. Not seven points; not
   T = 0.0 (near-greedy lock is already attested).
4. **Reuse, do not regenerate** the eight S2.2 raw cells
   (`s2-mechanism-20260901T071519Z-dfbb173a`) at `W = 4096`,
   T ∈ {0.3, 1.0}. New generation is two configs:
   `stage4_w4096_new_temps.yaml` (T ∈ {0.7, 1.5}) and
   `stage4_w8192.yaml` (all four temperatures).
5. **Order parameters** are looping / degeneracy rate, stop rate, block
   fill, and MSD `α` **on non-degenerate trajectories**. A cell with
   fewer than two clean trajectories reports `α` as undefined. `n_macro`
   is not computed as an S4 headline.
6. **12 turnovers**, `B = S = 1024`, `chunk_size = 1024`, both
   embedding spaces, seeds `physics` / `surreal`, two stochastic
   replicates — matched to S2, not to S3.0's `W = 256`.
7. **No generate until the human approves the estimate.**

## Alternatives considered

- **Run the written 7 × 4 × 3-model sketch.** Rejected: order
  parameters and budget are both wrong after Stage 3.
- **Regenerate the S2.2 W=4096 T=0.3/1.0 cells for a single run_id.**
  Rejected: they exist, they are COMPLETED, and regenerating them
  spends money to re-measure a known lock.
- **Add a second model (gemma-4-31b or glimmer).** Rejected for this
  opening: gemma dies into silence; glimmer barely completed in S2.
  A second family is a later pass if this grid shows T moves `α` on
  qwen at all.
- **Start at W=8192 only.** Rejected: without the matched W=4096 new
  temperatures the W-effect cannot be separated from a T-effect.

## Consequences

- `docs/research-plan.md` Stage 4 entry is rewritten to this matrix.
- Stage budget declared in the PLAN (stop-and-ask), not $120.
  CLI estimate at fill=1 is $2.47; S2.2 fill 0.65 is $3.33.
- Parked arms are listed in `docs/backlog.md`.
- Claims remain instruct-under-P1, `or-qwen3-8b` only, two windows.

## Reversal cost

Low. Widening T, W, or the model list is a new ADR plus a new
config. Nothing in this opening is invalidated by adding arms later.
