**int8_vs_nf4** — INT8 vs NF4 last-band G_t sign on Base and RLVR (F2 seeds). Limitations, not a third headline.

| rung   | embedding      |   nf4_G |   int8_G | nf4_sign   | int8_sign   | same_sign   | nf4_run                                            | int8_run                                            |
|:-------|:---------------|--------:|---------:|:-----------|:------------|:------------|:---------------------------------------------------|:----------------------------------------------------|
| base   | local-bge-m3   | 0.09439 |  0.09823 | +          | +           | True        | s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3 | s10-paperb-olmo-base-int8-20260918T050048Z-2b2cdfd8 |
| base   | qwen3-embed-8b | 0.1891  |  0.1445  | +          | +           | True        | s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3 | s10-paperb-olmo-base-int8-20260918T050048Z-2b2cdfd8 |
