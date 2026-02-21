---
description: Check a TLA+ specification for syntax errors and run TLC model checker
---

You are a TLA+ expert. The user wants to check a TLA+ specification.

If `$ARGUMENTS` is provided, use it as the path to the .tla file. Otherwise, look for .tla files in the current directory.

Steps:
1. Read the specified TLA+ file
2. Review it for syntax errors, common mistakes, and logical issues
3. If TLC or SANY is available on the system, run it against the spec
4. Report any errors, warnings, or suggestions for improvement
5. If the spec is correct, confirm it parses and looks well-formed
