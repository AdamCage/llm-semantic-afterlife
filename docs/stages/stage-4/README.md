# Stage 4

Opened 2026-09-03. Plan: [`PLAN.md`](PLAN.md). Decision:
[`ADR-0014`](../../decisions/ADR-0014-reduced-s4-temp-window.md).

**Question.** On `or-qwen3-8b` under P1, do T and `W` move looping
rate / fill / clean MSD `α`, or is T=1.5 still a lock?

Generate authorised 2026-09-04. CLI estimate **$2.47** (fill=1);
S2.2-calibrated fill 0.65 is **$3.33**.

| pass | status |
| --- | --- |
| S4.0 reuse S2.2 raw `W=4096` T=0.3, 1.0 (8 traj) | cells exist; not yet joined into stage-4 artifacts |
| S4.1 `stage4_w4096_new_temps.yaml` (8 traj) | **COMPLETED** `s4-w4096-new-temps-20260904T103121Z-589c8eb1` 8/8, $0.4379 |
| S4.2 `stage4_w8192.yaml` (16 traj) | generating |
| embed / degeneracy / geometry / separation | blocked on generate |

Scientific grid: 2 × 4 × 2 × 2 = 32 trajectories, 12 turnovers.
New tokens: 24 trajectories only.
