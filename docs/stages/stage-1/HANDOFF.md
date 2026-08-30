# Stage 1 — handoff

Operational detail for whoever executes this stage. The contract is
[`PLAN.md`](PLAN.md); this file is how to carry it out. Read `AGENTS.md` and the
`stage-execute` skill first.

**Branch:** `stage-1` (already created from `main`). Do not merge; that follows
scientific sign-off.

**Budget:** $10.5 forecast, $16 declared across the two arms. Project spend to
date $0.76 of $50. Stop and ask above $16.

**Wall clock:** roughly 22 h at concurrency 2, spread over as many sessions as
needed. Runs are resumable — re-invoking the same command continues from the last
completed step, so an interruption costs time, not data.

---

## What is already settled, and must not be re-litigated

These came out of Stage 0 and the Stage 1 probes. Each cost real measurement;
none should be re-decided without new evidence.

| Decision | Evidence |
| --- | --- |
| `W = 4096`, `T = 131072` (32 turnovers) | [VIABILITY-SWEEP.md](VIABILITY-SWEEP.md): the only window where both viable generators are at their best |
| Core generator `or-qwen3-8b` (Alibaba) | fill 0.942, repetition 1.7× natural, stable across all windows tested |
| Replication generator `or-muse-glimmer-30b` (`parasail/bf16`) | fill 1.000, stop rate 0.00, repetition 0.9× natural — cleaner than the reference corpus |
| mistral-nemo and llama-3.1-8b excluded | 6.5× and 10.6× natural repetition; fill never above 0.25 |
| `raw_completion`, `forcing = unforced` | ADR-0006: no base models exist on any provider |
| `reasoning_effort: none`, verified per step | ADR-0005: `include_reasoning: false` is accepted and does nothing |
| Degeneracy threshold 0.083 | 99th percentile of natural prose, same tokenizer and chunk size |

## Sequence

### 1. Confirm the environment and the endpoints

```bash
git switch stage-1
afterlife doctor
python scripts/probe_endpoints.py or-qwen3-8b --config configs/stages/stage0_audit_openrouter.yaml
python scripts/probe_endpoints.py or-muse-glimmer-30b --config configs/stages/stage0_audit_openrouter.yaml
```

Endpoint availability and throttling both drift. If the pinned endpoint no longer
serves, that is a finding for the report, not a reason to switch silently — record
it and say what you switched to and why.

### 2. Estimate, report, then generate

```bash
afterlife estimate --config configs/stages/stage1_pilot_core.yaml
afterlife estimate --config configs/stages/stage1_pilot_replication.yaml
```

Expect about $5.75 and $4.77. A materially different number means a price or a
block-fill assumption has moved — investigate before spending.

```bash
afterlife generate --config configs/stages/stage1_pilot_core.yaml
afterlife generate --config configs/stages/stage1_pilot_replication.yaml
```

`AFTERLIFE_MAX_RETRIES=8` is a reasonable setting: both endpoints throttle under
sustained load and recover with patience.

### 3. Check the protocol diagnostics **before** analysing

```bash
python scripts/summarise_run.py <core_run_id> <replication_run_id>
```

Gates, in order of severity. A failure here invalidates everything downstream, so
report it before running any analysis:

- **reasoning tokens must be 0.** Non-zero means the block appended to the window
  was only the visible part of what the model generated, so the implemented
  recursion is not the model's own.
- **round-trip failures must be 0.** A failure means the window boundary was not
  where the manifest claims, so `W` is void for that trajectory.
- **served provider must equal the pinned provider** on every step.
- **block fill** should be near 0.94 (qwen) and 1.00 (glimmer). A collapse means
  the stride is not `B`, the cost model is wrong, and the trajectory is probably
  degenerate. This was measured at `W = 8192`; `W = 4096` is a different regime,
  so **verify rather than assume** — that is exit criterion E7 and it is the
  mistake this project has made three times.
- **completion rate** ≥ 90% of planned trajectories. Failed trajectories are
  reported as missing data with a cause, never silently dropped.

### 4. Embed both spaces

```bash
afterlife embed --config configs/stages/stage1_pilot_core.yaml --run <core_run_id>
afterlife embed --config configs/stages/stage1_pilot_replication.yaml --run <replication_run_id>
```

Both `bge-m3` and `qwen3-embed-8b` are configured. A result that holds in one
representation space is not a result — that is exit criterion E5.

Embedding cost has not been verified at this volume (S0 measured $0 on tiny
probes, which may just be below the provider's reporting granularity). Check the
ledger after the first embed run and report the real per-million rate.

### 5. Analyse — degeneracy first

```bash
afterlife analyze degeneracy  --run <generation_run_id>
afterlife analyze geometry    --run <embed_run_id> --embedding bge-m3
afterlife analyze geometry    --run <embed_run_id> --embedding qwen3-embed-8b
afterlife analyze separation  --run <embed_run_id> --embedding bge-m3
afterlife analyze separation  --run <embed_run_id> --embedding qwen3-embed-8b
```

Degeneracy first is not a preference. A looping trajectory occupies one point in
representation space and will report a confined MSD for reasons that have nothing
to do with semantics; knowing which trajectories are degenerate changes how every
later figure reads. `analyze geometry` joins the labels automatically and will
warn loudly if it cannot find them.

`analyze separation` is the pass that answers the stage's question. It refuses to
run without the `D_within` control.

### 6. Write the report, scoring the predictions

`REPORT.md` per `.cursor/rules/40-stage-protocol.mdc`. Fill in the `observed`
column of the plan's prediction table honestly, including where the prediction
was wrong. Additionally required, because all of these have mattered here:
realised block-fill distribution, stop rate, reasoning-guard failures, and
trajectories lost to throttling.

### 7. Pass the gate, then hand off

```bash
afterlife review --stage s1
```

It must exit 0. Then commit, push `stage-1`, and hand off for review naming: the
headline finding in one sentence, the run ids behind it, and what you are
uncertain about.

---

## Known gaps you may hit

Honest list of what is not finished, so nobody rediscovers it:

1. **`afterlife report --stage N` only regenerates `INDEX.md`.** It does not
   assemble a stage report. Write `REPORT.md` by hand from the artifacts.
2. **Horizon annotations overlap on figures at high turnover counts.** Cosmetic;
   the `t = W`, `2W`, `3W` labels crowd together when the axis spans 32
   turnovers. Fix in `viz/theme.py::horizon_annotations` if it bothers a reader.
3. **The separation pass is underpowered at three stochastic repetitions.** Test
   `test_the_contrast_is_underpowered_at_the_pilot_replicate_count` records this:
   sampling noise of the contrast is ~0.05, which exceeds the signal from a
   weakly persistent seed. If the measured gap is small, the honest reading is
   "underpowered", not "absent" — say so rather than concluding no effect.
4. **Glimmer emits bare stop tokens at `W = 8192`** but not at 4096. If it starts
   doing so at 4096 the empty-completion guard will fail the trajectory after
   five in a row; that is correct behaviour and the rate is a finding.
5. **qwen's endpoint reports `unknown` quantization.** A provenance limitation to
   state in the report, not something to design away.
6. **Embedding-space cross-check is manual.** Nothing computes ARI/NMI between
   representations yet; that lands in Stage 3.

## If a decision is needed

Stop and ask rather than choosing. Specifically: spending above $16, changing a
threshold, dropping a planned cell, switching a generator or endpoint, or
adjusting sampling parameters to improve the look of the output. The last one is
the most tempting and the most damaging: if trajectories degenerate, that is a
measurement, not a defect to tune away.
