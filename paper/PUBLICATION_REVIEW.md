# Publication reading — assembled manuscript

Date: 2026-11-08  
Reviewer: independent Codex subagent (`/root/review_report`)  
Gate: **PASS** (`afterlife review --stage s13`, exit 0, independently rerun after the final English and Russian wording corrections)  
Verdict: **APPROVED** for the scientific and editorial assembly described below.

## Scope

This is an internal, independent reading of [the English manuscript](main.tex)
and [its Russian mirror](main.ru.tex) against the existing computational record.
It is not external peer review, a prediction of venue acceptance, or a claim
that the mechanical gate establishes scientific validity. No new trajectories,
embeddings, estimators, or statistical analyses were produced for this review.
Closed stage reports and published artifact values were not rewritten.

The reading covered the abstract, methods, results, captions, limitations,
discussion, and reproducibility statement. It checked that the Russian text
preserves the English distinctions between completion, a textual repetition
lock, a seed-conditioned gap, and a censored escape observation. The final
stop-rate wording correctly describes a fraction of calls ending other than
by the length limit, rather than a fraction of generated tokens.

Reviewed source SHA-256 values:

| Source | SHA-256 |
| --- | --- |
| `paper/main.tex` | `dcb39644e4d8bd5a135715637abfd16ffc5a0d78bebc0d23b3ff92b8df76b37c` |
| `paper/main.ru.tex` | `7beb58be88643580944504e3a52ec7c56088aab062a7ae9aa07f40c6af3fa0e9` |

After the scientific reading, each source changed only its S12 figure include
from the published PNG to `paper/build/figures/tau_escape_s12.pdf`. Reversing
that single path substitution recovers each previously approved source hash
exactly, so scientific prose, mathematical content, and captions are unchanged.
The deterministic [figure-layout rule](figure-layout.sed) relocates the legend
in a build copy of the published SVG. An independent XML comparison recovered
the original SVG tree exactly after removing that one legend translation;
the tracked experimental artifacts have no diff. This display-only change does
not alter the scientific approval.

## Blocking findings

None remain in the reviewed scientific text. The earlier issues with the
Gemma cross-space wording, the block/EOS description, the chunk-level
lock/escape rule, abstract scope, the auxiliary archival permutation
argument, and repeated numerical provenance have been resolved. The final
Russian stop-rate translation was corrected before this approval.

## Supported claims and their scope

- The measured process is blockwise re-prompting of the model's current tail.
  Calls continue after both full blocks and early stops. A continuous native
  sliding-attention cache was not measured. The methods retain this protocol
  restriction throughout the interpretation.
- Textual repetition can be confirmed before full seed eviction and persist
  afterward. The onset statements are tied to the published
  [Qwen lock table](../artifacts/stage-9/locks/persistence_locks_all.csv),
  with the confirmation-rule floor distinguished from a newly emerging
  post-horizon phenomenon.
- The primary occupancy evidence is the **new replication**, whose last-band
  gaps are positive in the representation spaces used on that panel. For
  example, BGE-M3 is 0.208 with interval [0.091, 0.314]; the source is the
  [replication last-band table](../artifacts/occupancy-replication/domain_separation_last_band.csv).
  This supports dependence on the initial text in the measured representation,
  not recovery of original facts or preservation of meaning independently of
  style. The [missing-data record](../artifacts/occupancy-replication/missing_data.csv)
  remains visible rather than being imputed away.
- Family and checkpoint comparisons retain their own completion counts and
  conditional last-band rows. Failures remain in the planned completion
  denominators. The manuscript does not turn those comparisons into a pooled
  instruction-tuning effect or infer equivalence from equal counts. Evidence:
  the [S9](../artifacts/stage-9/generate_status/generate_status.csv),
  [S10](../artifacts/stage-10/generate_status/generate_status.csv), and
  [S11](../artifacts/stage-11/generate_status/generate_status.csv) status tables,
  and the [published family-wise gap table](../artifacts/stage-13/gt_published/gt_published.csv).
- The selected long cohort supports no confirmed escape through its common
  observed horizon. It does not estimate the frequency of entering such a
  regime, a population escape rate, a mean escape time, or permanence. The
  [S12 table](../artifacts/stage-12/tau_escape/tau_escape.data.parquet) and
  [its metadata](../artifacts/stage-12/tau_escape/tau_escape.meta.json)
  determine the count, selection limits, and clock semantics.

## Required invariants

