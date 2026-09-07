**twin_last_band.legacy_invalid** — Quarantined F6 CI columns from twin_last_band. Not bootstrap intervals (ADR-0019 set(chosen)). Kept so the withdrawn numbers remain inspectable. Do not cite as CIs.

|   band | scope                           | embedding      |     delta |   d_twin |   d_control | divergent   |   n_twin_pairs |   n_control_pairs |   delta_ci_low |   delta_ci_high |
|-------:|:--------------------------------|:---------------|----------:|---------:|------------:|:------------|---------------:|------------------:|---------------:|----------------:|
|     12 | all                             | bge-m3         |  0.02819  |   0.2968 |      0.2686 | False       |              4 |                 4 |       -0.394   |          0.4748 |
|     12 | reactor-stable+reactor-unstable | bge-m3         |  0.007719 |   0.2046 |      0.1969 | False       |              2 |                 2 |       -0.07706 |          0.0925 |
|     12 | waterloo-lost+waterloo-won      | bge-m3         |  0.04866  |   0.3889 |      0.3403 | False       |              2 |                 2 |       -0.394   |          0.4914 |
|     12 | all                             | qwen3-embed-8b |  0.02269  |   0.3917 |      0.369  | False       |              4 |                 4 |       -0.6878  |          0.6707 |
|     12 | reactor-stable+reactor-unstable | qwen3-embed-8b |  0.05391  |   0.2769 |      0.223  | False       |              2 |                 2 |       -0.09168 |          0.1995 |
|     12 | waterloo-lost+waterloo-won      | qwen3-embed-8b | -0.008544 |   0.5065 |      0.515  | False       |              2 |                 2 |       -0.6878  |          0.6707 |
