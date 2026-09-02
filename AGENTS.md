# AGENTS.md — operating contract for agents working on this repository

This repository produces **one deliverable**: a peer-reviewable paper,
*Semantic Afterlife: Long-Run Dynamics of Large Language Models Beyond the
Context Horizon*, plus the reproducible computational record that backs every
number in it.

Everything in this file exists to serve that deliverable. The harness is a
tool, not a product. If a rule here starts costing more than it saves, open an
ADR and change it — do not silently work around it.

---

## 1. The research question, in one paragraph

A language model with context window `W` generates text forever. Its state is
the last `W` tokens; each step it emits a block and the oldest tokens fall out.
After roughly `W` tokens the original prompt is *physically gone* from the
model's input. We ask what the semantic trajectory does after that horizon:
does it retain information about the seed (self-sustaining semantic memory),
converge to model-specific attractors, or diffuse. We measure it as a
stochastic dynamical system — semantic half-life, mean squared displacement,
metastable states, non-reversible transition currents — not as a picture of
embeddings.

Formally, with `X_t ∈ V^W`, `Y_t ~ P_θ(· | X_t)`, `X_{t+1} = Tail_W(X_t ⊕ Y_t)`.

Read `docs/research-plan.md` before doing anything substantive.
Read `docs/methodology.md` before touching generation or analysis code.

---

## 2. Non-negotiables

These five rules are what makes the output publishable. Violating any of them
invalidates the affected result, and a reviewer will find it.

1. **No number without a run.** Every figure, table, and claim traces to a
   `run_id` under `runs/<run_id>/` containing a manifest, the config that
   produced it, and logs. If you cannot name the `run_id`, the number does not
   exist yet.
2. **Reproducible by construction.** A run is defined entirely by
   `configs/**` + code at a git SHA + a random seed. No interactive state, no
   notebook-only results, no hand-edited outputs. `afterlife reproduce <run_id>`
   must be able to re-derive it.
3. **Log more than feels reasonable.** Raw request/response bodies, token
   accounting, timings, cost, provider identity and quantization, retries,
   tokenizer round-trip checks. Logs are append-only JSONL. Disk is cheap;
   a rerun of a 20M-token generation is not.
4. **Artifacts are self-contained.** A figure ships with the tidy data that
   produced it and a caption that states what it shows and what it does not.
   Someone opening `artifacts/stage-N/` with no other context must understand
   the result.
5. **Analysis happens in the original high-dimensional space.** UMAP/t-SNE are
   *illustrations only* and must be labelled as such. Never a cluster count,
   never a statistical claim, from a 2-D projection.

---

## 2a. Roles, and the gate between them

Work is split between two roles, with a machine gate in the middle. Full contract
in `.cursor/rules/70-roles-and-branches.mdc`; skills: `stage-execute`,
`stage-review`.

**Executor** carries out a stage's planned computations, produces artifacts, and
keeps tests and the gate green. **Supervisor** decides whether the results mean
what the report says — and deliberately does *not* re-derive anything the gate
already checks.

```bash
afterlife review --stage N     # exit 0 = ready for scientific review
```

The gate checks what is objectively decidable: plan present with pre-registered
predictions, runs complete, output hashes intact, artifact bundles
self-contained, degeneracy labelled wherever confinement is claimed, budget
reconciled, report scoring its own predictions, no unverified citations in the
manuscript.

The supervisor's attention goes to what no tool can decide: whether the
conclusion follows, whether each threshold is calibrated rather than guessed,
whether a measurement was taken in the regime it is applied to, whether a claim
is generalised from one instance, whether every confound is named, and whether a
negative result is being softened.

**Never request review while the gate fails.** It spends the expensive reviewer
on work a tool already did.

## 3. Stage discipline

Work proceeds strictly stage by stage. Stages are defined in
`docs/research-plan.md`; each has an ID (`S0`…`S7`), entry criteria, planned
computations, exit criteria, and a budget.

```
branch  ->  plan  ->  execute  ->  produce artifacts  ->  write stage report
        ->  pass the gate  ->  scientific review  ->  merge  ->  re-plan
```

