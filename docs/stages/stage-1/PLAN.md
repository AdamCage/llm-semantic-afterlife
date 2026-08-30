# Stage 1 — Pilot: does the phenomenon exist?

**Status.** Opened 2026-08-30 on branch `stage-1`, after Stage 0 closed with all
exit criteria met and both prerequisites discharged.

**Revised 2026-08-30**, before any pilot data existed, after three cheap probes
changed the entry state materially. What changed and why:

| | Original | Revised | Reason |
| --- | --- | --- | --- |
| Window | `W = 8192` | **`W = 4096`** | the only window where both viable generators are at their best ([VIABILITY-SWEEP.md](VIABILITY-SWEEP.md)) |
| Length | `T = 262144` | **`T = 131072`** | halved with `W` so 32 turnovers are preserved |
| Core generator | llama-3.1-8b on `deepinfra/fp8` | **qwen3-8b on `alibaba`** | llama produces text at 10.6× natural repetition; qwen at 1.7× |
| Replication | qwen3-8b | **muse-glimmer-30b on `parasail/bf16`** | glimmer writes *cleaner* than the reference corpus and brings the hybrid local/global attention axis |
| Excluded | — | mistral-nemo, llama-3.1-8b | 6.5× and 10.6× natural repetition, block fill never above 0.25 |

The probes cost $0.72 in total and prevented committing ~$30 of generation to a
generator whose output is 18× more repetitive than human prose. The full account
is in [BLOCKFILL-AND-DEGENERACY.md](BLOCKFILL-AND-DEGENERACY.md) and
[VIABILITY-SWEEP.md](VIABILITY-SWEEP.md); the operational sequence is in
[HANDOFF.md](HANDOFF.md).

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
- **Core endpoint.** `alibaba` qwen3-8b: block fill 0.942, repetition 1.7×
  natural prose, type-token 0.475 and entropy 7.53 (both above the human
  reference), stable across `W ∈ {2048, 4096, 8192}`. Quantization is reported as
  `unknown` — a provenance limitation to state, not one we can design away.
- **Replication endpoint.** `parasail/bf16` muse-glimmer-30b: block fill 1.000,
  stop rate 0.000, prompt-token delta 1, repetition 0.9× natural. Architecturally
  different in kind (interleaved local/global attention, 2048-token local span).
- **Two generators disqualified on output quality**, not price or speed:
  mistral-nemo (6.5× natural repetition) and llama-3.1-8b (10.6×). Both were
  cheaper and one was 21× faster.
- **The stop token is a declared forcing.** The process continues only because we
  override the model's attempt to terminate; the stop rate is an order parameter
  (methodology §1.4).
- **Degeneracy threshold is calibrated**, at 0.083 — the 99th percentile of
  natural English prose chunked by the same tokenizer at the same size. An
  intuition-picked 0.5 was six times too high and inverted the reading of a whole
  trajectory.
- **Reproducibility.** L3 verified by cache replay; L1 is per-model and measured.
- **Cost model** calibrated to −0.6% on input after the block-fill correction.

## 3. Experiment matrix

| Arm | Config | Generator | Endpoint | Matrix | Trajectories | Forecast |
| --- | --- | --- | --- | --- | --- | --- |
| core | `stage1_pilot_core.yaml` | qwen3-8b | `alibaba` | 1 W × 2 temperatures × 8 semantic seeds × 3 stochastic | 48 | **$5.75** |
| replication | `stage1_pilot_replication.yaml` | muse-glimmer-30b | `parasail/bf16` | 1 W × 1 temperature × 8 semantic seeds × 2 stochastic | 16 | **$4.77** |

Both at `W = 4096`, `B = 1024`, `T = 131072` (32 turnovers, 128 chunk
observations per trajectory), `chunk_size = 1024`, non-overlapping.
Temperatures: core `{0.3, 1.0}`, replication `{1.0}`.
Semantic seeds: `physics, finance, biology, war, love, programming, surreal,
noise`. Both embedding spaces (`bge-m3`, `qwen3-embed-8b`) on every chunk.

Total **64 trajectories, ~8.4M output tokens, ~$10.5**, roughly 22 h at
concurrency 2.

Note that 128 chunk observations per trajectory is half what the original plan
would have given. That is the cost of `W = 4096`, and it matters for Stage 3's
Markov-state estimation more than for Stage 1's contrast — recorded here so the
constraint is visible when S3 is planned rather than discovered then.

## 4. Computations

| # | Pass | Command | Status |
| --- | --- | --- | --- |
| S1.0 | Full-size trajectory probe | `afterlife generate --config configs/stages/stage1_probe_single.yaml` | done — exposed the llama degeneracy |
| S1.0b | Block fill across four families | `configs/stages/stage1_blockfill_probe.yaml` | done — [BLOCKFILL-AND-DEGENERACY.md](BLOCKFILL-AND-DEGENERACY.md) |
| S1.0c | Viability sweep in `W` | `configs/stages/stage1_viability_sweep.yaml` | done — [VIABILITY-SWEEP.md](VIABILITY-SWEEP.md) |
| S1.1 | Core generation | `afterlife generate --config configs/stages/stage1_pilot_core.yaml` | pending — 48 trajectories |
| S1.2 | Replication generation | `afterlife generate --config configs/stages/stage1_pilot_replication.yaml` | pending — 16 trajectories |
| S1.3 | Protocol diagnostics | `python scripts/summarise_run.py <id>` | pending — gates E6, E7 |
| S1.4 | Embedding, both spaces | `afterlife embed --run <id>` | pending |
| S1.5 | Degeneracy | `afterlife analyze degeneracy --run <id>` | pending — gate E9, run **first** |
| S1.6 | Geometry | `afterlife analyze geometry --run <id>` | pending — MSD, drift, recurrence |
| S1.7 | Seed separation | `afterlife analyze separation --run <id>` | pending — **the verdict pass** |
| S1.8 | Stage report | by hand from artifacts | pending |
| S1.9 | Review gate | `afterlife review --stage s1` | pending — must exit 0 |

