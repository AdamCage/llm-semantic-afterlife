**s0_determinism__openrouter** — Exact-match and similarity rates over 5 identical seeded requests per model at temperature 0.7. This number, and not an assumption, determines the reproducibility level the paper may claim.

| generator           |   n_attempts |   n_responses |   exact_match_rate |   mean_similarity |   min_similarity |   distinct_outputs | served_providers   | errors   |
|:--------------------|-------------:|--------------:|-------------------:|------------------:|-----------------:|-------------------:|:-------------------|:---------|
| or-qwen3-8b         |            5 |             5 |                0.6 |            0.8163 |           0.5664 |                  3 | Alibaba            |          |
| or-gemma-4-31b      |            5 |             5 |                0.2 |            0.6352 |           0.5349 |                  5 | Venice             |          |
| or-gpt-oss-20b      |            5 |             5 |                0.2 |            0.2408 |           0.2032 |                  5 | DeepInfra          |          |
| or-gpt-oss-120b     |            5 |             5 |                0.2 |            0.3904 |           0.3087 |                  5 | AkashML            |          |
| or-muse-glimmer-30b |            5 |             5 |                1   |            1      |           1      |                  1 | Parasail           |          |
