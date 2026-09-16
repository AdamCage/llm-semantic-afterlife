# Stage 8 — Paper B foundations

Opened 2026-09-09 on branch `stage-8`. Plan: [`PLAN.md`](PLAN.md).
Decisions: [ADR-0023](../../decisions/ADR-0023-paper-b-local-four-family.md),
[ADR-0024](../../decisions/ADR-0024-local-nf4-lifecycle.md),
[ADR-0025](../../decisions/ADR-0025-persistence-metrics-and-horizon-ladder.md),
[ADR-0026](../../decisions/ADR-0026-seed-bank-v1-rationale-not-identification.md).

**Question.** Can the local P1 path load ten NF4 checkpoints, emit 32
new tokens each, and unload — without a 12W generate and without
hosted spend?

**No scientific claims.** \(G_t\), lock, and post-training Δ are S9+.
Frozen later order: **S9 Qwen → S10 OLMo → S11 Ministral+Gemma → S12
horizon → S13**.

Wave 0 hardware / model-card census lives in [`CENSUS.md`](CENSUS.md)
when a sibling writes it. Do not invent those numbers here. Do not
overwrite that file from this kickoff.

| pass | status |
| --- | --- |
| S8.0 Wave 0 census (`CENSUS.md`) | present |
| S8.1 Wave 1 harness (NF4 / unload / serialize / local embed / persistence) | done |
| S8.2 smoke 10 × 32 tok | **done** — [`SMOKE.md`](SMOKE.md) |
| S8.3 Wave 2 microbench 2 turnovers × 4 heads | **3/4** (Gemma IT empty-completion at `W=4096`) |
| S8.4 ruff / mypy / pytest on Wave 1 + loader tests | Wave 1 + new architecture tests green |
| S8 REPORT | **drafted** — [`REPORT.md`](REPORT.md); protocol fit for S9 Qwen |
| S9 12W | **opened** 2026-09-11 — see [`../stage-9/`](../stage-9/) |

**Matrix (YAML wins).** 10 NF4 slugs × `physics` × `s1` × `W=B=T=32` =
10 trajectories, 320 generated tokens, `$0`. INT8 twins are in the
library, not in this smoke. Config:
[`configs/stages/stage8_paperb_foundations.yaml`](../../../configs/stages/stage8_paperb_foundations.yaml).

Budget **$0 API**. Do not download weights until census + human yes.
Do not start S9 from this dashboard.
