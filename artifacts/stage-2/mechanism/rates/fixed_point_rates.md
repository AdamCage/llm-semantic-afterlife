**fixed_point_rates** — Fraction of trajectories at a textual fixed point, with a 95% bootstrap CI over trajectories. The dashed line is 0.5, the Stage 2 direction threshold (F2). A cell whose interval includes 0.5 does not decide a direction.

| generator           |   ci_low |   ci_high |   n |   n_positive |   rate |
|:--------------------|---------:|----------:|----:|-------------:|-------:|
| or-qwen3-8b         |    1     |         1 |   8 |            8 |  1     |
| or-qwen3-8b-prefill |    0.625 |         1 |   8 |            7 |  0.875 |
