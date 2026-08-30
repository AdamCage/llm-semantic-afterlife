# Related work and novelty positioning

Living document. Every entry carries a **verification status**, because
project-scoping notes contained references that have not yet been checked
against the actual literature, and an unverified citation in a submission is
worse than a missing one.

| Status | Meaning |
| --- | --- |
| `VERIFIED` | fetched, read, delta stated |
| `LEAD` | identifier recorded during scoping, **not yet verified** — do not cite |
| `REJECTED` | checked and not relevant / does not exist as described |

**Rule:** nothing enters `paper/` while still marked `LEAD`. Verification is a
Stage 1 task (it needs no API budget and de-risks the framing early).

---

## 1. Adjacent lines of work

### 1.1 LLMs as Markov chains / stochastic processes

- `LEAD` — *Large Language Models as Markov Chains*, arXiv:2410.02724.
  Recorded during scoping as providing a formalisation of an LLM with finite
  context as a Markov chain, including stationary-distribution results.
  **Why it matters to us:** it is the theoretical frame for our state
  `X_t ∈ V^W` and recursion `X_{t+1} = Tail_W(X_t ⊕ Y_t)`. If it says what the
  notes claim, we cite it as the theory our empirical work sits on top of, and
  we must not re-derive it as if novel.
  **Our delta:** they characterise the chain; we measure the *approach to the
  long-run regime in semantic space*, empirically, past the eviction of the
  initial condition.

### 1.2 Successive transformation as a dynamical system

- `LEAD` — *Unveiling Attractor Cycles in Large Language Models: A Dynamical
  Systems View of Successive Paraphrasing*, ACL 2025 (`2025.acl-long.624`).
  Reported to find fixed-point and periodic attractors, including two-cycles,
  under repeated paraphrasing.
  **Our delta:** repeated paraphrasing re-feeds the *whole* previous output as a
  transformation of a fixed meaning; our process is *free continuation* with a
  finite window, where the state is a moving tail of the model's own output and
  no target meaning is preserved by construction. Their process converges by
  design pressure; ours has no such pressure.
- `LEAD` — *Markovian Generation Chains in Large Language Models*,
  arXiv:2603.11228. Reported to study repeated output→input transformation with
  recurrent state sets.
  **Our delta:** as above — transformation chains vs. windowed free-running
  continuation.

### 1.3 Attractors in multi-turn conversation

- `LEAD` — *Attractor States Emerge in Multi-Turn LLM Conversations*,
  arXiv:2606.30571. Reported to show model-specific attractors in long LLM↔LLM
  dialogue with tracking in representation space.
  **This is the closest prior work in the scoping notes and the main novelty
  risk.** If it exists as described, it establishes that attractor-like
  behaviour occurs in long LLM interaction and tracks it in representation
  space — so we cannot present either as new.
  **Our delta, stated precisely:** (i) *no interlocutor* — a single model
  continuing its own text, so there is no second policy shaping the dynamics;
  (ii) *the window is the experimental variable*, imposed rather than native,
  which lets us hold `θ` fixed and vary memory; (iii) the regime studied begins
  *after* the initial condition has physically left the state; (iv) the
  measurement suite is dynamical-systems-grade — MSD scaling exponents,
  non-reversible MSM with probability currents, Markovianity validation,
  temperature×`W` order parameters — rather than attractor identification.

### 1.4 Long-horizon agents

- `LEAD` — *The Horizon Gap: Planning, Memory, Execution, Training, and
  Evaluation for Long-Horizon LLM Agents*, arXiv:2608.06663. Recorded as a 2026
  survey naming long-horizon reliability and trajectory-level diagnostics as
  open problems.
  **Why it matters:** the applied motivation. Agents fail through drift and
  finite-context management; trajectory-level diagnostics are exactly what we
  build. Cite for motivation, not for method.

### 1.5 Methods we borrow rather than invent

- `LEAD` — *Variational approach for learning Markov processes from time series
  data* (VAMP), arXiv:1707.04659.
- `LEAD` — *Identification of kinetic order parameters for non-equilibrium
  dynamics*, arXiv:1811.12551. Recorded as recommending VAMP over tICA for
  non-equilibrium dynamics — the direct justification for our choice.
- `VERIFIED` (tooling, not a claim) — `deeptime` documents tICA as assuming
  stationary/reversible dynamics and VAMP as applicable to off-equilibrium and
  non-reversible processes; PyEMMA's tutorials define the standard MSM
  validation workflow (implied timescales, Chapman–Kolmogorov) that we follow.
  These are cited as software/methodology references.
- Leiden community detection, PCCA+ coarse-graining, recurrence quantification
  analysis: standard methods, cited to their original sources at write-up.

## 2. Where we must be careful not to overclaim

Three sentences that **cannot** appear in the paper:

- "We are the first to apply the concept of attractors to LLMs."
- "We are the first to track embeddings over the course of generation."
- "We show that LLMs have attractor states."   ← unless timescale separation is
  demonstrated; otherwise *metastable states*.

## 3. The one-sentence delta

> We study unbounded free-running autoregressive generation under an *imposed*
> finite sliding context window, and characterise the semantic dynamics of the
> regime that begins once the initial condition has been fully evicted —
> measuring memory decay, diffusion scaling, metastability and
> time-irreversibility as functions of window size, temperature and model.

If, after verification, an existing paper already occupies this sentence, the
project pivots rather than competes; candidate pivots are kept in
`docs/backlog.md`.

## 4. Verification queue

| Item | Action | Owner stage |
| --- | --- | --- |
| all `LEAD` entries above | fetch, read, confirm or reject; move to `VERIFIED`/`REJECTED` with a two-line summary and the delta | S1 |
| systematic search | arXiv/ACL/Semantic Scholar for: free-running generation, self-conditioned generation collapse, sliding-window generation dynamics, model collapse under self-consumption, degeneration in open-ended generation | S1 |
| adjacent field | text-degeneration literature (nucleus sampling, repetition), and self-consuming-loop / model-collapse work — different question, overlapping phenomenology, must be distinguished explicitly | S1 |
