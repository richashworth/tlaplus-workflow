# tlaplus-workflow

Claude Code plugin that hides TLA+ formal verification behind a conversational interface. Users describe systems in plain language (or point at code); the plugin produces verified TLA+ specs, interactive playgrounds, property-based tests, and scaffolded implementations.

## Architecture

Six agents, one skill, one MCP server:

- **Skill** (`skills/tlaplus-workflow/SKILL.md`) — orchestrates the pipeline and owns all user interaction. Agents never talk to the user directly.
- **Agents** (`agents/*.md`) — extractor, specifier, verifier, animator, test-writer, implementer. Each has a single responsibility and communicates via files and structured output.
- **MCP server** (`tlaplus-mcp`) — wraps the TLA+ toolchain (TLC, SANY, PlusCal). Agents call MCP tools (`tla_parse`, `tlc_check`, `tla_state_graph`, etc.) — **never run Java, `tla2tools.jar`, or TLC/SANY via Bash, and never use Bash/Python to parse MCP tool results or TLC output**. The MCP server is the only interface to the TLA+ toolchain. The skill's only permitted Bash use is `open` to launch the playground browser.

## Critical path

`tla_parse` (syntax check) → `tlc_check` (model check + state graph dump) → `tla_state_graph` (parse DOT → playground JSON)

## Key conventions

- The **structured system summary** (9-section markdown) is the handoff format between interview/extractor and specifier. See the skill for the format.
- MCP tool contracts are documented in `mcp-server-reqts.md`.
- The post-write hook (`hooks/check-tla-syntax.sh`) runs SANY on `.tla` files using the jar at `$HOME/.tlaplus-mcp/lib/tla2tools.jar`. Hook registration is in `hooks/hooks.json` (triggers on Write and Edit of `.tla` files).
- `templates/playground.html` is the playground template — the deterministic shell (UI chrome, state engine, sidebar). The animator writes `playground-gen.js` (data + render functions) and `playground-gen.css` (domain styles) into a `playground/` subdirectory inside `<spec_dir>/<ModuleName>/`. The skill then copies the template into the same directory and opens it in the browser. The animator never touches the template. The template loads the gen files at runtime via `<script src>` and `<link>`.
