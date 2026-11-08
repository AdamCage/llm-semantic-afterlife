# Media and delivery checks

## Visuals

Inspect the actual rendered file, representative frames from every scene, every
data-panel switch and a few moving transitions. Check at playback scale and a
reduced size. Look for clipped text, unreadable ticks, captions obscuring plots,
overlapping legends, hidden uncertainty, truncated axes and unsupported visual
precision. Confirm plotted values match source rows, including omitted values.

Verify the shown condition matches the spoken condition at that time. A correct
graph displayed over narration about another group can communicate a false
comparison. Inspect fades at scene boundaries and ensure a late spoken caveat
is not covered by a premature visual conclusion.

AI metaphors, diagrams and real measurements must be distinguishable. Do not
infer statistical meaning from the look of an illustration. Check attribution
and rights/provenance for quoted text, real imagery and third-party audio.

## Audio and captions

Check the opening, a dense technical passage, quiet speech, a transition and
the ending. Assess intelligibility, pronunciations, numbers, pauses, music
masking, abrupt effects and cut-off speech. Check both headphone and small
speaker reproduction when available. Loudness/true peak measurement does not
replace listening; explicitly state when the latter was unavailable.

Subtitles must follow the actual voice and preserve technical distinctions.
Inspect low-confidence or interpolated alignment, names, numbers and clauses
around scene changes. Do not publish raw ASR errors because a script existed.
Selectable captions need valid positive time intervals and the right language.

## Mechanics and publication

The bundled checker can decode a whole MP4, inspect dimensions/fps/frames/audio,
measure loudness, verify chapters/subtitles, compare known hashes and extract
frames. It labels the scientific judgment and listening review as not performed.
Failure of a check is a defect to investigate, not a reason to change the target
so the test turns green.

For a public release verify the actual release URL, draft flag, intended source
commit/tag and all attached assets. Compare server-side digests with local
SHA-256. A successful upload call does not prove the right file is attached.
For a private destination preserve its access controls. Inspect archive members
and confirm a fresh user can replay without credentials or repeating paid calls.

Report precise residual limitations: for example, interpolated subtitle spans
or unavailable original plot vectors. Avoid generic disclaimers unrelated to
the actual result. Never describe a partial render or silent storyboard as the
requested completed film.
