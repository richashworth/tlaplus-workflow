#!/bin/bash
# Post-write hook: run SANY syntax check on .tla files.
# Uses the tla2tools.jar managed by the tlaplus-mcp server.

FILE_PATH="${CLAUDE_FILE_PATH:-}"
[[ "$FILE_PATH" == *.tla ]] || exit 0

JAR="$HOME/.tlaplus-mcp/lib/tla2tools.jar"
[[ -f "$JAR" ]] || exit 0

java -cp "$JAR" tla2sany.SANY "$FILE_PATH" 2>&1
