# Errata (2026-09-06) — TMLR correctness pass (ADR-0019)

Closed `REPORT.md` numbers are not rewritten. The `run_id`s remain the
data source. This file records what changed in the *published intervals
and wording*, not in the trajectories.

## What changed

- Bernoulli 95% intervals in
  [`artifacts/stage-2/model-axis/rates/fixed_point_rates.csv`](../../../artifacts/stage-2/model-axis/rates/fixed_point_rates.csv)
  are now **Clopper–Pearson exact**, not a percentile bootstrap of 0/1
  flags. Counts `k/n` are unchanged.
- `or-gemma-4-31b` $0/8$: was CI `[0, 0]`; is `[0, 0.369]`.
- `or-gpt-oss-120b` $8/8$: was `[1, 1]`; is `[0.631, 1]`.
- `or-qwen3-8b` $7/8$: was `[0.625, 1]` (excludes $0.5$); is
  `[0.473, 0.997]` (**includes** $0.5$). Direction (F2) is gemma versus
  120B, not this Qwen interval.
- Mechanism contrast $7/8$ vs $8/8$: Newcombe CI includes $0$; Fisher
  $p=1$. The old bootstrap difference CI `[-0.375, 0]` is withdrawn.

## What did not change

- Generate `run_id`s, lock flags, and the PARTIAL verdict.
- Historical `horizon_tokens` in JSONL (eviction start). Analysis of
  later stages does not read that field for F4.
