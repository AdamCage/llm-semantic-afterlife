# Stage 11 — Ministral replication + Gemma generalization at 12W

Opened 2026-09-19 after Stage 10 `--no-ff` close. Authoritative
question, two estimands, E1–E13, and empty observed table:
[`PLAN.md`](PLAN.md). Decisions: ADR-0023–0026, ADR-0029.

If PLAN prose and YAML disagree, **YAML wins**.

**Question.** Does local Ministral 3 8B replicate the *sign* of the
S9 Qwen completer pair at 12W, and does Gemma 4 12B show an
identified last-band gap at all?

**Status.** Opened. Generate not started.

| pass | status |
| --- | --- |
| S10 closed `--no-ff` | **yes** |
| S11.1 Ministral Base NF4 40 × 12W | pending |
| S11.2 Ministral Instruct NF4 40 × 12W | pending |
| S11.3 Gemma 4 12B Base NF4 40 × 12W | pending |
| S11.4 Gemma 4 12B IT NF4 40 × 12W | pending |
| S11.5 native-chat | **deferred** |
| Degeneracy before \(G_t\) | pending |
| BGE-M3 local embed | pending |
| Hosted `qwen3-embed-8b` | pending (ADR-0029, cap $5) |
| \(G_t\) / lock both spaces | pending |
| REPORT | not written |

| File | Role |
| --- | --- |
| [`PLAN.md`](PLAN.md) | question, matrix, exit criteria, predictions |
| [`HANDOFF.md`](HANDOFF.md) | operational status |
| [`configs/stages/stage11_ministral_gemma/`](../../../configs/stages/stage11_ministral_gemma/) | generate + embed YAML |
| [`artifacts/stage-11/`](../../../artifacts/stage-11/) | publication-grade outputs (after assemble) |

Do not pool with S9 Qwen or S10 OLMo. Do not start S12 from this
folder. Generate + local BGE **$0**. Hosted Qwen-embed cap **$5**.
Project **$10.54 / $200**.
