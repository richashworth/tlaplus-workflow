#!/usr/bin/env bash
# Run TLC model checker with state graph dump and output capture.
#
# Usage:
#   run-tlc.sh [--memory] <spec.tla> <spec.cfg>
#
# Creates <ModuleName>/ directory alongside the spec with:
#   states.dot       — TLC state graph dump (DOT format)
#   tlc-output.txt   — captured TLC stdout/stderr
#
# Exit codes:
#   0     — TLC finished (check tlc-output.txt for results)
#   12    — TLC found violations (TLC's own exit code for errors)
#   124   — timeout (TLC killed after 120 seconds)
#   1     — setup error (missing files, TLC not found)

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
. "$PLUGIN_ROOT/scripts/resolve-tlc.sh"

# Parse arguments
MEMORY=false
while [[ "${1:-}" == --* ]]; do
  case "$1" in
    --memory) MEMORY=true; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

SPEC_FILE="${1:?Usage: run-tlc.sh [--memory] <spec.tla> <spec.cfg>}"
CFG_FILE="${2:?Usage: run-tlc.sh [--memory] <spec.tla> <spec.cfg>}"

if [ ! -f "$SPEC_FILE" ]; then
  echo "Spec file not found: $SPEC_FILE" >&2
  exit 1
fi
if [ ! -f "$CFG_FILE" ]; then
  echo "Config file not found: $CFG_FILE" >&2
  exit 1
fi

# Set up artifact directory
SPEC_DIR="$(dirname "$SPEC_FILE")"
MODULE_NAME="$(basename "$SPEC_FILE" .tla)"
ARTIFACT_DIR="$SPEC_DIR/$MODULE_NAME"
mkdir -p "$ARTIFACT_DIR"

DUMP_FILE="$ARTIFACT_DIR/states.dot"
TLC_OUTPUT_FILE="$ARTIFACT_DIR/tlc-output.txt"

# Run TLC
set +e
if [ "$MEMORY" = true ]; then
  _TLA2TOOLS="$PLUGIN_ROOT/lib/tla2tools.jar"
  timeout 120 bash -c \
    'java -Xmx4g -jar "$5" -modelcheck -workers auto -dump dot,actionlabels,colorize "$3" -config "$1" "$2" 2>&1 | tee "$4"' \
    -- "$CFG_FILE" "$SPEC_FILE" "$DUMP_FILE" "$TLC_OUTPUT_FILE" "$_TLA2TOOLS"
else
  timeout 120 bash -c \
    'run_tlc -modelcheck -workers auto -dump dot,actionlabels,colorize "$3" -config "$1" "$2" 2>&1 | tee "$4"' \
    -- "$CFG_FILE" "$SPEC_FILE" "$DUMP_FILE" "$TLC_OUTPUT_FILE"
fi
TLC_EXIT=$?
set -e

# Report paths for caller
echo "---"
echo "artifact_dir=$ARTIFACT_DIR"
echo "dump_file=$DUMP_FILE"
echo "tlc_output=$TLC_OUTPUT_FILE"
echo "tlc_exit=$TLC_EXIT"

exit $TLC_EXIT
