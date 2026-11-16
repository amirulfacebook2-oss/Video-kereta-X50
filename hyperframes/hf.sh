#!/usr/bin/env bash
# Run the project-pinned Hyperframes CLI with sandbox-friendly defaults.
# - NODE_USE_ENV_PROXY: lets Node's fetch use HTTPS_PROXY (cloud sandbox).
# - HYPERFRAMES_BROWSER_PATH: use a local chrome-headless-shell for fast
#   BeginFrame capture when one is present (otherwise Hyperframes picks Chrome).
set -euo pipefail
cd "$(dirname "$0")"
export NODE_USE_ENV_PROXY="${NODE_USE_ENV_PROXY:-1}"
SHELL_BIN=/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell
if [[ -z "${HYPERFRAMES_BROWSER_PATH:-}" && -x "$SHELL_BIN" ]]; then
  export HYPERFRAMES_BROWSER_PATH="$SHELL_BIN"
fi
exec ./node_modules/.bin/hyperframes "$@"
