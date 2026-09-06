# ADR-0019: TMLR-readiness correctness pass (not a new stage)

Status: accepted
Date: 2026-09-06
Amends: [ADR-0018](ADR-0018-s7-manuscript-from-closed-stages.md)

## Context

S7 closed APPROVED WITH CHANGES with a TMLR-shaped manuscript at
`paper/main.tex`. A post-close scientific audit found four publication
blockers that the mechanical gate never checks:

1. The occupancy manuscript reports `B = 512`; the executed YAML is
   `block_size: 1024` ([`configs/stages/stage5_lock_occupancy.yaml`](../../configs/stages/stage5_lock_occupancy.yaml)).
2. `SlidingWindow.horizon_tokens` was documented as “no seed token
   remains” but computed `W − L_0` (window fill / eviction *start*).
   Full eviction is at generated count `W`. `past_horizon` and F4
   bands (`turnover ≥ 1`) already used the correct boundary.
3. The F6 “trajectory bootstrap” dropped resample multiplicities
   (`set(chosen)`), so published twin CIs were not bootstrap intervals.
4. `rate_ci` used a percentile bootstrap of Bernoulli flags, yielding
   `[0, 0]` and `[1, 1]` at `0/n` and `n/n`. Stage 2 and Stage 4 tables
   published those intervals.

The headline F4 last-band domain gap is believed to survive: its
estimator already resamples trajectories with multiplicity. F6, Bernoulli
CIs, the protocol sentence, and horizon prose do not.

This is not Stage 8 and not new generate. Planned stages S0–S7 remain
the experimental record. Paper B (model × post-training × `W` × `B` ×
temperature × EOS) is parked in [`docs/backlog.md`](../backlog.md).

## Decision

1. **Object.** A correctness pass on the closed S0–S7 record: library
   fixes, `$0` re-assembly of dependent artifacts, an independent
   headline audit, literature verification, and a quieter TMLR
   manuscript. No new generate. No new embed unless a restored snapshot
   is missing a file the assemble scripts already named.
2. **Horizon.** Log `eviction_start_tokens = max(0, W − L_0)` and
   `full_eviction_tokens = W` (when `L_0 > 0`). `horizon_tokens` means
   full eviction. Historical generate JSONL that stored
   `horizon_tokens = W − L_0` are not rewritten; analysis does not read
   that field for F4.
3. **Twin CI.** Weight pair distances by `counts[left] * counts[right]`,
   matching `compute_separation`. Last-band `CI ∋ 0` is labelled
   `no_detected_divergence`, not `collapsed`. F6 is not a headline.
   No equivalence TOST at `n = 2`.
4. **Bernoulli CI.** Clopper–Pearson exact intervals for rates.
   Two-sample contrasts report a Newcombe difference CI and Fisher
   exact `p`. `bootstrap_mean_ci` for continuous means is unchanged.
5. **Closed reports.** Dated Errata files on S2/S4/S5/S6/S7. Do not
   silently rewrite closed `REPORT.md` as if the old numbers never
   existed. The `run_id`s remain the data source.
6. **Paper.** Rewrite `paper/main.tex` as a TMLR existence case of
   *blockwise* self-conditioned generation after prompt eviction. Human
   yes is the audit that requested this pass.

## Alternatives considered

- **Open S8 as an experimental stage.** Rejected: no new scientific
  question, no generate matrix, and the research plan has no S8.
- **Regenerate occupancy with `B = 512` to match the manuscript.**
  Rejected: the YAML is the experiment; the sentence is wrong.
- **Leave F6 CIs and call them “approximate.”** Rejected: they are not
  a bootstrap distribution.
- **Equivalence test for semantic collapse.** Requires a pre-registered
  margin and larger `n`. Parked with Paper B.

## Consequences

- Occupancy remains an existence result on `or-qwen3-8b`, P1
  `raw_completion`, `W = 4096`, `B = 1024`, `T = 0.3`.
- Historical `horizon_tokens` in generate manifests is eviction start.
  New runs log both fields.
- Spend for this pass is `$0`.

## Reversal cost

Low for prose. Reverting the estimators would republish invalid CIs.
Regenerating trajectories is out of scope either way.
