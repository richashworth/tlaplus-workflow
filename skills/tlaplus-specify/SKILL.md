---
name: tlaplus-specify
description: >
  Take a structured system summary and run the full specification pipeline: generate TLA+ spec,
  verify with TLC, generate interactive playground, and offer property-based tests. Use when you
  have a confirmed system summary (from the interview or pasted directly).
user-invocable: true
---

# TLA+ Specify Pipeline

You orchestrate the full specification pipeline. You take a structured system summary and drive it through: specification → verification → playground. You don't do the domain work yourself — you invoke specialist agents and handle the conversation between steps.

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

### Step 1.5: Present and offer next steps

Tell the user what was created (file paths) and give a one-line summary of the module scope (e.g., "3 entities, 5 actions, 2 safety invariants, 1 liveness property"). Then ask what they'd like to do next:

- **Walk me through the spec** — summarize the spec in plain language: what the entities are, what transitions exist, what properties are checked, and why. No TLA+ syntax — just the domain story.
- **Explore it** — run TLC model checking and build an interactive playground to explore the design (Step 2).

Wait for the user's choice before proceeding.

### Step 2: Verify and Explore

This step runs TLC, generates the state graph, and builds the interactive playground.

1. **Invoke the verifier agent.** It runs TLC with `-dump dot,actionlabels,colorize` to dump the full state graph alongside checking invariants. It also runs `dot-to-json.py` to produce `.tlaplus/<Module>_state-graph.json`.

2. **Handle SANY errors** (syntax errors, not design violations): Don't surface to the user. Route to the specifier agent to fix. Re-verify. Only escalate after 2 failed attempts.

3. **If state graph is too large** (verifier reports exit code 2 from dot-to-json.py): Tell the user the state space is too large for an interactive playground. Suggest reducing constants or opening the `.tla` file in [Spectacle](https://github.com/will62794/spectacle). Continue with text-based verification output only.

4. **Invoke the animator agent** to build the playground from the state graph JSON. It reads `state-graph.json` and the system summary, generates `renderState`, `DOMAIN_STYLES`, and `ACTION_LABELS`, and writes `.tlaplus/playground.html`. Open it automatically.

5. **If violations were found**, present them to the user via AskUserQuestion. The playground has violation scenarios pinned (labeled v1, v2, etc.) so the user can explore them visually, then come back to Claude Code to discuss:

   First AskUserQuestion — list all violations:
   > "TLC found {N} scenarios where your design rules are violated. Explore them in the playground (the pinned scenarios match the IDs below), then tell me which to address."

   Options (one per violation):
   - **v1: {invariant_name} — {summary}**
   - **v2: {invariant_name} — {summary}**
   - "None of these are real problems"

   For each selected violation, follow-up AskUserQuestion:
   > "How should the system handle this scenario?"

   Options:
   - "This shouldn't be possible — fix the design" — update the spec to add a guard or constraint that prevents this scenario
   - "My requirements allow this — update the invariant" — relax or remove the invariant
   - "Let's discuss this more" — present the verifier's narrative translation of the violation for deeper discussion

   After the user's choice: commit current spec for rollback (`git add .tlaplus/*.tla .tlaplus/*.cfg && git commit -m "tlaplus: pre-refinement"`), update the spec, re-run TLC + state graph + playground. Repeat until clean.

6. **If clean** (no violations): The playground opens in exploration mode. Proceed to Step 3.

### Step 3: Offer extras

After the playground is open:

- **Code changes:** If the workflow started from code (the system summary has a source path), offer to apply spec-driven changes back to the source via the **implementer** agent.
- **Property-based tests** are available separately via `/tlaplus-test` — but don't offer them here. They require implementation code to test against, which may not exist yet.

## Rules

- **Stop after spec creation.** Always pause at Step 1.5 to let the user choose their next step. Don't auto-advance.
- **Don't stop between verify and animate.** Once verification finishes and the state graph is built, proceed directly to building the playground.
- **Do stop for violations.** When TLC finds bugs, present via AskUserQuestion and get user input before fixing.
- **Do stop for extras.** Tests and code changes are opt-in.
- **Domain knowledge lives in agents.** You handle sequencing and user interaction. The specifier knows TLA+, the verifier knows TLC, the animator knows HTML.
