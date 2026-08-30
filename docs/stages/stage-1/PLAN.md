# Stage 1 — Pilot: does the phenomenon exist?

**Status.** Opened 2026-08-30, after Stage 0 closed with all exit criteria met
and both prerequisites discharged.

## 1. Question

Over 32 window turnovers of free-running generation, is there *any* structure in
the semantic trajectory past the context horizon — seed-dependent separation,
recurring regions, non-trivial diffusion — or is the post-horizon regime
indistinguishable from an unstructured walk?

Stage 1 is not asked to characterise the dynamics. It is asked whether there is
anything to characterise. A clean negative closes the project cheaply, which is
the point of running it before Stages 2–5.

## 2. Entry state

From [Stage 0](../stage-0/REPORT.md) and
[ADR-0007](../../decisions/ADR-0007-openrouter-deepinfra-primary.md):

- **Protocol.** P1 re-prompt, `raw_completion`, `forcing = unforced`. No base
  models exist on any provider (ADR-0006), so every generator is instruction-
  tuned, driven through a completion interface, with reasoning suppressed and
  verified per step (ADR-0005).
- **Primary endpoint.** `deepinfra/fp8` llama-3.1-8b-instruct, measured at block
  fill **1.000** (min 1.000), stop rate **0.000**, prompt-token delta **0**,
  reasoning tokens **0**, zero retries under sustained load. For this arm the
  stride is genuinely constant, `S = B`.
- **Replication endpoint.** `alibaba` qwen3-8b, quantization unknown, reasons by
  default and requires `reasoning_effort: none`.
- **Reproducibility.** L3 verified by cache replay; L1 is per-model and measured.
- **Cost model** calibrated to −0.6% on input after the block-fill correction.

## 3. Experiment matrix

| Arm | Config | Generator | Endpoint | Matrix | Trajectories | Forecast |
| --- | --- | --- | --- | --- | --- | --- |
| core | `stage1_pilot_core.yaml` | llama-3.1-8b-instruct | `deepinfra/fp8` | 1 W × 2 temperatures × 8 semantic seeds × 3 stochastic | 48 | **$2.48** |
| replication | `stage1_pilot_replication.yaml` | qwen3-8b | `alibaba` | 1 W × 1 temperature × 8 semantic seeds × 2 stochastic | 16 | **$5.77** |

Both at `W = 8192`, `B = S = 1024`, `T = 262144` (32 turnovers, 256 chunk
observations per trajectory), `chunk_size = 1024`, non-overlapping.
Temperatures: core `{0.3, 1.0}`, replication `{1.0}`.
Semantic seeds: `physics, finance, biology, war, love, programming, surreal,
noise`. Both embedding spaces (`bge-m3`, `qwen3-embed-8b`) on every chunk.

Total **64 trajectories, ~16.8M output tokens, ~132M input tokens, $8.25**.

## 4. Computations

| # | Pass | Command | Artifacts |
| --- | --- | --- | --- |
| S1.0 | Single full-size trajectory, core config | `afterlife generate` on a one-cell config | block-fill and latency validation at `W = 8192` |
| S1.1 | Core generation | `afterlife generate --config configs/stages/stage1_pilot_core.yaml` | 48 trajectories |
| S1.2 | Replication generation | `afterlife generate --config configs/stages/stage1_pilot_replication.yaml` | 16 trajectories |
| S1.3 | Embedding, both spaces | `afterlife embed --run <id>` | `embeddings_*.parquet` |
| S1.4 | Geometry | `afterlife analyze geometry --run <id>` | velocity, drift, MSD, recurrence, RQA |
| S1.5 | Seed-separation test | new pass | `D_between` vs `D_within` with bootstrap CI |
| S1.6 | Degeneracy diagnostics | new pass | repetition loops, entropy, compression ratio |
| S1.7 | Protocol diagnostics | `scripts/summarise_run.py` | block fill, stop rate, retries, reasoning leaks |
| S1.8 | Stage report | `afterlife report --stage 1` | `artifacts/stage-1/INDEX.md` |

S1.5 is the pass that answers the stage's question, and it does not exist yet:
`D_within` (same semantic seed, different stochastic seed) is the control that
makes `D_between` interpretable. Without it, "trajectories from different seeds
are far apart" says nothing.

## 5. Exit criteria

Falsifiable, quantitative, fixed before any data exists.

