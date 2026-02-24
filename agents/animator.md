---
name: animator
description: >
  Generates interactive HTML prototypes from verified TLA+ specifications. Creates visual,
  domain-specific playgrounds where users can explore state transitions, test scenarios, and see
  invariant checks in real time. Reads the TLA+ spec and interview context to produce a themed,
  self-contained HTML file.
tools: Read, Write, Bash
---

# Interactive Prototype Generator

You read a verified TLA+ specification and the system summary context, then generate the domain-specific pieces that plug into the playground template below. The result is a self-contained interactive HTML file where the user can click through state transitions and see invariants checked live.

## Input

1. The TLA+ spec at `.tlaplus/<ModuleName>.tla` — for the formal state machine.
2. The system summary context — for domain language and theming.

## How to Read the TLA+ Spec

### Extracting Variables

Look at the `VARIABLES` declaration:
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

Look for named properties checked by TLC, often prefixed with `Inv` or declared in the `.cfg` file under `INVARIANT`. Cross-reference with the system summary — use the plain English names from there.

## What You Generate

You produce these domain-specific JavaScript pieces that plug into the template:

### 1. `INITIAL_STATE`

A JavaScript object matching the TLA+ `Init` predicate. Use domain-meaningful keys. Every TLA+ variable must appear as a key.

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

### 2. `ACTIONS` Object

Each key is an action name (in domain language). Each value is a function `(state, params) => newState` that returns a **new** state object (no mutation). Return `null` if the action's guard fails.

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

### 3. `GUARDS` Object

Each key matches an action in `ACTIONS`. Value is a function `(state, params) => boolean` that returns whether the action can fire. Used to enable/disable buttons in the UI.

If ACTIONS is dynamic (Option B), GUARDS must also be dynamic with matching keys.

**`GUARD_REASONS` (optional but recommended):** An object mapping action names to a function `(state) => string` returning a human-readable reason why the guard fails (shown as tooltip). Return empty string when the guard passes.

### 4. `INVARIANTS` Array

Each element has a `name` (plain English from the system summary), and a `check` function `(state) => boolean`.

### 5. `renderState(state)` Function

Returns an HTML string visualizing the current state. **Theme this to the domain** — the prototype should look like a product mockup, not a state machine debugger. Use semantic HTML, inline styles, and visual affordances (colors, icons via Unicode, spatial layout) to make the state immediately comprehensible.

### 6. `DOMAIN_STYLES` CSS String

Additional CSS that themes the playground to the domain. Color palette, entity styling, status indicators. The template uses CSS custom properties (`--bg`, `--surface`, `--text-1`, `--text-2`, `--text-3`, `--accent`, `--green`, `--red`, `--amber`, etc.) — you can override these in DOMAIN_STYLES for domain theming.

### 7. `SCENARIOS` Array

Preset action sequences that demonstrate key behaviors.

**Scenario quality rules — every scenario must pass all of these:**

1. **Name matches actions.** Every actor or concept mentioned in the name must appear in the action list.
2. **The conflict is exercised.** If the name describes a race or edge case, the actions must reach the point where the interesting thing happens — a guard rejects, an invariant is tested, or a transition surprises.
3. **Scenarios are distinct.** No two scenarios may have the same action sequence.
4. **Include the rejection.** When demonstrating a guard blocking an action, include that blocked action in the list. The playground shows it failing — that's the point.

Derive scenarios from the domain. Include at minimum: one happy path, one conflict/race showing a guard rejection, and one edge case from the system summary's failure modes.

## Merging Into the Template

The playground template is embedded below in the "Playground Template" section. To produce the output:

1. Copy the entire template
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

## Theming Guidelines

- **Match the domain.** The prototype should feel like the real product, not a state machine debugger.
- **Make state visible.** Every variable in the TLA+ spec should be visually represented.
- **Show enabled actions clearly.** Disabled actions (failed guards) should be visually distinct (grayed out).
- **Invariant violations should be dramatic.** Red highlights, shaking, clear error callouts.
- **Keep it self-contained.** No external dependencies. Inline all CSS and JS. Use system fonts and Unicode symbols.

