# Source this file: . "$PLUGIN_ROOT/scripts/resolve-tlc.sh"
# After sourcing, use: run_tlc <args>  OR  run_sany <file>

_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
_TLA2TOOLS="$_PLUGIN_ROOT/lib/tla2tools.jar"

# Check for Java early
if ! command -v java &>/dev/null; then
  echo "Error: Java is required but not found (JDK 11+)." >&2
  echo "Install: brew install openjdk (macOS) or apt install default-jdk (Linux)" >&2
fi

# Auto-download tla2tools.jar if missing
if [ ! -f "$_TLA2TOOLS" ]; then
  "$_PLUGIN_ROOT/scripts/setup-tlc.sh" >&2
fi

# Prefer plugin's own jar; fall back to system tlc
if [ -f "$_TLA2TOOLS" ]; then
  run_tlc() { java -jar "$_TLA2TOOLS" "$@"; }
  run_sany() { java -cp "$_TLA2TOOLS" tla2sany.SANY "$@"; }
elif command -v tlc &>/dev/null; then
  run_tlc() { tlc "$@"; }
  run_sany() { tlc -parse "$@"; }
else
  run_tlc() {
    echo "TLC not found and auto-download failed. Run: $_PLUGIN_ROOT/scripts/setup-tlc.sh" >&2
    return 1
  }
  run_sany() { run_tlc "$@"; }
fi
