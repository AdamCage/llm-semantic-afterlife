# Stage 11 — Ministral replication + Gemma generalization at 12W

Opened 2026-09-19 after Stage 10 `--no-ff` close. Plan:
[`PLAN.md`](PLAN.md). Report: [`REPORT.md`](REPORT.md).

**Question.** Does local Ministral 3 8B replicate the sign of the
S9 Qwen completer pair at 12W, and does Gemma 4 12B show an
identified positive last-band gap at all?

**Status.** Closed 2026-09-26. Review **APPROVED WITH CHANGES**;
phrase blocker applied. Human authorised the next stage.

| pass | status |
| --- | --- |
| S11.1 Ministral Base NF4 | **40/40** `…5896956b` |
| S11.2 Ministral Instruct NF4 | **40/40** `…a3093ea2` |
| S11.3 Gemma Base NF4 | **38/40** `…6cae9981` |
| S11.4 Gemma IT NF4 | **0/40** `…3b5b9427` FAILED empty-completion, kept |
| S11.5 native-chat | **deferred** |
| Degeneracy, BGE, hosted Qwen-embed, persistence | **done** 2026-09-23T07:35:12Z |
| REPORT | written; E2/E5 PARTIAL |

Headline: Ministral last-band \(G_t>0\) in both spaces, completion
40/40 both rungs, Instruct escape 4/40. Gemma positive gap did not
replicate: Base BGE is an identified negative, the Qwen-embed sign
is not established, IT is 0/40.

Do not pool with S9 Qwen or S10 OLMo. Generate + local BGE **$0**.
Hosted Qwen-embed **$0.00** / cap $5. Project **$10.54 / $200**.
