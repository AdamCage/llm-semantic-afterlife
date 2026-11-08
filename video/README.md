# Semantic Afterlife — public science video

An editorial companion to the closed research record, authorised 2026-11-09.
Russian narration is the intended publication language. This is not S14 and
does not reopen any experiment or modify the manuscript.

The production source is `episode.json`; each scene carries evidence pointers.
`film/` is the Remotion renderer. Build outputs and raw provider responses stay
outside the small scientific artifact tree. Existing figures are display inputs,
not new statistical estimates. Artistic illustrations and explanatory schematics
must be visibly distinguished from empirical measurements.

The soundtrack is an original, deterministic instrumental composition with soft
transitions and speech ducking. No music from reference channels is sampled.

Publication target: source and evidence index in Git, MP4/audio/subtitles attached
to a GitHub Release. The released video must retain its finite-horizon,
protocol, missing-data and representation qualifications.

## Build and replay

Requires the repository's uv environment, Node/npm and FFmpeg/ffprobe.

```powershell
# Repository root. Inspect the estimate before paid synthesis.
uv run python video/produce.py estimate
uv run python video/produce.py tts
uv run python video/produce.py prepare
uv run python video/produce.py sound
uv run --with faster-whisper==1.2.1 python video/align.py
cd video/film
npm ci
npm run dev
npx remotion render src/index.ts SemanticAfterlife ../output/semantic-afterlife.raw.mp4 --concurrency=4 --crf=20
cd ../..
uv run python video/finalize.py
```

To replay without paid synthesis, extract the release's `media-assets.zip`
inside `video/`. It restores `film/public/voice/` and `film/public/score.mp3`.
Run `prepare` and the renderer; do not call `tts` for a replay. Original
illustrations are preserved in `film/public/`, and final prompts are recorded in
`production/illustrations.json`. Regeneration is not bit-identical replay.

`Html5Audio` is intentional: Remotion 4.0.541's newer inline mixer raised a
Windows EINVAL on nonconsecutive QA frames. The documented HTML audio path
rendered the same sources successfully.

## Evidence

[The script](SCRIPT.ru.md) maps every scene to sources. Primary occupancy uses
`artifacts/occupancy-replication/`, not the archival panel whose vectors are
unrecoverable. Family comparisons use the published S13 rows without pooling
or re-estimation. Undefined estimates remain absent. S12 is a separate selected
cohort and a finite, right-censored count, not a population escape rate.
Practical monitoring and memory suggestions are engineering implications, not
tested improvements to agents. No research trajectory or manuscript changed.

## Sound and subtitles

The original procedural score uses sparse keyboard-like notes, soft pads and
transition pings. Its envelope drops during speech. No reference-channel music
was sampled. Final mastering targets −16 LUFS and −1.5 dBTP and is measured
again after AAC encoding.

Subtitles preserve the script. Timing uses local multilingual Whisper word
anchors, with interpolation for unmatched words; coverage and the method are
recorded in `production/alignment.json`. The MP4 includes selectable Russian
subtitles and chapters; SRT and VTT are also supplied separately.

`production/manifest.json`, `deliverables.json`, voice receipts and `SHA256SUMS`
record input/output hashes and character-priced TTS accounting. App image
generation has a separate billing context; its unknown dollar amount is not
represented as a free RouterAI call.
