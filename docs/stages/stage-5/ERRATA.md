# Errata (2026-09-06) — TMLR correctness pass (ADR-0019)

Closed `REPORT.md` numbers are not rewritten. The occupancy generate
`run_id` remains `s5-lock-occupancy-20260905T164327Z-6780902f`.

## What changed

- Occupancy block size in the *manuscript* was $B=512$. The executed YAML
  is `block_size: 1024`
  ([`configs/stages/stage5_lock_occupancy.yaml`](../../../configs/stages/stage5_lock_occupancy.yaml)).
  PLAN.md already said $B=S=1024$. The sentence was wrong; the experiment
  was not regenerated.
- F6 last-band label `collapsed` is withdrawn. The operational name is
  `no_detected_divergence`. $n=2$; twins are counterfactual narratives, not
  one-token flips.
- Published twin CI columns used `set(chosen)` and are **not** bootstrap
  intervals. Point $\Delta$ values in
  [`twin_last_band.csv`](../../../artifacts/stage-5/occupancy/twin_last_band.csv)
  are still the observed means. Occupancy embeddings were absent from the
  2026-09-01 `state-latest` snapshot, so CIs were not re-derived. F6 is not
  a headline.

## What did not change

- Lock occupancy $19/20$ domain trajectories, $10/10$ seeds with $\ge 1$
  lock. F4 last-band point estimates and trajectory-bootstrap CIs
  (`compute_separation` already weighted multiplicities).
- Degeneracy thresholds $0.083$ / $0.0122$. love $1/2$ kept.
