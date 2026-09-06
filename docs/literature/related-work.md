# Related work and novelty positioning

Living document. Every entry carries a **verification status**, because the
project-scoping notes contained references that had not been checked, and an
unverified citation in a submission is worse than a missing one.

| Status | Meaning |
| --- | --- |
| VERIFIED | fetched, read, delta stated |
| unverified | identifier recorded during scoping, not yet verified — do not cite |
| REJECTED | checked and not relevant / does not exist as described |

**Verification pass completed 2026-08-30.** All seven scoping citations exist and
say what the notes claimed — but three of them say *more* than the notes
recorded, in ways that change our framing. Those changes are flagged below.

---

## 1. The theoretical frame

### `VERIFIED` Zekri et al., *Large Language Models as Markov Chains*, arXiv:2410.02724

Draws an equivalence between an autoregressive LM with vocabulary `T` and context
window `K` and a Markov chain on a finite state space of size `O(T^K)`. Proves
the chain is an **ergodic unichain with a unique stationary distribution**,
derives its convergence rate and the influence of temperature on that rate, and
relates the formalism to pathological behaviour — repetition, incoherence at high
temperature. Validated on Llama and Gemma families.

**This is the frame our state `X_t ∈ V^W` sits in, and it constrains how we may
phrase H1.** The scoping notes recorded only "formalisation exists". What they
missed matters:

- A **unique** stationary distribution is proved to exist. So we must not claim
  "multiple attractors" in the sense of multiple stationary distributions — that
  would contradict established theory, and a reviewer will say so.
- Our H1 is nonetheless compatible with it: **metastability is about timescale
  separation on the way to the stationary distribution**, not about several
  stationary distributions. A unichain can have long-lived almost-invariant sets
  whose escape times exceed any feasible observation window. That is exactly what
  an MSM macrostate decomposition measures.
- Consequence for wording: our claim is about the *structure of the approach* to
  the stationary regime and the *timescales* involved, and about the fact that
  those timescales exceed the observation horizon. Phrasing it as "the model has
  several stationary states" would be wrong.
- Their temperature result is a direct predecessor to our H5, so H5 must be
  positioned as an empirical, semantic-space counterpart to their theoretical
  convergence-rate result, not as a new discovery that temperature matters.

**Our delta:** they characterise the chain and its asymptotics analytically in
token space; we measure the *approach* empirically in semantic space, past the
eviction of the initial condition, as a function of an imposed `W`.

## 2. Iterated-transformation dynamics — the closest work by mechanism

### `VERIFIED` Wang, Li, Yan, Cheng, Zhang, *Unveiling Attractor Cycles in Large Language Models: A Dynamical Systems View of Successive Paraphrasing*, ACL 2025 (`2025.acl-long.624`, pp. 12740–12755; arXiv:2502.15208)

Frames successive paraphrasing as a discrete dynamical system `P: T → T` and
finds convergence to **low-order limit cycles, characteristically 2-period**:
each paraphrase resembles the one two steps earlier. Measured with normalised
Levenshtein distance. Attributed to self-reinforcement — the model amplifies
textual forms it already favours. Robust across models, languages, text types,
prompts, **and increasing temperature**; they propose maximum-perplexity
selection as an intervention.

**The temperature robustness is a problem for our H5 and we should say so up
front.** They found cycles that temperature does not break. We predict a
temperature-driven confinement→diffusion transition. Either the regimes differ
(meaning-preserving transformation versus free continuation) or our prediction is
wrong. Registering this tension before running S4 is the honest move.

**Our delta:** paraphrasing is a *meaning-preserving* map with a fixed target, so
convergence is partly by design pressure; free continuation has no such pressure
and no target. Their state is the whole previous output; ours is a sliding tail of
the model's own generation with an imposed `W`. Their metric is surface-level
(Levenshtein); ours is semantic (embedding geometry, MSM).

### `VERIFIED` Geng, Mohamed, Shang, Vazirgiannis, Poibeau, *Markovian Generation Chains in Large Language Models*, arXiv:2603.11228

Defines iterative inference where each step sees only a fixed prompt template
plus the previous output — **no prior memory**. Experiments on iterative
rephrasing and round-trip translation. Two finite-horizon behaviours: early exact
recurrence (fixed point or short cycle), or long pre-recurrence transients
producing novel surface forms. Introduces recurrence time as the key metric.
Greedy decoding accelerates recurrence; **higher temperature lengthens transients
and increases diversity**. Explicitly distinguished from training-time model
collapse (Shumailov et al.).

