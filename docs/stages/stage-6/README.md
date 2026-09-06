# Stage 6

Opened 2026-09-06. Plan: [`PLAN.md`](PLAN.md). Decision:
[`ADR-0017`](../../decisions/ADR-0017-s6-third-space-occupancy-robustness.md).

**Question.** Do S5 occupancy *signs* (F4 last-band domain gap
excludes 0; F6 twins not last-band divergent) hold in
`gemini-embed-001` on the **same** 28 trajectories?

**No generate.** Embed not authorised until human yes.

| pass | status |
| --- | --- |
| S6.0 reuse S5.1 24 + S2.2 T=0.3 four | cells exist; not re-generated |
| S6.1 `stage6_third_space.yaml` gemini embed | **blocked on embed-yes** |
| occupancy assemble, three spaces | blocked on S6.1 |

Embed-in ~2.0M tokens. Catalogue-ish **~$0.30**; S0/S5 embeds ledgered
$0. YAML refuse **$2**. `afterlife estimate` generate print is **not**
a yes.
