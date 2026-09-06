**twin_last_band** — F6 last-band twin Δ per family and pooled, both embedding spaces. divergent is the F6 verdict.

|   band | scope                           |     delta |   d_twin |   d_control |   delta_ci_low |   delta_ci_high | divergent   |   n_twin_pairs |   n_control_pairs | embedding      |
|-------:|:--------------------------------|----------:|---------:|------------:|---------------:|----------------:|:------------|---------------:|------------------:|:---------------|
|     12 | all                             |  0.02819  |   0.2968 |      0.2686 |       -0.394   |          0.4748 | False       |              4 |                 4 | bge-m3         |
|     12 | reactor-stable+reactor-unstable |  0.007719 |   0.2046 |      0.1969 |       -0.07706 |          0.0925 | False       |              2 |                 2 | bge-m3         |
|     12 | waterloo-lost+waterloo-won      |  0.04866  |   0.3889 |      0.3403 |       -0.394   |          0.4914 | False       |              2 |                 2 | bge-m3         |
|     12 | all                             |  0.02269  |   0.3917 |      0.369  |       -0.6878  |          0.6707 | False       |              4 |                 4 | qwen3-embed-8b |
|     12 | reactor-stable+reactor-unstable |  0.05391  |   0.2769 |      0.223  |       -0.09168 |          0.1995 | False       |              2 |                 2 | qwen3-embed-8b |
|     12 | waterloo-lost+waterloo-won      | -0.008544 |   0.5065 |      0.515  |       -0.6878  |          0.6707 | False       |              2 |                 2 | qwen3-embed-8b |
