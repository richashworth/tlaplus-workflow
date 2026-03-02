# tlaplus-workflow

Claude Code plugin that hides TLA+ formal verification behind a conversational interface. Users describe systems in plain language (or point at code); the plugin produces verified TLA+ specs, interactive playgrounds, property-based tests, and scaffolded implementations.

## Architecture

Six agents, one skill, one MCP server:

- **Skill** (`skills/tlaplus-workflow/SKILL.md`) — orchestrates the pipeline and owns all user interaction. Agents never talk to the user directly.
- **Agents** (`agents/*.md`) — extractor, specifier, verifier, animator, test-writer, implementer. Each has a single responsibility and communicates via files and structured output.
- **MCP server** (`tlaplus-mcp`) — wraps the TLA+ toolchain (TLC, SANY, PlusCal). Agents call MCP tools (`tla_parse`, `tlc_check`, `tla_state_graph`, etc.) — **never run Java, `tla2tools.jar`, or TLC/SANY via Bash, and never use Bash/Python to parse MCP tool results or TLC output**. The MCP server is the only interface to the TLA+ toolchain. The skill's only permitted Bash use is to launch the playground in the browser (`open` on macOS, `xdg-open` on Linux).

## Critical path

`tla_parse` (syntax check) → `tlc_check` (model check + state graph dump) → `tla_state_graph` (parse DOT → playground JSON) → `playground_init` (copy template into playground dir)

## Key conventions

- The **structured system summary** (9-section markdown) is the handoff format between interview/extractor and specifier. See the skill for the format.
- MCP tool contracts are documented in the [tlaplus-mcp README](https://github.com/richashworth/tlaplus-mcp).
- The post-write hook (`hooks/check-tla-syntax.sh`) runs SANY on `.tla` files using the jar at `$HOME/.tlaplus-mcp/lib/tla2tools.jar`. Hook registration is in `hooks/hooks.json` (triggers on Write and Edit of `.tla` files).
- The playground template (`playground.html`) lives in the MCP server (single source of truth). `playground_init` writes `playground-data.js` (GRAPH + title, deterministic, never edited) and `playground-gen.js` (labels + render functions, rewritten by animator) plus `playground-gen.css` (domain styles) into a `playground/` subdirectory inside `<spec_dir>/<ModuleName>/`. The skill then calls the `playground_init` MCP tool to copy the template into the same directory, and opens the result in the browser. The animator never touches the template. The template loads the gen files at runtime via `<script src>` and `<link>`.
