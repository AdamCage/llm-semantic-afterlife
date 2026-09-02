# Stage 3

Opened 2026-09-01. Closed PARTIAL and merged to `main`. Plan:
[`PLAN.md`](PLAN.md). Decision:
[`ADR-0012`](../../decisions/ADR-0012-stage3-no-openrouter.md).
Review: [`REVIEW.md`](REVIEW.md) (APPROVED WITH CHANGES).

- **S3.0** — local `gemma-3-1b-pt` at `W = 256`, 12 turnovers. No
  OpenRouter. Embeddings deferred at opening; RouterAI follow-up
  2026-09-02: [`FOLLOWUP-embed.md`](FOLLOWUP-embed.md). Geometry unrun.
- **S3.1** — VAMP / MSM / Leiden on existing Stage 2 embeddings,
  restricted sample, both representation spaces.
