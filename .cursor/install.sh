#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the Semantic Afterlife harness.
# Installs the uv package manager (if absent) and syncs the locked
# environment, including the dev tooling and the Stage 3+ dynamics extra.
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
# The installer drops uv in ~/.local/bin and appends it to the shell profile;
# source its env shim so uv is on PATH within this non-login script too.
if [ -f "$HOME/.local/bin/env" ]; then
  # shellcheck disable=SC1091
  . "$HOME/.local/bin/env"
fi

# Deterministic install from uv.lock. Core + dev tooling + dynamics extra so
# geometry/VAMP/MSM/Leiden analysis is available out of the box.
uv sync --frozen --extra dev --extra dynamics
