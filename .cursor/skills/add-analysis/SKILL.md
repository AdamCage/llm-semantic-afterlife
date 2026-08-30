---
name: add-analysis
description: Add a new analysis pass (a measurement over trajectories) with its artifacts, tests and CLI wiring, following this repo's reproducibility and figure standards. Use when implementing a metric such as MSD, semantic half-life, recurrence, VAMP/MSM, Leiden communities, or any new quantity that will appear in the paper.
---

# Adding an analysis pass

An analysis pass reads trajectory embeddings from `runs/`, computes a quantity,
and writes artifacts. It never calls a generation API and never mutates its
inputs.

## 1. Define the measurement on paper first

Add the quantity to `docs/methodology.md` before coding: the formula, the units,
the estimator, how uncertainty is obtained, and the known failure modes. If you
cannot write down what the number means, the code will not save you.

Decide explicitly:

- **Units of the time axis.** Generator tokens, chunks, or window turnovers
  `t/W`. Report in tokens and annotate `t/W`; those are the two the paper uses.
- **Burn-in.** Almost every long-run quantity must exclude the pre-horizon
  transient. Default is to discard `t < W` and to report sensitivity to
  discarding `t < 3W`. State which you used; never mix them silently.
- **Aggregation level.** Per-trajectory first, then across trajectories. Never
  pool chunks from different trajectories into one sample before you have
  looked at the per-trajectory spread — that is how spurious attractors are
  manufactured.
- **Uncertainty.** Bootstrap over trajectories (the independent replicate unit),
  not over chunks (which are autocorrelated by construction).

## 2. Implement as a pure function

In `src/semantic_afterlife/analysis/<name>.py`:

```python
def compute_<quantity>(
    Z: np.ndarray,              # (n_chunks, d) float32 embeddings, one trajectory
    *,
    params: <Quantity>Params,   # pydantic, sourced from config
) -> <Quantity>Result:          # dataclass with arrays + a tidy DataFrame
```

No file I/O, no logging of results, no plotting. Aggregation across
trajectories is a separate function taking a list of per-trajectory results.
This split is what lets you test the mathematics against synthetic processes.

## 3. Test against a process with a known answer

Mandatory. Examples that work well here:

- isotropic Gaussian random walk ⇒ MSD exponent `α = 1.0 ± 0.05`
- Ornstein–Uhlenbeck ⇒ MSD plateaus at `2σ²`, autocorrelation decays with the
  known rate
- two-state hidden Markov generator with known rates ⇒ MSM recovers two
  macrostates and the transition rates within CI
- a deliberately non-reversible 3-cycle ⇒ probability currents are non-zero and
  match the analytic value

If your estimator cannot recover the truth on synthetic data, it will produce a
confident wrong number on real data.

## 4. Wire the CLI and artifacts

Add a subcommand in `cli.py`:

```bash
afterlife analyze <name> --run <run_id> [--config configs/analysis/<name>.yaml]
```

It creates its own `run_id` (analysis runs are runs too: manifest, events,
integrity block), writes tidy output to `data/`, and calls figure builders in
`viz/figures.py`.

## 5. Figures

Per `.cursor/rules/30-visualization.mdc`. For a new quantity, the minimum set
is: (a) per-trajectory traces with the ensemble summary and CI band overlaid,
(b) the aggregate across the experiment matrix, faceted by model with `W` and
temperature as visual channels, (c) a diagnostic figure that would reveal the
estimator failing (residuals, fit quality, sensitivity to burn-in or `τ`).

Mark `t = W` on every time axis. Annotate fitted exponents with their CI.

## 6. Record it

Add the quantity to `docs/glossary.md` with its symbol, and mention the new pass
in the current stage's `README.md` checklist.