**Note the tension with the paraphrasing paper**: here temperature *does* extend
transients; there it did not break cycles. Two adjacent regimes, opposite
temperature effects. Our regime is a third one, which makes the comparison
interesting rather than redundant — and means neither result licenses a
prediction for ours.

**Our delta:** their state is a *complete replacement* of the text at every step
under a transformation instruction; ours is *accretion with eviction* — the state
is the last `W` tokens of a continuously growing stream, and `W` is the
experimental variable. Their recurrence is exact string matching; ours is
semantic near-recurrence in embedding space, with RQA and MSM machinery. They
have no analogue of the context horizon.

### `VERIFIED` Perez, Kovač, Léger, Colas, Molinaro, Derex, Oudeyer, Moulin-Frier, *When LLMs Play the Telephone Game: Cultural Attractors as Conceptual Tools to Evaluate LLMs in Multi-turn Settings*, ICLR 2025 (OpenReview hash `dbdea7859f1d2fc10f2c9e79b8f5ae54`; arXiv:2407.04503)

Transmission chains: each agent receives the *whole* previous text and an
instruction (`rephrase` / `take inspiration` / `continue`). Tracks toxicity,
positivity, difficulty, and length. Finds instruction-dependent attractors;
open-ended instructions attract more strongly than constrained ones.

**Our delta:** they pass the entire previous document under an instructed
transform. We pass a *finite tail* of uninstructed continuation, then
*evict the seed* and keep going for many turnovers of `W`. Their attractor
is a property of a telephone chain; ours is occupancy after prompt eviction
on a blockwise re-prompt kernel. We do not inherit their “cultural attractor”
language as a finding about our trajectories.

### `VERIFIED` Mohamed, Geng, Vazirgiannis, Shang, *LLM as a Broken Telephone: Iterative Generation Distorts Information*, ACL 2025 (`2025.acl-long.371`, pp. 7493–7509; arXiv:2502.20258)

Translation chains: distortion accumulates with iteration; temperature
increases distortion. Adjacent to Geng et al. Markovian generation chains
(same group, replacement-of-state protocol).

**Our delta:** translation is a meaning-preserving map with a target language.
Our occupancy panel is free continuation of a sliding tail with no translation
objective. Temperature in their setting lengthens distortion; our Stage 4
cell at `T=1.5`, `W=4096` is the existence of a *non-locking* regime on one
generator, not a mixing-time or distortion law.

## 2a. Surface-form degeneration — closest alternative explanation of the lock

### `VERIFIED` Holtzman, Buys, Du, Forbes, Choi, *The Curious Case of Neural Text Degeneration*, ICLR 2020 (arXiv:1904.09751)

Maximization-based decoding (beam search) yields bland, repetitive loops;
nucleus (`top-p`) sampling is proposed as a remedy. The phenomenology — a
model that “gets stuck in repetitive loops” — is the surface of our
textual repetition lock.

**Our delta:** they study decoding *within a single prompt-conditioned
generation*. We measure what happens when that generation is *fed back as
the next prompt* after the original seed has left a finite window, for many
turnovers, at fixed temperature, with a calibrated lock detector. Nucleus
sampling is not our intervention; occupancy is not a decoding-strategy
paper.

### `VERIFIED` Xu, Liu, Yan, Cai, Li, Li, *Learning to Break the Loop: Analyzing and Mitigating Repetitions for Neural Text Generation*, NeurIPS 2022 (arXiv:2206.02369)

Quantifies a **self-reinforcement** of sentence-level repetition: the more
times a sentence appears in the context, the higher the probability of
continuing it. Closest mechanistic alternative to our lock: once a high-
probability sentence is emitted, the finite tail makes copying it even
more likely.

**Our delta:** they analyse and mitigate the loop inside one generation (DITTO
training). We *keep forcing continuation past stop* on a hosted instruct
model, so the lock is the typical low-`T` occupancy of an *externally
sustained* self-conditioning process, not a claim that greedy decoding
invented repetition. Xu et al. are the alternative explanation a reviewer
should reach for; we name them rather than claiming a new degeneration
mechanism.

### `VERIFIED` Shumailov, Shumaylov, Zhao, Papernot, Anderson, Gal, *AI models collapse when trained on recursively generated data*, Nature 631:755–759 (2024), doi:10.1038/s41586-024-07566-y

