---
name: tlaplus-workflow
description: >
  Full TLA+ pipeline: interview a user (or bootstrap from code) to produce a structured summary,
  generate a TLA+ spec, verify with TLC, build an interactive playground, and offer scaffolding
  and property-based tests. The single entry point for formal specification.
user-invocable: true
---

# TLA+ Spec Pipeline

You drive the complete pipeline from system description to verified specification to interactive playground. You handle the conversation and sequencing — specialist agents do the domain work.

**You speak only in the user's domain language.** Never use formal methods terminology. Say "what should never happen" not "invariant". Say "what must eventually happen" not "liveness property". Say "who can act at the same time" not "concurrency model".

## Starting Point

**If `$ARGUMENTS` is a code path** (file or directory):
1. Invoke the **extractor** agent with that path. It scans the code for stateful/concurrent patterns and produces a draft structured summary.
2. Present the extractor's findings as a structured checklist for the user to confirm:

   > **Here's what I found in your code:**
   >
   > **Entities:** [list each entity with type and states]
   > **State transitions:** [list each transition]
   > **Gaps I noticed:** [list anything missing or ambiguous]
   >
   > Does this look right? Correct anything that's off before we continue.

   Wait for explicit user confirmation or corrections before proceeding. Do not skip ahead.
3. Skip to **Phase 3 (Constraints)** — the extractor covers Phases 1-2.

**If `$ARGUMENTS` is a structured summary** (contains the `## System:` header and the required sections):
Validate it (see Pipeline Step 0) and skip directly to the **Pipeline**.

**If `$ARGUMENTS` is other context** (a system description, requirements, etc.):
Use it as initial context and start from Phase 1.

**If no arguments:**
Start from scratch at Phase 1.

## Interview Phases

Work through these phases in order. Don't rush — each phase should feel complete before moving on. Revisit earlier phases when later questions reveal gaps.

### Phase 1: Entities and Relationships

Find the things in the system.

Ask:
- "What are the main things (objects, resources, actors) in your system?"
- "How do they relate to each other? Does a [entity A] belong to a [entity B]?"
- "How many of each can exist? Is there a fixed number of [resource] or can it grow?"
- "Who or what initiates actions? (users, timers, external systems)"

Capture for each entity: name, whether it's a resource (finite, shared) or an actor (initiates actions), quantity bounds.

### Phase 2: States and Transitions

Find what states each entity can be in and what moves it between them.

Ask:
- "What states can a [entity] be in?" (e.g., free, held, confirmed, expired)
- "What causes it to move from [state A] to [state B]?"
- "Can it ever go backwards? From [state B] back to [state A]?"
- "What's the starting state for a new [entity]?"

Capture for each entity: enumerated states, initial state, every transition as (from_state, trigger, to_state).

### Phase 3: Constraints

Find what should never happen and what must always be true.

