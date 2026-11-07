# ADR-0030: Replication is the primary occupancy evidence

Status: accepted
Date: 2026-11-07
Amends: [ADR-0022](ADR-0022-occupancy-replication-panel.md) (manuscript clause only)

## Context

ADR-0022 put the occupancy replication *beside* the archival
last-band intervals and made sign agreement the manuscript sentence.
It also forbade silently replacing `0.201 [0.065, 0.332]`. That
replacement ban still holds: the archival embeddings are not
recoverable ([ADR-0021](ADR-0021-occupancy-record-not-recoverable.md)),
and a new interval is not the old one.

The assembled manuscript has a different job. The recoverable
measurement is the replication
(`artifacts/occupancy-replication/domain_separation_last_band.csv`,
generate `s5-lock-occupancy-repl-20260907T091450Z-e8452acb`). The
archival CSV remains a historical record of one panel. Treating the
two as co-equal headlines asks the reader to rest a claim on intervals
that cannot be recomputed.

## Decision

1. **Primary occupancy evidence** for the seed-conditioned last-band
   gap is the replication table. In BGE-M3 that gap is `0.208`
   `[0.091, 0.314]`. The other two spaces on the same generate stay
   in that table. They are not pooled onto one scale.
2. **Archival intervals stay in the manuscript**, in a table labeled
   historical, and are not a substitute for the replication. Do not
   replace `0.201 [0.065, 0.332]` with the replication interval, and
   do not delete it.
3. **Sign agreement** between the two tables is still reported. It is
   not the sentence the abstract leads with.
4. **Unchanged from ADR-0022.** Do not overwrite
   `artifacts/stage-5/occupancy/` or `artifacts/stage-6/occupancy/`.
   Do not rewrite closed stage reports. Do not mint a run for this
   editorial change.

## Consequences

`paper/notes/claims.md` and `paper/notes/figure-shortlist.md` recorded
the ADR-0022 manuscript rule ("replication is support, not the
archival headline"). Those notes now follow this decision. The S7
shortlist itself is not redrawn; the assembled `paper/main.tex` is the
source of record for which figures the paper prints.

## Reversal cost

Restore the ADR-0022 wording in the manuscript and in the two notes.
No runs, artifacts, or archival CSVs are involved.
