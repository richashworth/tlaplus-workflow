#!/usr/bin/env bash
# Post-write hook: run SANY parser on .tla files after edits
# Only triggers for .tla files; silently exits for other file types.

set -euo pipefail

FILE_PATH="${CLAUDE_FILE_PATH:-}"

# Only check .tla files
if [[ "$FILE_PATH" != *.tla ]]; then
  exit 0
fi

# Check if tla2tools.jar or sany is available
if command -v tlc &>/dev/null; then
  tlc -parse "$FILE_PATH" 2>&1 || true
elif [ -f "$CLAUDE_PLUGIN_ROOT/lib/tla2tools.jar" ]; then
  java -cp "$CLAUDE_PLUGIN_ROOT/lib/tla2tools.jar" tla2sany.SANY "$FILE_PATH" 2>&1 || true
else
  echo "TLA+ tools not found. Install TLC or place tla2tools.jar in $CLAUDE_PLUGIN_ROOT/lib/"
fi
