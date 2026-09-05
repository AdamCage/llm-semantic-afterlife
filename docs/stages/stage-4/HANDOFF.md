# Stage 4 — handoff

Operational detail. The contract is [`PLAN.md`](PLAN.md).

**Branch:** `cursor/stage-4-6dce`. Do not merge; that follows scientific
sign-off.

**Authorised spend:** CLI $2.47 (fill=1), S2.2-calibrated $3.33.
YAML refuse $4 + $10. Project remaining ~$188 of $200. Per-run env
ceiling is $7 — S4.2 forecast sits under it.

## Sequence

Generate is **done**. Do not mint a new generate `run_id`.

```bash
git switch cursor/stage-4-6dce

# S4.2 post-generate (degeneracy + protocol, then wait for embed, then
# geometry / separation / grid figures)
S42_EMBED_RUN=s4-embed-w8192-20260905T090901Z-15172d14 \
  bash scripts/run_s42_analysis.sh
```

Then `docs/stages/stage-4/REPORT.md`, `afterlife review --stage s4`.

Reuse, do not regenerate:

`s2-mechanism-20260901T071519Z-dfbb173a` — the eight
`or-qwen3-8b__W4096__T{0p3,1}__{physics,surreal}__s{1,2}` cells.

A bare `afterlife generate --config …` **mints a new `run_id`**. Do not
do that.

## Live ids

- S4.1 generate (done): `s4-w4096-new-temps-20260904T103121Z-589c8eb1` — 8/8, $0.4379
- S4.1 embed (done): `s4-embed-w4096-new-temps-20260904T120202Z-37e61e58`
- S4.1 degeneracy (done): `s4-degeneracy-20260904T120745Z-92b6f79e` — snapshot under `artifacts/stage-4/s41/`
- S4.2 generate (done): `s4-w8192-20260904T120057Z-ce82ce55` — 16/16, $3.0004. Do not regenerate.
- S4.2 embed (live): `s4-embed-w8192-20260905T090901Z-15172d14`

S4.1+S4.2 generate ≈ $3.44 versus the authorised $3.33 estimate (+$0.11).
Still under the $7 per-run and $14 stage YAML ceilings. Report in F10.

`--resume-run` is implemented (commit `77c14a7`) but generate is finished;
do not resume.
