# TLA+ Plugin for Claude Code

Formal verification without learning TLA+. Describe your system through conversation (or point at code), and get back a verified TLA+ spec, an interactive playground, and optionally property-based tests.

## Quick Start

### Full workflow (from conversation)

```
/tlaplus-interview
```

Walks you through describing your system — entities, states, transitions, constraints, concurrency, edge cases. Produces a structured summary, then automatically runs the specification pipeline.

### Full workflow (from code)

```
/tlaplus-interview src/booking/
```

Scans your code for stateful patterns (state machines, locks, queues, shared resources), pre-fills the interview with what it finds, then asks you to confirm and fill in gaps.

### Direct specification (with a summary)

```
/tlaplus-specify
```

Paste a structured system summary and go straight to: generate spec → verify → animate.

## Skills

| Skill | What it does |
|---|---|
| `/tlaplus-interview` | Interview → structured summary → hand off to specify pipeline. Optionally bootstraps from code. |
| `/tlaplus-specify` | Structured summary → TLA+ spec → TLC verification (with fix loop) → interactive playground. Offers tests and code changes. |
| `/tlaplus-verify` | Run TLC against an existing `.tla` file. Translates violations to plain-language narratives. |
| `/tlaplus-animate` | Generate an interactive HTML playground from an existing `.tla` file. |
| `/tlaplus-test` | Generate property-based tests from an existing `.tla` file. |

### Typical flow

```
/tlaplus-interview
    ↓ (conducts interview, produces summary)
/tlaplus-specify
    ↓ specifier agent → .tla + .cfg
    ↓ verifier agent → TLC check (loops on violations)
    ↓ animator agent → playground.html (opens in browser)
    ↓ offer: test-writer, implementer
```

### Standalone usage

Already have a spec? Use the standalone skills directly:

```
/tlaplus-verify .tlaplus/MySpec.tla    # Run TLC, get plain-language results
/tlaplus-animate .tlaplus/MySpec.tla   # Generate interactive playground
/tlaplus-test .tlaplus/MySpec.tla      # Generate property-based tests
```

## Agents

Agents are internal workers invoked by skills. They contain all the domain expertise.

| Agent | Role |
|---|---|
| **extractor** | Scans source code for stateful/concurrent patterns. Produces a draft structured summary. |
| **specifier** | Translates a structured summary into a TLA+ module (`.tla`) and TLC config (`.cfg`). |
| **verifier** | Runs TLC, parses output, translates counterexamples to plain-language bug reports. |
| **animator** | Generates a self-contained interactive HTML playground themed to your domain. |
| **test-writer** | Generates property-based tests mapping TLA+ invariants to your project's test framework. |
| **implementer** | Diffs original and refined specs, applies corresponding changes back to source code. |

## Hook

A SANY syntax check runs automatically whenever a `.tla` file is written or edited, catching syntax errors immediately.

## Output

All TLA+ artifacts go in `.tlaplus/`:

```
.tlaplus/
  MySpec.tla           # TLA+ specification
  MySpec.cfg           # TLC model-checking config
  playground.html      # Interactive prototype (opens in browser)
```

Property-based tests go in your project's existing test directory, following its conventions.

## Requirements

- **Java** — required to run TLC (JDK 11+)
- **TLC model checker** — run `scripts/setup-tlc.sh` to auto-download, or place `tla2tools.jar` in `lib/` manually

## File Structure

```
agents/
  specifier.md       # Structured summary → TLA+ spec
  verifier.md        # TLC runner + narrative translator
  animator.md        # Spec → interactive playground
  test-writer.md     # Spec → property-based tests
  extractor.md       # Code → draft structured summary
  implementer.md     # Spec diff → code changes

skills/
  tlaplus-interview/SKILL.md   # Interview workflow (entry point)
  tlaplus-specify/SKILL.md     # Specification pipeline orchestrator
  tlaplus-verify/SKILL.md      # Standalone verification
  tlaplus-animate/SKILL.md     # Standalone animation
  tlaplus-test/SKILL.md        # Standalone test generation

hooks/hooks.json               # SANY syntax check on .tla writes
scripts/check-tla-syntax.sh    # Hook implementation
scripts/setup-tlc.sh           # Downloads tla2tools.jar to lib/
scripts/resolve-tlc.sh         # Shared TLC resolution (sourced by other scripts)
lib/tla2tools.jar              # TLC model checker (auto-downloaded)
```
