---
name: tlaplus-workflow
description: >
  The single entry point for ALL TLA+ work. Use this skill whenever the user asks anything
  about TLA+ specs: writing, checking, verifying, model-checking, or exploring state graphs.
  Covers the full pipeline (interview → spec → TLC → verified results)
  and individual operations. Never run TLA+ tools (TLC, SANY, tla2tools.jar,
  Java) directly — this skill's agents handle the toolchain via MCP.
user-invocable: true
---

# TLA+ Spec Pipeline

You drive the complete pipeline from system description to verified specification. You handle the conversation and sequencing — specialist agents do the domain work.

**You speak only in the user's domain language.** Never use formal methods terminology. Say "what should never happen" not "invariant". Say "what must eventually happen" not "liveness property". Say "who can act at the same time" not "concurrency model".

## Starting Point

**If `$ARGUMENTS` is a code path** (file or directory):
1. Invoke the **extractor** agent with that path. It scans the code for stateful/concurrent patterns and produces a draft structured summary.
2. Present the extractor's findings as a structured checklist for the user to confirm:

   > **Here's what I found in your code:**
   >
   > **Entities:** [list each entity with type and states]
   > **State transitions:** [list each transition]
   > **Implementation details:** [transaction boundaries, concurrency primitives, API call sequences — if found]
   > **Gaps I noticed:** [list anything missing or ambiguous]

   Use AskUserQuestion:
   > "Does this look right?"

   Options:
   - "Looks good — continue" — proceed to Phase 3
   - "Some corrections" — the user provides corrections in their answer; apply them and re-present
   - "Start the interview from scratch" — ignore extractor findings and begin at Entities and Relationships
3. Skip to **Constraints** — the extractor covers Entities and Relationships and States and Transitions.

   If the extractor found implementation details (transaction boundaries, lock usage, API boundaries), include them in the structured summary under `### Implementation Detail`. When implementation detail is present, the specifier can write the spec at operation granularity from the start — modeling actual API calls and transaction boundaries rather than abstract domain actions. This catches concurrency and atomicity bugs without needing a separate refinement pass.

**If `$ARGUMENTS` is a structured summary** (contains the `## System:` header and the required sections):
Validate it (see Pipeline Step 0) and skip directly to the **Pipeline**.

**If `$ARGUMENTS` is other context** (a system description, requirements, etc.):
Use it as initial context and start from Entities and Relationships.

**If no arguments:**
Start from scratch at Entities and Relationships.

## Interview Phases

Work through these phases in order. Don't rush — each phase should feel complete before moving on. Revisit earlier phases when later questions reveal gaps.

### Entities and Relationships

Find the things in the system.

Ask:
- "What are the main things (objects, resources, actors) in your system?"
- "How do they relate to each other? Does a [entity A] belong to a [entity B]?"
- "How many of each can exist? Is there a fixed number of [resource] or can it grow?"
- "Who or what initiates actions? (users, timers, external systems)"

Capture for each entity: name, whether it's a resource (finite, shared) or an actor (initiates actions), quantity bounds.

**Gate:** Present what you've captured as a table or list. Use AskUserQuestion:
> "**Entities and Relationships** — here's what I have so far: [list]. Is this complete?"

Options:
- "Looks complete — next phase" — proceed to States and Transitions
- "Need to add/change something" — the user provides additions or corrections; update and re-present
- "Not sure yet — ask me more" — continue probing with follow-up questions, then re-present

### States and Transitions

Find what states each entity can be in and what moves it between them.

Ask:
- "What states can a [entity] be in?" (e.g., free, held, confirmed, expired)
- "What causes it to move from [state A] to [state B]?"
- "Can it ever go backwards? From [state B] back to [state A]?"
- "What's the starting state for a new [entity]?"

Capture for each entity: enumerated states, initial state, every transition as (from_state, trigger, to_state).

