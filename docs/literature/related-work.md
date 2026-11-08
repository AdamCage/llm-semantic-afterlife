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

**Publication update, 2026-11-08.** The Geng et al. entry now follows the
published EMNLP Findings paper and arXiv v2 (2026-10-22). StreamingLLM is
included as a direct neighbour for finite-window operation. This is a targeted
primary-source update, not a completed systematic search or a priority claim.
The contribution statements below describe the closed computational record;
planned half-life, semantic-state, and current measurements are not results.

---

## 1. The theoretical frame

### `VERIFIED` Zekri et al., *Large Language Models as Markov Chains*, arXiv:2410.02724

Draws an equivalence between an autoregressive LM with vocabulary `T` and context
window `K` and a Markov chain on a finite state space of size `O(T^K)`. For
their positive-temperature, full-support softmax kernel, proves the chain is an
**ergodic unichain with a unique stationary distribution**,
derives its convergence rate and the influence of temperature on that rate, and
relates the formalism to pathological behaviour — repetition, incoherence at high
temperature. Validated on Llama and Gemma families.

**This is the frame our state `X_t ∈ V^W` sits in, and it constrains how we may
phrase H1.** The scoping notes recorded only "formalisation exists". What they
missed matters:

- A **unique** stationary distribution is proved for that kernel. Top-p
  truncation can assign zero mass to tokens, so the proof is not automatically
  a theorem about our sampled kernel. Neither uniqueness nor multiple
  stationary distributions has been established empirically here.
- Our H1 is nonetheless compatible with it: **metastability is about timescale
  separation on the way to the stationary distribution**, not about several
  stationary distributions. A unichain can have long-lived almost-invariant sets
  whose escape times exceed any feasible observation window. That is exactly what
  an MSM macrostate decomposition measures.
- Consequence for wording: our finite observation of repetition locks is not a
  measurement of stationarity or a validated semantic metastable state. A
  censored escape time does not establish that a lock is permanent.
- Their temperature result is a direct predecessor to our H5, so H5 must be
  positioned as an empirical, semantic-space counterpart to their theoretical
  convergence-rate result, not as a new discovery that temperature matters.

**Our delta:** they characterise the chain and its asymptotics analytically in
token space. We measure textual repetition, seed-conditioned embedding-space
gaps, completion, and censored escape after explicit seed eviction under an
imposed finite-tail re-prompt protocol. These measurements do not recover the
stationary distribution or a semantic-memory half-life.

