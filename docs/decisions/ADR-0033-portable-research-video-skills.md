# ADR-0033: Package the editorial video workflow as portable skills

Status: accepted
Date: 2026-11-09
Type: tooling; no research stage

## Context

After approving the finished science video, the user requested detailed reusable
skills with scripts, local availability for other studies and a GitHub push.
The original production scripts deliberately depend on this repository's closed
tables, settings and paths. Copying them verbatim would not be a portable skill.

## Decision

Package two skills under `skills/`: `research-video` for production and
`research-video-review` for source reading and independent media checks. Install
them into the user's Codex skill directory with a conflict-safe installer.
Keep the original released video and its computational record unchanged.

The new scripts depend on Python/FFmpeg and explicit per-project configuration,
not `semantic_afterlife`. Use a source/claim registry instead of hardcoded study
tables. Keep real findings, explanations and untested practical suggestions
distinct. Templates contain demonstration text, not fabricated research.

Book conservative speech estimates before a request, preserve unresolved
attempts after timeouts and refuse duplicate sends. Respect host ceilings and
the existing ledger; incompatible host accounting needs an adapter. Skill
installation does not authorise spending or public uploads. Publication is
idempotent and never force-overwrites or retargets an existing release.

Validate with unit tests and an actual isolated short 1080p production using
labelled synthetic tones, original music, subtitles, chapters, full decode and
hash verification. Mark the fixture so it cannot be published as a research
film. Test subtitle alignment against already-preserved speech at no API cost.

## Consequences

The skills can be installed in other projects, with study-specific scientific
judgment and animations still required. Mechanical checks are not peer review.
No new research generation, stage, manuscript edit or paid API request is part
of this packaging task.
