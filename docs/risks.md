# Risk register

Ordered by expected damage to the paper. Each risk names its detection signal,
its mitigation, and the stage that owns it. Reviewed at every stage close.

## R1 — The effect is an artifact of the embedding space

**Damage: fatal.** A reviewer says the attractors live in the embedding model,
not the generator, and they would be right if we used one space.

*Signal:* macrostate decomposition disagrees between representation spaces
(low ARI); a "state" corresponds to a superficial textual feature (language,
formatting, length) rather than content.

*Mitigation:* two architecturally different primary spaces (causal decoder vs.
bidirectional encoder); a third closed-source space as an S6 check; ARI/NMI
reported with CI rather than asserted; a time-blind Leiden branch cross-checked
against the time-based MSM branch. **Owner: S3, S6.**

## R2 — Re-prompt is not sliding attention

**Damage: high.** Our `Tail_W` re-prompt restarts positions each step; true
sliding attention keeps a KV cache. If the dynamics we measure are an artifact of
periodic position resets, the central claim is about our harness, not about LLMs.

*Signal:* structure with a period equal to the block size `B`; discontinuities
at step boundaries; sensitivity of results to stride `S`.

*Mitigation:* the protocol is stated explicitly and early (never buried in an
appendix); stride sensitivity is a planned ablation; chunk boundaries are offset
from step boundaries in a sensitivity check; a local P2 control at small `W`
insofar as CPU-only hardware allows. **Owner: S6, and the limitations section.**

## R3 — Degenerate repetition swallows the experiment

**Damage: high.** At low temperature, free-running generation often collapses
into a loop. If most trajectories degenerate, "the model has few semantic
states" becomes trivially true and uninteresting.

*Signal:* repetition-loop rate above ~20%; `cos(z_k, z_{k−1}) → 1`; entropy
collapse; compression ratio dropping.

*Mitigation:* degeneracy is measured as an order parameter, not filtered; loops
are reported as a distinct dynamical phase; the temperature sweep is designed to
cross the boundary; low-temperature results are always reported alongside the
degeneracy rate so no reader can mistake a loop for an attractor.
**Owner: S1 (detect), S4 (characterise).**

## R4 — Instruct models will not free-run

**Damage: medium-high.** Chat models emit EOS, address the user, produce
meta-commentary, or restart as a new turn. That is a different process from
`P_θ(·|X)`.

*Signal:* high stop-event rate; second-person address; markdown scaffolding;
"As an AI…" openings.

*Mitigation:* base models are the primary arm; continuation mechanism audited
per model in S0; `unforced` vs. `chat_instructed` are separate arms and never
pooled; stop-event rate reported per condition. **Owner: S0.**

## R5 — Input-token amplification makes the plan unaffordable

**Damage: medium-high.** `input ≈ T·W/S`. At `W=32k, S=1024` that is 32× the
output tokens; a naive plan overruns the budget by an order of magnitude.

*Signal:* estimate exceeding the stage budget; actual cost diverging from the
model.

*Mitigation:* the cost law is stated in the research plan and enforced by
`afterlife estimate`; primary pilot window is `8k`; ledger with hard ceilings;
cheap models carry the wide matrix; `service_tier: flex` where available.
**Owner: S0 (calibrate), every stage (enforce).**

## R6 — Provider drift and unknown quantization

**Damage: medium.** A router silently serving a different endpoint or
quantization changes the generator mid-experiment, which is not a
reproducibility inconvenience but a change of the object being studied.

*Signal:* `provider`/`quantization` in a manifest differing from the pinned
value; a step-change in metrics with no configuration change.

*Mitigation:* `provider.only=[slug]` **and** `allow_fallbacks=false`; recorded
provider and quantization per request; determinism audit in S0; cross-provider
replication of headline results in S6; any run whose served provider differs from
the pinned one is regenerated, never patched. **Owner: S0, S6.**

## R7 — Novelty is contested

**Damage: medium.** Adjacent work exists on successive paraphrasing as a
dynamical system, LLMs as Markov chains, and attractors in multi-turn
conversations. A framing that reads as "attractors in LLMs, again" invites
rejection.

*Signal:* reviewer comparisons to that literature; our own difficulty stating
the delta in one sentence.

*Mitigation:* `literature/related-work.md` maintained continuously, with an
explicit delta table; the claim is scoped to *unbounded free-running generation
under a finite sliding window past eviction of the initial condition*; the
measurement suite (half-life, MSD scaling, non-reversible currents,
temperature × `W` phase behaviour) is the contribution, not the attractor
vocabulary. **Owner: S7, continuous.**

## R8 — Probe leakage inflates the semantic half-life

**Damage: medium.** If chunks from the same trajectory appear in both train and
test, the seed probe reads trajectory identity instead of semantic content, and
`T_½` becomes meaningless — in the direction that flatters our hypothesis.

*Signal:* implausibly high accuracy far past the horizon; accuracy insensitive
to `t`; shuffled-label baseline above chance.

*Mitigation:* trajectory-level splits enforced in code and tested;
label-shuffled and time-shuffled baselines reported next to every accuracy
curve; empirical rather than nominal chance level. **Owner: S2.**

## R9 — Statistical over-reach on autocorrelated data

**Damage: medium.** Chunks within a trajectory are strongly autocorrelated;
bootstrapping over chunks would shrink every CI in the paper.

*Signal:* implausibly tight CIs; significance that vanishes under a
trajectory-level bootstrap.

*Mitigation:* the replicate unit is the trajectory, everywhere, enforced in the
analysis API; effective sample size reported via integrated autocorrelation
time; multiple-comparison correction over a pre-declared family.
**Owner: S2, S3.**

## R10 — Not enough turnovers to say anything asymptotic

**Damage: medium.** Below ~10 turnovers the system is still in transient; claims
about long-run behaviour would be unsupported.

*Signal:* metrics still trending at the end of trajectories; MSD not
approaching any plateau; implied timescales comparable to `T`.

*Mitigation:* `R = T/W ≥ 16` in the pilot and `≥ 30` for headline results;
`R` reported on every figure axis; asymptotic language explicitly bounded by the
observed `R`. **Owner: S1, S2.**

## R11 — Wall-clock: long-run generation on one laptop

**Damage: low-medium.** Hundreds of sequential API steps per trajectory, hours
of wall-clock, on a machine that gets closed.

*Signal:* runs interrupted; partial trajectories.

*Mitigation:* checkpoint after every step; idempotent resume; parallelism across
trajectories with a bounded semaphore; `STATUS` file per run; partial
trajectories are either resumed or reported as missing data, never silently
truncated into the sample. **Owner: S0.**

## R12 — Harness becomes the project

**Damage: low, insidious.** Infrastructure is enjoyable and unbounded; the paper
is the deliverable.

*Signal:* a stage passing with no scientific artifact; commits that only touch
tooling; this file growing faster than `docs/stages/`.

*Mitigation:* stage exit criteria are scientific, never infrastructural (S0
excepted); each stage must produce artifacts a reviewer would read; tooling work
that is not unblocking a stage goes to `backlog.md`. **Owner: continuous.**
