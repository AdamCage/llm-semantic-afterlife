# Stage 9 — Qwen Base vs Instruct at 12W

Opened 2026-09-11 on working tree `stage-8`. Plan:
[`PLAN.md`](PLAN.md). Report: [`REPORT.md`](REPORT.md).
Handoff: [`HANDOFF.md`](HANDOFF.md).

**Question.** After full seed eviction, does local Qwen3-8B Instruct
keep a different seed-conditioned late regime than Base?

**Status.** Closed 2026-09-16. Review **APPROVED WITH CHANGES**;
phrase blockers applied. Human `--no-ff`. S10 is a new branch.

| pass | status |
| --- | --- |
| S8 REPORT says protocol fit | **yes** |
| S9.1 Instruct NF4 40 × 12W | **COMPLETED** 38/40 |
| S9.2 Base NF4 40 × 12W | **COMPLETED** 31/40 |
| S9.3 Instruct INT8 F2 10 | **COMPLETED** 9/10 |
| S9.4 Base INT8 F2 10 | **COMPLETED** 8/10 |
| S9.5 native-chat 8 | **deferred** |
| Degeneracy | **COMPLETED** four generate runs |
| BGE-M3 local embed | **COMPLETED** |
| Hosted `qwen3-embed-8b` | **COMPLETED** (ADR-0027, $0) |
| \(G_t\) / lock | **COMPLETED** 8/8 persistence runs |
| REPORT | **APPROVED WITH CHANGES** — phrase blockers applied |

Headline (two estimands): completer P8 Base≈Instruct (early-onset
repetition lock, no escape, late-window \(G_t>0\) = register /
loop-family separation); completion worse on Base (9/40 vs 2/40).

Generate + local BGE **$0**. Hosted Qwen-embed cap $5; realised **$0**.
