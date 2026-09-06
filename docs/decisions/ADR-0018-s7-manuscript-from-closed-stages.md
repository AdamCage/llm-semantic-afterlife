# ADR-0018: Stage 7 manuscript reports S0–S6, not the original kitchen-sink outline

Status: accepted
Date: 2026-09-06
Stage: S7
Amends: [ADR-0017](ADR-0017-s6-third-space-occupancy-robustness.md)

## Context

Stage 6 closed APPROVED WITH CHANGES (`ad1f244`). Occupancy *signs*
hold in `gemini-embed-001` on the same 28 trajectories: F4 last-band
gap 0.150 [0.029, 0.266] (NHST whisker); F6 last-band Δ CIs include
0. Gemini is closed. Hosted S6 **$0**. Project ledger **$16.34 of
$200**.

`.cursor/rules/50-paper.mdc` still lists a target structure written
before the stages ran: semantic half-life vs `W`, validated MSM
macrostates, probability currents, cross-model basins, chunk-size
and Leiden robustness. Stages falsified or never reached several of
those headlines:

- S1: seed identity past the horizon is mostly freeze (94% fixed
  point).
- S2: convergence is not universal; the S1 reading is a claim about
  `or-qwen3-8b` under P1.
- S3: `validated_macrostates = 0`; H1 unsupported on this sample.
- S4: H5 absent; T≤1.0 is lock at both `W`.
- S5–S6: occupancy signs on one generator, three spaces; F4 is an
  ensemble gap, not recovered memory; F6 collapsed ≠ one lock.

Writing the 50-paper outline as if those sections were measured
would exceed the artifacts.

## Decision

1. **Object.** S7 is the manuscript *from closed-stage artifacts*.
   No generate. No embed. No new analysis pass that would mint a
   `run_id` unless a missing figure cannot be assembled from disk
   — and then stop and ask.
2. **Claim bound.** Every quantitative sentence points at an
   artifact path and a `run_id`. Claims the stages marked
   unsupported (H1 as established, H5 as present, architecture-
   independence from gemini, occupancy of one lock, a lock as a
   basin, `n_macro` as an order parameter) stay unsupported in the
   paper.
3. **Structure.** Use 50-paper.mdc as a *checklist of topics to
   confront*, not as a table of contents that must be filled. Cut
   or recast sections the stages did not measure. Limitations are
   mandatory and specific (P1 vs sliding; one generator; closed
   gemini; n=2; F4 whisker; physics s1 last-band NaN).
4. **`paper/main.tex`.** Notes under `paper/notes/` may accumulate
   on this branch. Prose in `paper/main.tex` waits for an explicit
   human yes after this PLAN is committed.
5. **Parked arms stay parked.** T=1.0 occupancy, T=1.5, 200 seeds,
   a second generator, MSM, provider replication, chunk ablation,
   P1 vs sliding — not S7.

## Alternatives considered

- **Write the original 50-paper outline and mark missing
  sections TBD.** Rejected: a TBD MSM section reads as a gap the
  authors meant to fill, not as a negative result already in
  hand.
- **New generate to complete H1/MSM before writing.** Rejected:
  S3–S6 already decided those arms wait on their own PLAN/ADR.
  S7 budget is $0 API.
- **Skip a PLAN and draft `main.tex` immediately.** Rejected:
  stage discipline requires predictions registered before the
  manuscript exists.

## Consequences

- `docs/stages/stage-7/PLAN.md` has no generate YAML.
- `afterlife estimate` is not part of this opening.
- Literature entries marked `LEAD` are not cited.

## Reversal cost

Low. Notes are not the manuscript. Switching the outline later
does not regenerate trajectories.
