# ADR-0015: S5 does not treat T=1.0 as the semantic operating point

Status: accepted
Date: 2026-09-05
Stage: S4
Amends: [ADR-0014](ADR-0014-reduced-s4-temp-window.md)

## Context

Stage 4 measured looping rate and clean-`α` on `or-qwen3-8b` under P1
`raw_completion` at `W ∈ {4096, 8192}` and T ∈ {0.3, 0.7, 1.0, 1.5}.
Every T ≤ 1.0 cell is 4/4 degenerate at both windows. T=1.5 is the
only cell with a defined clean-`α`, and that exponent is subdiffusive
in both spaces. The seed-separation gap at the last band still
excludes 0, including at the lock.

The master-plan S5 sketch said "many seeds at the best-characterised
operating point." After Stage 2 that phrase quietly meant T=1.0 at
`W = 4096`. That point is now characterised: it is a textual fixed
point, not a semantic basin.

## Decision

1. **S5 does not open at T=1.0** on this process expecting semantic
   basins. A 200-seed occupancy map at T=1.0 would measure lock
   occupancy, and must say so.
2. **Two honest S5 objects**, pick one in the S5 PLAN before any
   generate: (a) the lock itself (surface-form attractor occupancy
   vs seed), or (b) the T=1.5 residual (the only band with
   `n_clean ≥ 2`). Mixing them is a new confound.
3. **`n_macro` stays off the headline.** Stage 4 did not revive it.
4. **No second generator in the S5 opening** unless the S5 PLAN
   names a question that one process cannot answer. ADR-0014's
   rejection of gemma-as-healthier still holds.

## Alternatives considered

- **Treat T=1.0 as "standard sampling" and map basins there.**
  Rejected: Stage 4's F5 is 4/4 degenerate at that point at both W.
- **Jump to T=1.5 and call it diffusion.** Rejected: clean-`α` is
  0.15 (bge-m3) / 0.25–0.28 (qwen3-embed-8b), CIs exclude 1, and
  the generated text is still the reviewer register.
- **Widen W or add a second model now.** Rejected for the same
  reason as ADR-0014: one process, one finding.

## Consequences

- `docs/research-plan.md` S5 entry names the two objects and
  forbids a silent T=1.0 "standard" opening.
- Stage 4 REPORT implications point here.
- A later S5 PLAN still needs its own estimate and generate-yes.

## Reversal cost

Low. Choosing object (a) or (b) is an S5 PLAN decision, not a
regeneration of Stage 4.