**Gate:** Present a state machine summary for each entity (states + transitions). Use AskUserQuestion:
> "**States and Transitions** — here's the state machine for each entity: [summary]. Is this complete?"

Options:
- "Looks complete — next phase" — proceed to Constraints
- "Need to add/change something" — the user provides additions or corrections; update and re-present
- "Not sure yet — ask me more" — continue probing with follow-up questions, then re-present

### Phase Assessment

After the States and Transitions gate, evaluate signals from Phases 1–2 to determine whether later phases can be skipped or simplified.

**Single actor check:** Count distinct actor types identified in Entities and Relationships. If exactly one actor type AND no entities marked as "resource" (finite, shared), then concurrency is irrelevant to this system.

**No external dependencies check:** If no timers, no external systems, and no multi-step processes were identified in Phases 1–2, then edge case probing can be simplified.

**Skip conditions:**

- **Phase 4 (Concurrency) is skippable** when: single actor type AND no shared resources. Record defaults: `Simultaneous actors: N/A — single actor system`, `Conflict resolution: N/A`, `Atomicity: N/A`.
- **Phase 5 (Edge Cases) can be collapsed** when: Phase 4 is skippable AND no timers AND no external systems identified. Instead of full adversarial probing, use a single lightweight prompt (see Phase 5 below).
- **Phase 3 (Constraints) is NEVER skippable** — constraints are sacred.
- **Phase 6 (Completeness Checklist) and Phase 7 (Summary Output) are NEVER skippable.**

If any phases will be skipped, present this to the user via AskUserQuestion:

> "Based on what you've described, this looks like a [single-actor system / system without concurrency]. I'm planning to skip [Phase X] because [reason]. I'll still cover Constraints, Completeness, and Summary. Sound right?"

Options:
- "Yes, skip those" — proceed with skips as determined
- "Actually, cover everything" — un-skip all phases and proceed normally through every phase

If no phases are skippable, proceed normally without any notification.

### Constraints

Find what should never happen and what must always be true.

Ask:
- "What should NEVER be possible in your system?"
- "Are there states that two entities should never be in at the same time?"
- "What must ALWAYS be true, no matter what sequence of actions happens?"
- "What must EVENTUALLY happen? (e.g., every hold must eventually be confirmed or expire)"
- "Is there a limit on [resource]? What happens when the limit is hit?"

Capture: every "should never" statement, every "must always" statement, every "must eventually" statement, every resource bound.

**Pressure-test:** Before presenting, check each constraint against the domain model captured in earlier phases. For each constraint, ask yourself:

- **Does it conflict with known transitions or failure modes?** A "must eventually" property that relies on an external system may not hold during outages. A "must never" property may conflict with a recovery path identified earlier.
- **Is the user stating a hard guarantee or an aspiration?** "Every order must eventually ship" sounds like liveness, but is it still required if the order is cancelled? If the constraint has implicit exceptions, surface them.
- **What would enforcing this actually require?** If a "must eventually" property requires the system to make progress even when competing actions keep preempting it, that has real design consequences — flag that.

For any constraint where the implications aren't obvious, explain what it would mean in practice before asking the user to confirm. For example:

> "You said every hold must eventually be confirmed or expire. That means your system must guarantee no hold stays in limbo forever — even during an outage of the confirmation service. Is that what you mean, or is it acceptable for holds to stay pending during downtime?"

This replaces the generic fairness follow-up. Instead of asking an abstract question about "continuously possible vs repeatedly possible", ground it: "What could prevent [the thing] from happening? When that happens, must the system still guarantee it eventually, or is it okay to wait?"

**Gate:** Present the rules in three groups (never / always / eventually), with any implications or caveats you surfaced during pressure-testing noted inline. Use AskUserQuestion:
> "**Constraints** — here are the rules I've captured: [list by group]. Is this complete?"

