# ADR-0022: Occupancy replication panel (new run_ids)

Status: accepted
Date: 2026-09-07
Amends: [ADR-0021](ADR-0021-occupancy-record-not-recoverable.md)

## Context

ADR-0021 recorded that named S5/S6 occupancy runs are not recoverable.
The human authorised a **new** occupancy generate if wall-clock is not
a multi-day engineering project and spend stays **≤ $10**.

This is not a restore of
`s5-lock-occupancy-20260905T164327Z-6780902f`. Hosted sampling is not
deterministic (Stage 2 exact-match 100/60/20/20 percent). New draws
mint new `run_id`s. Original F4 CIs stay archival CSV outputs.

S2.2 physics/surreal reuse is also gone. The scientific grid is 14
seeds × 2 stochastic = 28 trajectories. Regenerating only the original
S5.1 YAML would omit physics and surreal and would not be an F4 panel.

## Decision

1. **Object.** One replication generate of the full occupancy grid
   (10 domain seeds + 4 twins), then embed (two spaces + gemini),
   degeneracy, and F4 trajectory-bootstrap CI from the new vectors.
   Spend cap **$10**. YAML refuse on generate is $8; embed refuse $2.
2. **Config.**
   [`configs/stages/stage5_lock_occupancy_replication.yaml`](../../configs/stages/stage5_lock_occupancy_replication.yaml)
   copies S5.1 protocol (`W=4096`, `T=0.3`, `B=S=chunk=1024`, 12
   turnovers, P1 `raw_completion`, `or-qwen3-8b`, Alibaba, unforced)
   and **adds** `physics` and `surreal`. Do not reuse old `run_id`s.
3. **Artifacts.** Write replication tables under
   `artifacts/tmlr-correctness/occupancy-replication/`. Do **not**
   overwrite `artifacts/stage-5/occupancy/` or
   `artifacts/stage-6/occupancy/` headline CSVs. Closed `REPORT.md`
   files are not rewritten.
4. **Manuscript.** After CIs exist, report them as a *replication*
   beside the archival intervals. Sign agreement is the interesting
   sentence. Level mismatch is expected. Do not silently replace
   `0.201 [0.065, 0.332]`.
5. **Not this run.** Paper B. Stage 8. A second generator. T≠0.3.
   Raising the $10 cap.

## Estimate (2026-09-07, fill=1 catalogue)

S5.1 YAML (24 traj, no physics/surreal): **$1.06** (4.47M in + 1.18M
out). Linear 28/24: **$1.24**. Historical S5.1 realised $1.3385 on 24
traj (fill < 1 adds input round-trips); scaled ~**$1.56**. Embed was
$0 on RouterAI in S5/S6 with catalogue gemini ~$0.30; YAML refuse $2.
Total expected **~$2**, hard stop **$10**.

Wall clock: 28 × 48 steps = 1344 completions at `max_concurrent=2`.
At 25–40 s/step ≈ 5–8 h; original S5.1 took ~9.5 h with eight
`ep_poll` stalls. Overnight, not days.

## Alternatives considered

- **Regenerate S5.1 YAML only (24).** Rejected: F4 needs physics and
  surreal.
- **Put new parquet under old run_ids.** Rejected: manifest hashes.
- **Wait forever for the archive.** Rejected by the human.

## Consequences

- This VM had no `OPENROUTER_API_KEY` / `ROUTERAI_API_KEY` at
  decision time. Generate starts when those are present.
- Original occupancy numbers remain the Paper A archival panel until
  the replication is scored.

## Reversal cost

Delete the new `runs/s5/s5-lock-occupancy-repl-*` directory and the
replication artifact folder. Do not delete Stage 5/6 CSVs.