**Each stage lives on its own branch**, cut from `main`, merged back with
`--no-ff` when the stage closes, then deleted. The merge commit is the record of
the stage as a unit of work. Stage branches are never rebased once pushed: the
order in which things were tried, including the mistakes, is evidence. One stage
branch open at a time.

Project infrastructure that is not a stage result — harness changes, analysis
modules several stages need, tooling fixes — goes to `main` directly rather than
being held hostage to a stage.

Rules:

- **Never start stage N+1 before `docs/stages/stage-N/REPORT.md` exists** and
  its exit criteria are explicitly marked pass / fail / partial.
- A stage report that says "the hypothesis did not hold" is a **successful**
  stage. Negative results reshape the plan; they do not get buried.
- If reality contradicts the plan, **amend the plan in the same commit** as the
  finding, with an ADR in `docs/decisions/` explaining the change. The plan is
  a living document with a git history, not a prophecy.
- Do not widen a stage's scope mid-flight. Park the idea in
  `docs/backlog.md` and finish the stage.

---

## 4. Repository map

```
AGENTS.md                  this contract
README.md / README.ru.md   entry point (bilingual)
configs/                   every experiment parameter, versioned YAML
  base.yaml                shared defaults
  models/                  one file per generator, with provider pinning
  embeddings/              one file per representation model
  seeds/                   semantic seed banks
  stages/                  the concrete experiment matrix per stage
docs/
  research-plan.md(.ru)    master plan: stages, criteria, budgets
  methodology.md           formal protocol + measurement definitions
  stages/stage-N/          PLAN.md, REPORT.md, findings
  decisions/               ADR-NNNN-*.md, append-only decision log
  literature/              related work, novelty positioning
  glossary.md              exact meaning of every term we use
  risks.md                 methodological traps and their mitigations
  backlog.md               parked ideas
src/semantic_afterlife/    the library (see §5)
scripts/                   thin stage entry points; logic lives in src/
tests/                     unit + property + replay tests
runs/                      RAW OUTPUT, git-ignored, one dir per run_id
artifacts/                 SMALL PUBLICATION-GRADE OUTPUT, committed
paper/                     manuscript, built last, from artifacts only
```

`runs/` is regenerable and huge → ignored. `artifacts/` is small and is the
paper's evidence base → committed. Keep that boundary sharp.

---

## 5. Library conventions

`src/semantic_afterlife/`

| Module | Responsibility |
| --- | --- |
| `config.py` | `Settings` (env) + typed experiment configs loaded from YAML |
| `paths.py` | the only place that knows directory layout |
| `logging_utils.py` | structured JSONL + rich console; `get_logger()` |
| `provenance.py` | run manifests, git SHA, env capture, content hashing |
| `ledger.py` | append-only cost/token ledger and budget enforcement |
| `providers/` | RouterAI / OpenRouter / local HF / mock clients; identical interface |
| `tokenization.py` | generator tokenizers; exact `Tail_W` arithmetic |
| `generation/` | seed bank, sliding-window engine, trajectory runner |
| `embeddings/` | representation models + content-addressed cache |
| `analysis/` | geometry, diffusion, probes, VAMP/MSM, Leiden |
| `viz/` | one theme, plotly + seaborn, multi-format export |
| `reporting/` | tidy tables and stage report assembly |
| `cli.py` | `afterlife <command>`; the only supported entry point |

Conventions:

- Typed everywhere; `mypy` clean. Pydantic models for anything crossing an
  I/O boundary.
- Pure functions for analysis; side effects confined to runners and exporters.
- No hidden globals. Config in, artifacts out.
- New knob ⇒ it goes in a config file, never a literal in a function body.
- Randomness only through an explicitly passed seed. No bare `np.random.*`.

---

## 6. Running things