Primary source: [paper and proof](https://arxiv.org/html/2410.02724v2).

## 2. Iterated-transformation dynamics — the closest work by mechanism

### `VERIFIED` Wang, Li, Yan, Cheng, Zhang, *Unveiling Attractor Cycles in Large Language Models: A Dynamical Systems View of Successive Paraphrasing*, ACL 2025 (`2025.acl-long.624`, pp. 12740–12755; arXiv:2502.15208)

Frames successive paraphrasing as a discrete dynamical system `P: T → T` and
finds convergence to **low-order limit cycles, characteristically 2-period**:
each paraphrase resembles the one two steps earlier. Measured with normalised
Levenshtein distance. Attributed to self-reinforcement — the model amplifies
textual forms it already favours. Robust across models, languages, text types,
prompts, **and increasing temperature**; they propose maximum-perplexity
selection as an intervention.

**Relation to the original H5.** Their cycles survive increased generation
randomness. Our pre-registered temperature-transition prediction was therefore
not licensed by their result; the closed Stage 4 record did not establish a
semantic confinement-to-diffusion boundary
([Stage 4 artifacts](../../artifacts/stage-4/INDEX.md)).

**Our delta:** their instruction asks for meaning-preserving paraphrasing of
the previous output. Our next block extends a finite tail without a recurring
transformation instruction. We report a calibrated textual-repetition flag and
an embedding-space ensemble gap; neither licenses a semantic-state claim.

### `VERIFIED` Geng, Mohamed, Shang, Vazirgiannis, Poibeau, *Markovian Generation Chains in Large Language Models*, Findings of EMNLP 2026 (`2026.findings-emnlp.2188`, pp. 46847–46865; arXiv:2603.11228v2)

Defines iterative inference where each step sees only a fixed prompt template
plus the previous output — **no prior memory**. Experiments on iterative
rephrasing and round-trip translation. Two finite-horizon behaviours: early exact
recurrence (fixed point or short cycle), or long pre-recurrence transients
producing novel surface forms. Introduces recurrence time as the key metric.
Greedy decoding accelerates recurrence; **higher temperature lengthens transients
and increases diversity**. Explicitly distinguished from training-time model
collapse (Shumailov et al.). The 2026-10-22 revision also measures lexical and
semantic drift, including BERTScore and anchor preservation, and estimates
core-and-tail transition kernels with held-out checks. It is not a
strings-only study.

**Note the tension with the paraphrasing paper**: here temperature *does* extend
transients; there it did not break cycles. Two adjacent regimes, opposite
temperature effects. Our regime is a third one, which makes the comparison
interesting rather than redundant — and means neither result licenses a
prediction for ours.

**Our delta:** their state is replaced at each step under a transformation
instruction. Ours accrues generated blocks while evicting old tokens from an
imposed tail. Our evidence concerns repetition and seed-conditioned ensemble
gaps after that explicit eviction, checkpoint and family heterogeneity, and
censored continuation of selected locks. Semantic metrics and Markov modelling
are not a novelty distinction between the papers.

Primary sources: [published record](https://aclanthology.org/2026.findings-emnlp.2188/),
[v2 methods and results](https://arxiv.org/html/2603.11228v2).

### `VERIFIED` Xiao, Tian, Chen, Han, Lewis, *Efficient Streaming Language Models with Attention Sinks*, ICLR 2024 (arXiv:2309.17453v4)

StreamingLLM studies operation beyond a fixed KV-cache window. It compares
recent-window eviction with sliding-window recomputation and retains initial
attention-sink tokens to stabilise the cache. Its long language-modelling
experiment evaluates perplexity on a concatenated external PG19 corpus through
more than four million tokens; it is not a four-million-token self-generated
trajectory.

**Our delta:** multi-million-token operation with finite memory is prior work.
We measure the model's own generated continuation after complete seed eviction,
using blockwise re-prompting rather than persistent sink KVs. The long-horizon
result is censored persistence of selected repetition locks, not an inference
efficiency improvement or evidence about native sliding attention.

Primary sources: [paper, especially sections 3 and 4.1](https://arxiv.org/html/2309.17453v4),
[publication record](https://arxiv.org/abs/2309.17453).
Bibliography key: `streamingllm2024`.

### `VERIFIED` Heng Wang, Qiu, Zhao, Qian, Yang, Han, Ji, Savarese, Heinecke, Huan Wang, *Random Attention: Rethinking KV Cache Eviction for Efficient Reasoning*, arXiv:2609.03430 (3 Sep 2026)

KV-cache eviction for long chain-of-thought. Random Attention **keeps the
prompt** and then evicts non-prompt tokens by independent uniform draws
per attention head, with no importance score. Across four models and six
reasoning tasks it matches stronger selectors at matched budget; the
authors argue the prompt is the fragile part of the cache and the
generated trace is redundant enough to survive random eviction.

**Our delta:** they *pin the prompt* and randomly drop generated reasoning
tokens under a task. We *evict the seed completely* (`t_h = W`) and watch
uninstructed continuation of the remaining tail. Their object is serving
efficiency for reasoning; ours is occupancy after the initial condition
has physically left `W`. Do not cite this paper as evidence that random
eviction preserves seed identity in our protocol — they never drop the
prompt.

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
2. **The window is imposed.** Their debate protocol has growing conversation
   history and role instructions. We define an explicit finite-tail kernel.
   Holding its window fixed in the four-family comparison does not establish a
   general window-scaling law or a causal architectural effect.
3. **The regime begins after eviction.** Their conversations retain the whole
   history within context; nothing in their setup studies what happens once the
   initial condition has physically left the state. That period is our entire
   object.
4. **Different measured outcomes.** They report endpoint regions and pull
   coefficients. Our headline outcomes are textual repetition, seed-conditioned
   ensemble gaps, completion, and finite-horizon escape. The attempted Stage 3
   state model did not validate semantic macrostates; semantic-memory half-life
   and macrostate probability currents are not achieved contributions
   ([Stage 3 report](../stages/stage-3/REPORT.md)).
5. **A convergent detail.** Their meta-commentary trait resembles surface
   registers observed here. That resemblance motivates caution about treating
   embedding-space separation as recovered semantic memory; it is not an
   independent validation of a macrostate in our data.

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
problem. The closed record does not estimate that half-life or establish H2.
Cite for motivation and framing, not for an achieved memory result.

## 5. Methods we borrow rather than invent

### `VERIFIED` Wu & Noé, *Variational Approach for Learning Markov Processes from Time Series Data*, arXiv:1707.04659 (J. Nonlinear Sci. 30:23–66, 2020; doi:10.1007/s00332-019-09567-y)

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
- "We established several stationary distributions or semantic metastable
  states." — neither was established here. Zekri et al.'s uniqueness result
  applies to their full-support kernel; it does not validate our state model.
- "We show that temperature controls exploration." — Zekri et al. derive it
  theoretically; Geng et al. observe it; Wang et al. find cycles that survive it.
- "Runtime lock is model collapse." — Shumailov et al. is
  *training-time* recursive training. We never retrain.
- "We are the first to operate a finite-memory LLM for millions of tokens." —
  StreamingLLM already studies that length regime. Distinguish its external-text
  perplexity experiment from our self-generated continuation.
- "Prior chain studies measure only exact strings, while we measure semantics."
  — Geng et al. v2 also reports semantic-drift metrics.

## 7. The one-sentence delta

> We characterise repetition and seed-conditioned ensemble separation after
> explicit eviction under finite-tail self-conditioning, compare completion and
> persistence within four model families, and report censored continuation of
> selected existing locks, with protocol diagnostics and reproducible artifacts.

Among the primary sources inspected here, the closest protocols differ in
what is fed back: an instructed replacement text (Wang, Geng, Perez, Mohamed),
a debate history with an interlocutor (Ko & Geiping), or an external text
stream with persistent sink KVs (StreamingLLM). Holtzman and Xu establish
degeneration and self-reinforcement; those are alternative explanations, not
new mechanisms claimed here. This comparison supports a specific protocol and
measurement contribution, not an exhaustive first-in-literature claim.

The actual synthesis is in
[`artifacts/stage-13/`](../../artifacts/stage-13/INDEX.md). Families are not
pooled. The long-horizon table records 0/8 confirmed escapes through 4,999,168
original tokens for the selected continuations
([S12 artifact](../../artifacts/stage-12/tau_escape/tau_escape.meta.json));
it does not estimate an unconditional escape rate or permanence.

## 8. Remaining verification queue

Telephone / degeneration / training-time collapse entries above were verified
2026-09-06 for the TMLR correctness pass (ADR-0019). Random Attention
(arXiv:2609.03430) was verified 2026-09-07 (ADR-0020). Geng v2 and
StreamingLLM received the targeted publication update on 2026-11-08. The
items below document limits of the literature check; they do not open another
research stage or authorise new generation.

| Item | Action | Owner stage |
| --- | --- | --- |
| Systematic search | No exhaustive search completed. The targeted primary-source comparison above does not establish priority over all free-running or streaming generation studies. | Publication limitation |
| Metastability estimation | PCCA+ and non-reversible MSM literature, for the estimator we actually use in S3 | S3 (closed: `validated=0`) |
| Semantic-drift measurement | existing definitions of semantic drift in generation, to avoid reinventing a metric under a new name | S2 |
| “Execution Horizon Laws / 31-model census” | **Not found** under that title (search 2026-09-07: arXiv, web). A lookalike, *The Illusion of Diminishing Returns: Measuring Long Horizon Execution in LLMs* (arXiv:2509.09677), is a multi-turn *task-execution* benchmark with the prompt retained. It is **not** a substitute; do not cite it as this project's neighbour without a written delta, and do not cite it at all until VERIFIED for a reason other than the missing title. | ADR-0020 |
