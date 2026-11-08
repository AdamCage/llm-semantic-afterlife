# Narration, accounting and paid retries

## Before a paid call

Read the current host project's budget and accounting instructions. The skill
does not authorise new spending or increase a ceiling. Use the existing project
ledger; `video.py` refuses a separate ledger when it detects the familiar
`runs/_ledger/spend.jsonl`. For another ledger format, provide an adapter to that
project's reserve/record mechanism before making calls. Do not pretend a new
side ledger satisfies an incompatible host accounting contract.

Do not run paid host jobs concurrently unless both share a reservation protocol.
The included file lock coordinates this toolkit's workers only; it cannot make
an unrelated budget client respect its reservations. Existing AFTERLIFE ceiling
environment variables lower the configured caps; they never raise them.

Verify current pricing and units from primary provider documentation. RouterAI
TTS uses `/api/v1/audio/speech`, with `model`, `voice`, `input`, `response_format`.
The response is binary audio. The supplied adapter is specifically for a
verified RUB-per-character TTS model. A `pricing.prompt` number does not by
itself prove units: some models bill tokens, seconds or generated audio.
Do not apply this adapter to those models without changing estimation logic.

Primary references checked in the reference production:
- https://routerai.ru/docs/guides/overview/multimodal/text-to-speech
- https://routerai.ru/models/x-ai/grok-voice-tts-1.0

Refresh them when using a new model or when provider behaviour changes. Choose
a voice by a short real sample, especially with names, numbers and technical
terms. Keep one narrator unless dialogue serves the explanation. The starter's
voice is a usable starting choice, not a requirement for every future study.

Set the model's reviewed `max_rub_per_character`, current accounting
`usd_per_rub`, authorised caps and existing ledger path. Keep the key only in
the named environment variable. `uv run --env-file /path/to/.env python ...`
can use the existing local environment file without printing it.

Run `estimate`, report cost and remaining budget as required by the host, then
send one sample scene. The estimate is invalidated by text/evidence changes,
expires after 24 hours and is rejected if the live catalog price increased.

## Accounting semantics

Before each request the script books a conservative catalog estimate under
`kind=media_tts_estimate` with an attempt ID and character count. This amount
counts against ceilings even if the process crashes or the response is lost.
Success writes a receipt and append-only completion event; it does not charge
the same amount again. Tokens are zero because this adapter bills characters,
not because the request was free.

These are catalog estimates, not audited provider invoices. Reconcile provider
billing separately when available. If a failed request was not charged, append
a documented adjustment through the host's approved process; never rewrite a
historical entry or automatically assume failure was free.

The script stores request bodies, original audio bytes, selected non-secret
response headers and hashes. It does not log Authorization. Treat error bodies
and unpublished narration according to the study's data policy before release.
Built-in app image generation uses its own billing context; do not manufacture
a zero-dollar RouterAI ledger entry for an unknown image charge.

## Resuming and failures

Cached audio is reused only if both request hash and response-file hash match.
A changed narration/voice requires a deliberate new production version; do not
overwrite a paid asset silently. If a `.pending.json` remains, inspect the exact
attempt/provider generation ID. A timeout can mean the provider completed and
billed the request. Do not start another request merely because observation
timed out. Stale locks also require checking the owning process; never delete
them automatically by age.

Call only the missing scene after reconciliation. Preserve usable raw audio so
future renders and subtitle revisions cost nothing in speech API charges.
