# Music, sound effects, captions and mastering

The user's preferred result includes light music and sound design. Avoid a
silent slideshow unless that is requested. Use an original procedural score,
properly licensed music or user-supplied material with established permission.
Do not copy music from channels cited as style references.

`video.py music` generates original seeded stereo pads and sparse keyboard-like
notes, plus soft transition pings. Chords, tempo, seed, gains and fade time live
in `episode.json`. It writes an MP3 to the renderer and keeps intermediate WAV
out of Git. It does not generate music with a paid API or download stock tracks.
For a long film, vary instrumentation/sections if the repeating bed becomes
distracting. The starter is a sound bed, not a substitute for listening.

Music drops during the actual narration intervals and rises modestly in gaps.
Sound effects should punctuate a meaningful reveal, transition or operation.
Avoid a click for every word or a constant beat under a difficult explanation.
Keep effects away from plosive-heavy or quiet speech. Check headphones and a
small speaker if available. A numerically quiet track can still mask speech.

`align.py` performs local multilingual ASR (base model, CPU int8 by default),
matches normalised recognised words to the authored script and interpolates
unmatched word timings. Audio is decoded with FFmpeg to avoid PyAV decoder
compatibility failures encountered in the source project. ASR caches include
voice hashes so a changed recording cannot reuse stale timestamps.

The resulting Caption JSON preserves script wording and records per-scene
anchor fractions. Fractions below 0.8 trigger `needs_review`; the threshold is
a timing-triage heuristic, not an accuracy guarantee. Inspect names, acronyms,
numbers, the first/last sentence and low-coverage spans. A good coverage number
does not prove the voice pronounced every word correctly. Use a larger local
model or manual timing when needed. Do not invent word-perfect alignment.

SRT/VTT subtitles are split into short phrases. Keep Unicode and avoid captions
over scientific axis labels. The master includes selectable subtitles rather
than burning text over plots. If burned-in captions are requested, reserve a
safe caption region in the visual design and inspect it across the full film.

`video.py master` measures the rendered mix, performs two-pass EBU R128 loudness
normalisation, writes chapter metadata, muxes subtitles if present, extracts an
audio-only version, fully decodes the output and measures again after AAC.
Default target: about −16 LUFS integrated, −1.5 dBTP, LRA 11. These are editorial
targets for this workflow, not a platform-wide requirement. Configure different
targets when the destination specifies them.

Check clipping, abnormal pauses, abrupt cuts, stereo balance, music masking and
end-of-scene speech cutoffs. Do not describe technical loudness verification as
a complete listening review when no audio listening capability was used.
