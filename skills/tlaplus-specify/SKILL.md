---
name: tlaplus-specify
description: >
  Take a structured system summary and run the full specification pipeline: generate TLA+ spec,
  verify with TLC, generate interactive playground, and offer property-based tests. Use when you
  have a confirmed system summary (from the interview or pasted directly).
user-invocable: true
---

# TLA+ Specify Pipeline

You orchestrate the full specification pipeline. You take a structured system summary and drive it through: specification → verification → animation. You don't do the domain work yourself — you invoke specialist agents and handle the conversation between steps.

If `$ARGUMENTS` is provided, treat it as the structured summary or a path to a file containing one. Otherwise, expect the user to paste a structured summary.

## Pipeline

### Step 1: Specify

Invoke the **specifier** agent. Pass it the confirmed system summary. It writes `.tlaplus/<Module>.tla` and `.tlaplus/<Module>.cfg`.

### Step 2: Verify (loop)

Invoke the **verifier** agent. It runs TLC against the spec.

- **If violations are found:** Present the verifier's plain-language scenario to the user. Ask how the system should actually behave — frame it as a concrete question with options derived from the violation. Then update the spec (re-invoke specifier or edit directly) and re-verify. Repeat until TLC reports no violations.
- **If clean:** Report the stats and move on.

### Step 3: Animate

Invoke the **animator** agent. It reads the verified spec and produces `.tlaplus/playground.html`.

The animator opens the playground automatically. Tell the user:

> Click through actions to explore how your system behaves. The sidebar tracks which rules hold at every step.
> If something looks wrong, hit a report button — it copies a trace you can paste back here.

**This step is mandatory.** The playground is the payoff — never skip it.

### Step 4: Offer extras

After the playground is open:

- **Property-based tests:** If the project has a test framework (check for `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, etc.), offer to generate tests via `/tlaplus-test`. Don't push — just mention it's available.
- **Code changes:** If the workflow started from code (the system summary has a source path), offer to apply spec-driven changes back to the source via the **implementer** agent.

## Rules

- **Don't stop between steps.** The pipeline runs continuously. Don't ask "would you like me to continue?" between specify, verify, and animate — just go.
- **Do stop for violations.** When TLC finds a bug, present it and get the user's input before fixing. This is the one point where you pause.
- **Do stop for extras.** Tests and code changes are opt-in. Offer, don't push.
- **Domain knowledge lives in agents.** You handle sequencing and user interaction. The specifier knows TLA+, the verifier knows TLC, the animator knows HTML. Don't duplicate their expertise.
