# ADR-0016: Stage 5 opens as lock occupancy on seed_bank_v1

Status: accepted
Date: 2026-09-05
Stage: S5
Amends: [ADR-0015](ADR-0015-s5-operating-point-after-s4.md)

## Context

Stage 4 (APPROVED, merged `--no-ff` as `5c07751`) measured the
`or-qwen3-8b` P1 lock: T≤1.0 is 4/4 degenerate at both
`W ∈ {4096, 8192}`; T=1.5 is the only clean-`α` and is subdiffusive;
H5 is absent because there is no low-T clean-`α`. ADR-0015 forbids
opening S5 at T=1.0 as a semantic basin and requires the PLAN to pick
object (a) lock occupancy vs seed or (b) the T=1.5 residual.

The master-plan S5 sketch still said "200+ seeds per model" and
"basins of attraction." `configs/seeds/seed_bank_v1.yaml` has **14**
seeds (10 domains + 2 twin pairs), designed for this stage and marked
"extended, never edited in place." Inventing 186 new continuation
seeds mid-opening would be a new bank, not an occupancy measurement.

## Decision

1. **Object (a).** S5 measures lock occupancy versus seed, not the
   T=1.5 residual. The residual stays in the backlog.
2. **Operating point.** `W = 4096`, T=0.3, 12 turnovers, `or-qwen3-8b`
   under P1 `raw_completion`, Alibaba pin, `reasoning_effort: none`.
   T=0.3 is the lock with high fill that transferred across W (S4 Q4
   T=0.3 Δ=0.077). T=1.0 is a lock with a different stop mechanism
   (Q4 stop 0.954 at 4096 vs 0.450 at 8192) and is not this opening.
3. **Seed bank v1, not 200 invented seeds.** Occupancy uses the ten
   domain seeds. Sensitivity uses the two existing twin pairs
   (waterloo, reactor). A 200-seed bank is a later ADR.
4. **Reuse** the four S2.2 raw cells
   `or-qwen3-8b__W4096__T0p3__{physics,surreal}__s{1,2}` from
   `s2-mechanism-20260901T071519Z-dfbb173a`. Do not regenerate them.
5. **`n_macro` stays off the headline.** Degenerate trajectories are
   the *sample*, not rows to drop: this stage measures the lock.
6. **No second generator.** Same reason as ADR-0014 / ADR-0015.
7. **No generate until the human approves the estimate.**

## Alternatives considered

- **Object (b), T=1.5 residual.** Rejected for this opening: looping
  CI at `W=8192` is [0, 1], n_clean=2, text still the assistant
  register, and it is a different question.
- **T=1.0 occupancy.** Rejected: characterised as a lock, but fill
  collapse and stop-forced continuation make it a different
  mechanism (S4 REVIEW). Calling it the semantic operating point is
  what ADR-0015 forbids.
- **Write 200 new seeds now.** Rejected: that is a seed-bank stage.
  Occupancy on the designed 10+4 is the measurement we can take.
- **W=8192.** Rejected: S4 found no lock-rate lever; input scales as
  `T·W/S`.

## Consequences

- `docs/research-plan.md` S5 entry is rewritten to this matrix.
- Stage budget is the YAML refuse ($8), not the $120 sketch.
- CLI generate estimate at fill=1 is **$1.06** for 24 new
  trajectories. Fill 0.90 (S4 T=0.3 Q4) is ~$1.17.
- Parked: T=1.5 residual, T=1.0 occupancy, seed_bank_v2 (200),
  W=8192 occupancy, second generator.

## Reversal cost

Low. Object (b) or a larger bank is a new ADR plus a new config.
Nothing in this opening is invalidated by adding arms later.
