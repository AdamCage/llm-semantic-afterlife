# Occupancy replication (ADR-0022)

New 28-trajectory lock panel. **Not** a restore of
`s5-lock-occupancy-20260905T164327Z-6780902f`.

The generating `run_id` is
`s5-lock-occupancy-repl-20260907T091450Z-e8452acb`
under `runs/s5/` and is git-tracked (see `.gitignore`) so embeddings and
chunks cannot disappear with a cloud VM. Do not copy secrets here. `.env`
stays git-ignored.

Generate STATUS is `COMPLETED` (27/28 trajectories). Spend $1.518.
`noise s2` FAILED at 49151/49152 (`WindowProtocolError`); 47 chunks kept.
Three COMPLETED trajectories also have 47 chunks (`philosophy s1`,
`programming s2`, `war s2`). That is missing data, not a silent drop.

Embed: `s5-embed-lock-occupancy-repl-20260907T175131Z-4e48f831`
(bge-m3, qwen3-embed-8b) and `s6-embed-third-space-20260907T181515Z-bcde0a11`
(gemini-embed-001). RouterAI billed $0. Degeneracy
`s5-degeneracy-20260907T175009Z-f5accf8a`: 28/28 labelled (T=0.3 lock);
rows not filtered.

## F4 last-band replication (do not replace archival)

| space | archival | replication | sign agrees |
| --- | --- | --- | --- |
| bge-m3 | 0.201 [0.065, 0.332] | 0.208 [0.091, 0.314] | yes |
| qwen3-embed-8b | 0.390 [0.151, 0.593] | 0.400 [0.221, 0.590] | yes |
| gemini-embed-001 | 0.150 [0.029, 0.266] | 0.152 [0.073, 0.239] | yes |

Last band is 12. Because four domain trajectories have 47 chunks, band 12
has `n_within_pairs=6` and `n_between_pairs=114` (16 of 20 domain trajs).
Band 10 still has the full 80/1440 pair set and also excludes 0; it is not
Canonical tables: this directory. TMLR copies of headline CSVs:
`artifacts/tmlr-correctness/occupancy-replication/`.
Do not overwrite `artifacts/stage-5/occupancy/` or `artifacts/stage-6/occupancy/`.
