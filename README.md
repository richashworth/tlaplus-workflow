# tlaplus-workflow

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) plugin for formal verification without learning TLA+. Describe your system through conversation (or point at code), and get back a verified TLA+ spec with results presented narratively.

## Installation

Install the plugin once — it's then available in every project you open with Claude Code.

```
git clone https://github.com/richashworth/tlaplus-workflow ~/.claude/plugins/tlaplus-workflow
```

The [tlaplus-mcp](https://github.com/richashworth/tlaplus-mcp) MCP server is installed automatically via npx when the plugin is used. It handles TLC/SANY toolchain management.

## Usage in an existing project

Open Claude Code in your project directory and run the skill:

```
cd your-project/
claude
> /tlaplus-workflow
```

Or point it at specific code to bootstrap from:

```
> /tlaplus-workflow src/booking/
```

Specs are written into your project (default: `specs/`). No configuration needed.

## Quick Start

### From conversation

```
/tlaplus-workflow
```

Walks you through describing your system — entities, states, transitions, constraints, concurrency, edge cases. Then: generate spec → verify → results.

### From code

```
/tlaplus-workflow src/booking/
```

Scans your code for stateful patterns (state machines, locks, queues, shared resources), pre-fills the interview with what it finds, then asks you to confirm and fill gaps. When implementation details are found (transaction boundaries, concurrency primitives), the spec models operations at that granularity.

### With a structured summary

```
/tlaplus-workflow summary.md
```

Skip the interview — go straight to: generate spec → verify.

### Typical flow

```
/tlaplus-workflow
    ↓ interview (or bootstrap from code)
    ↓ specifier agent  → .tla + .cfg
    ↓ reviewer agent   → coverage + semantic check
    ↓ verifier agent   → TLC check + state graph
    ↓ results presented narratively in conversation
    ↓ violations? → discuss, fix, refine
```

### Standalone usage

Already have a spec? Just ask Claude directly — it picks the right agent:

```
"Verify specs/LockManager.tla"         # Runs the verifier agent
```

## Agents

Specialist workers invoked by the skill or used standalone. They contain all the domain expertise.

| Agent | Role |
|---|---|
| **extractor** | Scans source code for stateful/concurrent patterns. Produces a draft structured summary. |
| **specifier** | Translates a structured summary into a TLA+ module (`.tla`) and TLC config (`.cfg`). |
| **reviewer**  | Reviews a spec against its structured summary for coverage gaps and semantic mismatches. |
| **verifier**  | Runs TLC, parses output, translates counterexamples to plain-language bug reports. |

## Hook

A SANY syntax check runs automatically whenever a `.tla` file is written or edited, catching syntax errors immediately.

## Output

The pipeline asks where to store spec files on first run (default: `specs/`). If the project already has a directory with `.tla` files, it reuses that automatically.

```
specs/                          # (or .tlaplus/, or custom path)
  LockManager.tla               # TLA+ specification
  LockManager.cfg               # TLC model-checking config
  LockManager/                  # Derived artifacts
    states.dot                  # TLC state graph dump (DOT format)
    tlc-output.txt              # Captured TLC stdout/stderr
    state-graph.json            # Parsed state graph (structured JSON)
```

For interactive state-space exploration, load the spec in [Spectacle](https://github.com/will62794/spectacle).

## Requirements

- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** — the CLI tool this plugin extends
- **Java 11+** — runs TLC and SANY
- **Node.js 18+** — runs the tlaplus-mcp MCP server

The [tlaplus-mcp](https://github.com/richashworth/tlaplus-mcp) MCP server is fetched from GitHub via npx on first use and auto-downloads `tla2tools.jar` — no manual setup needed.

## File Structure

```
agents/
  extractor.md       # Code → draft structured summary
  specifier.md       # Structured summary → TLA+ spec
  reviewer.md        # Spec ↔ summary coverage + semantic check
  verifier.md        # TLC runner + narrative translator
skills/
  tlaplus-workflow/SKILL.md  # Full pipeline: interview → specify → verify → results

hooks/
  hooks.json                   # SANY syntax check on .tla writes
  check-tla-syntax.sh          # Hook implementation (uses tlaplus-mcp's jar)

.mcp.json                      # MCP server configuration (tlaplus-mcp)
.claude-plugin/plugin.json     # Plugin manifest (name, description, author)
.claude/settings.json          # Pre-configured permissions
```
