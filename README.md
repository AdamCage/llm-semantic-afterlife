# Semantic Afterlife

**Long-run dynamics of large language models beyond the context horizon.**

[Русская версия](README.ru.md) · [Research plan](docs/research-plan.md) · [Methodology](docs/methodology.md) · [Agent contract](AGENTS.md)

---

## The question

Give a language model a sliding context window of `W` tokens and let it generate
forever. Its state is the last `W` tokens; every step, new tokens enter and the
oldest fall out. After roughly `W` generated tokens **the original prompt has
physically left the model's input**.

```
t = 0     [SEED···························]
t = k     [SEED··············][NEW][NEW]
t > W     [NEW][NEW][NEW][NEW][NEW][NEW][NEW]      ← the seed is gone
```

What happens to the semantic state of a generative system after all information
about its initial condition has been evicted from the only memory it has?

Formally, with vocabulary `V`, fixed parameters `θ`, and `Tail_W` keeping the
last `W` tokens:

$$X_t \in V^W, \qquad Y_t \sim P_\theta(\cdot \mid X_t), \qquad X_{t+1} = \mathrm{Tail}_W(X_t \oplus Y_t)$$

This is a stochastic dynamical system with finite memory. This repository
measures its long-run behaviour.

## What we measure, and why it is not "let's look at where the embeddings go"

| Quantity | Question it answers |
| --- | --- |
| **Semantic half-life** `T_½` | How many generated tokens until half the measurable information about the seed is gone? Is `T_½ > W`, i.e. does the model sustain memory through its own output faster than the window discards it? |
| **MSD scaling** `MSD(τ) ∝ τ^α` | Free diffusion (`α ≈ 1`), confinement (`α < 1`, plateau), or directed drift (`α > 1`)? |
| **Metastable macrostates** | Is there a *finite* set of semantic states, validated by implied timescales and a Chapman–Kolmogorov test — not counted off a UMAP plot? |
| **Probability currents** `J_ij` | Are transitions time-irreversible, `A → B` far likelier than `B → A`? Genuine non-equilibrium semantic circulation? |
| **`temperature × W` phase behaviour** | Is there a boundary between semantic confinement and semantic diffusion? |
| **Basins of attraction** | Which seeds end where, and does the map differ between model families? |

The central pre-registered hypothesis:

> After the initial context has been fully evicted, a freely generating LLM does
> not perform unbounded random drift through semantic space. It occupies and
> transitions between a **finite set of model-specific metastable semantic
> states.**

## How the experiment actually works

**Protocol P1 (re-prompt).** Each step sends the last `W` tokens as a fresh
prompt and receives `B` new tokens; the window slides by `S = B`. This realises
the recursion exactly over any hosted API. It is **not** identical to true
sliding attention with KV-cache eviction — positions restart each step — and
that limitation is stated in the method section rather than buried
([ADR-0001](docs/decisions/ADR-0001-reprompt-window-protocol.md)).

**`W` is imposed by us, never taken from the model.** That is what turns
"compare five models" into "hold `θ` fixed and vary memory".

**The cost law that shapes everything.** Because the whole window is re-sent
every `S` tokens:

```
input_tokens ≈ T · W / S            output_tokens ≈ T
```

At `W = 32k`, `S = 1024`, `T = 512k` that is 16.4M input tokens for 512k
output — a 32× amplification. Halving `W` and `T` together preserves the number
of window turnovers at a quarter of the cost, which is why the pilot runs at
`W = 8k` ([ADR-0004](docs/decisions/ADR-0004-pilot-window-and-cost-law.md)).

**Two representation spaces, different in kind.** Qwen3-Embedding-8B (causal
decoder) and BGE-M3 (bidirectional encoder). Agreement between them is evidence
about the generator; agreement between two decoder-derived embedders would only
be evidence about decoders.

**Two independent analysis branches.**

```
                    chunk embeddings (1024 generator tokens, non-overlapping)
                                    │
              ┌─────────────────────┴─────────────────────┐
              ↓                                           ↓
      GEOMETRY (time-blind)                     DYNAMICS (time-based)
      PCA → mutual-kNN → Leiden                 PCA → VAMP → k-means
                                                → non-reversible MSM → PCCA+
              └─────────────────────┬─────────────────────┘
                                    ↓
                      agreement (ARI / NMI) across both
                      branches and both embedding spaces
```

VAMP rather than tICA because tICA presumes reversible dynamics with detailed
balance, and autoregressive generation has an arrow of time
([ADR-0002](docs/decisions/ADR-0002-vamp-over-tica.md)).

## Non-negotiables

Five rules make the output publishable; the tooling exists to enforce them.

1. **No number without a `run_id`.** Every figure and claim traces to
   `runs/<run_id>/` with a full manifest.
2. **Reproducible by construction.** run = `configs/**` + git SHA + seed. No
   notebook-only results, no hand-edited outputs.
3. **Over-log.** Raw request/response bodies, token accounting, provider identity
   and quantization, retries, tokenizer round-trip checks — append-only JSONL.
