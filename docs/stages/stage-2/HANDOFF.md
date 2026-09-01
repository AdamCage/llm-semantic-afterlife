# Stage 2 — handoff

Operational detail for whoever executes this stage, including a cloud agent. The
contract is [`PLAN.md`](PLAN.md); this file is how to carry it out. Read
`AGENTS.md` and the `stage-execute` skill first.

**Branch:** `stage-2`, already created from `main`. Do not merge; that follows
scientific sign-off.

**Budget:** $2.8 forecast, $6 declared. Project spend to date $9.03 of $50.

---

## 0. Starting in the cloud

The environment bootstraps itself. `.cursor/install.sh` installs `uv`, syncs the
locked environment with the dev and dynamics extras, and restores the working
state — `runs/` and `cache/` — from the public `state-latest` release. Both are
git-ignored by design, so without that restore there are no trajectories to
analyse and every generation command spends real money re-deriving what exists.

Three things to check before anything else:

```bash
afterlife doctor          # ROUTERAI_API_KEY, OPENROUTER_API_KEY, HF_TOKEN
ls runs/s1                # should list ~22 Stage 1 runs
afterlife review --stage s1   # should exit 0 — proves the restore is intact
```

`HF_TOKEN` is not optional here. `gemma-4-31b-it`'s tokenizer is gated on the
Hub, and window arithmetic is exact or it is nothing. If any key is missing, set
it as a Cursor Cloud secret rather than writing a `.env`.

If `runs/s1` is empty the snapshot did not restore. Re-run it explicitly rather
than proceeding:

```bash
afterlife snapshot restore --from .cache/snapshot --root .
```

## 1. What is already settled

Do not re-decide these; each cost a measurement.

| Decision | Evidence |
| --- | --- |
| Five generators, all measured at a real 4096-token window | [ADR-0009](../../decisions/ADR-0009-bounded-reasoning-and-the-stage2-model-axis.md) |
| gpt-oss runs with reasoning **allowed and bounded**, not disabled | every endpoint refuses `enabled=false`; 33–43 tokens of 1024 observed |
| glimmer is re-admitted | two full blocks at `W=4096`; its earlier exclusion generalised from four cells |
| `W = 4096`, `T = 49152` (12 turnovers) | convergence establishes itself by turnover 10 |
| Degeneracy verdict is split into fixed-point and productivity | S1.2: the two disagree, and collapsing them excluded the only viable cell |
| Only *rates* of degeneracy are reportable | S1.2: which cell degenerates is not reproducible across seed derivations |

## 2. Sequence

```bash
git switch stage-2
afterlife doctor

# Determinism first: two arms are MoE and may not be seed-reproducible.
afterlife audit determinism --config configs/stages/stage2_capability.yaml

afterlife estimate --config configs/stages/stage2_model_axis.yaml   # expect ~$1.87
afterlife generate --config configs/stages/stage2_model_axis.yaml

afterlife estimate --config configs/stages/stage2_mechanism.yaml    # expect ~$0.77
afterlife generate --config configs/stages/stage2_mechanism.yaml
```

Then, per generation run:

```bash
python scripts/summarise_run.py <run_id>
afterlife embed --config <same config> --run <run_id>
afterlife analyze degeneracy  --run <generation_run_id>
afterlife analyze geometry    --run <embed_run_id> --embedding bge-m3
afterlife analyze geometry    --run <embed_run_id> --embedding qwen3-embed-8b
afterlife analyze separation  --run <embed_run_id> --embedding bge-m3
afterlife analyze separation  --run <embed_run_id> --embedding qwen3-embed-8b
```

Degeneracy before geometry, always. A trajectory at a fixed point occupies one
point in representation space and reports a confined MSD for reasons unrelated to
semantics.

## 3. Read the diagnostics before believing any analysis

`summarise_run.py` gates the stage. Check per generator, and **per quarter of the
run, not as a run average** — nothing in this protocol is stationary, and Stage 1
failed a criterion because a reading from the first 5% of a run was trusted for
the whole of it.

- **reasoning tokens** within the per-model tolerance: 64 for gpt-oss-120b, 32
  for gpt-oss-20b, 0 for the rest. Above tolerance the step fails loudly, which
  is intended.
- **served provider** equals the pinned provider on every step.
- **round-trip failures** reported per generator. Non-zero means `W` was not
  exactly 4096 on those steps; name the trajectories rather than dropping them.
- **block fill and stop rate per quarter.** Stage 1 went from 0.995 to 0.653 and
  from 4.5% to 74%. Expect drift; report its shape.
- **empty completions** on glimmer. Five consecutive fail the trajectory. The
  rate is a finding, not a fault.

## 4. Two rules that are easy to break

**Do not tune away a phenomenon.** If trajectories converge, that is the
measurement. If a model stops early, that is data about the regime. Changing
sampling parameters to make the output look better is fabrication.

**Do not extrapolate across regimes.** This project has made that error six
times: block fill measured at one window trusted at another, a capability probe
on a 28-token prompt trusted at 4096, a criterion amended on the first 5% of a
run, glimmer excluded from four cells. If a parameter changes, re-measure. It
usually costs cents.

## 5. Report

`REPORT.md` per `.cursor/rules/40-stage-protocol.mdc`, scoring every prediction
Q1–Q9 including the wrong ones. The gate now enforces three things that were
learned the hard way, so write for them from the start:

- **Quote the model's own output** from at least three points of at least three
  trajectories. Twice in Stage 1 reading the text beat reading the metrics: every
  intra-chunk diagnostic called a trajectory healthy while it reprinted the same
  page.
- **Report block fill and stop rate across the run**, by quarter. A run-level
  mean hides monotone drift.
- **Take spend from `runs/_ledger/spend.jsonl`**, never from a field in the step
  events. `cumulative_cost_usd` accumulates per trajectory; reading its maximum
  as a run total under-reported Stage 1 by thirtyfold. The gate now compares the
  two and fails on disagreement.

## 6. Gate, then hand off

```bash
afterlife review --stage s2   # must exit 0
```

Fix what it reports. If a check seems wrong, argue it rather than working around
it. Then commit, push `stage-2`, and hand off naming the headline finding in one
sentence, the run ids behind it, and what you are uncertain about. Flagging your
own uncertainty is worth more than a clean story.

Refresh the snapshot when the stage's data is final, so the next session starts
where this one ended:

```bash
afterlife snapshot create
gh release upload state-latest .cache/snapshot/*.tar.gz .cache/snapshot/snapshot.manifest.json --clobber
```

## 7. Known gaps

1. **`afterlife report --stage N` only regenerates `INDEX.md`.** Write `REPORT.md`
   by hand from the artifacts.
2. **The reasoning trace is not recoverable** on `/completions` — only its token
   count. Stated as a limitation; `/chat/completions` returns it if this turns
   out to matter.
3. **Prefill does not obviously remove the reviewer register.** Two direct calls
   at `W=4096` came back in it. S2.2 measures the rate; the plan's Q3 was fixed
   before that observation and stays as registered.
4. **Register counting is manual.** F4 requires a hand count over ≥20
   trajectories per mechanism against a stated criterion, not an impression.
5. **No base-model arm.** ADR-0008 §S2.2 specifies a local 1–3B model as the
   control for the instruction-tuning confound. It is not implemented and is the
   most important unexecuted pass in the project.

## 8. Stop and ask

Before: spending above $6, changing a threshold, dropping a planned cell,
switching a generator or endpoint, or adjusting sampling parameters. The last is
the most tempting and the most damaging.
