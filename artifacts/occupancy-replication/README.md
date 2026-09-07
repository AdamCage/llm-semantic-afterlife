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

After embed+degeneracy, tidy F4 tables go in this directory. Do not
overwrite `artifacts/stage-5/occupancy/` or `artifacts/stage-6/occupancy/`.
Sign agreement (CI excludes 0) is the claim; do not replace archival
`0.201 [0.065, 0.332]`.
