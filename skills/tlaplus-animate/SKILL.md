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
2. **Invoke the animator agent.** Pass it the spec path. It reads the spec, generates domain-specific JS/CSS/HTML pieces, merges them into the playground template (embedded in its instructions), and writes `.tlaplus/playground.html`.
3. **Validate the playground.** Read the `.tla` spec, the `.cfg` file, and the generated `.tlaplus/playground.html`. Check that the playground faithfully covers the spec:
   - **Variables:** Read the `VARIABLES` declaration in the `.tla` file. Every variable listed there must appear as a key in `INITIAL_STATE` in the playground (the JS name may be camelCase or domain-language — use judgement, but every TLA+ variable must have a corresponding key).
   - **Actions:** Read the `Next` definition in the `.tla` file and identify each disjunct (each action name). Every action must be represented in the `ACTIONS` object in the playground. For parameterized actions, a single TLA+ action may map to multiple playground entries (one per parameter combo) or a dynamic generator — that's fine. What matters is that no TLA+ action is entirely missing.
   - **Invariants:** Read the `.cfg` file and find every `INVARIANT` line. Each named invariant must appear in the `INVARIANTS` array in the playground.
   - If **all items are covered**, move to step 4.
   - If **any items are missing**, list the specific missing variables/actions/invariants and re-invoke the animator with an explicit instruction to add only the missing items. Re-validate after the animator finishes. **Max 2 retries** — if still incomplete after 2 retries, warn the user and continue.
4. **Open the playground.** The animator opens it automatically via `open .tlaplus/playground.html`.
