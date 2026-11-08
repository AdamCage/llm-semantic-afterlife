# Portable production and schema

## Project layout

`scripts/video.py init --project /absolute/path/video-project` creates:

```text
episode.json            spoken script, visuals and production parameters
evidence.json           source/claim map
evidence/               starter marker; replace with actual source mapping
renderer/               pinned Remotion/React starter
media/voice/            original API responses, generated during synthesis
record/                 estimates, hashes, receipts, ASR and mastering checks
output/                 intermediate and final files; ignored by Git
```

The script uses Python 3.11+ standard library and FFmpeg/ffprobe. Only `music`
needs numpy. Subtitle alignment additionally needs faster-whisper. The toolkit
does not import the repository that originally hosted it. Use absolute script
and project paths so the shell's current directory does not affect the build.

## Minimal command sequence

Set `RV` to this skill's absolute `scripts` path in your shell; set `PROJECT` to
the new editorial folder. These are placeholders for actual absolute paths.

```text
python RV/video.py init --project PROJECT
# Author episode.json and evidence.json; point research_root at the real study.
python RV/video.py validate --project PROJECT
python RV/video.py prepare --project PROJECT --storyboard
# Before synthesis, follow speech-and-cost.md.
python RV/video.py estimate --project PROJECT
python RV/video.py tts --project PROJECT --scene 01
python RV/video.py tts --project PROJECT
python RV/video.py prepare --project PROJECT
uv run --with numpy python RV/video.py music --project PROJECT
uv run --with faster-whisper==1.2.1 python RV/align.py --project PROJECT
# In PROJECT/renderer:
npm install
npm run check
npm run dev
npm run render
# Back in any directory, using absolute script/project paths:
python RV/video.py master --project PROJECT
python RV/video.py bundle --project PROJECT
```

Commit the generated `package-lock.json`. On replay use `npm ci`. Version pins
are a known-working baseline, not a claim that they are the newest releases.
The starter intentionally uses the documented HTML audio path after the newer
Remotion inline mixer failed on Windows nonconsecutive QA-frame renders.

## Episode fields

`production_id` identifies an editorial build, not an experiment. Version it
when changing paid text or voice. `research_root` is relative to the editorial
project and identifies the evidence boundary. Source paths must stay inside
that root. `require_run_ids` enables the stronger rule used by run-based studies.

Set language, dimensions, fps, frame padding, palette, speech and budgeting
parameters explicitly. Starter budgets/prices/conversion are zero so it cannot
spend by accident. Do not turn zero defaults into arbitrary new authorisations.

Each scene requires safe unique `id`, chapter, title, narration, `claim_ids`,
visual and supporting `lines`. Visual modes:

| Mode | Inputs and meaning |
| --- | --- |
| `title` | Opening/chapter card with sequential text reveals |
| `cards` | Parallel concepts; keep wording short |
| `process` | Sequential mechanism; arrows in the starter |
| `quote` | An exact attributed quotation, with source claim mapping |
| `image` | `asset`, `asset_origin` (`ai`, `original`, `licensed`) |
| `figure` | `asset`, `caption`, `limitations`, `data_sources` IDs |

Paths for assets are relative to the editorial project and may not escape it.
Use a copy of the source figure with an appropriate video layout, never edit the
authoritative scientific output in place. Custom data animation belongs in the
renderer and must retain its data-source map and numerical fidelity.

`prepare` uses ffprobe durations, copies audio/assets into Remotion public files,
and records input hashes. Missing narration is an error unless `--storyboard`
is explicit. Storyboards are watermarked and cannot be mastered as a final video.
After changing text, audio, evidence or figures, prepare and render again.

## Replay

Download `media-assets.zip` and source at the release tag. Inspect the archive
member paths before extracting into a designated project directory. It restores
original audio, music and records. Do not call paid synthesis for replay.
Regenerate timing with `prepare`, install locked npm packages and render.
The archive contains the original project config; preserve deliberate local
edits before extraction. Exact byte replay of regenerated lossy encoding is not
promised across FFmpeg/platform versions; original release hashes verify the
published files. Record runtime versions for any new build.

## Offline toolchain test

```text
uv run --with numpy python RV/smoke_test.py --project /new/empty/demo-project
```

This checks project creation, TypeScript, a short real 1080p render, original
music, loudness mastering, chapters, subtitles and media bundling. It substitutes
labelled synthetic tones for speech, never calls paid APIs and never uploads.
The fixture is marked `smoke_test`, and the publication script refuses it.
Pass the project to `research-video-review/scripts/review.py --project PATH
--snapshots` for independent mechanical checks and extracted scene images.
