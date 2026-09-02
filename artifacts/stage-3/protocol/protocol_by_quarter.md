**protocol_by_quarter** — Block fill and stop-token rate by quarter of each trajectory, then averaged across trajectories of the same generator with a 95% bootstrap CI. Quarters are even bins over steps, not tokens: fill and stop are per-request properties, and late steps shorten when the model starts hitting stop.

| generator           |   quarter |   block_fill |   block_fill_ci_low |   block_fill_ci_high |   stop_rate |   stop_rate_ci_low |   stop_rate_ci_high |   n_trajectories |
|:--------------------|----------:|-------------:|--------------------:|---------------------:|------------:|-------------------:|--------------------:|-----------------:|
| local-gemma-3-1b-pt |         1 |       0.9992 |              0.9977 |                    1 |    0.005    |                  0 |             0.015   |                8 |
| local-gemma-3-1b-pt |         2 |       0.9992 |              0.9976 |                    1 |    0.005208 |                  0 |             0.01562 |                8 |
| local-gemma-3-1b-pt |         3 |       0.9974 |              0.9928 |                    1 |    0.01042  |                  0 |             0.02604 |                8 |
| local-gemma-3-1b-pt |         4 |       1      |              1      |                    1 |    0        |                  0 |             0       |                8 |