```bash
uv sync                                  # core env
uv sync --extra dynamics --extra dev     # + Stage 3 dynamics + tooling
uv sync --extra local                    # + torch/transformers for api: local (ADR-0011)

afterlife doctor                         # environment & key check, no cost
afterlife audit providers                # capability/pricing audit (cheap)
afterlife audit determinism --model M    # seed-reproducibility measurement
afterlife estimate --config configs/stages/stage1_pilot.yaml   # cost forecast
afterlife generate --config <cfg>        # produce trajectories
afterlife embed --run <run_id>           # embed chunks
afterlife analyze degeneracy --run <id>  # repetition/entropy; run BEFORE geometry
afterlife analyze geometry --run <id>    # displacement, MSD, recurrence
afterlife analyze separation --run <id>  # does seed identity outlive the horizon
afterlife report --stage N               # assemble stage artifacts + report
afterlife review --stage N               # mechanical gate before review
afterlife verify --stage N               # run status + output integrity
afterlife compare <run_a> <run_b>        # scientific-content diff between runs
afterlife reproduce <run_id>             # re-derive and diff against original
afterlife ledger                         # spend by kind

python scripts/summarise_run.py <id>     # protocol diagnostics per model
python scripts/calibrate_degeneracy.py   # re-derive the degeneracy threshold
python scripts/probe_endpoints.py <m>    # which endpoints actually serve
```

Run `analyze degeneracy` before reading any geometry. A looping trajectory
occupies one point in representation space and will report a confined MSD for
reasons that have nothing to do with semantics; this project drew that wrong
conclusion once already.

**Cost safety.** Anything that spends money must (a) print an estimate and the
remaining budget, (b) refuse to exceed `AFTERLIFE_BUDGET_USD_PER_RUN` /
`AFTERLIFE_BUDGET_USD_TOTAL`, (c) append to `runs/_ledger/spend.jsonl`.
Never bypass the ledger. Never raise a budget ceiling on your own initiative —
ask the human.

**Before a large generation run**, always: `afterlife estimate` → report the
number to the human → wait for confirmation.

---

## 7. Visualisation standard

Figures are a primary output of this project, not decoration.

- **Plotly** for interactive and for anything a reader may want to explore
  (trajectories, phase portraits, transition graphs, recurrence plots).
- **Seaborn/Matplotlib** for print-quality statistical panels going into the
  paper (distributions, regressions, faceted comparisons).
- Every figure exports as `.html` (plotly), `.png` @ 200 dpi, `.svg`,
  **plus** `<name>.data.parquet` — the exact tidy frame plotted — **plus**
  `<name>.meta.json` with `run_id`s, git SHA, and the caption.
- One theme, from `viz/theme.py`. No per-figure colour improvisation.
  Colour-blind-safe palette; perceptually uniform continuous maps.
- Axes labelled with units. Uncertainty shown wherever it exists (CI bands,
  bootstrap, error bars). A point estimate with no spread is a red flag.
- Figures never render an axis label of the form `component 1` without saying
  what the component *is*.

---

## 8. Writing the paper

The manuscript is written **after** the stages, from artifacts. While stages
are running you may accumulate `paper/notes/` — claims, phrasings, related
work — but not prose in `paper/main.tex`.

When writing: every claim carries a pointer to an artifact path. Reviewer-bait
gets pre-empted in a limitations section that names the real weaknesses
(re-prompt vs. true sliding attention, embedding-space dependence, provider
non-determinism, finite trajectory length).

---

## 9. Working style with the human

- The human's working language is Russian; repository content is English, with
  Russian mirrors for `README` and the research plan. Chat in Russian.
- Ask before: spending money above a stage budget, changing a
  non-negotiable, dropping a planned experiment, or committing anything into
  `paper/main.tex`.
- Don't ask before: writing code, refactoring, adding tests, producing
  artifacts, or amending a plan with an ADR.
- Report findings, not activity. "Half-life is 3.4W for Qwen3-8B at T=0.7,
  see `artifacts/stage-2/half_life/`" beats "I ran the analysis."

---

## 10. Definition of done, per stage

- [ ] `docs/stages/stage-N/PLAN.md` written before execution
- [ ] every planned computation has a `run_id` with a complete manifest
- [ ] `artifacts/stage-N/` populated: figures + tidy data + tables + captions
- [ ] `docs/stages/stage-N/REPORT.md` with results, exit criteria verdict,
      surprises, and threats to validity
- [ ] the master plan updated for stage N+1
- [ ] tests still green; `ruff` and `mypy` clean
- [ ] spend reconciled in `runs/_ledger/spend.jsonl`
