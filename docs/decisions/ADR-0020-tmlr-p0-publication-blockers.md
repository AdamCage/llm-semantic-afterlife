# ADR-0020: TMLR P0 publication blockers (not a new stage)

Status: accepted
Date: 2026-09-07
Amends: [ADR-0019](ADR-0019-tmlr-correctness-pass.md)

## Context

A post-ADR-0019 review scored the manuscript as technically much closer
to TMLR-ready, then listed remaining publication blockers. None of them
is a new experimental stage. Occupancy embedding parquet is still absent
from this workspace (`state-latest` is 2026-09-01; generate shells for
S5/S6 may exist without `data/embeddings_*.parquet`). Trajectory-bootstrap
F4 CIs therefore cannot be re-derived here. Paper B stays parked.

## Decision

1. **Object.** Second correctness pass on the closed S0–S7 record. No
   new generate. No live embed from this environment (chunks/embeddings
   for occupancy are not complete here). Spend **$0**.
2. **Stage 2.** The published `n=8` rates are pooled over
   `T ∈ {0.3, 1.0}`. The manuscript table is per temperature (`n=4`).
   Pooled rows remain in the old CSV; they are not labelled as `T=0.3`.
3. **F4 inferential target.** Last-band separation is
   *between-seed vs within-seed* across ten fixed seed texts (one text
   per labelled domain). Domain ≡ seed instance. Second inference from
   the committed seed-pair matrix: leave-one-seed-out and a
   within-pair randomisation test. Trajectory-bootstrap CI recompute
   waits on occupancy embeddings.
4. **F6.** Invalid CI columns leave the canonical `twin_last_band.csv`
   (and `twin_per_band.csv`) for a `*.legacy_invalid.csv` sidecar.
   Point Δ stays. F6 is not a headline.
5. **Docs.** `t_h` in the seed bank is eviction start; methodology P2 is
   planned, not recorded; tokenizer roundtrip in `SlidingWindow.append`
   matches `decode(encode(x))==x` (and token-id equality after `Tail_W`);
   README and `CITATION.cff` follow the manuscript, not H1.
6. **Literature.** Cite Random Attention (arXiv:2609.03430) after
   VERIFIED. “Execution Horizon Laws / 31-model census” was not found
   under that title; do not cite a lookalike.
7. **Anonymization.** `paper/compile.sh anonymous` blanks author and
   GitHub/branch strings. Identified PDFs remain the committed releases.
8. **Cache is not git.** Occupancy vectors, if restored, live in `runs/`
   and an immutable release the human cuts. Do not un-ignore `cache/`.

## Alternatives considered

- **Re-embed occupancy live.** Rejected here: generate `chunks.parquet`
  is not in this workspace; gemini may bill; ADR-0019 forbade a silent
  API embed. Human restore or a later authorised embed with new `run_id`.
- **Open S8 / Paper B.** Rejected: the review asked to close Paper A.

## Consequences

- Headline F4 *points* and published trajectory-bootstrap CIs are
  unchanged until embeddings exist. The paper states that CI recompute
  from raw vectors is pending the occupancy archive.
- Human checklist: restore `data/embeddings_*.parquet` into the named
  S5/S6 run directories (or re-embed with new `run_id`s), cut an
  immutable tag (do not move `state-latest`), merge after green PR CI.

## Reversal cost

Low for prose and CSV quarantine. Restoring F6 CI columns would republish
invalid intervals.
