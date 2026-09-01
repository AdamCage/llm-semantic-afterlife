# ADR-0008: Stage 2 measures the register confound and convergence time, not semantic half-life

Status: accepted
Date: 2026-09-01
Stage: S1 → S2

## Context

Stage 2 was specified as: *seed-identity probes as a function of generated
tokens ⇒ semantic half-life `T½` and its ratio to `W`*, with exit criteria
requiring `T½` with a CI **on ≥ 3 models**, the `T½` vs `W` relation on ≥ 2
windows, and `α` distinguishable from 1.0.

Stage 1 makes all three unreachable as written.

**There are not three models.** muse-glimmer-30b cannot free-run at `W = 4096`:
three of four probe cells died on five consecutive empty completions, the model
returning a bare stop token. llama-3.1-8b and mistral-nemo-12b were disqualified
on output quality (10.6× and 6.5× natural repetition) and then lost every probe
cell to HTTP 429 on their pinned endpoints. Across 396 OpenRouter and 468
RouterAI models there is no base model and no fourth viable free-running
generator. Stage 1's E2 could not be assessed at all.

**There is no half-life to measure.** `T½` presupposes decay. The observed
`D_between − D_within` gap falls for roughly ten turnovers and then holds flat to
32 — last-eight-band slope +0.00026 per turnover, against a gap of 0.147. This
was pre-registered as P2 and predicted to narrow monotonically; it does not. The
mechanism is deflationary rather than exciting: 94% of trajectories reach a
textual fixed point, and a process that has stopped moving neither forgets nor
remembers. Fitting an exponential to a plateau would produce a number with no
referent.

**A confound sits upstream of everything.** Every generator answers raw text in a
reviewer register — the first step of a physics-seeded trajectory began "Your
passage is a deep and insightful discussion of lattice field theory", from a seed
ending mid-sentence on "and", drawn from a bank whose fourth design constraint
explicitly excludes text inviting meta-commentary. Iterated self-review has a
natural fixed point, and two trajectories from unrelated seeds converged to the
same register of mystical mutual appreciation. Whether Stage 1 measured a
property of autoregressive generation under a sliding window, or a property of
instruction tuning under a re-prompt protocol, is not decidable from its data.

ADR-0006 recorded the absence of base models as a compromise. Stage 1 upgrades it
to a possible obstruction to the original question.

## Decision

**Stage 2 becomes "Does the phenomenon survive removal of the register?" rather
than "How fast does semantic memory decay?"**

1. **S2.1 — continuation mechanism.** Re-measure `assistant_prefill` at
   `W = 4096`, against `raw_completion` on matched cells. The mechanism exists in
   the harness and Stage 0 found it working on qwen3-8b, but only on a 28-token
   prompt; that measurement must not be assumed to transfer, which is the error
   this project has now made five times. Primary readout: does the reviewer
   register disappear, and does the fixed-point rate change.

2. **S2.2 — base-model existence check.** A small base model (1–3B) run locally
   at reduced `W`, as the escalation path ADR-0006 already recorded in the
   backlog. Not a full arm — CPU-only makes that infeasible — but an existence
   check on whether the convergence is instruction-tuning-specific. If a base
   model does not converge where an instruct model does, that is the paper's
   central control.

3. **S2.3 — convergence time replaces half-life.** The measurable quantity is not
   `T½` but the turnover at which a trajectory reaches its fixed point, and the
   plateau level of the gap. Both are estimable from Stage 1's data and both have
   referents. Reported per temperature, with the rate — not the incidence — since
   Stage 1 showed which cells degenerate is not reproducible.

4. **Exit criteria are rewritten** to require: the fixed-point rate under both
   continuation mechanisms with a CI; a base-model comparison at matched `W` and
   turnover count, or an explicit statement that it could not be obtained; and
   convergence time with a CI on the one viable hosted generator.

5. **The ≥ 3 models requirement is dropped and replaced by ≥ 2 continuation
   mechanisms on one generator, plus the base-model check.** Generator diversity
   is not available from hosted inference; mechanism diversity is, and it
   addresses the confound that actually threatens the result.

## Alternatives considered

- **Proceed with the half-life measurement as planned.** Rejected: it would fit a
  decay constant to a plateau produced by trajectories that stopped generating,
  and report it as semantic memory. This is the failure mode the project has
  already committed once, when an MSD exponent from a looping trajectory was read
  as confinement.

- **Rent GPUs and run a base model as a full arm.** The scientifically cleanest
  option and the most expensive. Deferred rather than rejected: S2.2's existence
  check is designed to establish whether it is worth the money, and a positive
  result there is the argument for spending it.

- **Declare the register a finding and build the paper on it.** Defensible, and
  partially what will happen regardless — the convergence result stands on its
  own. But publishing it *without* the base-model control would leave the central
  ambiguity unresolved for a reviewer to find, and the control is cheap enough
  that not attempting it is indefensible.

- **Widen the generator pool by relaxing the degeneracy bar.** Rejected: llama
  and mistral produce text at 6.5–10.6× natural repetition. Including them would
  add models whose output is already degenerate before the experiment starts, and
  the resulting "model diversity" would be decorative.

## Consequences

- Stage 2's budget shifts from generation-heavy (the `W` sweep) to
  comparison-heavy. The `W` sweep moves to Stage 3 or later, conditional on the
  register question resolving favourably.
- Stage 1's central result must be stated throughout as *attractor selection is
  seed-dependent*, not as *semantic memory persists*. The stronger phrasing is
  only available if S2.2 shows a base model behaving differently.
- `docs/research-plan.md` §S2 and its Russian mirror are amended in the same
  commit.
- If S2.1 and S2.2 both show the convergence persisting without the register, the
  result strengthens considerably and the original half-life programme may
  return — but on a process that actually moves.

## Reversal cost

Low. Nothing collected is invalidated; Stage 1's data stays the reference for the
`raw_completion` arm and becomes the control that S2.1 is compared against.
