# tlaplus-workflow

Claude Code plugin that hides TLA+ formal verification behind a conversational interface. Users describe systems in plain language (or point at code); the plugin produces verified TLA+ specs, interactive playgrounds, property-based tests, and scaffolded implementations.

## Architecture

Six agents, one skill, one MCP server:

- **Skill** (`skills/tlaplus-workflow/SKILL.md`) — orchestrates the pipeline and owns all user interaction. Agents never talk to the user directly.
- **Agents** (`agents/*.md`) — extractor, specifier, verifier, animator, test-writer, implementer. Each has a single responsibility and communicates via files and structured output.
- **MCP server** (`tlaplus-mcp`) — wraps the TLA+ toolchain (TLC, SANY, PlusCal). Agents call MCP tools (`tla_parse`, `tlc_check`, `tla_state_graph`, etc.) — never Java/Bash directly.

## Critical path

`tla_parse` (syntax check) → `tlc_check` (model check + state graph dump) → `tla_state_graph` (parse DOT → playground JSON)

## Key conventions

- The **structured system summary** (9-section markdown) is the handoff format between interview/extractor and specifier. See the skill for the format.
- MCP tool contracts are documented in `mcp-server-reqts.md`.
- The post-write hook (`hooks/check-tla-syntax.sh`) runs SANY on `.tla` files using the jar at `$HOME/.tlaplus-mcp/lib/tla2tools.jar`.
- `templates/playground.html` is the playground template — the deterministic shell (UI chrome, state engine, sidebar). The animator never modifies it; instead it writes `playground-gen.js` (data + render functions) and `playground-gen.css` (domain styles) as sibling files, and copies the template alongside them. The template loads these at runtime via `<script src>` and `<link>`.
