**looping_rate_by_cell** — Degenerate fraction per (W, T) cell on or-qwen3-8b under P1 raw_completion, with a 95% Clopper–Pearson CI (n = 4). Degenerate = calibrated looping fraction ≥ 0.5 or late-phase shingle Jaccard labelled a textual repetition lock (threshold 0.0122). W=4096 T∈{0.3,1.0} are the reused S2.2 raw eight; they were not regenerated. Intervals at 0/4 and 4/4 are not point masses.

|    W |   temperature |   n |   n_degenerate |   rate |   ci_low |   ci_high |   n_clean | method          |
|-----:|--------------:|----:|---------------:|-------:|---------:|----------:|----------:|:----------------|
| 4096 |           0.3 |   4 |              4 |    1   |  0.3976  |    1      |         0 | clopper_pearson |
| 4096 |           0.7 |   4 |              4 |    1   |  0.3976  |    1      |         0 | clopper_pearson |
| 4096 |           1   |   4 |              4 |    1   |  0.3976  |    1      |         0 | clopper_pearson |
| 4096 |           1.5 |   4 |              0 |    0   |  0       |    0.6024 |         4 | clopper_pearson |
| 8192 |           0.3 |   4 |              4 |    1   |  0.3976  |    1      |         0 | clopper_pearson |
| 8192 |           0.7 |   4 |              4 |    1   |  0.3976  |    1      |         0 | clopper_pearson |
| 8192 |           1   |   4 |              4 |    1   |  0.3976  |    1      |         0 | clopper_pearson |
| 8192 |           1.5 |   4 |              2 |    0.5 |  0.06759 |    0.9324 |         2 | clopper_pearson |
