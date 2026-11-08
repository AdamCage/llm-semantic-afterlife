---
name: research-video-review
description: "Review a scientific explainer or video podcast against its research evidence and finished media. Check claim strength, plots, uncertainty, narration, music, subtitles and publication integrity without rerunning experiments."
---

# Research Video Review

Review what the film actually communicates and whether its evidence supports
that communication. Distinguish scientific judgment from machine-checkable
production integrity. A successful decode or a claim/source link is not proof
that the conclusion follows.

## Inputs and scope

Read the user's request, repository instructions, final reports/corrections,
script, source tables/captions, video timeline and the actual rendered file.
For a project produced with `research-video`, use its `episode.json`,
`evidence.json` and `record/`. For another production layout, use its equivalents;
do not force a conversion merely to use this skill.

This review does not authorise new experiments, paid generation, Git pushes or
publication. Fix editorial defects when asked to fix them. If the user asks only
for a review, report findings without changing or publishing the film.

## Perform the review

1. Read [scientific reading](references/scientific-reading.md). Trace every
   numerical or generalised narrated claim to its exact source. Check meaning,
   scope, denominators, estimator, uncertainty, selection and negative results.
2. Run `scripts/review.py --project PATH` for the portable production layout,
   or `--video /path/to/file.mp4` for a standalone media check. Add `--snapshots`
   to extract representative frames. These are mechanical checks only.
3. Read [media and delivery](references/media-and-delivery.md). Inspect figures
   and all changing panel states, watch representative moving intervals, compare
   the narration to what is on screen, and assess the sound when playback is
   available. Report any unperformed listening review honestly.
4. Check source preservation, output hashes, and published release state when
   relevant. An uploaded draft is not a published release. Do not repeat checks
   already established by current trustworthy evidence without a reason.

## Report and resolve

Lead with blockers, then material scientific/production issues. Give each
finding an exact scene/time, the misleading observation, the supporting source
and a concrete fix. Separate an erroneous result from a correct result with an
overstated interpretation. Do not soften a negative finding to make the video
more encouraging.

When editing is authorised, fix findings and re-inspect affected parts. Changing
wording can change narration duration, subtitles, chart switches and music
ducking; regenerate those dependent pieces. Reuse paid assets only when their
request/response hashes still match. Do not rerun all experiments or all speech
for one caption correction.

Conclude with a bounded editorial verdict: ready, ready with named limitations,
or needs changes. State what was inspected and what remains unverified. Do not
call this external peer review, certify scientific validity from a mechanical
gate, or claim complete listening/visual inspection from metadata alone.
