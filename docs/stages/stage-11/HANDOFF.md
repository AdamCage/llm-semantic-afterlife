# Stage 11 HANDOFF — closed

Closed 2026-09-26 after APPROVED WITH CHANGES and the phrase
blocker. Do not pool with S9 Qwen or S10 OLMo.

Headline: Ministral Base and Instruct both complete 40/40 and both
have last-band \(G_t>0\) with intervals that exclude 0 in BGE-M3
and hosted Qwen-embed. Gemma did not replicate that positive gap.
IT is 0/40 empty-completion. Confirmed escape is 0 on Ministral
Base, 4/40 on Instruct, 15/38 on Gemma Base.

Report: [`REPORT.md`](REPORT.md).

## Uncertainty to judge

- Gemma Base BGE last-band is an identified negative. The
  Qwen-embed sign is not established (0.014 [−0.021, 0.019]
  includes 0). Cross-space sign agreement is not identified. It
  is not “true on the point.”
- Gemma IT lock-table \(n=8\) is not a 12W completer set and not a
  last-band.
- P2 is false (both Ministral cells 0 empty deaths). P11 is false
  (escapes exist). Those are findings.

## Do not

- Start S12.
- Call the lock absorbing.
- Say full attention is unnecessary.
- Average Ministral with Gemma, Qwen, or OLMo.
- Write `paper/main.tex`.
