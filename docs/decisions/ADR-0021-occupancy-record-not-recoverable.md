# ADR-0021: Occupancy run directories are not recoverable

Status: accepted
Date: 2026-09-07
Amends: [ADR-0020](ADR-0020-tmlr-p0-publication-blockers.md)

## Context

ADR-0020 left trajectory-bootstrap F4 CIs as *pending restore*: put
`data/embeddings_*.parquet` back into the named S5/S6 runs, or mint a
new embed `run_id`. The human then confirmed that **no occupancy run
directory remains** (not this workspace, not `state-latest`, not a
local generate shell).

Named ids that cannot be opened:

- generate `s5-lock-occupancy-20260905T164327Z-6780902f`
- two-space embed `s5-embed-lock-occupancy-20260906T030125Z-eab6e484`
- degeneracy `s5-degeneracy-20260906T030145Z-deb4c3bd`
- gemini `s6-embed-third-space-20260906T082301Z-588eff8f` and
  `s6-embed-third-space-20260906T082628Z-9077d587`
- S2.2 reuse `s2-mechanism-20260901T071519Z-dfbb173a` /
  `s2-embed-mechanism-20260901T131051Z-55761049` (also absent here;
  `state-latest` is 2026-09-01T01:41Z, before that generate)

The committed occupancy *artifacts* still exist: last-band points and
CIs in
[`artifacts/stage-6/occupancy/domain_separation_last_band.csv`](../../artifacts/stage-6/occupancy/domain_separation_last_band.csv),
the seed-pair matrix, and the ADR-0020 leave-one-out / randomisation
tables. What is gone is the generating parquet.

A new `afterlife generate` on `stage5_lock_occupancy.yaml` would **not**
restore those CIs. Hosted sampling is not deterministic (Stage 2
exact-match rates were 100/60/20/20 percent). New draws mint new
`run_id`s and a new occupancy panel. Putting new parquet under the old
ids would break manifest integrity hashes.

Paper B stays parked. This is not Stage 8.

## Decision

1. **Object.** Record that the occupancy computational record is lost.
   Spend **$0**. No generate. No live embed.
2. **Language.** Withdraw “CI recompute is pending”. The recompute of
   *those* named-run CIs from vectors cannot happen.
3. **What the paper may still claim.**
   - F4 *points* independently recomputed from the committed seed-pair
     matrix (ADR-0020; abs &lt; 0.002 vs headline).
   - Leave-one-seed-out and within-pair randomisation on that matrix
     (reproducible from git).
   - Published trajectory-bootstrap CIs as **archival analysis outputs**
     stored in the committed CSV, produced by `compute_separation`
     (multiplicity-preserving; ADR-0019). They are not independently
     re-derived from embeddings in this pass.
4. **What it must not claim.** That a reviewer can `afterlife reproduce`
   the occupancy embed runs, or that regenerating the 24+4 trajectories
   verifies the published intervals.
5. **Do not regenerate under old `run_id`s.** An optional *replication*
   panel (new ids, estimate first, human yes) is parked in
   [`docs/backlog.md`](../backlog.md). It is a new experiment, not this
   correctness pass.

## Alternatives considered

- **Regenerate occupancy now to “restore F4”. ** Rejected: new draws,
  new ids, ~$1.34 historical generate plus embed; cannot match the
  published intervals; needs keys and an explicit spend yes.
- **Drop the published CIs from Table F4.** Rejected: the CSV and the
  estimator in git still exist; the honest move is to label them
  archival, not to delete the only interval the original analysis
  produced.
- **Fake a restore by treating seed-pair means as a trajectory
  bootstrap.** Rejected: between-seed matrix cells are means of 2×2
  trajectory pairs; `compute_separation` resamples trajectories.

## Consequences

- Manuscript occupancy prose, table caption, and limitations name the
  lost record (ADR-0021). Closed `REPORT.md` files are not rewritten;
  ERRATA records the posture.
- Headline F4 numbers in the CSV do not change.
- An immutable occupancy-vector tag cannot be cut from this workspace.

## Reversal cost

If the named run directories reappear, restore parquet, recompute CIs
from vectors, and amend this ADR. A new generate is a replication
panel ([ADR-0022](ADR-0022-occupancy-replication-panel.md)), not that
restore.
