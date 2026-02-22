# Source this file: . "$PLUGIN_ROOT/scripts/resolve-tlc.sh"
# After sourcing, use: run_tlc <args>  OR  run_sany <file>

_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
_TLA2TOOLS="$_PLUGIN_ROOT/lib/tla2tools.jar"

if command -v tlc &>/dev/null; then
  run_tlc() { tlc "$@"; }
  run_sany() { tlc -parse "$@"; }
elif [ -f "$_TLA2TOOLS" ]; then
  run_tlc() { java -jar "$_TLA2TOOLS" "$@"; }
  run_sany() { java -cp "$_TLA2TOOLS" tla2sany.SANY "$@"; }
else
  run_tlc() {
    echo "TLC not found. Run: $_PLUGIN_ROOT/scripts/setup-tlc.sh" >&2
    return 1
  }
  run_sany() { run_tlc "$@"; }
fi
