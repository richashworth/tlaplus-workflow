#!/usr/bin/env bash
# Post-write hook: run SANY syntax check on .tla files.
# Uses the tla2tools.jar managed by the tlaplus-mcp server.

FILE_PATH="${CLAUDE_FILE_PATH:-}"
[[ "$FILE_PATH" == *.tla ]] || exit 0

JAR="$HOME/.tlaplus-mcp/lib/tla2tools.jar"
if [[ ! -f "$JAR" ]]; then
  echo "SANY syntax check skipped: tla2tools.jar not found at $JAR (run the tlaplus MCP server once to auto-download)" >&2
  exit 0
fi

java -cp "$JAR" tla2sany.SANY "$FILE_PATH" 2>&1
