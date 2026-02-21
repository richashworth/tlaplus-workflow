---
name: tlaplus-animate
description: >
  Generate an interactive HTML playground that animates a TLA+ specification as a domain-specific
  prototype. Reads a .tla spec and system summary, produces a split-pane HTML file where the left
  panel looks like a real product mockup and the right panel shows verification state (invariant
  badges, trace log, report-back buttons). Output is written to .tlaplus/playground.html.
user-invocable: true
---

# TLA+ Animator — Skill Instructions

You are the animator agent. Your job: take a TLA+ specification and its system summary, and produce a **single self-contained HTML file** that looks like a real product prototype but is actually an interactive TLA+ state explorer.

The PM clicking through your output doesn't know they're doing formal verification. Make it look like a product mockup with devtools docked to the side.

## Inputs

1. **TLA+ spec** — a `.tla` file in `.tlaplus/`
2. **System summary** — the structured output from the elicitor agent (entities, actions, guards, invariants, domain language)

If `$ARGUMENTS` is provided, use it as the path to the `.tla` file. Otherwise, look for `.tla` files in `.tlaplus/`.

## Output

Write a single file: **`.tlaplus/playground.html`**

This file is the playground template (from `skills/tlaplus-animate/templates/playground-template.html`) with all generated pieces merged in, replacing the placeholder markers.

## What You Generate

You produce six pieces that plug into the template. Each replaces a marked placeholder block.

### 1. `INITIAL_STATE` — the starting state

A plain JS object that mirrors the TLA+ `Init` predicate.

**TLA+ → JS type mapping:**

| TLA+ Type | JS Representation | Example |
|---|---|---|
| Set of values (`{a, b, c}`) | `Array` | `["a", "b", "c"]` |
| SUBSET S (power set) | not needed at runtime — pick one element | `["a"]` |
| Function `[S -> T]` | `Object` with string keys | `{node1: "idle", node2: "idle"}` |
| Sequence `<<a, b>>` | `Array` | `["a", "b"]` |
| Record `[field1 |-> v1]` | `Object` | `{field1: "v1"}` |
| Nat / Int | `number` | `0` |
| BOOLEAN | `boolean` | `true` |
| String | `string` | `"waiting"` |
| Model value (`c1, c2`) | `string` | `"c1"` |
| CHOOSE | pick a concrete value | `"node1"` |

Translate the `Init` predicate directly — every TLA+ variable becomes a key in this object.

### 2. `ACTIONS` — state transition functions

An object mapping action names to pure functions: `(state) => newState`.

Each action corresponds to a TLA+ action (Next disjunct). For parameterized actions, generate one entry per concrete parameter combination, or generate them dynamically.

**Strategy for parameterized actions:**

Option A — enumerate concrete combinations (best for small parameter spaces):
```javascript
const ACTIONS = {
  "Acquire R1 by N1": (state) => { /* clone, apply effect, return */ },
  "Acquire R1 by N2": (state) => { /* ... */ }
};
```

Option B — generate dynamically (for large parameter spaces):
```javascript
function makeActions(state) {
  const actions = {};
  for (const actor of Object.keys(state.actors)) {
    for (const res of Object.keys(state.resources)) {
      actions[`Acquire ${res} by ${actor}`] = (st) => { /* ... */ };
    }
  }
  return actions;
}
```

If using Option B, the template's `getActions()` helper supports dynamic action generation. Set `ACTIONS` to a function `(state) => ({...})` instead of a static object.

**Rules:**
- Never mutate the input state. Always deep-clone first.
- The returned object must have the exact same shape as `INITIAL_STATE`.
- Action names should use domain language, not TLA+ identifiers.

### 3. `GUARDS` — action preconditions

An object mapping each action name to a predicate: `(state) => boolean`.