Options:
- "Looks complete — next phase" — proceed to Concurrency
- "Need to add/change something" — the user provides additions or corrections; update and re-present
- "Not sure yet — ask me more" — continue probing with follow-up questions, then re-present

### Concurrency

**If the Phase Assessment determined concurrency is relevant**, proceed with this phase as written below.

**If the Phase Assessment determined concurrency is irrelevant**, skip this phase. The default values recorded during the assessment will be used in the summary.

Find what can happen simultaneously and what conflicts arise.

Ask:
- "Can two [actors] try to [action] the same [resource] at the exact same time?"
- "If they do, what should happen? First one wins? Both fail? Something else?"
- "Are there actions that must be atomic — they either fully complete or don't happen at all?"
- "Can a [timer/expiry/external event] fire while a [user action] is in progress?"

Capture: which actors can act simultaneously, conflict resolution rules, atomicity requirements.

**Gate:** Present the concurrency model. Use AskUserQuestion:
> "**Concurrency** — here's how simultaneous actions work: [summary]. Is this right?"

Options:
- "Looks right — next phase" — proceed to Edge Cases and Failure Modes
- "Need to add/change something" — the user provides additions or corrections; update and re-present
- "Not sure yet — ask me more" — continue probing with follow-up questions, then re-present

### Edge Cases and Failure Modes

**If the Phase Assessment determined this phase can be collapsed**, replace the full adversarial probing with a single lightweight prompt:

Ask: "Based on what you've described, this is a straightforward system. Is there anything that could go wrong that we haven't covered — any timeouts, retries, or unexpected failures?"

If the user raises new concerns, capture them as failure modes and probe further on those specific concerns. If not, record: "No additional failure modes identified beyond those captured in Constraints."

**Otherwise**, proceed with the full phase as written below.

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

**Gate:** Present the edge cases and failure modes captured. Use AskUserQuestion:
> "**Edge Cases and Failure Modes** — here are the failure scenarios and edge cases: [list]. Any others?"

Options:
- "That covers it — move to summary" — proceed to Completeness Checklist
- "Need to add/change something" — the user provides additions or corrections; update and re-present
- "Not sure yet — ask me more" — continue probing with follow-up questions, then re-present

### Completeness Checklist

Before finishing, verify every box is checked. If any are missing, go back and ask.

- [ ] All entities identified with their possible states
- [ ] All state transitions identified with their triggers
- [ ] All guards/preconditions on transitions are explicit
- [ ] All "should never happen" statements captured
- [ ] All "must eventually happen" statements captured
- [ ] Concurrency model clear — who can act simultaneously, and what happens on conflict (auto-passes with "N/A — single actor system" when the Phase Assessment determined concurrency is irrelevant)
- [ ] Failure and timeout behaviour specified for every multi-step process (when Phase 5 was collapsed, this passes if the user confirmed no additional failure modes exist)
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

Present the summary to the user. Use AskUserQuestion:
> "Here's the complete system summary. Ready to generate the spec?"

Options:
- "Looks good — generate the spec" — proceed to the Pipeline
- "Some corrections" — the user provides corrections; update the summary and re-present
- "Go back to [phase]" — reopen the specified interview phase

Once confirmed, proceed directly to the Pipeline — do not ask "would you like me to continue?".

---

## Pipeline

### Step 1: Validate Summary

Before invoking any agent, check that the structured summary contains all 9 required sections with non-empty content:

1. **System name** — the `## System:` header has a name
2. **Entities** — at least one entity listed with type, count, states, and initial state
3. **Transitions** — at least one transition with trigger and guard
4. **Should never happen** — at least one constraint
5. **Must always be true** — at least one constraint
6. **Must eventually happen** — at least one liveness property
7. **Concurrency** — simultaneous actors, conflict resolution, and atomicity specified (or "N/A" entries when the Phase Assessment determined concurrency is irrelevant)
8. **Resource Bounds** — at least one bound defined
9. **Failure Modes** — at least one failure scenario described