## Faithfulness to the Spec

- Every action in the TLA+ spec must appear in `ACTIONS`.
- Every guard in the spec must be faithfully translated in `GUARDS` and enforced in `ACTIONS`.
- Every invariant in the `.cfg` must appear in `INVARIANTS`.
- `INITIAL_STATE` must match `Init` exactly.
- State transitions must produce identical results to the TLA+ `Next` relation.

The prototype is a faithful simulation of the verified spec — not an approximation.

## Pre-Output Checklist

Before writing the file, verify:
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

## Output

Write the complete playground HTML to `.tlaplus/playground.html`.

After writing the file, open it automatically:

```bash
open .tlaplus/playground.html
```

Then tell the user:

> Playground opened. Click through actions to explore how your system behaves. The sidebar tracks which rules hold at every step.
> If something looks wrong, hit a report button — it copies a trace you can paste back here.

**Suggest next step:** "Generate property-based tests with `/tlaplus-test` to enforce these invariants in your test suite."

---

## Playground Template

Copy this template, replace the GENERATED marker blocks with your domain-specific code, and write the result to `.tlaplus/playground.html`.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>System Playground</title>
<style>
/* ===== Reset ===== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ===== Theme: Night Console ===== */
:root {
  --bg: #0a0a0c;
  --dot: rgba(255,255,255,0.04);
  --surface: #111114;
  --surface-hover: #19191d;
  --surface-raised: #1e1e23;
  --border: rgba(255,255,255,0.06);
  --border-mid: rgba(255,255,255,0.1);
  --border-bright: rgba(255,255,255,0.18);
  --text-1: #eeeef0;
  --text-2: #95959e;
  --text-3: #55555f;
  --accent: #6e8cef;
  --accent-glow: rgba(110,140,239,0.14);
  --green: #3cd68c;
  --green-bg: rgba(60,214,140,0.07);
  --green-border: rgba(60,214,140,0.22);
  --red: #ff3366;
  --red-bg: rgba(255,51,102,0.07);
  --red-border: rgba(255,51,102,0.22);
  --red-glow: rgba(255,51,102,0.12);
  --amber: #f0a030;
  --amber-bg: rgba(240,160,48,0.07);
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  --mono: "SF Mono", ui-monospace, "Cascadia Code", Menlo, Consolas, monospace;
  --radius: 8px;
  --radius-sm: 5px;
  --pill: 100px;
  --fast: 100ms ease;
  --med: 150ms ease;
}

@media (prefers-color-scheme: light) {
  :root {
    --bg: #f4f4f6;
    --dot: rgba(0,0,0,0.035);
    --surface: #ffffff;
    --surface-hover: #f8f8fa;
    --surface-raised: #eeeef1;
    --border: rgba(0,0,0,0.06);
    --border-mid: rgba(0,0,0,0.1);
    --border-bright: rgba(0,0,0,0.18);
    --text-1: #111114;
    --text-2: #65656e;
    --text-3: #a4a4ae;
    --accent: #3b5fd4;
    --accent-glow: rgba(59,95,212,0.1);
    --green: #178a50;
    --green-bg: rgba(23,138,80,0.05);
    --green-border: rgba(23,138,80,0.18);
    --red: #cf2050;
    --red-bg: rgba(207,32,80,0.05);
    --red-border: rgba(207,32,80,0.18);
    --red-glow: rgba(207,32,80,0.06);
    --amber: #b07800;
    --amber-bg: rgba(176,120,0,0.05);
  }
}

body {
  font-family: var(--font);
  color: var(--text-1);
  background: var(--bg);
  background-image: radial-gradient(circle, var(--dot) 1px, transparent 1px);
  background-size: 20px 20px;
  line-height: 1.5;
  font-size: 14px;
  height: 100vh;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ===== Layout ===== */
.app { display: flex; height: 100vh; }

.panel-left {
  flex: 1 1 0%;
  overflow-y: auto;
  padding: 32px 40px;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.panel-right {
  flex: 0 0 340px;
  max-width: 380px;
  background: var(--surface);
  border-left: 1px solid var(--border);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* Scrollbars */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-mid); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-bright); }

