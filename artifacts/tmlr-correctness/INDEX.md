# TMLR correctness pass (ADR-0019)

Independent headline audit after the Bernoulli CI rewrite. No new generate.

- [`headline_audit.json`](headline_audit.json) — F4 last-band point estimates vs seed-pair matrix; Clopper–Pearson k/n; lock 19/20; F6 CIs flagged invalid until occupancy embeddings exist.
- Source tables: `artifacts/stage-2/model-axis/rates/`, `artifacts/stage-4/grid/`, `artifacts/stage-5/occupancy/lock_rate_by_seed.csv`, `artifacts/stage-6/occupancy/domain_separation_last_band.csv`.

## ADR-0020 P0 tables

- [`fixed_point_rates_by_temperature.csv`](../stage-2/model-axis/rates/fixed_point_rates_by_temperature.csv) — Stage 2 lock rates per temperature (`n=4`).
- [`occupancy_seed_pair_gap.csv`](occupancy_seed_pair_gap.csv) — matrix F4 points.
- [`occupancy_leave_one_seed_out.csv`](occupancy_leave_one_seed_out.csv) — leave-one-seed-out.
- [`occupancy_within_pair_randomization.csv`](occupancy_within_pair_randomization.csv) — within-pair randomisation.
- F6 canonical CSVs no longer carry `delta_ci_*`; sidecars are `*.legacy_invalid.csv` under `artifacts/stage-5/occupancy/` and `artifacts/stage-6/occupancy/`.
- Trajectory-bootstrap F4 CIs are **not** recomputed (occupancy embeddings absent).
