# S1.1 — the core arm, and how its diagnostics decay with trajectory age

**Run:** `s1-pilot-core-20260830T134147Z-f1cce9ec`
**Matrix:** 48 trajectories, `W = 4096`, `T = 131072` (32 turnovers), qwen3-8b on
`alibaba`, 8 semantic seeds × 2 temperatures (0.3, 1.0) × 3 stochastic seeds.
**Result:** 47 trajectories reached `T`; 1 failed. 8,257 steps, **$6.32**.
**Status on disk:** `FAILED` — see the history below; the data is complete and
its integrity block verifies over all 147 files.

## How this run came to exist

It was launched as the planned core arm, and reported here as having been killed
at 441 steps after the first four trajectories were found to have converged to
textual fixed points. That report was wrong in two ways.

The kill targeted the wrong process. It severed the parent shell and its stdout;
the generation process was a child and survived. The run continued for a further
sixteen hours and completed the whole matrix, then crashed on its final console
write against the dead pipe — the `OSError: [Errno 22] Invalid argument` recorded
in the manifest notes. That is why `STATUS` reads `FAILED` while every output file
is present and hashes correctly.

The cost was also under-reported by roughly thirty-fold, because
`cumulative_cost_usd` in the step events accumulates **per trajectory**, not per
run; its maximum was read as the run total. The ledger was correct throughout.
This run cost $6.32 against a $7.00 per-run ceiling and a $9.00 arm budget.

The run was marked superseded on those false premises. That marker has been
removed: this is the stage's core dataset, not a discarded probe.

## The finding: every protocol diagnostic decays with trajectory age

Measured over the run in quarters:

| segment | block fill | stop rate | round-trip failures |
| --- | --- | --- | --- |
| first 441 steps | **0.995** | 4.5% | 0 |
| first 25% | 0.881 | 35.1% | 3 |
| 25–50% | 0.765 | 44.1% | 3 |
| 50–75% | 0.693 | 64.7% | 9 |
| last 25% | **0.653** | **74.0%** | 8 |
| whole run | 0.748 | 54.5% | 23 |

Nothing here is stationary. The generator fills less of each block, tries to stop
more often, and round-trips less reliably, monotonically, as its own output
accumulates in the window.

**The stop rate is the headline.** By the final quarter the model attempts to
terminate on three steps out of four, and the process only continues because the
protocol overrides it. Under P1 the "free-running" trajectory is, late in its
life, almost entirely forced. This is the declared forcing of methodology §1.4
becoming the dominant term rather than a caveat, and it must be stated wherever a
long-run claim is made from this data.

## E7 fails, and the amendment that said otherwise was made on 5% of the run

E7 required block fill not to collapse at `W = 4096`, against a probe value of
0.942. It was amended mid-run from two-sided to one-sided on the observation that
fill was 0.995 — better than the probe, so the two-sided form would have recorded
a failure for a favourable result.

That observation came from the first 441 steps, which is 5% of the run. Over the
full trajectory fill is **0.748**, and **0.653** in the final quarter: not merely
outside the ±0.05 band but far below the probe value in the direction the
criterion exists to catch.

**Verdict: E7 fails.** The stride is not constant, `S ≠ B`, and any cost forecast
built on fill = 0.942 underestimates input tokens by about a quarter.

The amendment itself is the more useful lesson. It transferred a number across
*time within a run* rather than across window size, which is the same error this
project had already made four times across other regimes, and it was committed
with an argument about why it was safe. A measurement taken in the first 5% of a
process whose defining feature is that it evolves is not a measurement of that
process.

## Thirteen trajectories carry a round-trip caveat

23 of 8,257 steps (0.28%) failed the tokenizer round-trip, spread over 13 of the
48 trajectories, and concentrated late:

| trajectory | failed steps |
| --- | --- |
| `T0p3__love__s2` | 4 |
| `T1__biology__s2` | 4 |
| `T0p3__programming__s3` | 2 |
| `T1__love__s2`, `T1__love__s3`, `T1__noise__s2` | 2 each |
| seven further trajectories | 1 each |

A round-trip failure means the window boundary was not where the manifest says,
so `W` is not exactly 4096 for those steps. The rate is low and the affected
trajectories are identified rather than dropped, but any per-trajectory claim
must carry the flag.

## What the arm is good for

Despite all of the above it is the only balanced dataset the stage has: 24
trajectories at each temperature, 6 per semantic seed, 3 stochastic replicates
per cell, all at 32 turnovers. The probes that preceded it had two replicates and
returned a separation interval containing zero — underpowered by construction.

The trajectories converge, which the probes established at 12 turnovers and this
arm extends to 32. That convergence is the measurement, not a defect in it. What
this arm can support is a properly powered contrast of `D_between` against
`D_within` at the planned operating point, with the confounds — reviewer
register, rising stop rate, non-constant stride — named alongside it.

**Reasoning tokens: 0. Served provider: Alibaba on 8,257 of 8,257 steps.** Those
two guards held for the whole run.
