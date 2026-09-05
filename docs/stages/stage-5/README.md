# Stage 5

Opened 2026-09-05. Plan: [`PLAN.md`](PLAN.md). Decisions:
[`ADR-0015`](../../decisions/ADR-0015-s5-operating-point-after-s4.md),
[`ADR-0016`](../../decisions/ADR-0016-s5-lock-occupancy-on-seed-bank-v1.md).

**Question.** On `or-qwen3-8b` under P1, at the S4 lock (`W=4096`,
T=0.3), do seed_bank_v1 domain seeds occupy distinguishable locks,
and do twin pairs stay apart relative to the stochastic control?

Generate authorised 2026-09-05. CLI estimate **$1.06** (fill=1);
S4 T=0.3 fill 0.90 is **~$1.17**. YAML refuse **$8**. Live `run_id`
and resume instructions: [`HANDOFF.md`](HANDOFF.md).

| pass | status |
| --- | --- |
| S5.0 reuse S2.2 raw `W=4096` T=0.3 physics/surreal (4 traj) | cells exist; not yet joined |
| S5.1 `stage5_lock_occupancy.yaml` (24 traj) | generating |
| embed / degeneracy / separation / twins | blocked on generate |

Scientific grid: 14 seeds × 2 stochastic = 28 trajectories, 12 turnovers.
New tokens: 24 trajectories only.
