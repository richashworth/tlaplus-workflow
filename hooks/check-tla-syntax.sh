#!/usr/bin/env bash
# Post-write hook: run SANY syntax check on .tla files.
# Uses the tla2tools.jar managed by the tlaplus-mcp server.

FILE_PATH="${CLAUDE_FILE_PATH:-}"
[[ "$FILE_PATH" == *.tla ]] || exit 0

# Check Java is available
if ! command -v java &>/dev/null; then
  echo "SANY syntax check skipped: Java not found on PATH (JDK 11+ required)" >&2
  exit 0
fi

# Find the tla2tools jar — pick the newest version available rather than
# hardcoding a specific version, so the hook stays in sync with tlaplus-mcp.
JAR_DIR="$HOME/.tlaplus-mcp/lib"
JAR=""
if [[ -d "$JAR_DIR" ]]; then
  JAR="$(ls -t "$JAR_DIR"/tla2tools-*.jar 2>/dev/null | head -1)"
fi

if [[ -z "$JAR" || ! -f "$JAR" ]]; then
  # Fallback: download the latest known version
  JAR="$JAR_DIR/tla2tools-1.8.0.jar"
  JAR_URL="https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar"
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
