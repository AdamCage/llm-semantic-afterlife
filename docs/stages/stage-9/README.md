# Stage 9 — Qwen Base vs Instruct at 12W

Opened 2026-09-11 on working tree `stage-8` (S9 files added after
S8 REPORT). Plan: [`PLAN.md`](PLAN.md). Handoff: [`HANDOFF.md`](HANDOFF.md).

**Question.** After full seed eviction, does local Qwen3-8B Instruct
keep a different seed-conditioned late regime than Base?

**No hosted Instruct.** No S10 until this REPORT. Native-chat generate
is deferred (PLAN E3).

| pass | status |
| --- | --- |
| S8 REPORT says protocol fit | **yes** — [`../stage-8/REPORT.md`](../stage-8/REPORT.md) |
| S9.1 Instruct NF4 40 × 12W | **COMPLETED** 38/40 |
| S9.2 Base NF4 40 × 12W | **COMPLETED** 31/40 |
| S9.3 Instruct INT8 F2 10 | **COMPLETED** 9/10 |
| S9.4 Base INT8 F2 10 | **COMPLETED** 8/10 |
| S9.5 native-chat 8 | **deferred** |
| Degeneracy | **COMPLETED** four generate runs |
| BGE-M3 local embed | **COMPLETED** |
| Hosted `qwen3-embed-8b` | **COMPLETED** (ADR-0027, $0) |
| \(G_t\) / lock / REPORT | **next** |

**Matrix (YAML wins).** 2 × 10 × 4 NF4 `raw_bytes` = 80 traj;
INT8 5 × 2 × 2 = 20. `W=4096`, `T=49152`. Configs:
[`configs/stages/stage9_qwen/`](../../../configs/stages/stage9_qwen/).

Generate + local BGE **$0**. Hosted Qwen-embed cap $5 (ADR-0027);
realised **$0**. No S10 until REPORT.
