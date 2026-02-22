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

### Step 0: Validate Summary

Before invoking any agent, check that the structured summary contains all 9 required sections with non-empty content:

1. **System name** — the `## System:` header has a name
2. **Entities** — at least one entity listed with type, count, states, and initial state
3. **Transitions** — at least one transition with trigger and guard
4. **Should never happen** — at least one constraint
5. **Must always be true** — at least one constraint
6. **Must eventually happen** — at least one liveness property
7. **Concurrency** — simultaneous actors, conflict resolution, and atomicity specified
8. **Resource Bounds** — at least one bound defined
9. **Failure Modes** — at least one failure scenario described

If any section is missing or empty, stop and ask the user to fill the gap before proceeding. List exactly which sections need content.

### Step 1: Specify

Invoke the **specifier** agent. Pass it the confirmed system summary. It writes `.tlaplus/<Module>.tla` and `.tlaplus/<Module>.cfg`.

### Step 2: Verify (loop)

Invoke the **verifier** agent. It runs TLC against the spec.

- **If SANY error (not a violation):** Don't surface parse errors to the user. Route the error message back to the specifier agent to fix the syntax issue, then re-verify. Only escalate to the user if the specifier can't resolve it after 2 attempts.
- **If violations are found:** Before updating the spec, commit the current version for rollback: `git add .tlaplus/*.tla .tlaplus/*.cfg && git commit -m "tlaplus: pre-refinement v$(git log --oneline .tlaplus/ | wc -l | tr -d ' ')"`. Then present the verifier's plain-language scenario to the user. Ask how the system should actually behave — frame it as a concrete question with options derived from the violation. Then update the spec (re-invoke specifier or edit directly) and re-verify. Repeat until TLC reports no violations.
- **If clean:** Report the stats and move on.

### Step 3: Animate

Invoke the **animator** agent. It reads the verified spec and produces `.tlaplus/playground.html`.

**After the animator finishes, validate the playground:**

Read the `.tla` spec, the `.cfg` file, and the generated `.tlaplus/playground.html`. Check coverage:

1. Every variable from the `VARIABLES` declaration in the `.tla` file has a corresponding key in `INITIAL_STATE`.
2. Every action disjunct from `Next` in the `.tla` file is represented in `ACTIONS` (parameterized actions may expand to multiple entries or use a dynamic generator — that's fine, but no action should be entirely absent).
3. Every `INVARIANT` from the `.cfg` file appears in the `INVARIANTS` array.

If anything is missing, re-invoke the animator with the specific list of missing items. Max 2 retries. If still incomplete after 2 retries, give the user the verified spec and warn: "The interactive playground is incomplete — [list missing items]. You have the verified spec at `.tlaplus/<Module>.tla`. I can try regenerating the playground later if you'd like." Do not silently continue as if the playground is fine.

The animator opens the playground automatically. Tell the user:

> Click through actions to explore how your system behaves. The sidebar tracks which rules hold at every step.
> If something looks wrong, hit a report button — it copies a trace you can paste back here.

**This step is mandatory.** The playground is the payoff — never skip it.

### Step 4: Offer extras

After the playground is open:

- **Code changes:** If the workflow started from code (the system summary has a source path), offer to apply spec-driven changes back to the source via the **implementer** agent.
- **Property-based tests** are available separately via `/tlaplus-test` — but don't offer them here. They require implementation code to test against, which may not exist yet. The user can invoke `/tlaplus-test` when they're ready.

## Rules

- **Don't stop between steps.** The pipeline runs continuously. Don't ask "would you like me to continue?" between specify, verify, and animate — just go.
- **Do stop for violations.** When TLC finds a bug, present it and get the user's input before fixing. This is the one point where you pause.
- **Do stop for extras.** Tests and code changes are opt-in. Offer, don't push.
- **Domain knowledge lives in agents.** You handle sequencing and user interaction. The specifier knows TLA+, the verifier knows TLC, the animator knows HTML. Don't duplicate their expertise.
