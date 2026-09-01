# Stage 2 — Is the convergence a property of the model, or of the protocol?

**Status.** Opened 2026-09-01 on branch `stage-2`, after Stage 1 closed with a
PARTIAL verdict.

## 1. Question

Stage 1 established that seed identity is measurably present past the context
horizon out to 32 turnovers, in both representation spaces, with every band's
bootstrap interval excluding zero — and that 94% of trajectories reached a
textual fixed point, so a process that stopped moving cannot forget. What it
could not establish is whether any of that is a fact about language models.

Two reasons. **E2 was never assessed**: every number came from qwen3-8b, because
the replication arm could not be run. And an untested confound sits upstream of
everything: under protocol P1 an instruction-tuned model turns continuation into
self-review, and self-review has a natural fixed point.

Stage 2 attacks both. Not "how fast does semantic memory decay" — Stage 1 showed
there is no decay to fit, the gap plateaus — but "does the phenomenon survive
changing the model, and changing the mechanism".

## 2. Entry state

From [Stage 1](../stage-1/REPORT.md), [ADR-0008](../../decisions/ADR-0008-stage2-replan-after-convergence.md)
and [ADR-0009](../../decisions/ADR-0009-bounded-reasoning-and-the-stage2-model-axis.md):

- **Five generators, measured at a real 4096-token window** (S2.0), where Stage 1
  had one:

  | generator | architecture | reasoning /1024 | block fill observed |
  | --- | --- | --- | --- |
  | `or-qwen3-8b` | dense 8B | 0 | 0.75 → 0.65 over a run |
  | `or-gemma-4-31b` | dense 30.7B | 0 | 0.78, 0.58 |
  | `or-gpt-oss-20b` | MoE 21B/3.6B active | 0 | 1.00, 0.44 |
  | `or-gpt-oss-120b` | MoE 117B/5.1B active | 33–43 | 1.00, 1.00 |
  | `or-muse-glimmer-30b` | hybrid attention 30B | 0 | 1.00, 1.00 |

- **Bounded reasoning is admissible** (ADR-0009): the gpt-oss endpoints refuse to
  disable reasoning, spend 3–4% of the block on it, and fill every block. The
  per-step guard is unchanged and fails a step above tolerance.
- **The trace text is not returned on `/completions`**, only its token count. A
  stated provenance gap, not a closed one.
- **Two arms carry MoE non-determinism.** Stage 0 measured 20% exact-match
  reproducibility for the only MoE audited, even pinned. Claims for those arms
  are distributional.
- **`assistant_prefill` works on qwen3-8b** — measured in Stage 0 on a 28-token
  prompt, which is exactly the kind of number this project has trusted across
  regimes five times and been wrong about. It is re-measured here before use.
- **Degeneracy incidence is not reproducible** (S1.2): the same cell is clean
  under one seed derivation and degenerate under another. Only rates are
  estimable; naming which cells degenerated is reporting noise.

## 3. Experiment matrix

| # | Pass | What it decides | Trajectories | Forecast |
| --- | --- | --- | --- | --- |
| S2.0 | Capability probe | which generators can run this protocol | 0 | done, $0.02 |
| S2.1 | Model axis at `W = 4096`, 12 turnovers | is convergence model-specific (**E2**) | 40 | **$1.9** |
| S2.2 | Mechanism axis: `assistant_prefill` vs `raw_completion` | is the reviewer register removable | 16 | **$0.8** |
| S2.3 | Determinism audit, all five | the reproducibility rate each arm may claim | 0 | $0.05 |

**S2.1** — 5 generators × 2 semantic seeds (`physics`, `surreal`) × 2 temperatures
(0.3, 1.0) × 2 stochastic replicates = 40 trajectories at 12 turnovers. Twelve
because convergence in Stage 1 established itself by turnover 10, and matching
that length makes the arm directly comparable to the convergence probe and to the
core arm's first twelve bands.

**S2.2** — qwen3-8b only, both mechanisms, 2 seeds × 2 temperatures × 2
replicates = 16 trajectories. qwen because it is the only generator with a
32-turnover baseline to compare against, and because Stage 0 found prefill works
on it and errors or returns empty on the others.

Both embedding spaces on every chunk, as in Stage 1.

## 4. Exit criteria

Falsifiable, quantitative, fixed before any data exists.

| # | Criterion | Threshold |
| --- | --- | --- |
| F1 | **E2 answered** | fixed-point rate reported per generator with a bootstrap CI, on ≥ 4 of the 5 generators; the fifth declared as missing data with cause |
| F2 | Convergence is or is not universal | either ≥ 4 generators show a fixed-point rate whose CI excludes 0.5, in the same direction, or the disagreement is reported as the result |
| F3 | Mechanism effect measured | fixed-point rate under `assistant_prefill` vs `raw_completion` on qwen3-8b, with a CI on the difference |
| F4 | Register measured, not asserted | the fraction of step-1 completions opening in reviewer register, counted by hand over ≥ 20 trajectories per mechanism, reported per mechanism |
| F5 | Protocol integrity | reasoning tokens within the per-model tolerance on 100% of steps; served provider equals pinned provider on 100%; round-trip failures reported per generator |
| F6 | Determinism declared | exact-match reproducibility measured per generator before generation and stated in the report; no arm claims seeded determinism it has not measured |
| F7 | Block fill reported across the run | fill and stop rate per quarter per generator, never as a run-level mean |
| F8 | Completion rate | ≥ 80% of planned trajectories reach `T`; the rest reported as missing data with cause |

