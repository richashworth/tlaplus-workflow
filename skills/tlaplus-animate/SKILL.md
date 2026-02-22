---
name: tlaplus-animate
description: >
  Generate an interactive HTML playground from a TLA+ specification. Creates a domain-themed
  prototype where users can click through state transitions and see invariant checks live.
user-invocable: true
---

# TLA+ Animate

Generate an interactive playground from a TLA+ spec.

If `$ARGUMENTS` is provided, use it as the path to the `.tla` file. Otherwise, look for `.tla` files in `.tlaplus/` and the current directory.

## Process

1. **Find the spec.** Locate the `.tla` file and its `.cfg` file.
2. **Invoke the animator agent.** Pass it the spec path. It reads the spec, generates domain-specific JS/CSS/HTML pieces, merges them into the playground template at `skills/tlaplus-animate/templates/playground-template.html`, and writes `.tlaplus/playground.html`.
3. **Open the playground.** The animator opens it automatically via `open .tlaplus/playground.html`.
