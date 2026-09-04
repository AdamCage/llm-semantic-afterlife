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

A bare `afterlife generate --config …` **mints a new `run_id`**. Do not
do that for an unfinished arm. Resume the same directory:

```bash
export AFTERLIFE_BUDGET_USD_TOTAL=200 AFTERLIFE_BUDGET_USD_PER_RUN=7.0 \
       AFTERLIFE_EXECUTION_MODE=live
uv run afterlife generate --config configs/stages/stage4_w8192.yaml --yes \
  --resume-run s4-w8192-20260904T120057Z-ce82ce55
```

Intra-run checkpoints are `*.steps.jsonl`. Kill a hung generate **by PID
only**, then resume; never start a second live generate against the same
`run_id`.

Live ids:

- S4.1 generate (done): `s4-w4096-new-temps-20260904T103121Z-589c8eb1`
- S4.2 generate: `s4-w8192-20260904T120057Z-ce82ce55`