If any section is missing or empty, stop and ask the user to fill the gap before proceeding. List exactly which sections need content.

### Step 2: Choose Spec Directory

Before generating any files, determine where to put them.

**If the project already has a directory containing `.tla` files**, use that directory and skip the prompt.

**Otherwise**, use AskUserQuestion:

> "Where should I store the TLA+ spec files?"

Options:
1. **`specs/`** — visible project directory (Recommended)
2. **`.tlaplus/`** — hidden directory
3. Other — custom path

Store the chosen path as the **spec directory**. Pass it to all agents so they write files there.

### Step 3: Specify

Invoke the **specifier** agent. Pass it the confirmed system summary and the **spec directory**. It writes `<spec_dir>/<ModuleName>.tla` and `<spec_dir>/<ModuleName>.cfg`.

### Step 4: Review Spec

Invoke the **reviewer** agent with the `.tla` file, `.cfg` file, and the confirmed structured summary. The reviewer maps spec definitions to summary requirements (by reading the TLA+ logic, not by relying on annotations) and back-translates each definition to verify the TLA+ logic matches the stated requirement.

Handle results:

- **`pass`** — proceed to Step 5.
- **`issues`** — route fixes back to the specifier silently:
  - **Coverage gaps** (uncovered requirements or orphaned definitions): pass the gap list to the specifier and ask it to add missing definitions or remove orphaned ones. Re-review after the fix.
  - **Mismatches** (spec behaviour diverges from stated requirement): pass each mismatch (definition, matched requirement, actual behaviour, discrepancy) to the specifier and ask it to fix the TLA+ logic to match the requirement. Re-review after the fix.
  - Escalate to the user after 2 failed review attempts: "I've tried to align the spec with the requirements twice but some issues persist — here's what's still off: [details]."

### Step 5: Verify Spec

Automatically run TLC to catch encoding errors before presenting the spec to the user. Invoke the **verifier** agent — pass the spec files and the confirmed structured summary. This is a full verifier run (same as Step 7), but the state graph is discarded. The purpose is solely to surface and fix problems before the user sees the spec.

**Spec coding errors** (`spec_error`) — route back to the specifier with the violation trace and the `fix_suggestion`. Re-verify after the fix. Do this silently — the user doesn't need to see encoding bugs. Escalate to the user only after 2 failed fix attempts.

**Requirement conflicts** (`requirement_conflict`) — these are design issues the user must resolve. Present each conflict with:
- The rule that was broken
- A one-sentence summary of the scenario
- Which requirements are in tension
- Possible resolutions (do not pick one)

Use AskUserQuestion to let the user choose a resolution. Once they decide, update the structured summary, route to the specifier to update the spec, and re-verify from the start of this step.

**Clean** — proceed to Step 6. Coverage data from this run is not presented to the user — coverage is shown only in Step 7.

### Step 6: Present and offer next steps

Tell the user what was created (file paths) and give a one-line summary of the module scope (e.g., "3 entities, 5 actions, 2 safety invariants, 1 liveness property"). Then use AskUserQuestion:
> "What would you like to do next?"

Options:
- **Walk me through the spec** — summarize the spec in plain language: what the entities are, what transitions exist, what properties are checked, and why. No TLA+ syntax — just the domain story. After the walkthrough, re-present this same choice so the user can proceed.
- **Generate a PDF** — invoke the **specifier** agent to produce a typeset PDF. Pass it the `.tla` file path, the structured summary, and these instructions: read the spec and add a plain-language summary at the top of the module (as a block of TLA+ comments) that describes what the spec models, the key entities, and what properties it checks. Beyond the summary, only add inline comments where the TLA+ logic is genuinely non-obvious — e.g., a subtle guard condition, a fairness choice, or an encoding trick that wouldn't be clear from reading the code. Do NOT annotate every variable, action, or invariant — well-named definitions speak for themselves. Comments should be concise, readable prose aimed at someone unfamiliar with TLA+. After annotating, call the `tla_tex` MCP tool with `shade: true` to typeset the spec into a PDF. Return the PDF path. Tell the user where the PDF was written. Re-present this same choice so the user can proceed.
- **Explore it** — run TLC model checking to explore the design (Step 7).

