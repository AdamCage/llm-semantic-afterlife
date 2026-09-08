**fixed_point_rates_by_temperature** — Stage 2 model-axis repetition-lock rates split by temperature. Each cell is n=4 except or-gpt-oss-20b, which did not complete the design T. 95% Clopper–Pearson. The pooled n=8 table fixed_point_rates.csv remains; it is not a T=0.3 table.

| generator           |   temperature |   rate |   ci_low |   ci_high |   n |   n_positive | method          | k_over_n   |
|:--------------------|--------------:|-------:|---------:|----------:|----:|-------------:|:----------------|:-----------|
| or-gemma-4-31b      |           0.3 | 0      | 0        |    0.6024 |   4 |            0 | clopper_pearson | 0/4        |
| or-gemma-4-31b      |           1   | 0      | 0        |    0.6024 |   4 |            0 | clopper_pearson | 0/4        |
| or-gpt-oss-120b     |           0.3 | 1      | 0.3976   |    1      |   4 |            4 | clopper_pearson | 4/4        |
| or-gpt-oss-120b     |           1   | 1      | 0.3976   |    1      |   4 |            4 | clopper_pearson | 4/4        |
| or-gpt-oss-20b      |           0.3 | 0.25   | 0.006309 |    0.8059 |   4 |            1 | clopper_pearson | 1/4        |
| or-gpt-oss-20b      |           1   | 0.3333 | 0.008404 |    0.9057 |   3 |            1 | clopper_pearson | 1/3        |
| or-muse-glimmer-30b |           0.3 | 0.5    | 0.06759  |    0.9324 |   4 |            2 | clopper_pearson | 2/4        |
| or-muse-glimmer-30b |           1   | 0      | 0        |    0.6024 |   4 |            0 | clopper_pearson | 0/4        |
| or-qwen3-8b         |           0.3 | 0.75   | 0.1941   |    0.9937 |   4 |            3 | clopper_pearson | 3/4        |
| or-qwen3-8b         |           1   | 1      | 0.3976   |    1      |   4 |            4 | clopper_pearson | 4/4        |
