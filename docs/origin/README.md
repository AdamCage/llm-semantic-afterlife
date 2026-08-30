# Origin documents

Where the project came from, kept for provenance. **Not normative.**

| File | What it is |
| --- | --- |
| `scoping-conversation.ru.md` | The original Russian-language scoping discussion that produced the research idea, the model shortlist, the sizing estimates, and the embedding/clustering design. |
| `title-candidate.md` | The working title chosen during scoping. |

## How to read these

They are a record of thinking, not a specification. Where they disagree with
[`../research-plan.md`](../research-plan.md) or
[`../methodology.md`](../methodology.md), the plan and the methodology win —
they are the documents that get amended by ADRs and by stage reports.

Three specific cautions:

1. **The citations are unverified.** The scoping conversation cites several
   papers by arXiv identifier. None has been checked. They are tracked with
   status `LEAD` in [`../literature/related-work.md`](../literature/related-work.md)
   and must not enter the manuscript until verified. Treat every reference here
   as a search hint, not a fact.
2. **The sizing has been revised.** Scoping proposed `W = 32k`, `T = 1M` as the
   main experimental standard. That remains the headline target, but the pilot
   runs at `W = 8k` because under the re-prompt protocol the input cost scales as
   `T·W/S` — see [`ADR-0004`](../decisions/ADR-0004-pilot-window-and-cost-law.md).
3. **The method has been sharpened.** Scoping proposed tICA; we use VAMP as
   primary because tICA presumes reversible dynamics
   ([`ADR-0002`](../decisions/ADR-0002-vamp-over-tica.md)). Scoping also did not
   distinguish re-prompting from true sliding attention; that distinction is now
   explicit ([`ADR-0001`](../decisions/ADR-0001-reprompt-window-protocol.md)).
