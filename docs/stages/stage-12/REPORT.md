<!-- s12-research-draft -->
# Stage 12 report

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| E1 | Eight continuation runs, each named | PASS | `artifacts/stage-12/tau_escape/tau_escape.data.parquet` |
| E2 | Comparisons use T_min | PASS | T_min = 4999168 tokens (1220.5000 turnovers) |
| E3 | Round-robin within one 48-step slice | PASS | step spread 0 |
| E4 | Estimand is tau_escape with a censoring flag | PASS | `artifacts/stage-12/tau_escape/tau_escape.meta.json` |
| E5 | No confirmed escape through T where none was observed | PASS | table column `confirmed_escape_through_tmin` |
| E6 | Every generate step served locally | PASS | `providers` column |
| E7 | F1 looping flag, N_confirm=3 | PASS | same classifier as the L0 degeneracy runs |
| E8 | L1 not run; persistence-to-lock not run; families not pooled | PASS | this report |
| E9 | Generate spend $0 | PASS | summed `cost_usd` on completed steps |

## 2. Results

Common horizon T_min = 4999168 original tokens (1220.5000 turnovers of W=4096), the shortest cell in the cohort. Clock origin is the L0 lock at 0.75 turnover, not the first continuation token. 0 of 8 cells have a confirmed escape through T_min. 8 of 8 have no confirmed escape through T_min.

| cell | run_id | status | additional tokens | tau_escape | censored | escape through T_min |
| --- | --- | --- | ---: | ---: | --- | --- |
| mb-physics-s1 | `s12-paperb-l2-mb-physics-s1-20260926T000516Z-6c25fa59` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| mb-physics-s2 | `s12-paperb-l2-mb-physics-s2-20260926T113312Z-7922c7f0` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| mb-love-s1 | `s12-paperb-l2-mb-love-s1-20260926T120115Z-87d89c22` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| mb-love-s2 | `s12-paperb-l2-mb-love-s2-20260926T122833Z-ce475f0c` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| qi-physics-s1 | `s12-paperb-l2-qi-physics-s1-20260926T125607Z-b0af1ba5` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| qi-physics-s2 | `s12-paperb-l2-qi-physics-s2-20260926T132741Z-75a4c96c` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| qi-love-s1 | `s12-paperb-l2-qi-love-s1-20260926T135816Z-c9de2297` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| qi-love-s2 | `s12-paperb-l2-qi-love-s2-20260926T140850Z-dd90cb82` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |

## 3. Prediction vs outcome

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| P1 | A majority have no confirmed escape through T_min | 0.55 | True (8/8) |
| P2 | Thinking tokens stay 0 on completed steps | 0.80 | True (sum 0) |
| P3 | An empty-completion death is kept and is not relabelled as escape | — | 0 death(s); the escape flag comes from the looping series, not from the failure |
| P4 | L2-persistence-to-lock stays closed on these two checkpoints | 0.90 | not run |

## 4. Surprises

The measured escape count is the surprise column. A majority result that misses P1 is a finding, and so is a clean no-escape result.

## 5. Threats to validity

The continuation is a reprompt of a tail, not native sliding attention. F1 is a surface-form looping flag, so a lexically varied but semantically static stretch counts as an escape. Degeneracy of the continuation is a separate run from the L0 degeneracy runs, joined only by the turnover clock. T_min censors anything after the shortest cell. Provider non-determinism was not re-measured on this horizon. Families are not pooled.

## 6. Cost

Forecast $0. Sum of per-step cost_usd = 0.0000.

## 7. Implications for the plan

S13 is not opened by this report. L1 and L2-persistence-to-lock stay closed.

## Diagnostics by segment

Block fill and stop rate by quarter of completed steps, not as a run-level mean.

### mb-physics-s1

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### mb-physics-s2

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### mb-love-s1

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### mb-love-s2

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### qi-physics-s1

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### qi-physics-s2

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### qi-love-s1

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### qi-love-s2

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

## Samples of generated text

> mb-physics-s1 early: loop is zero, and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop is zero, and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The P

> mb-physics-s1 middle: and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop is zero, and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop i

> mb-physics-s1 late: generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop is zero, and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop is zero, and the configurati

> mb-physics-s2 early: is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not 

> mb-physics-s2 middle: observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observa

> mb-physics-s2 late: trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial
