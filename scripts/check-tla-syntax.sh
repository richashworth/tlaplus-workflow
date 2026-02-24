#!/usr/bin/env bash
# Post-write hook: run SANY parser on .tla files after edits
# Only triggers for .tla files; silently exits for other file types.

set -euo pipefail

FILE_PATH="${CLAUDE_FILE_PATH:-}"

# Only check .tla files
if [[ "$FILE_PATH" != *.tla ]]; then
  exit 0
fi

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
. "$PLUGIN_ROOT/scripts/resolve-tlc.sh"

run_sany "$FILE_PATH" 2>&1
