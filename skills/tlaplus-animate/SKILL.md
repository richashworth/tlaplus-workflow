---
name: tlaplus-animate
description: >
  Generate an interactive HTML playground from a TLA+ specification. Creates a domain-themed
  prototype where users can click through state transitions and see invariant checks live.
user-invocable: true
---

# TLA+ Animate

Generate an interactive playground from a TLA+ spec's state graph.

If `$ARGUMENTS` is provided, use it as the path to the `.tla` file. Otherwise, look for `.tla` files in `.tlaplus/` and the current directory.

## Process

1. **Find the state graph.** Look for `<ModuleName>_state-graph.json` alongside the `.tla` file. If it doesn't exist, invoke the **verifier** agent first to run TLC and generate it.
2. **Invoke the animator agent.** Pass it the state graph JSON path and the system summary context. It reads the graph, generates `renderState`, `DOMAIN_STYLES`, and `ACTION_LABELS`, merges them into the playground template, and writes `.tlaplus/playground.html`.
3. **Open the playground.** The animator opens it automatically via `open .tlaplus/playground.html`.
