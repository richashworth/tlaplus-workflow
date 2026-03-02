#!/usr/bin/env bash
# Post-write hook: run SANY syntax check on .tla files.
# Uses the tla2tools.jar managed by the tlaplus-mcp server.

FILE_PATH="${CLAUDE_FILE_PATH:-}"
[[ "$FILE_PATH" == *.tla ]] || exit 0

JAR="$HOME/.tlaplus-mcp/lib/tla2tools.jar"
if [[ ! -f "$JAR" ]]; then
  JAR_URL="https://nightly.tlapl.us/dist/tla2tools.jar"
  JAR_DIR="$(dirname "$JAR")"
  mkdir -p "$JAR_DIR"
  if curl -fsSL --max-time 60 -o "$JAR" "$JAR_URL" 2>/dev/null; then
    echo "Downloaded tla2tools.jar to $JAR" >&2
  else
    rm -f "$JAR"
    echo "SANY syntax check skipped: failed to download tla2tools.jar" >&2
    exit 0
  fi
fi

java -cp "$JAR" tla2sany.SANY "$FILE_PATH" 2>&1
