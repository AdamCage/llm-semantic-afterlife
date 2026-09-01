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

# ---------------------------------------------------------------------------
# Restore the working state.
#
# `runs/` and `cache/` are git-ignored: large, regenerable, and kept out of the
# tree so the repository stays reviewable. But regenerating them costs money and
# hours, so without this an agent clones the repo and finds no trajectories to
# analyse and no response cache to replay -- every analysis command fails and
# every generation command spends real money re-deriving what we already have.
#
# The snapshot is a public release asset, so no token is needed to read it.
# AFTERLIFE_SNAPSHOT_TAG=none skips this entirely, for a code-only environment.
# ---------------------------------------------------------------------------
SNAPSHOT_TAG="${AFTERLIFE_SNAPSHOT_TAG:-state-latest}"
SNAPSHOT_DIR=".cache/snapshot"
BASE="https://github.com/AdamCage/llm-semantic-afterlife/releases/download/${SNAPSHOT_TAG}"

if [ "$SNAPSHOT_TAG" = "none" ]; then
  echo "snapshot restore skipped (AFTERLIFE_SNAPSHOT_TAG=none)"
elif [ -d runs/s1 ] && [ -n "$(ls -A runs/s1 2>/dev/null)" ]; then
  echo "runs/s1 already populated; leaving local state alone"
else
  mkdir -p "$SNAPSHOT_DIR"
  ok=1
  for asset in snapshot.manifest.json runs.tar.gz cache.tar.gz; do
    # --fail so a 404 is an error rather than an HTML page saved as a tarball,
    # which would then fail the digest check with a confusing message.
    if ! curl -fsSL --retry 3 -o "${SNAPSHOT_DIR}/${asset}" "${BASE}/${asset}"; then
      echo "could not download ${asset} from ${SNAPSHOT_TAG}" >&2
      ok=0
      break
    fi
  done
  if [ "$ok" -eq 1 ]; then
    # Verifies every archive against its recorded digest before writing, and
    # refuses a corrupt one rather than putting unattributable data under runs/.
    uv run afterlife snapshot restore --from "$SNAPSHOT_DIR"
  else
    echo "continuing without the snapshot: code and tests work, but analysis" >&2
    echo "passes have no data and generation would spend money re-deriving it." >&2
  fi
fi
