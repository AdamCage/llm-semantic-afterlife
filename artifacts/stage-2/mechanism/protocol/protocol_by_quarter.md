**protocol_by_quarter** — Block fill and stop-token rate by quarter of each trajectory, then averaged across trajectories of the same generator with a 95% bootstrap CI. Quarters are even bins over steps, not tokens: fill and stop are per-request properties, and late steps shorten when the model starts hitting stop.

| generator           |   quarter |   block_fill |   block_fill_ci_low |   block_fill_ci_high |   stop_rate |   stop_rate_ci_low |   stop_rate_ci_high |   n_trajectories |
|:--------------------|----------:|-------------:|--------------------:|---------------------:|------------:|-------------------:|--------------------:|-----------------:|
| or-qwen3-8b         |         1 |       0.7041 |              0.5045 |               0.8503 |      0.5972 |             0.3963 |              0.7753 |                8 |
| or-qwen3-8b         |         2 |       0.6176 |              0.4204 |               0.8193 |      0.6737 |             0.3646 |              0.975  |                8 |
| or-qwen3-8b         |         3 |       0.6278 |              0.4348 |               0.813  |      0.6215 |             0.3391 |              0.875  |                8 |
| or-qwen3-8b         |         4 |       0.6688 |              0.4595 |               0.8598 |      0.6147 |             0.2771 |              0.8546 |                8 |
| or-qwen3-8b-prefill |         1 |       0.8694 |              0.758  |               0.9568 |      0.4793 |             0.2019 |              0.7581 |                8 |
| or-qwen3-8b-prefill |         2 |       0.922  |              0.8593 |               0.9796 |      0.4869 |             0.1667 |              0.7984 |                8 |
| or-qwen3-8b-prefill |         3 |       0.9151 |              0.8044 |               0.9869 |      0.4904 |             0.125  |              0.8462 |                8 |
| or-qwen3-8b-prefill |         4 |       0.9101 |              0.819  |               0.9713 |      0.4958 |             0.1883 |              0.8138 |                8 |
