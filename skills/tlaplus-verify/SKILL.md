---
name: tlaplus-verify
description: >
  Run the TLC model checker against a TLA+ specification and translate violations into
  plain-language narratives. Use for standalone verification of existing specs.
user-invocable: true
---

# TLA+ Verify

Run TLC against a TLA+ spec and present the results.

If `$ARGUMENTS` is provided, use it as the path to the `.tla` file. Otherwise, look for `.tla` files in `.tlaplus/` and the current directory.

## Process

1. **Find the spec.** Locate the `.tla` file and its `.cfg` file (same basename, same directory).
2. **Invoke the verifier agent.** Pass it the spec path. It handles SANY, TLC, output parsing, and narrative translation.
3. **If violations are found:** Present the verifier's narrative to the user. Ask how the system should actually behave. Update the spec based on their answer. Re-invoke the verifier. Repeat until clean.
4. **If clean:** Report the stats. Done.
