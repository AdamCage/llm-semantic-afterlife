**protocol_by_quarter** — Block fill and stop rate by trajectory-quarter (four even step bins per trajectory, then mean across trajectories in the cell). Not a run-level mean.

| cell      | generate_run_id                                     |   quarter |   n_trajectories |   n_steps |   block_fill_mean |   block_fill_min |   stop_rate_mean |
|:----------|:----------------------------------------------------|----------:|-----------------:|----------:|------------------:|-----------------:|-----------------:|
| base-int8 | s10-paperb-olmo-base-int8-20260918T050048Z-2b2cdfd8 |         1 |               10 |        69 |            0.8909 |           0.549  |          0.325   |
| base-int8 | s10-paperb-olmo-base-int8-20260918T050048Z-2b2cdfd8 |         2 |                7 |        64 |            1      |           1      |          0       |
| base-int8 | s10-paperb-olmo-base-int8-20260918T050048Z-2b2cdfd8 |         3 |                7 |        64 |            0.9986 |           0.99   |          0.1429  |
| base-int8 | s10-paperb-olmo-base-int8-20260918T050048Z-2b2cdfd8 |         4 |                7 |        64 |            0.8615 |           0.086  |          0.1905  |
| base-nf4  | s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3  |         1 |               40 |       340 |            0.8433 |           0.021  |          0.3019  |
| base-nf4  | s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3  |         2 |               28 |       326 |            1      |           1      |          0       |
| base-nf4  | s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3  |         3 |               30 |       328 |            0.9332 |           0.038  |          0.06944 |
| base-nf4  | s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3  |         4 |               28 |       325 |            0.965  |           0.019  |          0.03571 |
| dpo-nf4   | s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f   |         1 |               40 |        81 |            0.928  |           0.447  |          0.375   |
| dpo-nf4   | s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f   |         2 |               16 |        54 |            0.9534 |           0.255  |          0.0625  |
| dpo-nf4   | s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f   |         3 |               27 |        65 |            0.622  |           0.009  |          0.5926  |
| dpo-nf4   | s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f   |         4 |               11 |        48 |            0.6303 |           0.176  |          0.6364  |
| rlvr-int8 | s10-paperb-olmo-rlvr-int8-20260918T142301Z-7125ccca |         1 |               10 |        12 |            0.8855 |           0.563  |          0.5     |
| rlvr-int8 | s10-paperb-olmo-rlvr-int8-20260918T142301Z-7125ccca |         2 |                4 |         5 |            0.8183 |           0.273  |          0.25    |
| rlvr-int8 | s10-paperb-olmo-rlvr-int8-20260918T142301Z-7125ccca |         3 |                6 |         7 |            0.3898 |           0.018  |          0.8333  |
| rlvr-int8 | s10-paperb-olmo-rlvr-int8-20260918T142301Z-7125ccca |         4 |                1 |         2 |            0.964  |           0.964  |          0.5     |
| rlvr-nf4  | s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc  |         1 |               40 |        89 |            0.8345 |           0.271  |          0.475   |
| rlvr-nf4  | s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc  |         2 |               12 |        59 |            1      |           1      |          0       |
| rlvr-nf4  | s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc  |         3 |               21 |        68 |            0.62   |           0.005  |          0.5714  |
| rlvr-nf4  | s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc  |         4 |                8 |        55 |            0.7716 |           0.383  |          0.4375  |
| sft-nf4   | s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e   |         1 |               40 |       262 |            0.7887 |           0.17   |          0.4103  |
| sft-nf4   | s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e   |         2 |               22 |       241 |            0.9816 |           0.5945 |          0.02273 |
| sft-nf4   | s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e   |         3 |               27 |       247 |            0.7981 |           0.015  |          0.2593  |
| sft-nf4   | s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e   |         4 |               22 |       240 |            0.9432 |           0.143  |          0.07386 |
