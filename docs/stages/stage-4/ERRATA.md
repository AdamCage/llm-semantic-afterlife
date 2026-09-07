# Errata (2026-09-06) — TMLR correctness pass (ADR-0019)

Closed `REPORT.md` numbers are not rewritten. The `run_id`s remain the
data source.

## What changed

- [`looping_rate_by_cell.csv`](../../../artifacts/stage-4/grid/looping_rate_by_cell.csv)
  intervals are Clopper–Pearson. Counts per cell are unchanged.
- $4/4$: was CI `[1, 1]`; is `[0.398, 1]`.
- $0/4$ at $W=4096$, $T=1.5$: was `[0, 0]`; is `[0, 0.602]`.
- $2/4$ at $W=8192$, $T=1.5$: was `[0, 1]`; is `[0.068, 0.932]`.
- New table
  [`looping_rate_contrasts.csv`](../../../artifacts/stage-4/grid/looping_rate_contrasts.csv):
  Newcombe CI and Fisher exact $p$ for $T=0.3$ vs $T=1.5$. At $W=4096$,
  $4/4$ vs $0/4$ is $p\approx 0.029$. That is a cell contrast, not a
  temperature law.

## ADR-0020 (2026-09-07)

Fisher $p\approx 0.029$ remains in the CSV. It is **not** in the
manuscript narrative. The paper reports the $4/4$ vs $0/4$ cell contrast
without the $p$-value.

## What did not change

- H5 remains **absent**. Clean $\alpha$ is still defined only at $T=1.5$.
- Generate `run_id`s
  `s4-w4096-new-temps-20260904T103121Z-589c8eb1` and
  `s4-w8192-20260904T120057Z-ce82ce55`.
