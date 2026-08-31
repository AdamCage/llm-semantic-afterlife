# S1.2 — the sub-seed defect did not contaminate the stage's result

**Run:** `s1-seed-independence-20260831T153748Z-49010fa0` — 9/9 trajectories,
675 steps, **$0.51**. Zero cache hits, confirming the new derivation really was
exercised rather than replayed.

## What was tested

The core arm was generated with per-step seeds derived arithmetically:

```
stochastic_seed * 1_000_003 + step * 31 + attempt * 7_919 + 17
```

which put replicates exactly 1,000,003 apart at every step and consecutive steps
exactly 31 apart — three parallel arithmetic progressions rather than three
independent streams, and a violation of the project's own rule requiring
`SeedSequence.spawn`.

This mattered because `D_within` — same semantic seed, different stochastic seed
— is the control that makes `D_between` interpretable, and it carries half of the
stage's result. A control whose replicates might not be independent is not a
control.

Nine trajectories reproduce core-arm cells under `SeedSequence`-derived seeds:
same generator, window, temperature, and the same three stochastic seed *values*.
Only the derivation differs. Twelve turnovers, compared against the core arm
truncated to its first twelve bands, on the three semantic seeds whose `s2`
replicate had survived.

## Result: the contrast is unchanged

| | `D_within` | `D_between` | gap | 95% CI on the gap |
| --- | --- | --- | --- | --- |
| old (arithmetic) | 0.3525 | 0.4854 | **0.1329** | [0.040, 0.232] |
| new (`SeedSequence`) | 0.3320 | 0.4631 | **0.1312** | [0.016, 0.257] |

The gap differs by **0.0017**, about 1.3% of its value, against bootstrap
intervals roughly 0.2 wide. Both distances shifted down by almost exactly the
same amount (−0.021 and −0.022), so their difference is preserved — consistent
with a different random draw of trajectories rather than with a change in
structure.

Per-band `D_within` is consistently a little lower under the new derivation
(deltas −0.004 to −0.063, mean −0.019), with the largest difference in the final
band where the least data sits.

**The defect was harmless for the quantity the stage depends on.** That is now a
measurement rather than an assumption, which was the point.

Bounded honestly: nine trajectories give nine within-pairs and twenty-seven
between-pairs, so this excludes an effect of order 0.1 in the gap, not one of
order 0.01. What it establishes is that the defect did not change the conclusion,
not that it changed nothing.

## The `s2` pattern was chance, and it does not reproduce

The suspicion that prompted this probe was that all three non-degenerate
trajectories in the 48-cell core arm carried stochastic seed `s2`.

| derivation | non-degenerate trajectories |
| --- | --- |
| old, same three semantic seeds | `biology__s2`, `surreal__s2`, `war__s2` |
| new | `biology__s1`, `biology__s3`, `war__s1` |

No `s2` survives under the new derivation, and `biology__s2` — clean before —
now sits at a late-phase pairwise similarity of 0.8135. The pattern was an 8%
coincidence, as its own probability suggested.

## The incidental finding is the more useful one

Whether a trajectory reaches a fixed point is **not a property of its cell**. The
same `(semantic seed, stochastic seed)` combination is clean under one seed
derivation and firmly degenerate under another; `biology__s2` moved from
non-degenerate to a pairwise median of 0.81, while `biology__s1` and `biology__s3`
moved the other way.

Degeneracy is a stochastic outcome of the individual trajectory. Two consequences
follow directly:

- **No claim about degeneracy may rest on a single replicate.** Rates are
  estimable; incidence is not predictable.
- **Reporting which cells degenerated is reporting noise.** Only the rate, with
  its uncertainty, is a finding.

Rates here are not comparable to the core arm's without care: 3 of 9 clean at
twelve turnovers against 3 of 24 at thirty-two. Longer trajectories have more
opportunity to converge, and the difference is at least partly length rather than
derivation.

## Protocol diagnostics reproduce the core arm's decay

Block fill 0.651 and stop rate 74.4% over these twelve-turnover trajectories,
against 0.653 and 74.0% in the core arm's *final quarter*. Three round-trip
failures in 675 steps. Reasoning tokens zero.

That the twelve-turnover average matches the thirty-two-turnover tail is worth
noting rather than glossing: these runs reached the degraded regime faster, and
the reason is not established here.
