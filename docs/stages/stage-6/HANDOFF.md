# Stage 6 — handoff

Operational detail. The contract is [`PLAN.md`](PLAN.md).

**Branch:** `cursor/stage-6-6dce` (from `main` `9cb2845`).
Do not write `paper/main.tex`. Do not raise ceilings. Do **not**
`afterlife generate` with `configs/stages/stage6_third_space.yaml`.
That YAML is embed-only in intent; generate would mint a new
`run_id` and re-spend S5.

**Embed authorised 2026-09-06.** Live, YAML refuse $2,
`AFTERLIFE_BUDGET_USD_PER_RUN=2.0`. S5.1 first, then S2.2.
tmux `s6-embed-s5` / `s6-embed-s2`. Logs `/tmp/s6_embed_s5.log`
and `/tmp/s6_embed_s2.log`. Recurring 15 min stall timer
`s6-embed-watch`. Prefer waiting over killing an embed PID:
CLI has no resume; a kill forces a new `run_id`.

**Object.** Third-space robustness of S5 occupancy signs. Not T=1.0.
Not T=1.5. Not 200 seeds. Not a second generator. Not MSM.

## Sources (do not regenerate)

| role | `run_id` |
| --- | --- |
| S5.1 generate | `s5-lock-occupancy-20260905T164327Z-6780902f` |
| S2.2 generate | `s2-mechanism-20260901T071519Z-dfbb173a` |
| S5.1 embed (two spaces) | `s5-embed-lock-occupancy-20260906T030125Z-eab6e484` |
| S2.2 embed (two spaces) | `s2-embed-mechanism-20260901T131051Z-55761049` |
| S5.1 degeneracy | `s5-degeneracy-20260906T030145Z-deb4c3bd` |

## After embed-yes

```bash
git restore uv.lock
export AFTERLIFE_EXECUTION_MODE=live
export AFTERLIFE_BUDGET_USD_TOTAL=200
export AFTERLIFE_BUDGET_USD_PER_RUN=2.0

uv run afterlife embed --config configs/stages/stage6_third_space.yaml \
  --run s5-lock-occupancy-20260905T164327Z-6780902f

uv run afterlife embed --config configs/stages/stage6_third_space.yaml \
  --run s2-mechanism-20260901T071519Z-dfbb173a
```

Record both new embed `run_id`s. A fresh `afterlife embed` mints a
new id (no resume). If RUNNING, do not mint a sibling. Restore
`uv.lock`. YAML refuse $2.

S2.2 embed will include prefill and T=1.0 surplus rows. Occupancy
assemble keeps raw T=0.3 physics/surreal only.

## Do not

- `afterlife generate` on the S6 YAML
- Re-embed `bge-m3` / `qwen3-embed-8b`
- Move 0.083 / 0.0122
- Pool twins into domain `D_between`
- Call last-band collapsed “one lock”
- Open provider replication / chunk ablation / forced / Gemma
- Merge without scientific review
- Write `paper/main.tex`