Wait for the user's choice before proceeding.

### Step 7: Verify and Explore

This step runs TLC, generates the state graph, and presents results narratively. Encoding errors (`spec_error`) should already be resolved by Step 5 — this run focuses on generating the state graph and presenting violations. Follow this exact sequence — steps cannot be reordered.

**Step 7.1: Invoke the verifier agent.** Pass it the spec files **and** the confirmed structured summary (so it can classify violations as spec errors vs requirement conflicts). It returns structured results:
- `status`: clean | violations | error
- `violation_count` and violation summaries (one line each), each categorized as `spec_error` or `requirement_conflict`
- `state_graph`: generated | partial | failed | skipped
- `state_graph_file`: path to `state-graph.json`
- `sample_state`: vars from initial state (for domain labeling)
- `actions`: list of unique action names (for domain labeling)
- `invariants`: list of invariant/property names (for domain labeling)
- `stats`: states found, distinct states, depth

**Step 7.2: Handle verifier results by category.** The verifier classifies each violation as either a `spec_error` or a `requirement_conflict`:

**Spec coding errors** (`spec_error`) — the TLA+ code doesn't correctly encode the user's requirements. These are bugs in the spec, not in the design. Route back to the specifier agent with the violation trace and the `fix_suggestion`. Re-verify after the fix. Escalate to the user only after 2 failed fix attempts ("I've tried to fix this twice but the issue persists — here's what's going wrong: [details]").

**Requirement conflicts** (`requirement_conflict`) — two or more stated requirements are mutually unsatisfiable. These are design decisions that only the user can resolve. For each conflict, present:
- The rule that was broken
- The step-by-step trace showing how the system reaches the bad state
- Which requirements are in tension
- A list of possible resolutions (do not pick one)

Use AskUserQuestion to let the user choose a resolution. Once they decide, update the structured summary to reflect the resolution, route to the specifier to update the spec, and re-verify from Step 7.1.

**SANY errors** (syntax/parse errors, not violations): Don't surface to the user. Route to the specifier agent to fix silently. Re-verify. Escalate after 2 failed attempts.

**Step 7.3: Handle state graph availability.** The verifier always produces a state graph when TLC runs successfully — either a full graph (`generated`) or a traces-only graph (`partial`) when the full state space is too large. Proceed to Step 7.4 to present results narratively.

- `generated` or `partial` → proceed to Step 7.4. If `stats.distinct_states` exceeds 10,000, additionally note: "The state space is large ({stats.distinct_states} distinct states). For interactive exploration, you can load the spec in [Spectacle](https://github.com/will62794/spectacle)."
- `failed` or `skipped` → no state graph is available. Present violations as text in Step 7.4. Tell the user: "No state graph was produced. For interactive exploration, you can load the spec in [Spectacle](https://github.com/will62794/spectacle)."

**Step 7.4: Present results narratively.**

By this point, all `spec_error` violations have been resolved in Step 7.2. Only `requirement_conflict` violations (if any) remain.

**If requirement conflicts found** — construct a narrative report using this XML structure internally, then render it as readable text for the user:

```xml
<verification-results status="violations" states="{N}" distinct="{M}">
  <violation id="v1" rule="{invariant name}" rule-description="{plain-English from structured summary}">
    <narrative>
      Here's what can happen: First, {actor does action in domain language}.
      Then {actor does action}. At this point, {describe the state that
      breaks the rule and why it's a problem}.
    </narrative>
    <trace>
      <step n="1" action="Initial state">
        <var name="{name}" value="{value}"/>
        <!-- all vars for initial state -->
      </step>
      <step n="2" action="{domain action label}">
        <change var="{name}" from="{old}" to="{new}"/>
        <!-- only changed vars -->
      </step>
      <!-- ... -->
      <step n="{last}" action="{domain action label}" breaking="true">
        <change var="{name}" from="{old}" to="{new}"/>
      </step>
    </trace>
  </violation>
  <!-- more violations -->
</verification-results>
```

