**fixed_point_rates** — Fraction of trajectories labelled a textual repetition lock, with a 95% Clopper–Pearson CI. The dashed line is 0.5, the Stage 2 direction threshold (F2). 0/8 is [0, 0.369], not [0, 0]; 8/8 is [0.631, 1], not [1, 1].

| generator           |   ci_low |   ci_high |   n |   n_positive |   rate | method          |
|:--------------------|---------:|----------:|----:|-------------:|-------:|:----------------|
| or-gemma-4-31b      |  0       |    0.3694 |   8 |            0 | 0      | clopper_pearson |
| or-gpt-oss-120b     |  0.6306  |    1      |   8 |            8 | 1      | clopper_pearson |
| or-gpt-oss-20b      |  0.03669 |    0.7096 |   7 |            2 | 0.2857 | clopper_pearson |
| or-muse-glimmer-30b |  0.03185 |    0.6509 |   8 |            2 | 0.25   | clopper_pearson |
| or-qwen3-8b         |  0.4735  |    0.9968 |   8 |            7 | 0.875  | clopper_pearson |
