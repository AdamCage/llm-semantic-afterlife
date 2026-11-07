# Paper B notes (S13)

Written from the assembly `s13-paperb-synthesis-20261107T085555Z-c0f6b853`. Numbers below are copies.

## Allowed

- S9–S11, read by family, are the Paper B story. Artifact: `artifacts/stage-13/gt_published/gt_published.data.parquet`.
- Gemma Base BGE last-band G_t is -0.010628 [-0.0377395, -0.00608505], ci_excludes_0 yes, an identified negative. generate_run_id `s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981`.
- Gemma Base Qwen-embed last-band G_t is 0.0141659 [-0.0208935, 0.0186512], ci_excludes_0 no. The sign is not established. generate_run_id `s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981`.
- S12 is 0 of 8 confirmed escapes through 4999168 original tokens, censored, families counted separately. Artifact: `artifacts/stage-13/tau_escape_s12/tau_escape_s12.data.parquet`. Source run ids are the eight `run_id` values in that table (8 rows).

## Do not write

- A pooled family rate, or one instruct effect.
- Permanence language banned by ADR-0025 section 3.
- The S11 necessary-condition sentence about attention on every layer.
- A claim that the two Gemma spaces have opposite established signs.
- A claim that S12 shows the lock cannot break after T_min.
- A statistic taken from a 2-D projection.

## Limitations the manuscript must name

P1 reprompt of a tail, raw_bytes, local NF4. Native sliding attention was not measured. Last-band G_t is seed-conditioned ensemble persistence in one embedding space. The two spaces are not on a common scale and are not pooled. Families are not pooled. A CI that includes 0 is not an established sign. An unidentified last-band is not a sign flip and is not drawn as zero. INT8 rows are concordance, not a third headline. Provider non-determinism was not re-measured on these horizons. L0 is finite: 12 turnovers, 49152 tokens. S12 is a separate censored count through 4999168 original tokens, not a pooled rate and not a permanence claim. Gemma Base BGE is an identified negative. The Gemma Base Qwen-embed sign is not established. Cross-space sign agreement for Gemma is not identified. Lock-table n is not the 12W completer count.
