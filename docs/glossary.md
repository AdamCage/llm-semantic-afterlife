# Glossary

Single source of truth for terminology and notation. Code variable names,
figure axes, stage reports, and the manuscript all use these. Introducing a new
term means adding it here in the same commit.

## Protocol

| Term | Symbol | Definition |
| --- | --- | --- |
| sliding window | `W` | number of **generator** tokens visible to the model. Always imposed by us, never the model's native context. |
| block | `B` | tokens requested per API call. |
| stride | `S` | tokens by which the window advances per step. `S = B` throughout. |
| step | `t` (index `k`) | one API call: prompt `Tail_W`, receive ≤ `B` tokens. |
| trajectory length | `T` | total generated tokens in one trajectory, excluding the seed. |
| turnover | `R = T/W` | how many times the entire memory has been replaced. The honest measure of observation length. |
| context horizon | `t_h` | generated-token count after which no seed token remains in the window; `t_h = W − L_0`. |
| seed | — | the initial text. **Semantic seed** = its content/topic; **stochastic seed** = the integer passed to the sampler. Never abbreviate to "seed" alone in writing. |
| chunk | — | analysis unit: exactly `chunk_size` (default 1024) generator tokens, **non-overlapping**. |
| protocol P1 | — | re-prompt: send `Tail_W` as a fresh prompt each step. Primary. |
| protocol P2 | — | true sliding attention with KV eviction. Local control only. |
| continuation mechanism | — | `raw_completion` / `assistant_prefill` / `chat_instructed`. |
| forcing condition | — | `unforced` (no system prompt) vs. `fixed` (a recorded system prompt present at every step). |
| burn-in | — | discarded pre-horizon segment. Default `t < W`; sensitivity at `t < 3W`. |

## Representation

| Term | Symbol | Definition |
| --- | --- | --- |
| embedding | `z_k ∈ R^d` | representation of chunk `k` under a named embedding model. |
| representation space | — | a specific embedding model. Results must hold in ≥2 architecturally different ones. |
| semantic velocity | `d_k` | `1 − cos(z_k, z_{k+1})`. |
| semantic acceleration | — | first difference of semantic velocity. |

## Dynamics

| Term | Symbol | Definition |
| --- | --- | --- |
| MSD | `MSD(τ)` | `E_t‖z_{t+τ} − z_t‖²` on L2-normalised embeddings. |
| diffusion exponent | `α` | `MSD(τ) ∝ τ^α`. `α<1` subdiffusion/confinement, `≈1` free diffusion, `>1` directed drift. |
| lag time | `τ` | temporal offset, in chunks; always also reported in tokens. |
| microstate | `S_i` | a k-means cell in VAMP space. **Not** a semantic state. |
| macrostate | — | a validated metastable set from PCCA+ coarse-graining of the MSM. Only these may be called *semantic states*. |
| implied timescale | `t_i` | `−τ / ln|λ_i|`; must be flat in `τ` for the MSM to be usable. |
| dwell / residence time | — | expected time before leaving a macrostate. |
| probability current | `J_ij` | `π_i T_ij − π_j T_ji`. Non-zero ⇒ genuine non-equilibrium circulation. |
| semantic half-life | `T_½` | generated tokens after which half the measurable seed information is gone (see `methodology.md` §3.4). Reported in tokens and in units of `W`. |
| basin of attraction | — | set of semantic seeds whose trajectories end in a given macrostate; occupancy reported as a fraction with CI. |
| metastable | — | long-lived but not permanent. **Default word.** "Attractor" is reserved for demonstrated timescale separation; "fixed point" for demonstrated convergence. |
| degeneracy | — | collapse into repetition loops or entropy collapse. A measured dynamical state, never a filtering criterion. |

## Infrastructure

| Term | Definition |
| --- | --- |
| `run_id` | `<stage>-<slug>-<UTC timestamp>-<8 hex of config hash>`; identifies one result-producing invocation. |
| run | a directory under `runs/` with manifest, resolved config, event log, raw requests, data, status. |
| artifact | a small publication-grade output under `artifacts/`, always with tidy source data and metadata. Committed. |
| stage | `S0`…`S7`; the unit of work, with `PLAN.md` before and `REPORT.md` after. |
| ADR | append-only decision record in `docs/decisions/`. |
| ledger | `runs/_ledger/spend.jsonl`; append-only cost record and budget enforcement. |
| L1 / L2 / L3 | reproducibility levels: statistically equivalent / analysis-exact / bit-exact replay. |
| execution mode | `live` (real API) / `replay` (cache only, fails on miss) / `mock` (deterministic synthetic, free). |

## Words we do not use loosely

- **"Attractor"** — only with demonstrated timescale separation. Otherwise
  *metastable state*.
- **"Cluster"** — for geometric groupings (Leiden, k-means). Dynamical objects
  are *macrostates*.
- **"Context length"** — a property of a model. Our imposed window is `W`.
- **"Converges"** — only with a stated criterion and a CI.
- **"Semantic state"** — reserved for validated MSM macrostates.
- **"Deterministic"** — never asserted of an LLM API; we report a measured rate.