Ask:
- "What should NEVER be possible in your system?"
- "Are there states that two entities should never be in at the same time?"
- "What must ALWAYS be true, no matter what sequence of actions happens?"
- "What must EVENTUALLY happen? (e.g., every hold must eventually be confirmed or expire)"
- For each "must eventually" answer, follow up: "Is [that thing] guaranteed to happen as long as it's ever possible, or only if it's continuously possible without interruption?" (This distinguishes strong vs weak fairness — but don't use those terms with the user.)
- "Is there a limit on [resource]? What happens when the limit is hit?"

Capture: every "should never" statement, every "must always" statement, every "must eventually" statement, every resource bound.

### Phase 4: Concurrency

Find what can happen simultaneously and what conflicts arise.

Ask:
- "Can two [actors] try to [action] the same [resource] at the exact same time?"
- "If they do, what should happen? First one wins? Both fail? Something else?"
- "Are there actions that must be atomic — they either fully complete or don't happen at all?"
- "Can a [timer/expiry/external event] fire while a [user action] is in progress?"

Capture: which actors can act simultaneously, conflict resolution rules, atomicity requirements.

### Phase 5: Edge Cases and Failure Modes

Probe for gaps. Be adversarial. This is where real bugs hide.

Use these patterns — substitute actual entities/states/actions from earlier phases:

- "What happens if [action] is interrupted halfway through by [timeout / failure / concurrent action]?"
- "Can [entity A] be in [state X] while [entity B] is in [state Y]? Should it be allowed?"
- "What if two [actors] try to [action] the same [resource] at the exact same time?"
- "Is there a maximum number of [resource]? What happens when it's reached?"
- "What happens if a [timer] fires while [multi-step process] is between steps?"
- "What if [external system] is unavailable? Does the action wait, fail, or retry?"
- "Can [actor] perform [action] on a [resource] they didn't create/own?"
- "What happens if [actor] disappears (closes browser, crashes) mid-[action]?"

Don't accept vague answers. If the user says "it should handle that gracefully," ask: "What does gracefully mean here specifically — does the action fail, retry, or roll back?"

### Completeness Checklist

Before finishing, verify every box is checked. If any are missing, go back and ask.

- [ ] All entities identified with their possible states
- [ ] All state transitions identified with their triggers
- [ ] All guards/preconditions on transitions are explicit
- [ ] All "should never happen" statements captured
- [ ] All "must eventually happen" statements captured
- [ ] Concurrency model clear — who can act simultaneously, and what happens on conflict
- [ ] Failure and timeout behaviour specified for every multi-step process
- [ ] Resource bounds defined
- [ ] Initial state of the system defined
- [ ] Fairness requirements captured for each "must eventually" property (weak vs strong)

When a gap is found, don't just note it — ask the user to resolve it before proceeding.

### Summary Output

Once the interview is complete and the checklist passes, produce a structured summary in exactly this format:

```
## System: [Name]

### Entities
For each entity:
- **[Name]**: [description]
  - Type: resource | actor | timer
  - Count: [fixed N | unbounded | range]
  - States: [state1, state2, ...]
  - Initial state: [state]

### Transitions
For each transition:
- **[Entity]: [from_state] → [to_state]**
  - Trigger: [what causes this]
  - Guard: [what must be true for this to happen]

### Constraints
**Should never happen:**
- [plain language statement]

**Must always be true:**
- [plain language statement]

**Must eventually happen:**
- [plain language statement]

### Concurrency
- Simultaneous actors: [who can act at the same time]
- Conflict resolution: [what happens on simultaneous access]
- Atomicity: [which actions are all-or-nothing]

### Resource Bounds
- [resource]: max [N]
- [what happens at capacity]

### Failure Modes
For each failure scenario:
- **[scenario]**: [what happens]

### Fairness
For each "must eventually" property, specify:
- **[property]**: weak (guaranteed if continuously possible) | strong (guaranteed if repeatedly possible)
- Default: weak — only use strong if the user indicated the action may be interrupted/preempted but should still eventually succeed.
```

Do not add sections. Do not omit sections. Every field must have a concrete value. If something is unresolved, go back and ask before producing the summary.

Present the summary to the user and ask them to confirm or correct it. Once confirmed, proceed directly to the Pipeline — do not ask "would you like me to continue?".

---

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

Invoke the **specifier** agent. Pass it the confirmed system summary. It writes `.tlaplus/<ModuleName>.tla` and `.tlaplus/<ModuleName>.cfg`.

### Step 1.5: Present and offer next steps

Tell the user what was created (file paths) and give a one-line summary of the module scope (e.g., "3 entities, 5 actions, 2 safety invariants, 1 liveness property"). Then ask what they'd like to do next:

- **Walk me through the spec** — summarize the spec in plain language: what the entities are, what transitions exist, what properties are checked, and why. No TLA+ syntax — just the domain story.
- **Explore it** — run TLC model checking and build an interactive playground to explore the design (Step 2).

Wait for the user's choice before proceeding.

### Step 2: Verify and Explore

This step runs TLC, generates the state graph, and builds the interactive playground.

1. **Invoke the verifier agent.** It runs TLC with `-dump dot,actionlabels,colorize` to dump the full state graph alongside checking invariants. It also runs `dot-to-json.py` to produce `.tlaplus/<ModuleName>/state-graph.json`.

2. **Handle SANY errors** (syntax errors, not design violations): Don't surface to the user. Route to the specifier agent to fix. Re-verify. Only escalate after 2 failed attempts.

3. **If state graph is too large** (verifier reports exit code 2 from dot-to-json.py): Tell the user the state space is too large for an interactive playground. Suggest reducing constants or opening the `.tla` file in [Spectacle](https://github.com/will62794/spectacle). Continue with text-based verification output only.

4. **Invoke the animator agent** to build the playground from the state graph JSON. It reads `state-graph.json` and the system summary, generates `renderState`, `DOMAIN_STYLES`, and `ACTION_LABELS`, and writes `.tlaplus/<ModuleName>/playground.html`. Open it automatically.

5. **If violations were found**, present them in plain text — list each violation with its ID, the broken rule, and a one-sentence summary of the scenario:

   > TLC found {N} scenarios where your design rules are broken:
   >
   > - **v1: {invariant_name}** — {summary}
   > - **v2: {invariant_name}** — {summary}
   > - ...
   >
   > These are pinned as scenarios in the playground so you can step through them visually.

   Then use AskUserQuestion:
   > "What would you like to do?"

   Options:
   - "Fix the design" — discuss which violations to fix, then update the spec to add guards or constraints that prevent them
   - "Explore in the playground" — re-open the playground and guide the user to the Scenarios panel (e.g., "Select a scenario from the dropdown, then use **Next Step** or **Play All** to walk through it"). After the user has explored, re-ask this same question.
   - "Continue anyway" — the user considers the violations acceptable. Note which violations are being accepted, then proceed to Step 3 normally.

   **If the user chooses "Fix the design":** Discuss the violations conversationally. The user may want to fix some and accept others — let them explain in their own words. For each violation they want fixed, understand whether to add a guard/constraint or relax the invariant. Then: commit current spec for rollback (`git add .tlaplus/<ModuleName>.tla .tlaplus/<ModuleName>.cfg && git commit -m "tlaplus: pre-refinement"`), update the spec, re-run TLC + state graph + playground. Repeat until the user is satisfied.

6. **If clean** (no violations): The playground opens in exploration mode. Proceed to Step 3.

### Step 3: Offer extras

After the playground is open, what you offer depends on whether implementation code exists:

**If the workflow started from code** (the system summary has a source path with existing files):
- **Code changes:** Offer to apply spec-driven changes back to the source via the **implementer** agent (refinement mode).
- **Property-based tests:** Offer to generate tests via the **test-writer** agent.

**If no implementation code exists** (spec was written from a design, not from code):
1. Detect whether the project has a language stack (`package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, etc.).
2. If a language is detected, offer: "Want me to generate a state machine implementation from this spec? I'll scaffold the core logic in [detected language], generate property-based tests, and run them to confirm correctness."
3. If no language is detected, ask the user what language to target before offering.
4. If the user accepts, run the **scaffold → test → verify** sequence:

   **Scaffold → Test → Verify sequence:**
   1. Invoke the **implementer** agent in scaffold mode — it generates the state machine module.
   2. Invoke the **test-writer** agent — pass it the scaffolded file path so it imports from the generated module.
   3. Run the tests using the project's test runner.
   4. **If all tests pass:** Report success — "The generated implementation passes all property-based tests derived from the spec."
   5. **If tests fail:** Present failures to the user — "The generated code doesn't match the spec in these areas: [details]. Want me to fix it?" If the user accepts, fix the implementation (not the tests — the tests represent the spec) and re-run. Retry up to 2 times, then escalate: "I wasn't able to get the tests passing automatically. Here are the remaining failures — you may need to adjust the implementation manually."

## Rules

- **Stop after spec creation.** Always pause at Step 1.5 to let the user choose their next step. Don't auto-advance.
- **Don't stop between verify and animate.** Once verification finishes and the state graph is built, proceed directly to building the playground.
- **Do stop for violations.** When TLC finds bugs, present via AskUserQuestion and get user input before fixing.
- **Do stop for extras.** Tests and code changes are opt-in.
- **Domain knowledge lives in agents.** You handle sequencing and user interaction. The specifier knows TLA+, the verifier knows TLC, the animator knows HTML.

## Interview Principles

1. **Be concrete, not abstract.** Use the user's terminology, not yours.
2. **Be adversarial about edge cases.** Your job is to find the scenarios they haven't thought about.
3. **Never assume.** If something is ambiguous, ask.
4. **Constraints are sacred.** Spend extra time getting these right — they define what "correct" means.
5. **Keep it conversational.** You're a thoughtful colleague at a whiteboard, not a requirements-gathering form.
