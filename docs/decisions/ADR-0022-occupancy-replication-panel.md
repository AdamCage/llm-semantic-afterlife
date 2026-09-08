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

## Postscript (2026-09-07, CIs exist)

Generate `s5-lock-occupancy-repl-20260907T091450Z-e8452acb` billed **$1.518**
(27/28 COMPLETED; `noise s2` FAILED at 49151/49152, 47 chunks kept).
Two-space embed `s5-embed-lock-occupancy-repl-20260907T175131Z-4e48f831`
and gemini `s6-embed-third-space-20260907T181515Z-bcde0a11` billed **$0**.
Degeneracy `s5-degeneracy-20260907T175009Z-f5accf8a`: 28/28 labelled.

Last-band replication CIs (`n_boot=2000`, seed 0):

| space | archival | replication | sign agrees |
| --- | --- | --- | --- |
| bge-m3 | 0.201 [0.065, 0.332] | 0.208 [0.091, 0.314] | yes |
| qwen3-embed-8b | 0.390 [0.151, 0.593] | 0.400 [0.221, 0.590] | yes |
| gemini-embed-001 | 0.150 [0.029, 0.266] | 0.152 [0.073, 0.239] | yes |

Band 12 has `n_within_pairs=6` and `n_between_pairs=114` because four
domain trajectories stop at turnover 11.75. Band 10 still has 80/1440
and also excludes 0; it is not the pre-registered F4 number. Do not
impute.

Canonical tables: `artifacts/occupancy-replication/`.
TMLR copies of headline CSVs:
`artifacts/tmlr-correctness/occupancy-replication/`.
Archival `artifacts/stage-6/occupancy/domain_separation_last_band.csv`
is unchanged. The manuscript reports replication *beside* Table
`tab:s6-f4`; sign agreement is the claim; do not replace
`0.201 [0.065, 0.332]`.
