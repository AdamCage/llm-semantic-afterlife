# Stage 5 — handoff

Operational detail. The contract is [`PLAN.md`](PLAN.md).

**Branch:** `cursor/stage-5-6dce` (from `main` `5c07751`). Do not merge.
Do not write `paper/main.tex`. Do not raise ceilings. Do not mint a
second generate `run_id`.

**Object.** Lock occupancy vs seed at the S4 lock (`W=4096`, T=0.3)
on `or-qwen3-8b` under P1. Not T=1.0-as-basin. Not the T=1.5 residual.
Not 200 invented seeds.

## Live generate (authorised 2026-09-05)

| field | value |
| --- | --- |
| `run_id` | `s5-lock-occupancy-20260905T164327Z-6780902f` |
| config | `configs/stages/stage5_lock_occupancy.yaml` |
| STATUS | `RUNNING` (fourth resume 2026-09-05T22:00:50Z) |
| forecast | $1.06 fill=1 / ~$1.17 at S4 T=0.3 fill 0.90 |
| YAML refuse | $8 |
| tmux | `s5-generate` |
| log | `/tmp/s5_generate.log` |
| env | `AFTERLIFE_EXECUTION_MODE=live`, `AFTERLIFE_BUDGET_USD_TOTAL=200`, `AFTERLIFE_BUDGET_USD_PER_RUN=8.0` |

First steps at launch: finance s1/s2, served `Alibaba`, `reasoning_tokens=0`,
`tokenizer_roundtrip_ok=true`. Fill on those steps 0.65–0.92 with
`finish_reason=stop` (expected at T=0.3; do not retune).

S5.0 reuse (do **not** regenerate):
`s2-mechanism-20260901T071519Z-dfbb173a`,
`or-qwen3-8b__W4096__T0p3__{physics,surreal}__s{1,2}`.

## Stall 2026-09-05T18:13 → 19:01 (S4-style `ep_poll`)

Last `generation.step.completed` at 18:13:27Z on `programming` s1/s2
(steps 19 / 18). Hourly at 19:00 found ~48 min idle, python PID
111858 in `ep_poll`. Killed **that PID only**. Resumed the same
`run_id` at 19:01:20Z. New steps immediately: programming s2 step 19
and s1 step 20, Alibaba, `reasoning_tokens=0`.

Resume **re-emits** `generation.trajectory.finished` for already
completed trajectories. Count **unique** `trajectory_id`, not event
rows. Do not read the JSONL line count as n/24.

## Stall 2026-09-05T19:15 → 20:00 (same `ep_poll`)

After the first resume, programming s1/s2 finished (~19:11Z). Then
`philosophy` s1/s2 ran to steps 13/14 and sat ~45 min. Hourly at
20:00: python PID 114194 in `ep_poll`. Killed that PID. Resumed the
same `run_id`. New steps immediately: philosophy s1 step 14 and s2
step 15, Alibaba, `reasoning_tokens=0`. Unique COMPLETED at that
resume: **12/24** (previous ten plus programming ×2).

This is now two Alibaba TCP stalls ~1 h apart. Same mitigation: PID
kill + `--resume-run`. Do not mint a new `run_id`.

## Stall 2026-09-05T20:15 → 21:00 (same `ep_poll`)

Philosophy s1/s2 finished after the second resume. `noise` s1/s2 ran
to steps 11/9 and sat ~45 min. Hourly at 21:00: python PID 114798 in
`ep_poll`. Killed that PID. Resumed the same `run_id`. New steps
immediately: noise s1 step 12 and s2 step 10, Alibaba,
`reasoning_tokens=0`. Unique COMPLETED at that resume: **14/24**
(plus philosophy ×2).

Three stalls, ~hourly, each after a new pair has made ~10–20 steps.
Mitigation unchanged. Do not mint a new `run_id`.

## Stall 2026-09-05T21:15 → 22:00 (same `ep_poll`)

Noise s1/s2 finished after the third resume. `waterloo-won` s1/s2
ran to step 9/9 and sat ~45 min. Hourly at 22:00: python PID 115332
in `ep_poll`. Killed that PID. Resumed the same `run_id`. New steps
immediately: both waterloo-won step 10, Alibaba, `reasoning_tokens=0`.
Unique COMPLETED at that resume: **16/24** (plus noise ×2). First
twin pair is now the live pair.

Four stalls, ~hourly. Same mitigation. Do not mint a new `run_id`.

## Resume (same `run_id` only)