Training-time collapse: recursively generated data as the *next training
set* erases distribution tails. Geng et al. already distinguish this from
runtime recurrence.

**Our delta, stated as a prohibition:** a textual repetition lock at inference
is **not** model collapse. We never retrain. Citing Shumailov is only to
keep those two words from being used interchangeably.

## 3. Attractors in multi-agent interaction — the closest work by claim

### `VERIFIED` Ko & Geiping, *Attractor States Emerge in Multi-Turn LLM Conversations*, arXiv:2606.30571

7 LLMs × 20 controversial topics, self-play versus mixed-play dyadic debates,
tracking trajectories in representation space plus discourse traits and stances.
Finds **model-specific attractor basins**: self-play settles into reproducible,
topic-independent endpoint regions. In mixed play, endpoints move along the axis
between the two models' basins, with **asymmetric influence** — Claude Haiku is a
resistant attractor (0.266 average partnerward pull) that pulls partners toward
its traits such as meta-commentary; GPT-4.1 nano is malleable (0.665). Metrics:
basin separation score, pair contraction, directional dominance.

**This is our main novelty risk, and it is real.** It establishes, in
representation space, that long LLM interaction has model-specific attractor-like
structure. We cannot present either the attractor framing or representation-space
trajectory tracking as new.

**Our delta, stated precisely:**

1. **No interlocutor.** Their dynamics are shaped by a second policy; the
   asymmetric-influence result is *about* that interaction. Ours is a single
   model conditioned only on its own output, so any structure found is a property
   of one model rather than of a pair.
2. **The window is the experimental variable.** They use the models' native
   growing conversation context. We impose `W` and vary it while holding `θ`
   fixed, which is what converts "models differ" into "memory size controls
   dynamics".
3. **The regime begins after eviction.** Their conversations retain the whole
   history within context; nothing in their setup studies what happens once the
   initial condition has physically left the state. That period is our entire
   object.
4. **Dynamics-grade measurement.** They report endpoint regions and pull
   coefficients. We report MSD scaling exponents, non-reversible MSM transition
   matrices with probability currents, Markovianity validation (implied
   timescales, Chapman–Kolmogorov), semantic half-life, and order parameters
   across `temperature × W`.
5. **A convergent detail worth citing.** Their strongest attractor trait is
   *meta-commentary*. Our own S0 audit found that suppressed reasoning traces are
   meta-commentary about the task. If our macrostate decomposition also surfaces
   a meta-textual state, their result is independent corroboration — and a reason
   to treat that state carefully rather than as an artifact.

## 4. Applied motivation

### `VERIFIED` Chen, Wang, Qu, *The Horizon Gap: Planning, Memory, Execution, Training, and Evaluation for Long-Horizon LLM Agents*, arXiv:2608.06663

Surveys 1,547 arXiv papers (2024–2026). Names the *horizon gap*: the distance
between single-step capability and reliable long-task completion, with failure
modes including "quietly drifting from the goal". Finds outcome-only signals grow
uninformative as horizon grows, and that harness engineering rather than model
capability is often the binding constraint.

**It also hands us terminology discipline we should adopt.** It disambiguates
three axes the literature routinely conflates:

| Axis | Property of | In our project |
| --- | --- | --- |
| **long-horizon** | the task — number of steps required | our turnover count `T/W` |
| **long-context** | the model — tokens attendable at once | our imposed `W` |
| **long-term memory** | the system — persistence across steps | what H2 asks about: does information persist *without* any memory system? |

Framed this way, H2 becomes sharp: we ask whether **long-term memory emerges from
long-context generation alone**, with no retrieval, no scratchpad, no memory
harness — purely because the model re-emits information faster than the window
evicts it. That is a cleaner statement of the contribution than "semantic
half-life exceeds the context window", and it connects directly to a named open
problem. Cite for motivation and framing, not for method.

## 5. Methods we borrow rather than invent

### `VERIFIED` Wu & Noé, *Variational Approach for Learning Markov Processes from Time Series Data*, arXiv:1707.04659 (J. Nonlinear Sci. 2019, doi:10.1007/s00332-019-09567-y)

Introduces VAMP. The best linear model comes from the top singular components of
the Koopman operator, giving the VAMP-`r` score family plus VAMP-E for
cross-validation. Stated explicitly: **valid for both reversible and
non-reversible processes, and for stationary and non-stationary ones.** This is
the justification ADR-0002 rests on.

