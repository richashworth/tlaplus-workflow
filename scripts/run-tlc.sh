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

# Resolve timeout command (GNU coreutils: timeout on Linux, gtimeout on macOS)
if command -v timeout &>/dev/null; then
  TIMEOUT_CMD=timeout
elif command -v gtimeout &>/dev/null; then
  TIMEOUT_CMD=gtimeout
else
  echo "Error: 'timeout' (GNU coreutils) is required but not found." >&2
  echo "On macOS: brew install coreutils" >&2
  exit 1
fi

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
# Note: bash -c is needed so timeout can kill the entire pipeline (including tee).
# We re-source resolve-tlc.sh inside the subshell since functions don't cross
# process boundaries. For --memory mode we pass the jar path directly since we
# need to control JVM flags.
set +e
if [ "$MEMORY" = true ]; then
  if [ ! -f "${_TLA2TOOLS:-}" ]; then
    echo "--memory requires tla2tools.jar but it's not available." >&2
    echo "Run: $PLUGIN_ROOT/scripts/setup-tlc.sh" >&2
    exit 1
  fi
  $TIMEOUT_CMD 120 bash -c '
    java -Xmx4g -jar "$1" -modelcheck -continue -workers auto \
      -dump dot,actionlabels,colorize "$4" -config "$2" "$3" 2>&1 | tee "$5"
  ' _ "$_TLA2TOOLS" "$CFG_FILE" "$SPEC_FILE" "$DUMP_FILE" "$TLC_OUTPUT_FILE"
else
  $TIMEOUT_CMD 120 bash -c '
    export CLAUDE_PLUGIN_ROOT="$1"
    . "$1/scripts/resolve-tlc.sh"
    run_tlc -modelcheck -continue -workers auto \
      -dump dot,actionlabels,colorize "$4" -config "$2" "$3" 2>&1 | tee "$5"
  ' _ "$PLUGIN_ROOT" "$CFG_FILE" "$SPEC_FILE" "$DUMP_FILE" "$TLC_OUTPUT_FILE"
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