| Invariant | Verdict | Reading and evidence |
| --- | --- | --- |
| S12 count, clock, and censoring | **PASS** | Both texts state 0/8 confirmed escapes through 4,999,168 original tokens per trajectory, counted from the first L0 token. Lock is at 0.75 turnover and censoring at 1220.5 absolute turnovers, or 1219.75 after lock. No infinite or absorbing-lock conclusion is drawn. [S12 source](../artifacts/stage-12/tau_escape/tau_escape.meta.json), [S13 copy](../artifacts/stage-13/tau_escape_s12/tau_escape_s12.meta.json). |
| Families remain separate | **PASS** | Qwen, OLMo, Ministral, and Gemma are not reduced to one frequency or averaged effect. The selected long cohort is also kept separate from the short-horizon matrix. [Family table](../artifacts/stage-13/gt_published/gt_published.csv). |
| Gemma signs are distinguished correctly | **PASS** | Gemma Base BGE-M3 is an established negative gap; its Qwen-embedding sign is not established. The text says a common cross-space sign is not established, without claiming opposite established signs or cross-space disagreement. [S11 source](../artifacts/stage-11/gt_last_band/gt_last_band.csv). |
| No attention-necessity inference | **PASS** | Neither language concludes that full attention is unnecessary. The Gemma contrast is explicitly insufficient to identify a causal role for attention layout. |
| Required validity limits are named | **PASS** | Both texts name re-prompt versus native sliding attention, representation-space and pipeline dependence, provider non-determinism, and finite trajectories. They also retain seed/style entanglement, selected-cohort conditioning, survivor composition, and quantisation limits. |
| Quantitative claims retain provenance | **PASS** | Result blocks, tables, and captions retain artifact paths and run identifiers; protocol values also cite versioned configurations or protocol records. The publication assembly copies existing measurements rather than presenting new estimates. [S13 index](../artifacts/stage-13/INDEX.md), [replication record](../artifacts/occupancy-replication/README.md). |

## Primary replication and archival evidence

The replication and the first occupancy panel are explicitly different draws.
The replication is primary evidence for the occupancy gap and has its own
generating and embedding run identifiers. The first panel's published
intervals are preserved as historical outputs; the original generating and
embedding directories are not recoverable. A seed-pair point recomputation
and leave-one-seed-out check do not restore those vector-based intervals.
This is consistent with [ADR-0021](../docs/decisions/ADR-0021-occupancy-record-not-recoverable.md)
and [ADR-0022](../docs/decisions/ADR-0022-occupancy-replication-panel.md).
The text makes neither a blanket promise of bit-exact fresh hosted generation
nor a blanket assertion that the whole research record is irreproducible.

## Explicit limits of the approval

The manuscript does not establish recovered semantic memory, a semantic-memory
half-life, validated metastable semantic states, or currents between those
states. Failure of the early state-model validation is not presented as proof
that such phenomena are absent in every regime. The temperature/window record
does not become a semantic phase-transition or scaling law. Relevant closed
evidence remains the [state-model stability table](../artifacts/stage-3/dynamics/k_stability.md)
and [clean MSD grid](../artifacts/stage-4/grid/clean_alpha_by_cell.csv).

The review accepts the published artifact estimands and uncertainty outputs
within that scope; it did not independently re-estimate their intervals or
validate a new estimator. It does not establish a universal post-training
mechanism, an architectural explanation, or a remedy for agent memory,
task completion, or long-text quality. No new research stage is required or
opened by this publication reading.

Build and visual evidence are recorded separately by the assembling agent;
they are outside this scientific-reading verdict.

## Build and rendered-page verification

Assembling agent: primary Codex agent. Date: 2026-11-08.

- `bash -n paper/compile.sh`: PASS.
- `bash paper/compile.sh all`: PASS (identified English and Russian).
- `bash paper/compile.sh anonymous`: PASS.
- `afterlife review --stage s13`: PASS on the final manuscript sources.
- Final LaTeX logs contain no overfull boxes, unresolved or multiply defined
  references, missing citations, missing glyphs, or font warnings. The build
  includes a final reference-resolution pass and refuses unresolved labels.
- Every page was rendered with Poppler. English and anonymous pages were
  visually inspected by the assembling agent. All Russian pages were also
  inspected by an independent Russian-reading subagent. The S12 legend
  overlap was resolved in the deterministic display-only build copy; the
  updated page was rechecked independently. No remaining clipping, text
  overlap, or missing Cyrillic glyphs was observed.
- English/Russian parity: all 216 inline mathematical expressions, 58
  label/reference/citation calls, 105 evidence comments, and 120 run-ID
  occurrences match in order. All cited local source and figure paths exist.
- The anonymous PDF has `Anonymous` in its author metadata and no author
  identity in extracted visible text.
- Upstream TMLR style files match the vendored source checksums. All S12
  SVG nodes are identical to the published vector source after removing
  the sole legend-placement transform.
- No experimental artifacts, experiment configurations, library code,
  stage reports, or generation scripts were modified by the assembly.
  No generation, embedding, or statistical re-estimation was run.

Final PDF hashes (these identify this build; rebuilding can change PDF
creation timestamps and therefore byte hashes):

| Release | Pages | SHA-256 |
| --- | ---: | --- |
| [`semantic-afterlife-en.pdf`](releases/semantic-afterlife-en.pdf) | 11 | `b821eeaa47a6fb8a3b1d8cc4196664b4a6aff473521b9ed3b62592b05a5bf531` |
| [`semantic-afterlife-ru.pdf`](releases/semantic-afterlife-ru.pdf) | 12 | `e7d8933e927a25eab714b22608339ec827887e84230d22c9784838bc110fbfa7` |
| [`semantic-afterlife-anonymous.pdf`](releases/semantic-afterlife-anonymous.pdf) | 11 | `dcfe3ee28b77dcfd7906a9b46a7f9cb346bcbd0d7e0ab541fed272b308379a59` |
