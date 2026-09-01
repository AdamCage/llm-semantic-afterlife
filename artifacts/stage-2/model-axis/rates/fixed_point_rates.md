**fixed_point_rates** — Fraction of trajectories at a textual fixed point, with a 95% bootstrap CI over trajectories. The dashed line is 0.5, the Stage 2 direction threshold (F2). A cell whose interval includes 0.5 does not decide a direction.

| generator           |   ci_low |   ci_high |   n |   n_positive |   rate |
|:--------------------|---------:|----------:|----:|-------------:|-------:|
| or-gemma-4-31b      |    0     |    0      |   8 |            0 | 0      |
| or-gpt-oss-120b     |    1     |    1      |   8 |            8 | 1      |
| or-gpt-oss-20b      |    0     |    0.5714 |   7 |            2 | 0.2857 |
| or-muse-glimmer-30b |    0     |    0.625  |   8 |            2 | 0.25   |
| or-qwen3-8b         |    0.625 |    1      |   8 |            7 | 0.875  |