```bash
# look up the live PID; never pkill -f
pgrep -af 'afterlife generate'

# if hung (no generation.step.completed ~15+ min, or TCP stall / ep_poll):
# kill the python afterlife PID only, then:
export AFTERLIFE_BUDGET_USD_TOTAL=200
export AFTERLIFE_BUDGET_USD_PER_RUN=8.0
export AFTERLIFE_EXECUTION_MODE=live
tmux -f /exec-daemon/tmux.portal.conf has-session -t '=s5-generate' 2>/dev/null \
  || tmux -f /exec-daemon/tmux.portal.conf new-session -d -s s5-generate -c /workspace -- bash -l
tmux -f /exec-daemon/tmux.portal.conf send-keys -t s5-generate:0.0 \
  'export AFTERLIFE_BUDGET_USD_TOTAL=200 AFTERLIFE_BUDGET_USD_PER_RUN=8.0 AFTERLIFE_EXECUTION_MODE=live; uv run afterlife generate --config configs/stages/stage5_lock_occupancy.yaml --yes --resume-run s5-lock-occupancy-20260905T164327Z-6780902f 2>&1 | tee -a /tmp/s5_generate.log' C-m
```

`git restore uv.lock` after every `uv run`. Do not commit it.

Stop and ask if wall clock exceeds 24 h or completions are empty.
Stop and ask before a second YAML.

## Progress check

```bash
RID=s5-lock-occupancy-20260905T164327Z-6780902f
ROOT=runs/s5/$RID
cat $ROOT/STATUS
python3 - <<'PY'
import json
from collections import defaultdict
from pathlib import Path
root = Path("runs/s5/s5-lock-occupancy-20260905T164327Z-6780902f")
finished = []
last = {}
providers = defaultdict(int)
reasoning = 0
steps = 0
for line in (root / "events.jsonl").open():
    ev = json.loads(line)
    if ev.get("event") == "generation.step.completed":
        steps += 1
        last[ev["trajectory_id"]] = ev
        providers[ev.get("served_provider")] += 1
        if ev.get("reasoning_tokens", 0):
            reasoning += 1
    elif ev.get("event") == "generation.trajectory.finished":
        finished.append(ev)
print("STATUS", (root / "STATUS").read_text().strip())
print(f"finished {len(finished)}/24; live traj {len(last)}; step events {steps}")
print("providers", dict(providers), "reasoning_nonzero_steps", reasoning)
if last:
    newest = max(last.values(), key=lambda e: e["ts"])
    print("newest", newest["ts"], newest["trajectory_id"], "step", newest["step"],
          "fill", newest.get("block_fill_ratio"), "stop", newest.get("finish_reason"))
for ev in finished:
    print("done", ev.get("trajectory_id"), ev.get("status"),
          "tokens", ev.get("generated_tokens"), "$", ev.get("cost_usd"))
PY
```

Healthy: `STATUS=RUNNING`, Alibaba every step, `reasoning_tokens=0`,
round-trip ok, new `generation.step.completed` within ~15 min at
concurrency 2.

## When 24/24 COMPLETED

Do **not** start a new generate. Then, in order:

1. `git restore uv.lock`
2. `python scripts/summarise_run.py s5-lock-occupancy-20260905T164327Z-6780902f`
   — fill, stop, round-trip, reasoning, served provider = Alibaba
3. `afterlife embed --run s5-lock-occupancy-20260905T164327Z-6780902f` (both spaces)
4. `afterlife analyze degeneracy` on S5.1 **and** the reused S2.2 T=0.3 four.
   Threshold **0.083** / late Jaccard **0.0122**. Keep degenerate rows.
5. `afterlife analyze geometry` (diagnostic only)
6. `afterlife analyze separation` on the **ten domain seeds only**
7. `afterlife analyze twins` on the two twin pairs only
8. Artifacts + `REPORT.md` scoring F1–F10 and Q1–Q8
9. `afterlife review --stage s5` must exit 0 before requesting scientific review

Unsubscribe the six 10-minute debug timers once generate completes.
Keep the hourly timer until analysis + REPORT, or the human says stop.

## Do not

- `afterlife generate` without `--resume-run s5-lock-occupancy-20260905T164327Z-6780902f`
- Kill by name (`pkill -f`); kill the specific afterlife PID
- Raise `AFTERLIFE_BUDGET_USD_*` or YAML `budget_usd`
- Open T=1.0 occupancy, T=1.5 residual, `W=8192`, 200 seeds, Gemma
- Pool twins into domain `D_between`
- Drop degenerate rows before occupancy / twin tables
- Call a lock a semantic basin; put `n_macro` on the headline
- Merge to `main` or write `paper/main.tex`
