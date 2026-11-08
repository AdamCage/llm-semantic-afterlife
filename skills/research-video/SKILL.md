---
name: research-video
description: "Produce a sourced public science video from completed research: script, real figures, explanatory animation, narration, music, subtitles, mastering and reproducible delivery. Use for research explainers and scientific video podcasts, including revisions of that workflow."
---

# Research Video

Turn the study the user selected into an understandable, engaging video while
preserving the strength and boundaries of its evidence. Deliver the requested
finished media, source project and publication, not just a production plan.

## Establish the scope

Read the repository contract and current research summary before making claims.
Use final reports, corrections and source artifacts as authoritative; an initial
hypothesis is not a result. Honour the audience, language, duration and release
destination already specified. Ask only for missing choices that materially
affect the work and cannot be inferred. Do not open new experiments to make a
more satisfying story.

The user's demonstrated preference is a calm, polished science explainer:
real data, precise animated mechanisms, restrained AI imagery, clear narration,
light instrumental music and subtle sound effects. Treat reference channels as
examples of explanatory pacing, not permission to copy their music or identity.
Adapt to explicit preferences in the current request.

## Route the work

1. Read [evidence and storytelling](references/evidence-and-story.md). Build a
   claim/source map, choose the narrative, and author the spoken script.
2. Read [production and schema](references/production.md). Initialise a separate
   editorial project with `scripts/video.py init --project PATH`; fill its
   `episode.json` and `evidence.json`. The starter contains demonstration text,
   not research findings. Keep unrelated manuscript and research artifacts intact.
3. Read [visual direction](references/visuals.md). Reuse real plot data and
   uncertainty; create mechanism animations appropriate to this study. Use the
   built-in image-generation tool when available for bitmap artwork, following
   its available skill. Preserve generated files, prompts, origin and hashes.
4. Read [speech, cost and replay](references/speech-and-cost.md) before paid
   narration. Produce a short voice sample, then the rest. Estimate and enforce
   the actual host project's budgets and ledger; do not infer spending authority
   from this skill. Stop on unresolved paid attempts instead of retrying blindly.
5. Read [sound and captions](references/sound-and-captions.md). Compose or license
   the requested music, duck it beneath speech, add meaningful effects, align
   subtitles and master the actual encoded mix.
6. Read [verification and publishing](references/verification-and-publishing.md).
   Inspect rendered frames and moving footage, listen to representative audio
   when the environment supports it, verify the whole file and publish only to
   the destination the user authorised. A request to create a video alone does
   not authorise a public upload. Do not introduce a new confirmation step when
   the current conversation already authorises publication.

## Essential invariants

- Every scientific statement and empirical scene maps to a verified source.
  Keep missing estimates missing, uncertainty visible and populations/conditions
  separate when the study does. Label projections, metaphors and illustrations.
- Separate observed findings, interpretation and untested engineering advice.
  A negative result is part of the story. Do not substitute a stronger claim for
  a complicated but accurate one.
- Scripts validate mechanical properties; they do not prove the conclusions.
  Use `research-video-review` if available for a separate review pass, or perform
  the same source reading and media inspection directly. It is not a mandatory
  dependency and does not require spawning agents.
- Preserve raw generated audio for replay. Repeating an API request, even with
  identical text, is not a promise of identical synthesis.
- This is an editorial pipeline. Its production ID and logs are not research
  run IDs, and rendering an old table is not a new experiment.
- Never count an unknown app-image charge as a zero-dollar provider expense.
- Paid synthesis, public upload and Git pushes require the authorisation and
  accounting applicable to the current task. Installation or invocation of this
  skill grants none of those permissions by itself.

## Completion

Return a playable/downloadable full video, audio if requested, subtitles and
source/evidence links. State duration and any real limitation of the delivery.
For GitHub, verify server asset digests and the published tag, not just CLI exit
status. Do not mark a storyboard, draft release or partial render as complete.

The included scripts and renderer are portable starter machinery. Add
study-specific animations and data panels where needed; do not reduce an
explanatory scene to a text card merely because the starter makes cards easy.
