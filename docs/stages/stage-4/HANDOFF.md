# Stage 4 — handoff

Operational detail. The contract is [`PLAN.md`](PLAN.md).

**Branch:** `cursor/stage-4-6dce`. Do not merge; that follows scientific
sign-off.

**Authorised spend:** CLI $2.47 (fill=1), S2.2-calibrated $3.33.
YAML refuse $4 + $10. Project remaining ~$188 of $200. Per-run env
ceiling is $7 — S4.2 forecast sits under it.

## Sequence

```bash
git switch cursor/stage-4-6dce
afterlife doctor

afterlife generate --config configs/stages/stage4_w4096_new_temps.yaml --yes
python scripts/summarise_run.py <s4.1 run_id>

afterlife generate --config configs/stages/stage4_w8192.yaml --yes
python scripts/summarise_run.py <s4.2 run_id>
```

Then embed, degeneracy (including the reused S2.2 raw eight), geometry,
separation — both spaces. Pairing for separation is same `(W, T)` only.

Reuse, do not regenerate:

`s2-mechanism-20260901T071519Z-dfbb173a` — the eight
`or-qwen3-8b__W4096__T{0p3,1}__{physics,surreal}__s{1,2}` cells.

A killed generate creates a new `run_id` if re-invoked. Keep the tmux
session; resume is intra-run via `*.steps.jsonl`.