Build this from the verifier's violation traces. Map action names to domain phrases using the transition descriptions from the structured summary. The XML trace data is kept internally so you can present it on demand when the user asks for details.

**Generate trace diagrams.** For each violation, generate a mermaid sequence diagram (for multi-actor concurrent traces) or state diagram (for single-actor traces) using domain action labels from the trace. Write `traces.md` to the artifact directory (`<spec_dir>/<ModuleName>/traces.md`) — one mermaid diagram per violation, each preceded by the violation's one-line summary.

Present to the user as readable text, with the trace diagram location included directly:

> TLC found {N} scenarios where your design rules conflict:
>
> **1. {rule-description}**
> {narrative text}
>
> **2. {rule-description}**
> {narrative text}
>
> Trace diagrams for each violation: `<artifact_dir>/traces.md`

Then use AskUserQuestion:
> "What would you like to do?"

Options:
- "Show me the full trace for [violation]" — render the `<trace>` for that violation as a numbered step list: step number, domain action label, and each `<change>` shown as `var: old → new`. After showing, re-ask this same question.
- "View trace diagrams" — tell the user to open `<artifact_dir>/traces.md`, which contains one mermaid sequence diagram (for multi-actor concurrent traces) or state diagram (for single-actor traces) per violation, labeled with domain actions. After noting the path, re-ask this same question.
- "Fix the design" — discuss which violations to fix, then update the spec to add guards or constraints that prevent them
- "Continue anyway" — the user considers the violations acceptable. Note which violations are being accepted, then proceed to Step 8.

**If the user chooses "Fix the design":** Discuss the violations conversationally. The user may want to fix some and accept others — let them explain in their own words. For each violation they want fixed, understand whether to add a guard/constraint or relax the invariant. Then use AskUserQuestion:
> "Want me to commit the current spec before I make changes? (Makes it easy to roll back.)"

Options:
- "Yes, commit first" — commit, then update the spec
- "No, just make the changes" — update without committing

Then update the spec and re-run from Step 7.1. Repeat until the user is satisfied.

**If clean** (no violations): construct internally:

```xml
<verification-results status="clean" states="{N}" distinct="{M}">
  <invariants>
    <invariant name="{name}" description="{plain-English}" status="pass"/>
    <!-- one per invariant -->
  </invariants>
</verification-results>
```

Present as a one-line summary: "{M} distinct states explored — all rules hold." Then list each invariant with its description as confirmation.

If the verifier's result includes `coverage` data (not `"unavailable"`):

After listing the verified invariants, present coverage analysis:

If `actions_never_fired` is non-empty:
> **Coverage note:** {coverage_ratio as percentage}% of actions were exercised during model checking. The following actions never fired:
> - **{action_name}** — this behavior was never exercised. It may be unreachable with the current model constants, or its guard may be too restrictive.
>
> This doesn't mean the spec is wrong — but these actions weren't tested by the model checker. Consider whether the model constants are large enough to exercise them.

If all actions fired:
> **Coverage:** All {total_actions} actions were exercised during model checking.

Proceed to Step 8.

### Step 8: What's next

Tell the user what's been created:
- Spec files: `<spec_dir>/<ModuleName>.tla` and `.cfg`
- State graph: `<spec_dir>/<ModuleName>/state-graph.json` (if generated)
- Trace diagrams: `<spec_dir>/<ModuleName>/traces.md` (if violations were found)

Then use AskUserQuestion:
> "What would you like to do next?"