Guards correspond to the enabling conditions of TLA+ actions (the part before `/\` that constrains when the action can fire).

If ACTIONS is dynamic (Option B), GUARDS must also be dynamic with matching keys.

**Important:** When a guard returns false, the UI disables the button. Add a `GUARD_REASONS` object (optional) that maps action names to a function `(state) => string` returning a human-readable reason shown as a tooltip. Return empty string when the guard passes.

### 4. `INVARIANTS` — safety properties

An array of objects, each with:
- `name`: plain English label (from the elicitor's invariant list)
- `check`: `(state) => boolean` — returns true when the invariant holds

Each invariant from the system summary must have a corresponding entry. The `name` should be the plain English statement from the summary, not the TLA+ identifier.

### 5. `DOMAIN_STYLES` — CSS for the prototype panel

CSS rules scoped to `#prototype` that make the left panel look like the real product domain.

Use the domain to guide visual choices. Examples of what domain-appropriate styling looks like:
- **Lock manager** → node circles, holder badges, queue lists
- **Payment flow** → transaction cards, status pills, balance displays
- **Chat system** → message bubbles, user avatars, channel lists
- **Queue system** → visual queue with items and capacity indicator

### 6. `renderState(state)` — render function

A function that takes the current state and returns an HTML string for the prototype panel.

**Design principles:**
- Make it look like a real product UI, not a debugging tool
- Use the domain language everywhere (no TLA+ jargon)
- Show all state variables in a natural way for the domain
- Use color, layout, and typography to convey status
- Keep it readable — a PM should immediately understand what they're looking at

### 7. `SCENARIOS` — preset action sequences

An array of named sequences for replaying interesting traces (especially TLC counterexamples).

**Scenario quality rules — every scenario must pass all of these:**

1. **Name matches actions.** Every actor or concept mentioned in the name must appear in the action list. A scenario named "two actors, same resource" must include actions from both actors on the same resource.
2. **The conflict is exercised.** If the name describes a race, conflict, or edge case, the actions must reach the point where the interesting thing happens — a guard rejects an action, an invariant is tested, or a state transition surprises. Don't stop short.
3. **Scenarios are distinct.** No two scenarios may have the same action sequence. If two scenarios would produce identical steps, one of them isn't demonstrating what it claims.
4. **Include the rejection.** When a scenario demonstrates a guard blocking an action, include that blocked action in the list. The playground will show it failing — that's the point.

Derive scenario names and action sequences from the domain. Include at minimum: one happy path, one conflict/race showing a guard rejection, and one edge case from the system summary's failure modes.

## How to Read the TLA+ Spec

### Extracting Variables

Look at the `VARIABLES` declaration or `variables` keyword:
```tla
VARIABLES nodeState, lockHolder, queue
```
Each variable becomes a key in the state object.

### Extracting Init

The `Init` predicate defines starting values. Translate each conjunct to a JS property assignment.

### Extracting Actions

Each disjunct of `Next` is an action:
```tla
Next == Acquire \/ Release \/ Enqueue

Acquire(n, r) ==
  /\ nodeState[n] = "idle"         \** ← guard (no prime = current state constraint)
  /\ lockHolder[r] = "none"        \** ← guard
  /\ nodeState' = [nodeState EXCEPT ![n] = "holding"]  \** ← effect (prime = next state)
  /\ lockHolder' = [lockHolder EXCEPT ![r] = n]        \** ← effect
```
- Lines without primed variables (`'`) that constrain current state → **guards**
- Lines with primed variables → **effects**

### Extracting Invariants

Look for named properties checked by TLC, often prefixed with `Inv` or declared in the `.cfg` file under `INVARIANT`.

Cross-reference with the elicitor's system summary — use the plain English names from there.

## Merging Into the Template

1. Read the template from `skills/tlaplus-animate/templates/playground-template.html`
2. For each generated piece, find the corresponding marker block:
   ```
   // === GENERATED: INITIAL_STATE ===
   const INITIAL_STATE = {}; // REPLACE
   // === END GENERATED ===
   ```
3. Replace everything between `=== GENERATED: X ===` and `=== END GENERATED ===` (exclusive of markers) with your generated code
4. For `DOMAIN_STYLES`, find the `/* === GENERATED: DOMAIN_STYLES === */` CSS block and replace similarly
5. Update the page `<title>` to match the domain (e.g., "Lock Manager — Playground")
6. Write the merged result to `.tlaplus/playground.html`

## Checklist Before Writing Output

- [ ] Every TLA+ variable is represented in INITIAL_STATE
- [ ] Every TLA+ action has a corresponding ACTIONS entry (with all parameter combos)
- [ ] Every action has a matching GUARD entry
- [ ] Every invariant from the system summary has an INVARIANTS entry
- [ ] renderState displays ALL state variables (nothing hidden)
- [ ] Action names use domain language, not TLA+ identifiers
- [ ] Invariant names are plain English
- [ ] DOMAIN_STYLES makes the prototype look like a real product
- [ ] No external dependencies — everything is inline
- [ ] The HTML file opens correctly in a browser with no errors in console

After writing the file, **open it automatically** by running:

```bash
open .tlaplus/playground.html
```

Then tell the user:

> Playground opened. Click through actions to explore how your system behaves. The sidebar tracks which rules hold at every step.
> If something looks wrong, hit a report button — it copies a trace you can paste back here.
