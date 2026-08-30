# ADR-0004: `W = 8k` as the primary pilot window, driven by the input-token cost law

Status: accepted
Date: 2026-08-30
Stage: S0

## Context

Project scoping proposed `W = 32k`, `T = 1M` as the main experimental standard —
32 turnovers and 1024 chunk observations per trajectory. That is the right target
for headline results. It is not the right place to start, because of the cost
structure of protocol P1 (ADR-0001).

Under re-prompting, the entire window is re-sent every `S` tokens:

```
input_tokens ≈ T · W / S            output_tokens ≈ T
```

Worked numbers at `S = B = 1024`:

| `W` | `T` | turnovers `T/W` | input tokens | input amplification |
| --- | --- | --- | --- | --- |
| 8k | 256k | 32 | 2.05M | 8× |
| 8k | 512k | 64 | 4.10M | 8× |
| 32k | 512k | 16 | 16.4M | 32× |
| 32k | 1M | 32 | 33.6M | 32× |

Turnover count — the scientifically meaningful measure of how long we watched the
system — depends on `T/W`, while cost depends on `T·W/S`. **Halving `W` and `T`
together preserves turnovers at a quarter of the cost.** A small window is
therefore an experimental advantage here, not a compromise.

Approved pilot budget is $50.

## Decision

- **Primary pilot window: `W = 8192`**, `B = S = 1024`, `T = 256k`
  (32 turnovers, 250 chunk observations per trajectory).
- A **`W = 32768` arm on one or two models** at reduced trajectory count, purely
  to check that conclusions are not specific to the small window.
- `W = 32k, T = 1M` is retained as the *headline* configuration for later
  stages, funded only after the pilot demonstrates the effect exists.
- `afterlife estimate` implements the cost law explicitly and refuses to launch
  a matrix whose forecast exceeds the stage budget.
- The `W`-sweep for scaling questions runs at fixed turnover count, not fixed
  `T`, so that comparisons across `W` are comparisons at equal observation
  length.

## Alternatives considered

- **`W = 32k` from the start.** Four times the cost for half the turnovers.
  Rejected: it buys realism we do not need before knowing whether the effect
  exists.
- **Larger `B` to reduce amplification.** `B = 4096` cuts input cost fourfold,
  but coarsens the window advance and reduces the number of observations per
  token. Retained as a Stage 6 stride ablation rather than a default, since
  changing it silently would confound the protocol.
- **Prefix-cache-friendly sawtooth window** (grow to `W`, truncate, repeat).
  Potentially much cheaper, but the effective window oscillates instead of
  sliding, which changes the object of study. Parked in `backlog.md` pending a
  formal equivalence argument.
- **Fewer trajectories at large `W`.** Rejected as the primary strategy: with a
  stochastic generator, 20 short trajectories are worth far more than one long
  one, because basin occupancy and variance need replicates.

## Consequences

- Pilot cost lands in the low tens of dollars rather than the low hundreds.
- Every reported result carries its turnover count `T/W`, and asymptotic
  language is bounded by it.
- `W` appears on both sides of the cost law, so any future request to increase
  `W` must be accompanied by a decision about `S`.
- Absolute-token comparisons across `W` are meaningless in this project;
  turnover-normalised comparisons are the default in figures.

## Reversal cost

Low. `W` and `T` are config values; the constraint is budget, not code.
Increasing `W` later requires new generation but invalidates nothing already
collected.