4. **Self-contained artifacts.** Every figure ships with its tidy source data
   (`.data.parquet`), metadata (`.meta.json`), and a caption saying what it shows
   *and what it does not*.
5. **Statistics in the full space.** UMAP/t-SNE are illustrations only, always
   labelled. Never a cluster count from a 2-D projection.

LLM API determinism is never assumed. It is measured
(`afterlife audit determinism`) and reported as a rate.

## Getting started

```bash
git clone https://github.com/AdamCage/llm-semantic-afterlife
cd llm-semantic-afterlife

uv venv --python 3.11
uv pip install -e ".[dev]"                 # core + tooling
uv pip install -e ".[dev,dynamics]"        # + VAMP/MSM/Leiden, needed from Stage 3

cp .env.example .env                       # then fill in ROUTERAI_API_KEY
afterlife doctor                           # environment check, costs nothing
```

Run the whole pipeline offline first — no API key, no cost, and it catches most
bugs. The offline generator is a hidden Markov chain over five topics with a
deliberately non-reversible transition matrix, so the analysis has a known
ground truth to be checked against:

```powershell
$env:AFTERLIFE_EXECUTION_MODE="mock"
afterlife plan     --config configs/stages/stage0_smoke.yaml
afterlife generate --config configs/stages/stage0_smoke.yaml
afterlife embed    --config configs/stages/stage0_smoke.yaml --run <run_id>
afterlife analyze geometry --run <embed_run_id>
```

Then the live path:

```powershell
$env:AFTERLIFE_EXECUTION_MODE="live"
afterlife audit providers        # availability, quantization, prices — cheap
afterlife audit tokenizers       # round-trip integrity — free
afterlife audit continuation     # which continuation mechanisms work per model
afterlife audit determinism      # measured seed reproducibility
afterlife audit embeddings       # dimension, normalisation, cost
afterlife estimate --config configs/stages/stage1_pilot.yaml
```

Every command that spends money prints a forecast and the remaining budget, and
refuses to cross `AFTERLIFE_BUDGET_USD_PER_RUN` / `_TOTAL`.

## Repository layout

```
AGENTS.md          operating contract — read this before contributing
configs/           every experiment parameter, versioned YAML
  models/          generator definitions with pinned endpoints
  embeddings/      representation spaces
  seeds/           semantic seed banks
  stages/          the concrete experiment matrix per stage
docs/
  research-plan.md stages S0–S7 with entry/exit criteria and budgets
  methodology.md   the normative measurement protocol
  glossary.md      exact meaning of every term and symbol
  risks.md         methodological traps and mitigations
  decisions/       ADRs — append-only decision log
  stages/          PLAN.md before, REPORT.md after, per stage
  literature/      related work with verification status
src/semantic_afterlife/
  providers/       RouterAI / OpenRouter / offline mock, one interface
  generation/      sliding window, chunker, trajectory runner
  embeddings/      representation models + content-addressed cache
  analysis/        geometry, diffusion, probes, VAMP/MSM, Leiden
  viz/             one theme, plotly + seaborn, multi-format export
runs/              raw output, git-ignored, regenerable
artifacts/         small publication-grade output, committed
paper/             manuscript — written last, from artifacts only
```

## Stages

Work proceeds strictly stage by stage. Each has a plan written *before*
execution with pre-registered predictions, and a report written after with an
explicit `PASS`/`FAIL`/`PARTIAL` verdict per exit criterion. A stage that
falsifies its own hypothesis and says so is a stage well spent.

| Stage | Question | Status |
| --- | --- | --- |
| **S0** | Can this be run reproducibly, at what cost, and what do the providers actually do? | in progress |
| S1 | Does the phenomenon exist over ~32 window turnovers? | planned |
| S2 | Semantic half-life and diffusion scaling | planned |
| S3 | Metastability, Markov state models, representation robustness | planned |
| S4 | `temperature × W` phase portrait | planned |
| S5 | Basins of attraction; sensitivity to initial conditions | planned |
| S6 | Robustness, ablations, cross-provider replication | planned |
| S7 | Manuscript | planned |

## Novelty, stated honestly

We are **not** first to apply attractor language to LLMs, nor first to track
embeddings over generation. Adjacent work exists on successive paraphrasing as a
dynamical system, LLMs as Markov chains, and attractors in multi-turn
conversation; it is catalogued with verification status in
[`docs/literature/related-work.md`](docs/literature/related-work.md), and nothing
enters the manuscript while still unverified.

Our contribution is the specific regime:

> unbounded free-running autoregressive generation under an **imposed** finite
> sliding context window, characterising the semantic dynamics of the period that
> begins once the initial condition has been fully evicted — memory decay,
> diffusion scaling, metastability and time-irreversibility as functions of
> window size, temperature and model.

## Licence

Code: [MIT](LICENSE). Research artifacts (figures, tables, derived datasets,
stage reports, manuscript): CC BY 4.0. Generated trajectories are model outputs
and remain subject to the originating model's licence; each released bundle
carries a `PROVENANCE.md`.