All three analysis passes now exist and are tested against synthetic processes
with known answers. S1.7 is the pass that answers the stage's question: `D_within`
(same semantic seed, different stochastic seed) is the control that makes
`D_between` interpretable, and the estimator refuses to run without it.

S1.5 runs before S1.6 deliberately. A looping trajectory occupies one point in
representation space and reports a confined MSD for reasons unrelated to
semantics; the geometry pass joins the degeneracy verdicts so that no exponent is
presented unqualified.

Operational detail: [HANDOFF.md](HANDOFF.md).

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
| E7 | Block fill does not collapse at the pilot window | fill ≥ probe value − 0.05 at `W = 4096` (probe: 0.942 core, 1.000 replication), or the variable-stride caveat is reinstated for that arm |
| E8 | Completion rate | ≥ 90% of planned trajectories reach `T`; the rest reported as missing data with cause |
| E9 | Non-degeneracy | < 20% of trajectories flagged degenerate at the calibrated threshold; if more, the result is reported as measured on a degenerate ensemble and Stage 2 is re-planned |

E1 is the stage. E2 and E5 decide whether the result is worth Stages 2–5.

E7 exists because block fill was measured at `W ∈ {2048, 8192}` and the pilot runs
at 4096. Assuming it carries is the mistake this project has made three times: a
number measured in one regime and trusted in another.

**E7 amended 2026-08-30, 81 steps into the core run, from two-sided to one-sided.**
Observed fill is 0.995 against a probe value of 0.942 — outside a ±0.05 band, but
in the direction that makes the protocol *better*: the stride is more nearly
constant than assumed, so `S = B` holds more tightly and the cost law is if
anything conservative. The original two-sided wording would have recorded a
criterion failure for a favourable result, which is a defect in the criterion
rather than in the run. What the criterion is actually for is catching a
*collapse* in fill, because that is what breaks stride constancy, invalidates the
cost model and signals degeneracy. Recorded rather than silently reinterpreted;
the amendment tightens nothing and loosens nothing on the failure side.

E9 replaces the original E4 wording. It is now checkable against a calibrated
threshold rather than an intuition, and its failure mode is explicit — a
degenerate ensemble is still reportable, but everything derived from it is a
statement about repetition rather than about semantics.

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
| P8 | Block fill at `W = 4096` stays within 0.05 of the probe values | 0.65 | |
| P9 | The two embedding spaces agree on the sign of E1 but differ in effect size by > 25% | 0.55 | |
| P10 | At least one trajectory exhibits a visible metastable transition (a displacement spike separating two low-displacement regimes), as the offline fixture did | 0.5 | |
| P11 | Fewer than 20% of trajectories are flagged degenerate, i.e. these two generators do not collapse over 32 turnovers the way llama did over 32 at `W = 8192` | 0.6 | |
| P12 | Degeneracy rate is higher at `T = 0.3` than at `T = 1.0` on the core arm | 0.75 | |
| P13 | Repetition rises with turnover count even in non-degenerate trajectories — self-conditioning accumulates redundancy slowly | 0.55 | |

P3 is the one we are least sure of and the one that matters most: if seed
separation is gone by 10 turnovers, "semantic afterlife" is a short-lived
transient and Stage 2's half-life measurement becomes the whole paper rather than
one section of it.

P2 deserves a note. If the gap were *flat* rather than narrowing, that would
suggest genuinely persistent memory rather than slow decay — a stronger result
than we predict, and one we would need to scrutinise hard for leakage before
believing.

## 7. Budget and wall clock

- **Cost:** $10.5 forecast, $16 declared across the two arms. Project spend to
  date $0.76 of $50.
- **Wall clock:** ~19 s per step measured on both endpoints, so ~45 min per
  trajectory and roughly 22 h for both arms at concurrency 2.
- Runs are resumable: re-invoking the same command continues from the last
  completed step, so a throttled or interrupted run costs wall clock, not data.
- **Stop and ask** if actual spend passes $16, if the completion rate falls below
  90%, or if the wall-clock projection exceeds four days.

## 8. Stage-specific risks

| Risk | Mitigation |
| --- | --- |
| Both arms run on single endpoints with no fallback | measured before the batch; concurrency held at 2; runs resumable so throttling costs wall clock rather than data |
| Probe leakage inflates seed separation | the `D_within` control is enforced in code — `compute_separation` refuses to run without it (risks.md R8) |
| Block fill differs at `W = 4096` | E7 makes it an explicit criterion rather than an assumption |
| The contrast is underpowered at 3 repetitions | recorded as a test: sampling noise ~0.05 exceeds a weak signal, so a small gap must be reported as underpowered rather than absent |
| Degeneracy contaminates the geometry | `analyze geometry` joins per-trajectory verdicts and refuses to present an exponent unqualified; E9 makes the rate a criterion |
| 128 chunks per trajectory is thin for S3 | accepted for the pilot; Stage 3 either lengthens trajectories or reduces `chunk_size`, decided from S1's autocorrelation time |
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
