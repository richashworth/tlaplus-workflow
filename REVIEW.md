# Review Plan (2026-02-23)

Status: in progress

## Bugs to fix before/with merge

- [x] **1. tlaplus-mcp README describes pre-migration state** — "shells out to bash scripts" is stale. Update in the other repo.
- [x] **2. Violation `name` vs `invariant`/`property` field inconsistency** — added note to verifier documenting that `tla_state_graph` uses `invariant`/`property` instead of `name`.
- [x] **3. Hook silently no-ops if jar missing** — hook now prints a message to stderr explaining the jar is missing and how to get it.
- [x] **4. Hardcoded absolute paths in committed agent frontmatter** — removed `mcpServers` blocks from `specifier.md` and `verifier.md`. `.mcp.json` is the source of truth.

Also: commit `mcp-server-reqts.md` (replaces deleted `MCP_requirements.md`).

## Improvements (revisit after bugs)

- [ ] **5. No CLAUDE.md** — add one (project purpose, architecture, conventions).
- [ ] **6. Extractor output misses 3 of 9 required summary sections** — Resource Bounds, Failure Modes, Fairness not produced by extractor. Skill skips to Phase 3 after extractor, but those sections aren't covered by any phase.
- [ ] **7. State-space estimation asks LLM to do combinatorial math** — unreliable. Move to MCP tool or go reactive (handle OOM after the fact).
- [ ] **8. Redundant `mcpServers` in agent frontmatter** — overlaps with #4.
- [ ] **9. "Walk me through" option has no follow-up in skill** — user gets a summary then nothing. Add re-offer of Step 4 choices.
- [ ] **10. `continue: true` can produce redundant violations** — add dedup-by-invariant guidance to verifier.
- [ ] **11. Animator missing `Glob` in tools** — one-word fix.
- [ ] **12. No template marker validation before injection** — animator should verify markers exist.
- [ ] **13. Skill auto-commits without asking user** — `git add && git commit` in Step 5.5 should be gated on confirmation.
- [ ] **14. Test-writer can't validate TLA+ spec** — add `mcp__tlaplus__tla_parse` to its tools.
- [ ] **15. plugin.json says "five" agents, there are six** — word fix.

## Architectural observations (not actionable now)

- **16.** Structured summary is free-text markdown — fragile. Consider JSON schema.
- **17.** No retry/backoff for MCP server transport failures.
- **18.** Playground template (1037 lines) maintained via marker injection — may not scale.
- **19.** MCP resources (`tla://specs`, etc.) declared but unused by any agent.
