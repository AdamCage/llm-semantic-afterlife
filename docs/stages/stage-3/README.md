# Stage 3

Opened 2026-09-01. Plan: [`PLAN.md`](PLAN.md). Decision:
[`ADR-0012`](../../decisions/ADR-0012-stage3-no-openrouter.md).

- **S3.0** — local `gemma-3-1b-pt` at `W = 256`, 12 turnovers. No
  OpenRouter. Embeddings deferred.
- **S3.1** — VAMP / MSM / Leiden on existing Stage 2 embeddings,
  restricted sample, both representation spaces.

Do not request scientific review while `afterlife review --stage 3`
fails.
