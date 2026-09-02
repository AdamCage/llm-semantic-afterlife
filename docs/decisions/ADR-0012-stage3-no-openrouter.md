# ADR-0012: Stage 3 opens without OpenRouter; S3.0 embeddings are deferred

Status: accepted
Date: 2026-09-01
Stage: S3
Amends: [ADR-0010](ADR-0010-stage2-findings-replan-s3.md), [ADR-0011](ADR-0011-local-base-provider.md)

## Context

Stage 3 has two independent jobs (ADR-0010):

1. **S3.0** — a local 1–3B *base* model at reduced `W` and a matched
   turnover count, so later claims are not only about instruct models
   under P1.
2. **S3.1** — VAMP / MSM / Leiden on the Stage 2 arms that actually
   reached ~12 turnovers, reported per process, never pooled.

The human opened Stage 3 with one constraint: OpenRouter balances are
empty and must not be spent. RouterAI is not used for S3.0 (the
candidate is local) and is not needed for S3.1 (the embeddings already
exist under `runs/s2/`).

S3.0 *generation* is `$0` under `api: local`. S3.0 *embedding* is not:
both representation spaces (`bge-m3`, `qwen3-embed-8b`) are hosted on
OpenRouter. Calling them now would fail or spend a zero balance.

## Decision

1. **No OpenRouter calls in this opening of Stage 3.** No hosted
   generation, no hosted embedding, no hosted audit.
2. **S3.0 runs generation + surface diagnostics only** (degeneracy,
   protocol, rates, quoted text). Geometry and seed-separation on the
   base model wait until an embedding balance exists. Until then every
   S3.1 sentence stays labelled *instruct-under-P1*.
3. **S3.1 consumes the existing Stage 2 embedding runs.** Those runs
   already paid for both spaces. Re-embedding is not a Stage 3 cost and
   is not attempted.
4. **S3.0 matrix is `local-gemma-3-1b-pt` at `W = 256`, `T = 12W`,
   `B = 32`.** The smoke (`W = 128`, two turnovers) is not S3.0. Gemma 4
   E2B stays out (ADR-0011). The reduced `W` is a CPU constraint, not a
   scientific preference; results do not transfer to `W = 4096` without
   a measurement there.

## Alternatives considered

- **Wait for OpenRouter before opening the stage.** Rejected: S3.1 and
  S3.0 generation do not need it, and the stage's blocking question
  (does a base model enter the reviewer register / a loop / silence?)
  is answerable from generated text.
- **Add a local embedding model so S3.0 can have geometry now.**
  Rejected as a mid-stage scope widening. A new representation space is
  an ADR of its own and would not be one of the two spaces the paper
  already uses.
- **Run S3.0 at `W = 4096` to match Stage 2.** Rejected on this
  hardware: 1B at `W = 4096` is a different wall-clock and memory
  regime, and ADR-0010 already accepted a reduced `W` for the existence
  check.

## Consequences

- `docs/stages/stage-3/PLAN.md` states F3 as "embeddings deferred" and
  forbids reading S3.1 as a base-model result.
- `configs/stages/stage3_local_base.yaml` lists no embedding models.
- Closing the *interpretation* of H1 / H4 on a base model remains
  blocked until S3.0 is embedded. Closing S3.1 on instruct-under-P1
  does not require that.

## Reversal cost

Low. When OpenRouter is funded, embed the S3.0 run and add geometry /
separation as a recorded follow-up pass. Do not silently rewrite this
stage's report as if those numbers existed at opening.
