**looping_rate_contrasts** — Newcombe 95% CI and two-sided Fisher exact p for the 4/4 lock cell (T=0.3) versus the T=1.5 cell at each W. Not a temperature law: n=4.

|    W | cell_a   | cell_b   |   k_a |   n_a |   k_b |   n_b |   diff |   ci_low |   ci_high |   fisher_p | method               |
|-----:|:---------|:---------|------:|------:|------:|------:|-------:|---------:|----------:|-----------:|:---------------------|
| 4096 | T=0.3    | T=1.5    |     4 |     4 |     0 |     4 |    1   |   0.3072 |      1    |    0.02857 | newcomb+fisher_exact |
| 8192 | T=0.3    | T=1.5    |     4 |     4 |     2 |     4 |    0.5 |  -0.1021 |      0.85 |    0.4286  | newcomb+fisher_exact |
