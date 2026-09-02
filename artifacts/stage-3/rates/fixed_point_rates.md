**fixed_point_rates** — Fraction of trajectories at a textual fixed point, with a 95% bootstrap CI over trajectories. The dashed line is 0.5, the Stage 2 direction threshold (F2). A cell whose interval includes 0.5 does not decide a direction.

| generator           |   temperature |   ci_low |   ci_high |   n |   n_positive |   rate |
|:--------------------|--------------:|---------:|----------:|----:|-------------:|-------:|
| local-gemma-3-1b-pt |           0.3 |        1 |         1 |   4 |            4 |      1 |
| local-gemma-3-1b-pt |           1   |        1 |         1 |   4 |            4 |      1 |