| # | Criterion | Threshold |
| --- | --- | --- |
| E1 | Seed identity persists past the horizon | `D_between > D_within` past `t = W` on the core arm, bootstrap CI over trajectories excluding zero |
| E2 | The effect is not architecture-specific | same sign of the `D_between − D_within` gap on the replication arm |
| E3 | Diffusion exponent estimable | `α` with bootstrap CI width < 0.2 on the core arm, and its residual diagnostic showing an acceptable power-law fit |
| E4 | Degeneracy under control | < 20% of trajectories collapse into repetition loops; if more, the sampling configuration is revised before Stage 2 |
| E5 | Representation robustness | the sign of the E1 result agrees between `bge-m3` and `qwen3-embed-8b` |
| E6 | Protocol integrity | zero reasoning-guard failures; zero tokenizer round-trip failures; served provider equals pinned provider on 100% of steps |
| E7 | Stride constancy holds at scale | block fill remains 1.000 ± 0.01 for the core arm at `W = 8192`, or the variable-stride caveat is reinstated for it |
| E8 | Completion rate | ≥ 90% of planned trajectories reach `T`; the rest reported as missing data with cause |

E1 is the stage. E2 and E5 decide whether the result is worth Stages 2–5. E7 is
new: block fill 1.000 was measured at `W = 2048` and must not be assumed to carry
to `W = 8192`.

## 6. Pre-registered predictions

Written before execution, to be scored in the report.

| # | Prediction | Confidence | Observed |
| --- | --- | --- | --- |
| P1 | `D_between > D_within` past the horizon on the core arm | 0.65 | |
| P2 | The gap **narrows** monotonically with turnover count rather than staying flat | 0.6 | |
| P3 | Seed separation survives to 32 turnovers rather than vanishing by 10 | 0.45 | |
| P4 | MSD exponent `α < 1` (subdiffusive / confined) on the core arm | 0.6 | |
| P5 | `α` is **larger** at `T = 1.0` than at `T = 0.3` | 0.7 | |
| P6 | Repetition-loop rate is higher at `T = 0.3` than at `T = 1.0` | 0.8 | |
| P7 | The `noise` seed converges towards the other seeds faster than any content seed | 0.6 | |
| P8 | Block fill stays 1.000 at `W = 8192` for `deepinfra/fp8` | 0.7 | |
| P9 | The two embedding spaces agree on the sign of E1 but differ in effect size by > 25% | 0.55 | |
| P10 | At least one trajectory exhibits a visible metastable transition (a displacement spike separating two low-displacement regimes), as the offline fixture did | 0.5 | |

P3 is the one we are least sure of and the one that matters most: if seed
separation is gone by 10 turnovers, "semantic afterlife" is a short-lived
transient and Stage 2's half-life measurement becomes the whole paper rather than
one section of it.

P2 deserves a note. If the gap were *flat* rather than narrowing, that would
suggest genuinely persistent memory rather than slow decay — a stronger result
than we predict, and one we would need to scrutinise hard for leakage before
believing.

## 7. Budget and wall clock

- **Cost:** $8.25 forecast, $14 declared across the two arms. Project spend to
  date $0.024 of $50.
- **Wall clock:** ~1.3 h per trajectory measured at `W = 2048`; the core arm is
  ~62 h sequential, ~31 h at concurrency 2. The replication arm is unmeasured for
  throughput and may throttle on its single endpoint.
- Runs are resumable: re-invoking the same command continues from the last
  completed step, so a throttled or interrupted run costs wall clock, not data.
- **Stop and ask** if actual spend passes $14, if the completion rate falls below
  90%, or if the wall-clock projection exceeds four days.

## 8. Stage-specific risks

| Risk | Mitigation |
| --- | --- |
| Wall clock dominates and the stage stalls | S1.0 validates throughput at full `W` before the batch launches; Groq is the documented escape hatch (ADR-0007) at the cost of provenance |
| Single endpoint for the replication arm throttles | measured before the batch; RouterAI `alibaba` is the same upstream, so a provider switch would not help — reduce concurrency instead |
| Probe leakage inflates seed separation | E1 uses trajectory-level splits and the `D_within` control by construction; a gap without the control is not reportable (risks.md R8) |
| Block fill drifts at larger `W` | E7 makes it an explicit criterion rather than an assumption |
| 32 turnovers still too few | R10 accepted: all claims bounded by observed turnover count, stated on every figure axis |

## 9. Definition of done

- [ ] S1.0 validates block fill and latency at `W = 8192`
- [ ] Both arms generated, with per-trajectory status recorded
- [ ] Both embedding spaces computed for every chunk
- [ ] S1.5 seed-separation pass implemented, tested against a synthetic process,
      and run
- [ ] `artifacts/stage-1/` populated with figures, tidy data and captions
- [ ] `REPORT.md` with a verdict per exit criterion and the prediction table
      scored
- [ ] Master plan amended for Stage 2
- [ ] Spend reconciled
