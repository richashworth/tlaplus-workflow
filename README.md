# tlaplus-workflow

Formal verification without learning TLA+. Describe your system through conversation (or point at code), and get back a verified TLA+ spec, an interactive playground, and optionally property-based tests and scaffolded implementation code.

## Installation

Clone this repo into your Claude Code plugins directory:

```
git clone https://github.com/richashworth/tlaplus-workflow ~/.claude/plugins/tlaplus-workflow
```

The [tlaplus-mcp](https://github.com/richashworth/tlaplus-mcp) MCP server is installed automatically via npx when the plugin is used. It handles TLC/SANY toolchain management.

## Quick Start

### From conversation

```
/tlaplus-workflow
```

Walks you through describing your system — entities, states, transitions, constraints, concurrency, edge cases. Then: generate spec → verify → interactive playground → offer implementation scaffolding and tests.

### From code

```
/tlaplus-workflow src/booking/
```

Scans your code for stateful patterns (state machines, locks, queues, shared resources), pre-fills the interview with what it finds, then asks you to confirm and fill in gaps.

### With a structured summary

```
/tlaplus-workflow summary.md
```

Skip the interview — go straight to: generate spec → verify → animate.

### Typical flow

```
/tlaplus-workflow
    ↓ interview (or bootstrap from code)
    ↓ specifier agent → .tla + .cfg
    ↓ verifier agent → TLC check + state graph dump
    ↓ animator agent → playground/ (opens in browser)
    ↓ violations? → explore in playground, discuss in Claude Code
    ↓ offer: implementer (scaffold or refine), test-writer
```

### Standalone usage

Already have a spec? Just ask Claude directly — it picks the right agent:

```
"Verify specs/LockManager.tla"         # Runs the verifier agent
"Build a playground for LockManager"    # Runs the animator agent
"Generate tests from the TLA+ spec"    # Runs the test-writer agent
```

## Agents

Specialist workers invoked by the skill or used standalone. They contain all the domain expertise.

| Agent | Role |
|---|---|
| **extractor** | Scans source code for stateful/concurrent patterns. Produces a draft structured summary. |
| **specifier** | Translates a structured summary into a TLA+ module (`.tla`) and TLC config (`.cfg`). |
| **verifier** | Runs TLC, parses output, translates counterexamples to plain-language bug reports. |
| **animator** | Generates a self-contained interactive HTML playground from TLC's pre-computed state graph. |
| **test-writer** | Generates property-based tests mapping TLA+ invariants to your project's test framework. |
| **implementer** | Scaffolds a new implementation from a verified spec, or diffs two spec versions and applies changes to existing code. |

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
    state-graph.json            # Parsed state graph (drives the playground)
    playground/                 # Playground subdirectory
      playground.html           # Interactive prototype (opens in browser)
      playground-gen.js         # Generated data + render functions
      playground-gen.css        # Generated domain styles
```

Property-based tests go in your project's existing test directory, following its conventions.

## Requirements

- **Java 11+** — runs TLC and SANY
- **Node.js 18+** — runs the tlaplus-mcp MCP server
- **[tlaplus-mcp](https://github.com/richashworth/tlaplus-mcp)** — MCP server that wraps the TLA+ toolchain. Auto-downloads `tla2tools.jar` on first use

## File Structure

```
agents/
  specifier.md       # Structured summary → TLA+ spec
  verifier.md        # TLC runner + narrative translator
  animator.md        # Spec → interactive playground
  test-writer.md     # Spec → property-based tests
  extractor.md       # Code → draft structured summary
  implementer.md     # Spec → code (scaffold or refine)

skills/
  tlaplus-workflow/SKILL.md  # Full pipeline: interview → specify → verify → animate → extras

hooks/
  hooks.json                   # SANY syntax check on .tla writes
  check-tla-syntax.sh          # Hook implementation (uses tlaplus-mcp's jar)

.mcp.json                      # MCP server configuration (tlaplus-mcp)
.claude-plugin/plugin.json     # Plugin manifest (name, description, author)
.claude/settings.json          # Pre-configured permissions
```
