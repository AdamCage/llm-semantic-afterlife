# Stage 10 — OLMo 3 7B post-training ladder at 12W

Opened 2026-09-16 after Stage 9 `--no-ff` close. Authoritative
question, two estimands, E1–E11, and empty observed table:
[`PLAN.md`](PLAN.md). Decisions: ADR-0023–0026, ADR-0028.

If PLAN prose and YAML disagree, **YAML wins**.

**Question.** On the local OLMo 3 7B Instruct line (Base → SFT →
DPO → RLVR), at 12W P1 `raw_bytes`, do completer persistence and
completion differ across adjacent ladder edges?

**Status.** Computations complete 2026-09-18. REVIEW **APPROVED
WITH CHANGES**; two phrase blockers applied. Awaiting human
`--no-ff`. Do not start S11.

| pass | status |
| --- | --- |
| S9 closed `--no-ff` | **yes** |
| S10.1 Base NF4 40 × 12W | **27/13** `…6d7b4be3` COMPLETED |
| S10.2 SFT NF4 40 × 12W | **19/21** `…2b7b5b6e` COMPLETED |
| S10.3 DPO NF4 40 × 12W | **3/37** `…64ad9f9f` COMPLETED |
| S10.4 RLVR NF4 40 × 12W | **4/36** `…30b5b3fc` COMPLETED |
| S10.5 Base INT8 F2 10 | **5/5** `…2b2cdfd8` COMPLETED |
| S10.6 RLVR INT8 F2 10 | **0/10** `…7125ccca` FAILED (empty-completion; kept) |
| S10.7 native-chat | **deferred** |
| Degeneracy before \(G_t\) | **done** (six `s10-degeneracy-*`) |
| BGE-M3 local embed | **done** |
| Hosted `qwen3-embed-8b` | **done** (ledger $0.00) |
| \(G_t\) / lock both spaces | **done** ([`REPORT.md`](REPORT.md)) |
| Adjacent-edge table | both spaces; no sign flip |
| REPORT | written; E1/E2/E5 PARTIAL |

| File | Role |
| --- | --- |
| [`PLAN.md`](PLAN.md) | question, matrix, exit criteria, predictions |
| [`REPORT.md`](REPORT.md) | verdicts, scored predictions, threats |
| [`REVIEW.md`](REVIEW.md) | APPROVED WITH CHANGES; blockers closed |
| [`HANDOFF.md`](HANDOFF.md) | waiting on human `--no-ff` |
| [`configs/stages/stage10_olmo/`](../../../configs/stages/stage10_olmo/) | generate + embed YAML |
| [`artifacts/stage-10/`](../../../artifacts/stage-10/) | publication-grade outputs |

Do not pool with S9 Qwen. Do not start S11 from this folder.
Generate + local BGE **$0**. Hosted Qwen-embed **$0.00** / cap $5.
Project **$10.54 / $200**.
