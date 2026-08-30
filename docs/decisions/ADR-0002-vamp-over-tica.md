# ADR-0002: VAMP as the primary slow-coordinate estimator; tICA as ablation

Status: accepted
Date: 2026-08-30
Stage: S0

## Context

The dynamics pipeline needs a projection onto slow coordinates before
discretisation and MSM estimation. The standard choice in molecular kinetics is
tICA. tICA's estimator presumes dynamics that are stationary and reversible —
`p(x_t=A, x_{t+τ}=B) ≈ p(x_t=B, x_{t+τ}=A)`, i.e. detailed balance.

Autoregressive generation has an arrow of time. There is no reason to expect
`A → B` to be as likely as `B → A`: a trajectory may move from exposition to
narrative to meta-commentary without the reverse ever occurring. Imposing
reversibility would not merely be inefficient — it would erase one of the
potentially most interesting findings, namely non-zero probability currents.

VAMP (variational approach for Markov processes) is formulated for
non-reversible and non-stationary processes and provides a cross-validatable
score for model selection.

## Decision

Primary dynamics pipeline:

```
E → PCA(256, projection only, no whitening) → VAMP(τ) → k-means microstates
  → MSM estimated WITHOUT imposing detailed balance → PCCA+ macrostates
```

tICA is run as an ablation with the same downstream steps. The **discrepancy**
between the tICA and VAMP solutions is reported as a diagnostic of
irreversibility, not hidden as a robustness footnote.

PCA precedes VAMP for numerical stability of the covariance estimates
(4096-dimensional embeddings against ~10^3 observations per trajectory), with
`n_pca ∈ {128, 256, 512}` sensitivity. No whitening, since VAMP performs its own
covariance normalisation.

## Alternatives considered

- **tICA as primary.** Simpler and more familiar to readers, but assumes away
  the arrow of time. Rejected on substance.
- **VAMPnets / deep TICA.** More expressive, far harder to validate, and prone
  to overfitting at ~10^3 observations per trajectory. Not justified at this
  sample size.
- **Skip the projection, cluster raw embeddings.** Loses the slow-coordinate
  structure and makes microstates dominated by high-variance, fast directions.

## Consequences

- Detailed balance is a *hypothesis to be tested*, and `J_ij = π_i T_ij −
  π_j T_ji` becomes a headline quantity rather than a check.
- MSM estimation must use a non-reversible estimator throughout; any library
  default that imposes reversibility must be explicitly overridden and the
  override tested.
- Model selection is by out-of-sample VAMP score plus implied-timescale
  flatness plus a Chapman–Kolmogorov test — three independent criteria, all
  reported.
- The `deeptime` dependency is required from Stage 3, and is therefore an
  optional extra rather than a core dependency.

## Reversal cost

Low. Both estimators run in the same pipeline; switching which is primary is a
config change and a re-run of Stage 3 analysis (compute-bound, no API cost).
