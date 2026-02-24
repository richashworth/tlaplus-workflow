# Future Improvements

## Spectacle `_anim.tla` generation

Offer an alternative to the domain-specific HTML playground: generate a `Spec_anim.tla` file compatible with [Spectacle](https://github.com/will62794/spectacle). Uses the SVG module to define visuals in TLA+ itself. Useful for TLA+ power users who prefer exploring specs in Spectacle's native UI.

## Spectacle fallback for large state spaces

When the state graph exceeds the playground threshold (>50K states), automatically generate a `Spec_anim.tla` file for Spectacle instead of building the HTML playground. Currently we just suggest the user open their `.tla` in Spectacle directly — this would provide a better experience with pre-configured visuals.

## MCP server wrapping TLC + state graph utils

Replace the current bash scripts (`resolve-tlc.sh`, `setup-tlc.sh`, `check-tla-syntax.sh`) with an MCP server that exposes structured tools: `check_syntax`, `model_check`, `get_state_graph`. Internally manages TLC (Java) and `tlaplus-state-graph-utils` (Python). Agents get JSON responses instead of parsing stdout. Timeouts, memory flags, and state space concerns all live in one place. Would also replace `dot-to-json.py` with a `get_state_graph` tool that returns the JSON directly.

## Contribute invariant checking to Spectacle

Spectacle's JS interpreter can evaluate arbitrary TLA+ expressions but doesn't evaluate invariants in the UI. Contributing this upstream would make Spectacle useful as a standalone verification tool, not just an explorer.
