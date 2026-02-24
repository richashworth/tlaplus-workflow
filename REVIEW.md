# Review Plan (2026-02-23)

Status: complete

## Bugs (fixed)

- [x] **1. tlaplus-mcp README describes pre-migration state** — updated in tlaplus-mcp repo.
- [x] **2. Violation `name` vs `invariant`/`property` field inconsistency** — added note to verifier.
- [x] **3. Hook silently no-ops if jar missing** — hook now prints a message to stderr.
- [x] **4. Hardcoded absolute paths in committed agent frontmatter** — removed `mcpServers` blocks.

## Improvements (fixed)

- [x] **5. No CLAUDE.md** — added.
- [x] **6. Extractor output misses 3 of 9 required summary sections** — added Resource Bounds, Failure Modes, Fairness stub sections to extractor output format.
- [x] **7. State-space estimation asks LLM to do combinatorial math** — replaced with reactive OOM handling (run TLC, reduce constants on failure).
- [x] **8. Redundant `mcpServers` in agent frontmatter** — fixed with #4.
- [x] **9. "Walk me through" option has no follow-up in skill** — added re-offer of Step 4 choices after walkthrough.
- [x] **10. `continue: true` can produce redundant violations** — added dedup-by-property guidance to verifier.
- [x] **11. Animator missing `Glob` in tools** — added.
- [x] **12. No template marker validation before injection** — added verification step to animator.
- [x] **13. Skill auto-commits without asking user** — now asks user before committing.
- [x] **14. Test-writer can't validate TLA+ spec** — added `mcp__tlaplus__tla_parse` to its tools.
- [x] **15. plugin.json says "five" agents, there are six** — fixed to "six".

## Architectural observations (not actionable now)

- **16.** Structured summary is free-text markdown — fragile. Consider JSON schema.
- **17.** No retry/backoff for MCP server transport failures.
- **18.** Playground template (1037 lines) maintained via marker injection — may not scale.
- **19.** MCP resources (`tla://specs`, etc.) declared but unused by any agent.