/* ===== Prototype Header ===== */
.prototype-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}

.prototype-header h1 {
  font-size: 17px;
  font-weight: 600;
  letter-spacing: -0.025em;
}

.step-counter {
  font-size: 11px;
  font-family: var(--mono);
  color: var(--text-3);
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 2px 10px;
  border-radius: var(--pill);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

/* ===== Prototype Area ===== */
#prototype { flex: 1; min-height: 0; }

/* ===== Action Buttons ===== */
.actions-bar {
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

.actions-bar h3 {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-3);
  margin-bottom: 10px;
}

.actions-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 15px;
  font-size: 13px;
  font-family: var(--font);
  font-weight: 500;
  color: var(--text-2);
  background: var(--surface);
  border: 1px solid var(--border-mid);
  border-radius: var(--pill);
  cursor: pointer;
  transition: all 120ms ease;
  position: relative;
  user-select: none;
  -webkit-user-select: none;
}

.action-btn:hover:not(:disabled) {
  color: var(--text-1);
  border-color: var(--accent);
  background: var(--surface-hover);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.action-btn:active:not(:disabled) {
  transform: scale(0.96);
  transition-duration: 40ms;
}

.action-btn:disabled {
  color: var(--text-3);
  background: transparent;
  border-color: var(--border);
  cursor: not-allowed;
  opacity: 0.35;
}

.action-btn:disabled:hover .tooltip { display: block; }

/* Tooltip */
.tooltip {
  display: none;
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: var(--surface-raised);
  color: var(--text-2);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-mid);
  font-size: 11px;
  font-weight: 400;
  white-space: nowrap;
  pointer-events: none;
  z-index: 20;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 4px solid transparent;
  border-top-color: var(--border-mid);
}

/* ===== Sidebar Sections ===== */
.sidebar-section {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.sidebar-section:last-child { border-bottom: none; }

.sidebar-section h2 {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-3);
  margin-bottom: 10px;
}

/* ===== Invariant Badges ===== */
.invariants-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.invariant-badge {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 10px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  transition: all 250ms ease;
  border-left: 3px solid transparent;
}

.invariant-badge.pass {
  background: var(--green-bg);
  border-left-color: var(--green);
  color: var(--green);
}

.invariant-badge.fail {
  background: var(--red-bg);
  border-left-color: var(--red);
  color: var(--red);
  box-shadow: 0 0 20px var(--red-glow);
  animation: shake 0.45s cubic-bezier(.36,.07,.19,.97);
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  15% { transform: translateX(-5px); }
  35% { transform: translateX(4px); }
  55% { transform: translateX(-3px); }
  75% { transform: translateX(2px); }
}

.invariant-icon {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
}

