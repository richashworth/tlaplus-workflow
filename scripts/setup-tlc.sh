#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
LIB_DIR="$PLUGIN_ROOT/lib"
JAR="$LIB_DIR/tla2tools.jar"

if [ -f "$JAR" ]; then
  echo "tla2tools.jar already installed at $JAR"
  exit 0
fi

mkdir -p "$LIB_DIR"

echo "Downloading tla2tools.jar..."
curl -fSL -o "$JAR" "https://nightly.tlapl.us/dist/tla2tools.jar"

# Verify it's a valid jar (zip) file
if ! file "$JAR" | grep -q "Java archive\|Zip archive\|JAR"; then
  rm -f "$JAR"
  echo "Download failed — file is not a valid jar" >&2
  exit 1
fi

echo "Installed tla2tools.jar to $JAR"
