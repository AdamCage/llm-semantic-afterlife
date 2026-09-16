# Stage 10 — OLMo 3 7B post-training ladder at 12W

Opened 2026-09-16 after Stage 9 `--no-ff` close. Authoritative
question, two estimands, E1–E11, and empty observed table:
[`PLAN.md`](PLAN.md). Decisions: ADR-0023–0026, ADR-0028.

If PLAN prose and YAML disagree, **YAML wins**.

**Question.** On the local OLMo 3 7B Instruct line (Base → SFT →
DPO → RLVR), at 12W P1 `raw_bytes`, do completer persistence and
completion differ across adjacent ladder edges?

**Status.** Kickoff. Generate **blocked** until estimate + human «да».

| pass | status |
| --- | --- |
| S9 closed `--no-ff` | **yes** |
| S10.1 Base NF4 40 × 12W | pending |
| S10.2 SFT NF4 40 × 12W | pending |
| S10.3 DPO NF4 40 × 12W | pending |
| S10.4 RLVR NF4 40 × 12W | pending |
| S10.5 Base INT8 F2 10 | pending |
| S10.6 RLVR INT8 F2 10 | pending |
| S10.7 native-chat | **deferred** |
| Degeneracy before \(G_t\) | pending |
| BGE-M3 local embed | pending |
| Hosted `qwen3-embed-8b` | pending (ADR-0028, cap $5) |
| \(G_t\) / lock both spaces | pending |
| Adjacent-edge table | pending |
| REPORT | not started |

| File | Role |
| --- | --- |
| [`PLAN.md`](PLAN.md) | question, matrix, exit criteria, predictions |
| [`HANDOFF.md`](HANDOFF.md) | next executor: generate after human «да» |
| [`configs/stages/stage10_olmo/`](../../../configs/stages/stage10_olmo/) | generate + embed YAML |
| [`artifacts/stage-10/`](../../../artifacts/stage-10/) | publication-grade outputs (empty at kickoff) |
| [`scripts/s10_run_one.sh`](../../../scripts/s10_run_one.sh) | one generate |
| [`scripts/s10_run_matrix.sh`](../../../scripts/s10_run_matrix.sh) | S10.1→S10.6 sequential |
| [`scripts/s10_embed_bge.sh`](../../../scripts/s10_embed_bge.sh) | local BGE-M3 |
| [`scripts/s10_embed_qwen_hosted.sh`](../../../scripts/s10_embed_qwen_hosted.sh) | hosted Qwen-embed |

Do not pool with S9 Qwen. Do not start S11 from this folder.
Generate + local BGE **$0** (180 traj, 8.85M output tokens).
Hosted Qwen-embed cap **$5**. Exclusive-GPU sketch **~93 h**
(OLMo Base microbench 0.517 h/traj). Project remaining
**$189.46 / $200**.
