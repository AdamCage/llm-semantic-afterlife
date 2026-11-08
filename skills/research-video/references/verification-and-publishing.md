# Verification, source preservation and GitHub publication

## Scientific reading

For each narrated finding read its source and ask whether the wording follows.
Check population, protocol, units, time origin, uncertainty, missingness,
selection, censoring and alternative explanations. Keep practical implications
labelled. `validate` is a reference-integrity check, not peer review. A claim map
that points to the wrong table is still wrong even when the file exists.

Read the full scientific content before releasing. Use the companion
`research-video-review` skill when available, or do that reading directly.
Follow any real repository gate; do not invent a new approval requirement.

## Visual and audio QA

Open the actual Remotion composition. Render representative stills from every
scene and all changing data-panel states. Inspect them full-size and reduced.
Check titles, labels, intervals, omitted rows, captions and AI-image notices.
Inspect moving intervals for synchronisation; stills cannot establish timing.

Known-working rendering examples, from inside the generated renderer:

```text
npx remotion still src/index.ts ResearchVideo ../output/title.png --frame=150
npx remotion render src/index.ts ResearchVideo ../output/frames --frames=150,500,900 --sequence --image-format=png --muted
npm run render
```

Choose actual frames from the prepared timeline, not these illustrative numbers.
The bundled browser is the baseline. On Windows, use the HTML audio components
already in the starter if the newer inline mixer fails; do not restart the whole
paid media workflow to fix a rendering problem.

Run `master` and `bundle`. Inspect their real outputs, not just the existence of
a manifest. Ensure a full video/audio decode passes; dimensions, duration, frame
count, chapters and subtitle stream match the production; loudness is within
the configured range. Verify the beginning, a dense result and the ending. Keep
source and output hashes. Record FFmpeg, Python, Node and renderer versions.

## Git source and media boundary

Commit script, evidence map, configs, renderer source/lockfile, small artwork,
receipts and QA records. Keep large audio/video intermediates out of normal Git.
Use release assets for the final MP4, MP3, SRT/VTT, checksums and reusable media
archive. Do not move or rewrite the authoritative scientific record to package
the video. Verify archives contain only intended source/media and no secrets.

Before Git operations inspect status. Stage only the intended paths. Respect
repository branch rules and any unrelated edits; do not force-push. Push the
exact reviewed source commit before creating a release. Do not publish just
because the skill includes an upload script: confirm the current conversation
actually requests that destination. Existing explicit authorisation persists.

## Upload script

`publish.py` uses GitHub CLI. Provide the explicit repository, tag, full
40-character source commit, title and notes file. It is dry-run by default.
`--execute` creates or resumes a draft; adding `--publish` publishes only after
server-side digest verification. It preserves the repository's existing latest
release with `--latest=false`.

```text
python RV/publish.py --project PROJECT --repo OWNER/REPO --tag video-DATE-v1 --commit FULL_SHA --title TITLE --notes PROJECT/release-notes.md
# Same arguments with --execute to upload a draft.
# Add --publish only when the requested scope includes publication.
```

Do not reuse an occupied tag for a different build. Existing matching assets
are reused, conflicting assets stop the script, and no `--clobber`, deletion or
retargeting is performed. A request timeout is not proof an upload failed: inspect
the same draft before retrying. Draft tags can return 404 through the tag API;
`gh release view` can still locate the draft. Short source SHA values were
rejected by GitHub in the source production; use the full SHA.

After publication verify `isDraft=false`, all expected assets uploaded, byte
sizes and SHA-256 digests match, the tag points to the intended commit and the
download URL is accessible with the expected privacy. For a private repository,
do not turn it public to make a download work. Return the actual release link.