F1 is the stage. F2 and F3 decide what the paper can claim.

The completion bar is 80% rather than Stage 1's 90% deliberately: two arms are
new, one was re-admitted after failing, and a bar set where failure is likely
would only invite quiet exclusion of the arms that fail.

## 5. Pre-registered predictions

| # | Prediction | Confidence | Observed |
| --- | --- | --- | --- |
| Q1 | All five generators reach a fixed point in > 50% of trajectories at 12 turnovers | 0.6 | |
| Q2 | The two gpt-oss arms, which fill every block, converge *more* than the arms that stop early — the stop token is an escape from the attractor rather than a symptom of it | 0.35 | |
| Q3 | `assistant_prefill` reduces the reviewer-register rate by more than half | 0.5 | |
| Q4 | `assistant_prefill` does **not** significantly change the fixed-point rate — the register is a surface, and the attractor is not | 0.45 | |
| Q5 | The MoE arms show a *lower* fixed-point rate than the dense arms, because routing noise perturbs the trajectory out of shallow attractors | 0.5 | |
| Q6 | Exact-match determinism is below 50% for both gpt-oss arms and above 90% for gemma-4-31b | 0.7 | |
| Q7 | Block fill decays monotonically within a run for every generator, as it did for qwen3-8b | 0.65 | |
| Q8 | At least one generator fails to produce viable trajectories at all, as glimmer did in Stage 1 | 0.55 | |
| Q9 | Larger models converge no less than smaller ones — scale does not rescue the process | 0.6 | |

Q4 is the one that matters most and the one I am least sure of. If prefill
removes the register and the fixed-point rate is unchanged, the convergence is a
property of the sliding-window process rather than of the chat persona, and the
project's original question survives. If the rate moves with the register, Stage
1 measured a dialogue artifact and the paper is about instruction tuning.

**Note on Q3, recorded after the predictions were fixed and before S2.2 runs.**
Two direct calls with the window prefilled into the assistant turn at `W = 4096`
both returned full 1024-token blocks — and both in the reviewer register:

> Your passage is indeed a **comprehensive and well-structured exploration** of
> key concepts…

> You've provided an excellent and comprehensive overview of **lattice field
> theory**…

Two calls are not a rate, and Q3 stands as registered at 0.5 rather than being
revised to match an observation made after the fact. But the mechanism plainly
works at the target window — 1024-token blocks, 12 tokens of template overhead —
so S2.2 measures how much the register changes rather than whether prefill is
usable at all. If the register survives the mechanism, the remaining lever is the
base-model check of ADR-0008 §S2.2, and that becomes the stage's most important
unexecuted pass.

Q2 is deliberately contrarian. The intuitive reading is that a model which stops
early is failing; the alternative is that stopping is the only thing preventing
it from settling. Stage 1 cannot distinguish these.

## 6. Budget and wall clock

- **Cost:** $2.8 forecast, $6 declared. Project spend to date $9.03 of $50.
- **Wall clock:** ~19 s/step at concurrency 2 gives roughly 8 h for S2.1 and
  3 h for S2.2.
- **Stop and ask** if spend passes $6, if completion falls below 80%, or if any
  arm's reasoning-guard failure rate exceeds 5% of steps.

## 7. Stage-specific risks

| Risk | Mitigation |
| --- | --- |
| MoE non-determinism makes the arms incomparable | measured per generator before generation (S2.3); claims for those arms stated distributionally |
| The reasoning trace is unrecoverable on `/completions` | bounded at ~4% of the block and recorded per step; stated as a limitation, and `/chat/completions` is available as a contrast if it turns out to matter |
| glimmer's intermittent empty completions recur | the guard fails the trajectory after five consecutive, so the rate is observable; F8's 80% bar accommodates one arm failing |
| Prefill measured at 28 tokens does not transfer to 4096 | re-measured in S2.2 rather than assumed — this is the fifth instance of that error and the first where it was anticipated |
| Register counted subjectively | F4 requires a hand count over ≥ 20 trajectories per mechanism with the criterion stated, not an impression |
| 12 turnovers is shorter than Stage 1's 32 | accepted: convergence established itself by turnover 10, and the comparison is against Stage 1's first twelve bands rather than its full run |

## 8. Definition of done

- [ ] S2.1 and S2.2 generated, per-trajectory status recorded
- [ ] Both embedding spaces computed for every chunk
- [ ] Degeneracy, geometry and separation run for every arm, degeneracy first
- [ ] `artifacts/stage-2/` populated with figures, tidy data and captions
- [ ] `REPORT.md` with a verdict per exit criterion and the prediction table
      scored, quoting generated text from at least three points
- [ ] `afterlife review --stage s2` exits 0
- [ ] Master plan amended for Stage 3
- [ ] Spend reconciled
