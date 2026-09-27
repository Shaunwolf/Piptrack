#!/bin/bash
# Prepares a Claude Code on the web session: dependencies, env vars, latest pump research data.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Dependencies (including pytest and ruff from the dev group); uv reuses its cache between sessions
uv sync

# Session environment: skip background scanner threads, use the project venv
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo 'export DISABLE_BACKGROUND_SCANNER=1'
    echo "export PATH=\"$PWD/.venv/bin:\$PATH\""
  } >> "$CLAUDE_ENV_FILE"
fi

# Latest collected pump data (published by the "Collect pump data" workflow), if any
if git ls-remote --exit-code --heads origin pump-data >/dev/null 2>&1; then
  git fetch -q origin pump-data
  mkdir -p pump_data
  git archive origin/pump-data | tar -x -C pump_data
  echo "Pump research data loaded into pump_data/ from origin/pump-data"
fi
