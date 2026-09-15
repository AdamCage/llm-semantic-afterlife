#!/usr/bin/env bash
set -eu
ls -l /home/adam/hf-paperb/hub/models--google--gemma-4-12B/blobs/
echo ---ps---
ps aux | grep -E 'afterlife|transformers|huggingface' | grep -v grep | head -20
echo ---incomplete---
stat -c '%s %n' /home/adam/hf-paperb/hub/models--google--gemma-4-12B/blobs/*.incomplete 2>/dev/null || true
