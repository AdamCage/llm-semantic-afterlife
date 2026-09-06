# TMLR correctness pass (ADR-0019)

Independent headline audit after the Bernoulli CI rewrite. No new generate.

- [`headline_audit.json`](headline_audit.json) — F4 last-band point estimates vs seed-pair matrix; Clopper–Pearson k/n; lock 19/20; F6 CIs flagged invalid until occupancy embeddings exist.
- Source tables: `artifacts/stage-2/model-axis/rates/`, `artifacts/stage-4/grid/`, `artifacts/stage-5/occupancy/lock_rate_by_seed.csv`, `artifacts/stage-6/occupancy/domain_separation_last_band.csv`.
