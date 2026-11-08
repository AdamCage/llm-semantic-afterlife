# Reusable research video skills

Portable tools extracted from the completed Semantic Afterlife science video.
They do not import `semantic_afterlife`, contain that study's results or require
its directory layout. The original production remains in `video/`.

- [research-video](research-video/SKILL.md): evidence mapping, script, visuals,
  RouterAI narration with bounded accounting, original music and effects,
  captions, Remotion rendering, mastering, replay and GitHub delivery.
- [research-video-review](research-video-review/SKILL.md): scientific source
  reading and independent checks of finished media and release integrity.

## Install once, use in other projects

After cloning this repository:

```text
python skills/install.py
```

This installs both skills into `$CODEX_HOME/skills` (or `~/.codex/skills`). Existing
skills are not overwritten. `--update` explicitly replaces these two skills
after preserving a dated backup. Start a new Codex chat if the current skill
catalog has not refreshed.

Example request:

> Use $research-video to make a Russian science video about this completed
> study, like the Semantic Afterlife episode: real plots, explanatory animation,
> narration, light music and sound design. Keep claims tied to sources.

Add your desired duration, audience and publication destination. Naming a skill
does not itself authorise spending, a public upload or a Git push. The workflow
uses the current task's actual authorisation and existing project rules.

## What is included

Python 3.11+ scripts for project creation, evidence validation, priced/resumable
speech, timeline preparation, original procedural music with ducking, local
word-anchored captions, two-pass loudness mastering, chapters, full-file decode,
checksums, reusable-media archives and idempotent GitHub releases. The rendering
starter uses pinned React/Remotion versions. Ordinary production mechanics use
stdlib + FFmpeg; music needs numpy and local subtitles need faster-whisper.

Guides cover the decision-heavy work: preserving negative results and uncertainty,
writing spoken scientific explanations, choosing visual forms, synchronising
data panels with narration, avoiding duplicate paid requests and distinguishing
an editorial check from peer review. The pipeline is a starting point for
study-specific animation, not an automatic scientific script generator.

Tests are in `tests/test_research_video_skills.py`; live API calls are mocked.
