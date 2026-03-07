# tlaplus-workflow

Claude Code plugin that hides TLA+ formal verification behind a conversational interface. Users describe systems in plain language (or point at code); the plugin produces verified TLA+ specs and interactive playgrounds.

## Structure

```
skills/tlaplus-workflow/SKILL.md   # Orchestrator — owns all user interaction
agents/*.md                        # Five specialist agents (extractor, specifier, reviewer, verifier, animator)
hooks/check-tla-syntax.sh          # Post-write hook — runs SANY on .tla files
hooks/hooks.json                   # Hook registration (Write/Edit on .tla)
.mcp.json                          # MCP server config (tlaplus-mcp)
```

## Development

The MCP server lives in a sibling repo (`tlaplus-mcp`). To use a local build during development, point `.mcp.local.json` at the built `dist/index.js`.

Runtime instructions (what agents can/cannot do, tool usage rules, critical path) live in the skill and agent prompts — not here. Edit those files directly when changing runtime behavior.
