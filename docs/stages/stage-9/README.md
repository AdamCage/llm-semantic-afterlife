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
| S9.1 Instruct NF4 40 × 12W | **RUNNING** `s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6` |
| S9.2 Base NF4 40 × 12W | queued (after S9.1) |
| S9.3 Instruct INT8 F2 10 | **resumed** `s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498` |
| S9.4 Base INT8 F2 10 | queued |
| S9.5 native-chat 8 | **deferred** |
| Embed + degeneracy + \(G_t\) | not started |

**Matrix (YAML wins).** 2 × 10 × 4 NF4 `raw_bytes` = 80 traj;
INT8 5 × 2 × 2 = 20. `W=4096`, `T=49152`. Configs:
[`configs/stages/stage9_qwen/`](../../../configs/stages/stage9_qwen/).

Budget **$0 API**. Exclusive-GPU sketch **~44 h** NF4 + INT8 after.
One `afterlife generate` at a time.