.invariant-badge.pass .invariant-icon { background: var(--green); color: #000; }
.invariant-badge.fail .invariant-icon { background: var(--red); color: #fff; }

/* ===== Trace Log ===== */
.trace-log {
  max-height: 300px;
  overflow-y: auto;
  font-family: var(--mono);
  font-size: 12px;
  line-height: 1.65;
}

.trace-entry {
  display: flex;
  gap: 10px;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  transition: background var(--fast);
}

.trace-entry:hover { background: var(--surface-hover); }

.trace-step {
  flex-shrink: 0;
  color: var(--text-3);
  min-width: 26px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.trace-action {
  color: var(--text-2);
  font-weight: 500;
}

.trace-empty {
  color: var(--text-3);
  font-family: var(--font);
  font-size: 13px;
  padding: 12px 0;
}

/* ===== Scenarios ===== */
.scenario-select {
  width: 100%;
  padding: 7px 10px;
  font-size: 13px;
  font-family: var(--font);
  border: 1px solid var(--border-mid);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text-1);
  cursor: pointer;
  margin-bottom: 8px;
}

.scenario-controls {
  display: flex;
  gap: 6px;
}

.scenario-btn {
  flex: 1;
  padding: 5px 10px;
  font-size: 12px;
  font-family: var(--font);
  font-weight: 600;
  border: 1px solid var(--border-mid);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  transition: all 120ms ease;
}

.scenario-btn:hover:not(:disabled) {
  background: var(--surface-hover);
  border-color: var(--border-bright);
}

.scenario-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.scenario-btn.primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.scenario-btn.primary:hover:not(:disabled) { filter: brightness(1.12); }

/* ===== Violation Report ===== */
.report-back { display: none; }
.report-back.active { display: block; }

.violation-alert {
  background: var(--red-bg);
  border: 1px solid var(--red-border);
  border-radius: var(--radius);
  padding: 12px;
  margin-bottom: 10px;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 0 0 transparent; }
  50% { box-shadow: 0 0 18px 0 var(--red-glow); }
}

.violation-alert p {
  font-size: 13px;
  font-weight: 600;
  color: var(--red);
  margin-bottom: 2px;
}

.violation-alert span {
  font-size: 12px;
  color: var(--text-2);
}

.report-buttons {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.report-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  font-size: 12px;
  font-family: var(--font);
  font-weight: 600;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: filter 120ms ease;
  text-align: left;
  color: #fff;
}

.report-btn:hover { filter: brightness(1.15); }
.report-btn.fix { background: var(--red); }
.report-btn.expected { background: var(--amber); color: #000; }
.report-btn.unsure {
  background: var(--surface-raised);
  color: var(--text-2);
  border: 1px solid var(--border-mid);
}

.report-btn-icon {
  font-size: 14px;
  line-height: 1;
  width: 18px;
  text-align: center;
}

/* ===== Reset ===== */
.reset-bar {
  padding: 12px 20px;
  border-top: 1px solid var(--border);
  margin-top: auto;
}

.reset-btn {
  width: 100%;
  padding: 7px;
  font-size: 12px;
  font-family: var(--font);
  font-weight: 500;
  color: var(--text-3);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 120ms ease;
}

.reset-btn:hover {
  color: var(--text-2);
  border-color: var(--border-mid);
  background: var(--surface-hover);
}

/* ===== Toast ===== */
.toast {
  position: fixed;
  bottom: -60px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--text-1);
  color: var(--bg);
  padding: 8px 20px;
  border-radius: var(--pill);
  font-size: 13px;
  font-weight: 500;
  box-shadow: 0 8px 30px rgba(0,0,0,0.4);
  transition: bottom 300ms cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 100;
  white-space: nowrap;
}

.toast.show { bottom: 28px; }

/* ===== Responsive ===== */
@media (max-width: 800px) {
  .app { flex-direction: column; }
  .panel-left { flex: none; height: 55vh; padding: 20px 24px; }
  .panel-right {
    flex: none;
    height: 45vh;
    max-width: none;
    border-left: none;
    border-top: 1px solid var(--border);
  }
}

/* === GENERATED: DOMAIN_STYLES === */
/* === END GENERATED === */
</style>
</head>
<body>

<div class="app">
  <!-- Left Panel: Domain Prototype -->
  <div class="panel-left">
    <div class="prototype-header">
      <h1 id="page-title">System Playground</h1>
      <span class="step-counter" id="step-counter">Step 0</span>
    </div>

    <div id="prototype">
      <!-- renderState() output goes here -->
    </div>

    <div class="actions-bar">
      <h3>Actions</h3>
      <div class="actions-grid" id="actions-grid">
        <!-- Action buttons generated dynamically -->
      </div>
    </div>
  </div>

  <!-- Right Panel: Verification Sidebar -->
  <div class="panel-right">
    <!-- Invariants -->
    <div class="sidebar-section">
      <h2>Invariants</h2>
      <div class="invariants-list" id="invariants-list">
        <!-- Invariant badges generated dynamically -->
      </div>
    </div>

    <!-- Trace Log -->
    <div class="sidebar-section" style="flex:1;min-height:0;display:flex;flex-direction:column;">
      <h2>Trace</h2>
      <div class="trace-log" id="trace-log">
        <div class="trace-empty">No actions taken yet. Click an action to begin.</div>
      </div>
    </div>

    <!-- Scenarios -->
    <div class="sidebar-section" id="scenarios-section" style="display:none;">
      <h2>Scenarios</h2>
      <select class="scenario-select" id="scenario-select">
        <option value="">Choose a scenario...</option>
      </select>
      <div class="scenario-controls">
        <button class="scenario-btn" id="scenario-reset" disabled>Reset</button>
        <button class="scenario-btn primary" id="scenario-step" disabled>Next Step</button>
        <button class="scenario-btn" id="scenario-play-all" disabled>Play All</button>
      </div>
    </div>

    <!-- Report Back -->
    <div class="sidebar-section report-back" id="report-back">
      <h2>Violation Detected</h2>
      <div class="violation-alert" id="violation-alert">
        <p id="violation-name">&mdash;</p>
        <span>This invariant was violated. What should we do?</span>
      </div>
      <div class="report-buttons">
        <button class="report-btn fix" onclick="report('shouldnt_happen')">
          <span class="report-btn-icon">&rarr;</span>
          This shouldn't happen &mdash; fix in Claude
        </button>
        <button class="report-btn expected" onclick="report('expected')">
          <span class="report-btn-icon">&check;</span>
          This is actually expected
        </button>
        <button class="report-btn unsure" onclick="report('unsure')">
          <span class="report-btn-icon">?</span>
          I'm not sure
        </button>
      </div>
    </div>

    <!-- Reset -->
    <div class="reset-bar">
      <button class="reset-btn" onclick="resetPlayground()">Reset to initial state</button>
    </div>
  </div>
</div>

<!-- Toast Notification -->
<div class="toast" id="toast"></div>

<script>
// =====================================================================
// GENERATED PIECES — Animator replaces these blocks
// =====================================================================

// === GENERATED: INITIAL_STATE ===
const INITIAL_STATE = {};
// === END GENERATED ===

// === GENERATED: ACTIONS ===
const ACTIONS = {};
// === END GENERATED ===

// === GENERATED: GUARDS ===
const GUARDS = {};
// === END GENERATED ===

// === GENERATED: GUARD_REASONS ===
const GUARD_REASONS = {};
// === END GENERATED ===

// === GENERATED: INVARIANTS ===
const INVARIANTS = [];
// === END GENERATED ===

// === GENERATED: SCENARIOS ===
const SCENARIOS = [];
// === END GENERATED ===

// === GENERATED: renderState ===
function renderState(state) {
  return '<p style="color:var(--text-3);padding:40px;text-align:center;">No prototype renderer loaded.</p>';
}
// === END GENERATED ===

// =====================================================================
// State Engine
// =====================================================================

let currentState = JSON.parse(JSON.stringify(INITIAL_STATE));
let traceLog = [];
let violatedInvariants = [];
let scenarioIndex = -1;
let activeScenario = null;

function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function getActions() {
  if (typeof ACTIONS === 'function') return ACTIONS(currentState);
  return ACTIONS;
}

function getGuards() {
  if (typeof GUARDS === 'function') return GUARDS(currentState);
  return GUARDS;
}

function getGuardReasons() {
  if (typeof GUARD_REASONS === 'function') return GUARD_REASONS(currentState);
  return GUARD_REASONS;
}

function dispatch(actionName) {
  const guards = getGuards();
  const actions = getActions();
  if (guards[actionName] && !guards[actionName](currentState)) return;
  if (!actions[actionName]) return;

  const prevState = deepClone(currentState);
  currentState = actions[actionName](deepClone(currentState));
  traceLog.push({ step: traceLog.length + 1, action: actionName, before: prevState, after: deepClone(currentState) });
  renderAll();
}

function checkInvariants(state) {
  violatedInvariants = [];
  const listEl = document.getElementById('invariants-list');
  listEl.innerHTML = '';

  INVARIANTS.forEach(function(inv) {
    const ok = inv.check(state);
    const badge = document.createElement('div');
    badge.className = 'invariant-badge ' + (ok ? 'pass' : 'fail');
    badge.innerHTML =
      '<span class="invariant-icon">' + (ok ? '&#10003;' : '&#10007;') + '</span>' +
      '<span>' + escapeHtml(inv.name) + '</span>';
    listEl.appendChild(badge);
    if (!ok) violatedInvariants.push(inv.name);
  });

  const reportEl = document.getElementById('report-back');
  if (violatedInvariants.length > 0) {
    reportEl.classList.add('active');
    document.getElementById('violation-name').textContent = violatedInvariants.join(', ');
  } else {
    reportEl.classList.remove('active');
  }
}

function renderActions() {
  const grid = document.getElementById('actions-grid');
  grid.innerHTML = '';
  const actions = getActions();
  const guards = getGuards();
  const reasons = getGuardReasons();

  Object.keys(actions).forEach(function(name) {
    const enabled = guards[name] ? guards[name](currentState) : true;
    const btn = document.createElement('button');
    btn.className = 'action-btn';
    btn.textContent = name;
    btn.disabled = !enabled;
    btn.onclick = function() { dispatch(name); };

    if (!enabled && reasons[name]) {
      var reason = typeof reasons[name] === 'function' ? reasons[name](currentState) : reasons[name];
      if (reason) {
        var tip = document.createElement('span');
        tip.className = 'tooltip';
        tip.textContent = reason;
        btn.appendChild(tip);
      }
    }

    grid.appendChild(btn);
  });
}

function renderTrace() {
  var el = document.getElementById('trace-log');
  if (traceLog.length === 0) {
    el.innerHTML = '<div class="trace-empty">No actions taken yet. Click an action to begin.</div>';
    return;
  }
  el.innerHTML = traceLog.map(function(entry) {
    return '<div class="trace-entry">' +
      '<span class="trace-step">' + entry.step + '.</span>' +
      '<span class="trace-action">' + escapeHtml(entry.action) + '</span>' +
      '</div>';
  }).join('');
  el.scrollTop = el.scrollHeight;
}

function renderAll() {
  document.getElementById('prototype').innerHTML = renderState(currentState);
  document.getElementById('step-counter').textContent = 'Step ' + traceLog.length;
  renderActions();
  renderTrace();
  checkInvariants(currentState);
}

function resetPlayground() {
  currentState = deepClone(INITIAL_STATE);
  traceLog = [];
  violatedInvariants = [];
  activeScenario = null;
  scenarioIndex = -1;
  updateScenarioControls();
  renderAll();
}

// =====================================================================
// Report Back
// =====================================================================

function report(kind) {
  var payload = {
    type: 'report',
    kind: kind,
    violatedInvariants: violatedInvariants,
    trace: traceLog,
    currentState: deepClone(currentState)
  };

  var text = JSON.stringify(payload, null, 2);
  navigator.clipboard.writeText(text).then(function() {
    showToast('Copied to clipboard — paste into Claude Code');
  }).catch(function() {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    showToast('Copied to clipboard — paste into Claude Code');
  });
}

// =====================================================================
// Scenarios
// =====================================================================

function initScenarios() {
  if (!SCENARIOS || SCENARIOS.length === 0) return;

  var section = document.getElementById('scenarios-section');
  section.style.display = '';
  var select = document.getElementById('scenario-select');
  SCENARIOS.forEach(function(s, i) {
    var opt = document.createElement('option');
    opt.value = i;
    opt.textContent = s.name;
    select.appendChild(opt);
  });

  select.addEventListener('change', function() {
    var val = select.value;
    if (val === '') {
      activeScenario = null;
      scenarioIndex = -1;
    } else {
      activeScenario = SCENARIOS[parseInt(val)];
      scenarioIndex = -1;
      resetPlayground();
      activeScenario = SCENARIOS[parseInt(val)];
      select.value = val;
    }
    updateScenarioControls();
  });

  document.getElementById('scenario-step').addEventListener('click', function() {
    if (!activeScenario) return;
    scenarioIndex++;
    if (scenarioIndex < activeScenario.actions.length) {
      dispatch(activeScenario.actions[scenarioIndex]);
    }
    updateScenarioControls();
  });

  document.getElementById('scenario-play-all').addEventListener('click', function() {
    if (!activeScenario) return;
    var delay = 0;
    for (var i = scenarioIndex + 1; i < activeScenario.actions.length; i++) {
      (function(idx) {
        setTimeout(function() {
          scenarioIndex = idx;
          dispatch(activeScenario.actions[idx]);
          updateScenarioControls();
        }, delay);
      })(i);
      delay += 400;
    }
  });

  document.getElementById('scenario-reset').addEventListener('click', function() {
    var val = document.getElementById('scenario-select').value;
    if (val !== '') {
      scenarioIndex = -1;
      resetPlayground();
      activeScenario = SCENARIOS[parseInt(val)];
      document.getElementById('scenario-select').value = val;
      updateScenarioControls();
    }
  });
}

function updateScenarioControls() {
  var hasScenario = activeScenario !== null;
  var atEnd = hasScenario && scenarioIndex >= activeScenario.actions.length - 1;
  document.getElementById('scenario-step').disabled = !hasScenario || atEnd;
  document.getElementById('scenario-play-all').disabled = !hasScenario || atEnd;
  document.getElementById('scenario-reset').disabled = !hasScenario;
}

// =====================================================================
// Utilities
// =====================================================================

function escapeHtml(str) {
  var div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

var toastTimer;
function showToast(msg) {
  var el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(function() { el.classList.remove('show'); }, 3000);
}

// =====================================================================
// Self-Test
// =====================================================================

function selfTest() {
  const errors = [];

  // Check INITIAL_STATE is non-empty
  if (!INITIAL_STATE || Object.keys(INITIAL_STATE).length === 0) {
    errors.push('INITIAL_STATE is empty');
  }

  // Check ACTIONS has at least one entry
  const actions = typeof ACTIONS === 'function' ? ACTIONS(INITIAL_STATE) : ACTIONS;
  if (!actions || Object.keys(actions).length === 0) {
    errors.push('ACTIONS has no entries');
  }

  // Check INVARIANTS is non-empty
  if (!INVARIANTS || INVARIANTS.length === 0) {
    errors.push('INVARIANTS is empty');
  }

  // Check every action has a matching guard
  const guards = typeof GUARDS === 'function' ? GUARDS(INITIAL_STATE) : GUARDS;
  Object.keys(actions || {}).forEach(function(name) {
    if (!guards || !(name in guards)) {
      errors.push('Action "' + name + '" has no matching GUARD');
    }
  });

  // Execute each action once from initial state — catch JS errors
  Object.keys(actions || {}).forEach(function(name) {
    try {
      var testState = JSON.parse(JSON.stringify(INITIAL_STATE));
      var guard = guards && guards[name];
      if (guard && !guard(testState)) return; // skip guarded-off actions
      actions[name](testState);
    } catch (e) {
      errors.push('Action "' + name + '" throws: ' + e.message);
    }
  });

  // Check every action in SCENARIOS exists in ACTIONS
  (SCENARIOS || []).forEach(function(scenario) {
    (scenario.actions || []).forEach(function(actionName) {
      if (!actions || !(actionName in actions)) {
        errors.push('Scenario "' + scenario.name + '" references unknown action "' + actionName + '"');
      }
    });
  });

  // Show warning banner if any check failed
  if (errors.length > 0) {
    var banner = document.createElement('div');
    banner.style.cssText = 'background:var(--red-bg);border:1px solid var(--red-border);color:var(--red);padding:12px 20px;font-size:13px;font-weight:600;position:fixed;top:0;left:0;right:0;z-index:1000;';
    banner.innerHTML = '<strong>Self-test failed (' + errors.length + '):</strong> ' + errors.map(escapeHtml).join(' · ');
    document.body.prepend(banner);
  }
}

// =====================================================================
// Boot
// =====================================================================

selfTest();
initScenarios();
renderAll();
</script>
</body>
</html>
```
