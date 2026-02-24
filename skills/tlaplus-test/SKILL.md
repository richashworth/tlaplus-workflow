---
name: tlaplus-test
description: >
  Generate property-based tests from a TLA+ specification. Maps invariants to test assertions
  and actions to randomized transitions. Use when you have a verified spec and want executable tests.
user-invocable: true
---

# TLA+ Test Generation

Generate property-based tests from a TLA+ spec.

If `$ARGUMENTS` is provided, use it as the path to the `.tla` file. Otherwise, look for `.tla` files in `.tlaplus/` and the current directory.

## Process

1. **Find the spec.** Locate the `.tla` file and its `.cfg` file.
2. **Invoke the test-writer agent.** Pass it the spec path. It detects the project's test framework, maps the spec to test code, and writes the test files.
3. **Report results.** Tell the user which test files were generated and how to run them.