Options:
- "Adjust the spec" — the user wants to change the system design (add entities, modify transitions, change constraints, etc.). Discuss what they want to change, update the structured summary to reflect the changes, then re-enter the pipeline at Step 3 (Specify). This runs the full specify → verify cycle with the updated summary.
- "Refine the design" — drill into implementation-level detail to catch concurrency and atomicity bugs. Ask the user about their implementation:
  - "How are these operations actually implemented? Single database transactions? Multiple API calls? Message queues?"
  - "What concurrency control does your system use? Database locks, optimistic concurrency, distributed coordination?"
  - "Where could a failure leave things partially done?"

  Update the structured summary with an `### Implementation Detail` section capturing: operation granularity (which domain actions are actually multi-step), transaction boundaries, atomicity guarantees, retry/failure semantics. Then re-enter the pipeline at Step 3 (Specify). The specifier rewrites the spec at finer granularity — splitting previously-atomic domain actions into multi-step operations with intermediate states, exposing potential interleavings. Re-verify to catch concurrency bugs the abstract spec missed.
- "Update my tests" — generate or update implementation tests to reflect the verified spec. Use AskUserQuestion:
  > "Where is the implementation code I should test against?"

  The user provides a file or directory path. Invoke the **test-gen** agent with: the `.tla` file path, the confirmed structured summary, the implementation path, and any counterexample traces from Step 7 (if violations were found and resolved or accepted during this session). The test-gen agent reads the spec, discovers existing tests, identifies gaps, and generates tests (property-based tests for invariants, state transition tests for action sequences, boundary tests from type constraints, and regression tests from counterexample traces).

  When the test-gen agent returns:
  - **`completed`**: Tell the user what was created — list each test file and the tests within it, grouped by type. Note any new dependencies needed (e.g., a PBT library).
  - **`partial`**: Show what was created, then list the gaps that couldn't be covered and why (usually because the mapping between spec concepts and implementation code was unclear). Use AskUserQuestion to let the user clarify the mapping, then re-invoke the test-gen agent with the clarifications.
  - **`no_implementation_found`**: Tell the user the agent couldn't find implementation code at the path provided. Ask them to point at the right location.

  After presenting results, re-present Step 8 options.
- "Generate a PDF" — same as the Step 6 PDF option: invoke the **specifier** agent to add a top-of-module summary and selective inline comments (only where the logic is non-obvious), then typeset via `tla_tex` with `shade: true`. Tell the user where the PDF was written. Re-present Step 8 options.
- "Done" — wrap up. Note: "The verified spec is at `<path>`. For interactive state-space exploration, load the spec in [Spectacle](https://github.com/will62794/spectacle)."

## Rules

- **Use AskUserQuestion for all decision points.** Never present choices as plain text. Every point where the user must choose between options uses AskUserQuestion.
- **Stop after spec creation.** Always pause at Step 6 to let the user choose their next step. Don't auto-advance.
- **Do stop for violations.** When TLC finds bugs, present via AskUserQuestion and get user input before fixing.
- **Domain knowledge lives in agents.** You handle sequencing and user interaction. The specifier knows TLA+, the verifier knows TLC.
- **Never use Bash for TLA+ toolchain work.** Do not run TLC, SANY, Java, or Python to parse TLC output. Do not read cached MCP tool result files. All TLA+ toolchain interaction is handled by agents calling MCP tools — the verifier returns everything you need.

## Interview Principles

1. **Be concrete, not abstract.** Use the user's terminology, not yours.
2. **Be adversarial about edge cases.** Your job is to find the scenarios they haven't thought about.
3. **Never assume.** If something is ambiguous, ask.
4. **Constraints are sacred.** Spend extra time getting these right — they define what "correct" means.
5. **Structured but conversational.** Each phase is a gate — present what you've captured, get confirmation, then move on. But within each phase, probe conversationally using the user's language. The gates keep things complete; the conversation within keeps things natural.