**Caveat the scoping notes missed, and it changes our validation plan.** Because
VAMP works with singular values of the Koopman operator rather than eigenvalues
of a reversible transfer operator, **its singular values cannot in general be
read as relaxation timescales** (deeptime's own documentation is explicit about
this trade-off: greater generality, less interpretability). So:

- Implied timescales must be computed from the **MSM transition-matrix
  eigenvalues**, not from VAMP singular values.
- For a non-reversible transition matrix those eigenvalues may be complex;
  timescales come from `|λ_i|`, and any rotational component is itself a signal
  of circulation and should be reported rather than discarded.
- VAMP-E / VAMP-2 scores are for **feature and hyperparameter selection only**
  (choosing `n_pca`, `n_vamp`, `K`), not for timescale claims.

`methodology.md` §3.5 has been corrected accordingly.

### `VERIFIED` Identification of kinetic order parameters for non-equilibrium dynamics, arXiv:1811.12551 (doi:10.1063/1.5083627)

Develops VAMP-based dimension reduction for non-equilibrium dynamics, stating
that TICA "is only valid if the dynamics obeys detailed balance (microscopic
reversibility) and typically requires long, equilibrated trajectories", and
concluding: "**We recommend VAMP as a replacement for the less general TICA
method.**" Demonstrated on ASEP (single-file diffusion) and on a driven KcsA ion
channel. Also **extends the Chapman–Kolmogorov test to validate the Markov
property of the VAMP-reduced model**.

Directly supports ADR-0002, and the CK extension is the specific validation
procedure we should follow rather than improvising one.

### `VERIFIED` (software/methodology) `deeptime` and PyEMMA

`deeptime` documents TICA as a subclass of VAMP and VAMP as handling
time-inhomogeneous, non-reversible, and non-stationary-data cases; PyEMMA
documents the standard MSM validation workflow (implied timescales,
Chapman–Kolmogorov) that we follow. Cited as software and methodology
references. Note `scaling="kinetic_map"` if Euclidean distances in the projected
space are to approximate kinetic distances — relevant if we cluster in VAMP space.

Leiden community detection, PCCA+ coarse-graining and recurrence quantification
analysis: standard methods, cited to their original sources at write-up.

## 6. Where we must not overclaim

Sentences that **cannot** appear in the paper:

- "We are the first to apply the concept of attractors to LLMs." — Wang et al.
  2025, Ko & Geiping 2026.
- "We are the first to track embeddings over the course of generation." — Ko &
  Geiping 2026.
- "LLMs have multiple stationary distributions / multiple attractors." — Zekri
  et al. prove a **unique** stationary distribution. Say *metastable states* and
  mean timescale separation.
- "We show that temperature controls exploration." — Zekri et al. derive it
  theoretically; Geng et al. observe it; Wang et al. find cycles that survive it.
- "Runtime lock is model collapse." — Shumailov et al. is
  *training-time* recursive training. We never retrain.

## 7. The one-sentence delta

> Finite-tail self-conditioning after explicit prompt eviction, over many
> turnovers of an imposed `W`, with stochastic replicas, a post-eviction
> domain-occupancy test, and protocol diagnostics (block fill, stop,
> degeneracy). Not “we discovered attractors.”

No verified paper occupies that sentence. Telephone-game papers keep the whole
previous text and an instruction (Perez et al.; Mohamed et al.). Paraphrase
and Markovian chains replace the state under a transform (Wang et al.; Geng
et al.). Multi-agent attractors keep an interlocutor and the growing history
(Ko & Geiping). Holtzman and Xu describe in-window degeneration; Shumailov
is training-time collapse. Zekri et al. work analytically in token space.

## 8. Remaining verification queue

Telephone / degeneration / training-time collapse entries above were verified
2026-09-06 for the TMLR correctness pass (ADR-0019). Still outstanding:

| Item | Action | Owner stage |
| --- | --- | --- |
| Systematic search | arXiv/ACL/Semantic Scholar for: free-running generation, self-conditioned generation, sliding-window generation dynamics, unbounded/open-ended generation degeneration | parked with Paper B |
| Metastability estimation | PCCA+ and non-reversible MSM literature, for the estimator we actually use in S3 | S3 (closed: `validated=0`) |
| Semantic-drift measurement | existing definitions of semantic drift in generation, to avoid reinventing a metric under a new name | S2 |
