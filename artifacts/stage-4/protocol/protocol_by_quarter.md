**protocol_by_quarter** — Block fill and stop-token rate by quarter of each trajectory, then averaged across trajectories of the same generator with a 95% bootstrap CI. Quarters are even bins over steps, not tokens: fill and stop are per-request properties, and late steps shorten when the model starts hitting stop.

| generator   |   quarter |   block_fill |   block_fill_ci_low |   block_fill_ci_high |   stop_rate |   stop_rate_ci_low |   stop_rate_ci_high |   n_trajectories |
|:------------|----------:|-------------:|--------------------:|---------------------:|------------:|-------------------:|--------------------:|-----------------:|
| or-qwen3-8b |         1 |       0.7437 |              0.6241 |               0.8465 |      0.5726 |             0.4036 |              0.7361 |               16 |
| or-qwen3-8b |         2 |       0.7571 |              0.6315 |               0.869  |      0.5977 |             0.409  |              0.79   |               16 |
| or-qwen3-8b |         3 |       0.7682 |              0.6374 |               0.8941 |      0.6136 |             0.4129 |              0.8133 |               16 |
| or-qwen3-8b |         4 |       0.7983 |              0.6722 |               0.9125 |      0.502  |             0.2993 |              0.699  |               16 |
