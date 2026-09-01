**protocol_by_quarter** — Block fill and stop-token rate by quarter of each trajectory, then averaged across trajectories of the same generator with a 95% bootstrap CI. Quarters are even bins over steps, not tokens: fill and stop are per-request properties, and late steps shorten when the model starts hitting stop.

| generator           |   quarter |   block_fill |   block_fill_ci_low |   block_fill_ci_high |   stop_rate |   stop_rate_ci_low |   stop_rate_ci_high |   n_trajectories |
|:--------------------|----------:|-------------:|--------------------:|---------------------:|------------:|-------------------:|--------------------:|-----------------:|
| or-gemma-4-31b      |         1 |       0.2153 |             0.1399  |               0.313  |    0.9892   |             0.9772 |             1       |                8 |
| or-gemma-4-31b      |         2 |       0.1762 |             0.08085 |               0.2847 |    0.9459   |             0.8801 |             0.9957  |                8 |
| or-gemma-4-31b      |         3 |       0.2078 |             0.06495 |               0.3738 |    0.8511   |             0.6525 |             0.9942  |                8 |
| or-gemma-4-31b      |         4 |       0.2727 |             0.132   |               0.4934 |    0.8267   |             0.5809 |             0.9678  |                8 |
| or-gpt-oss-120b     |         1 |       0.9944 |             0.9831  |               1      |    0.009615 |             0      |             0.02885 |                8 |
| or-gpt-oss-120b     |         2 |       1      |             1       |               1      |    0        |             0      |             0       |                8 |
| or-gpt-oss-120b     |         3 |       0.9953 |             0.9859  |               1      |    0.009615 |             0      |             0.02885 |                8 |
| or-gpt-oss-120b     |         4 |       1      |             1       |               1      |    0        |             0      |             0       |                8 |
| or-gpt-oss-20b      |         1 |       0.9756 |             0.9269  |               1      |    0.125    |             0      |             0.375   |                8 |
| or-gpt-oss-20b      |         2 |       0.9214 |             0.7643  |               1      |    0.1429   |             0      |             0.4286  |                7 |
| or-gpt-oss-20b      |         3 |       0.7203 |             0.4394  |               1      |    0.2857   |             0      |             0.7143  |                7 |
| or-gpt-oss-20b      |         4 |       0.5043 |             0.2732  |               0.7035 |    0.7667   |             0.5    |             1       |                5 |
| or-muse-glimmer-30b |         1 |       0.9947 |             0.984   |               1      |    0.03125  |             0      |             0.09375 |                8 |
| or-muse-glimmer-30b |         2 |       0.8876 |             0.6628  |               1      |    0.2      |             0      |             0.6     |                5 |
| or-muse-glimmer-30b |         3 |       0.6956 |             0.4042  |               0.9483 |    0.5      |             0.125  |             0.875   |                8 |
| or-muse-glimmer-30b |         4 |       0.6959 |             0.3917  |               1      |    0.4167   |             0      |             0.8333  |                4 |
| or-qwen3-8b         |         1 |       0.829  |             0.7035  |               0.9495 |    0.4403   |             0.2083 |             0.6851  |                8 |
| or-qwen3-8b         |         2 |       0.7642 |             0.6072  |               0.904  |    0.6667   |             0.3333 |             1       |                8 |
| or-qwen3-8b         |         3 |       0.7401 |             0.5678  |               0.9057 |    0.5625   |             0.25   |             0.875   |                8 |
| or-qwen3-8b         |         4 |       0.6453 |             0.4551  |               0.8481 |    0.5967   |             0.245  |             0.8696  |                8 |
