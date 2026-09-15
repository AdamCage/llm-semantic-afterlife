# Stage 8 artifacts

Harness / smoke outputs only. No \(G_t\), lock tables, or 12W
figures belong here.

- `smoke/` — Wave 2 load records. Authoritative frames:
  `smoke_10x32.parquet` and `microbench.parquet` (each with `.meta.json`).
  See [`docs/stages/stage-8/SMOKE.md`](../../docs/stages/stage-8/SMOKE.md).
  Not \(G_t\), not lock, not 12W.

Every later figure still needs tidy data + `.meta.json` + a caption
that states what it does not show. S8 should not produce scientific
figures.
