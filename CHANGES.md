# Workflow Plugin Changes

Three changes from the architecture review. Changes 1 and 3 modify the verifier agent prompt. Change 2 updates the animator prompt and skill to reference the new split file structure.

---

## Change 1: Verifier reads traces from state-graph.json instead of re-parsing TLC output

**Problem:** The verifier (section 5, lines 153-199) instructs the LLM to read the raw TLC output file and hand-parse counterexample traces in TLC's `State N: ... /\ var = value` format. Meanwhile, `tla_state_graph` already parses these traces deterministically into structured JSON with `stateId`, `action`, and `vars` for each step. The verifier generates state-graph.json in section 4 before reaching section 5, so the data is already available.

**What to do:**

Rewrite section 5 of `agents/verifier.md` (lines 153-199). Replace the TLC output parsing instructions with instructions to read the structured violation traces from state-graph.json.

Replace the current section 5 content with:

```markdown
## 5. Interpret Violations

The `tlc_check` response lists violations with summary info:

- `type`: `"invariant"`, `"deadlock"`, or `"temporal"`
- `name`: the TLA+ property name (e.g., `MutualExclusion`) — may be absent for deadlocks
- `summary`: a brief description

### Reading counterexample traces

The state graph JSON (generated in Step 4 at `<artifact_dir>/state-graph.json`) contains complete structured violation traces. Read it using the Read tool. The `violations` array contains entries like:

```json
{
  "id": "v1",
  "type": "invariant",
  "invariant": "MutualExclusion",
  "summary": "...",
  "trace": [
    {"stateId": "1", "action": null, "vars": {"lock": "free", "clients": {"c1": "idle", "c2": "idle"}}},
    {"stateId": "3", "action": "Acquire", "vars": {"lock": "c1", "clients": {"c1": "holding", "c2": "idle"}}},
    {"stateId": "7", "action": "Acquire", "vars": {"lock": "c2", "clients": {"c1": "holding", "c2": "holding"}}}
  ]
}
```

For each violation trace:
1. The `type` field tells you the violation kind: `"invariant"`, `"deadlock"`, or `"temporal"`.
2. The violated property is in the `invariant` field (for safety violations) or `property` field (for liveness violations). Deadlocks have neither.
3. Each trace step has a `stateId`, `action` (null for the initial state), and `vars` (the complete variable assignment at that state).
4. Diff `vars` between consecutive steps to identify which variables changed.

For **invariant violations**, the trace ends at a state where the invariant is false.

For **deadlocks**, the trace ends at a state where no action in `Next` is enabled.

For **temporal (liveness) violations**, the trace ends with a "Back to state" entry — a lasso indicating an infinite cycle. The property fails because something that should eventually happen never does within that loop.

Use the structured trace data to classify each violation (see section 6).

**Fallback:** If the state graph is unavailable (`state_graph` is `failed` or `skipped`), fall back to reading the raw TLC output file at `output_file`. Parse the `State N:` blocks manually as described in the fallback narrative protocol (section 6).
```

This eliminates the TLC output format documentation (lines 167-197 currently) from the main path and makes it a fallback only. The verifier gets clean structured data with typed fields instead of asking the LLM to parse `State N: <ActionName line N, col M ...>` blocks.

**File:** `agents/verifier.md`

---

## Change 2: Update animator and skill for split playground files

**Problem:** After the MCP server change that splits `playground-gen.js` into `playground-data.js` (GRAPH + title) and `playground-gen.js` (labels + render functions), the animator prompt and skill need to reference the smaller file correctly.

**Depends on:** MCP server Change 2 (the file split) being deployed first.

### `agents/animator.md`

**Line 6 (input section):** Change:
> 6. **`playground_gen_js_path`** — path to the existing `playground-gen.js` to read and rewrite.

No change needed here — the path still points to `playground-gen.js`, which now contains only the sections the animator edits.

**Line 28 (what you produce):** Change:
> Read the existing `playground-gen.js` and its companion `playground-gen.css`, then rewrite ONLY these sections:

To:
> Read the existing `playground-gen.js` and its companion `playground-gen.css`, then rewrite them. The file contains only labels and render functions — the GRAPH data and PLAYGROUND_TITLE live in a separate `playground-data.js` file that you never need to read.

**Lines 369-370 (key constraints):** Change:
> 1. **Never read `state-graph.json`.** The `sample_state` tells you the shape of all variables. The `GRAPH` data in `playground-gen.js` is managed by the deterministic generator.
> 2. **Do NOT modify `GRAPH` or `PLAYGROUND_TITLE`.** These are correct as generated. Only edit the sections listed above.

To:
> 1. **Never read `state-graph.json` or `playground-data.js`.** The `sample_state` tells you the shape of all variables. The GRAPH data and PLAYGROUND_TITLE live in `playground-data.js`, managed by the deterministic generator.
> 2. `playground-gen.js` contains only the sections you edit — no GRAPH or PLAYGROUND_TITLE to worry about.

**Lines 375-378 (steps):** Change step 1:
> 1. Read the existing `playground-gen.js` at the given path.

To:
> 1. Read the existing `playground-gen.js` at the given path. (This file contains only labels and render functions — no GRAPH data.)

**Lines 394-395 (pre-output checklist):** Change:
> - [ ] Did NOT modify `GRAPH` or `PLAYGROUND_TITLE`

To:
> - [ ] Did NOT create or modify `playground-data.js` (GRAPH and PLAYGROUND_TITLE are managed separately)

**File:** `agents/animator.md`

### `skills/tlaplus-workflow/SKILL.md`

**Step 5.4 (line 333):** Update the `playground_init` call to pass the system name as `title`. Change:
> Call the `playground_init` MCP tool with `state_graph_file` set to the verifier's `state_graph_file` path and `target_dir` set to `<spec_dir>/<ModuleName>/playground/`.

To:
> Call the `playground_init` MCP tool with `state_graph_file` set to the verifier's `state_graph_file` path, `target_dir` set to `<spec_dir>/<ModuleName>/playground/`, and `title` set to the system name from the structured summary `## System:` header.

**Step 5.4 (line 335):** Update the animator invocation reference. Change:
> `playground_gen_js_path` set to `<spec_dir>/<ModuleName>/playground/playground-gen.js`.

This doesn't change — the path is still `playground-gen.js`, which now just contains the smaller file.

**File:** `skills/tlaplus-workflow/SKILL.md`

### `CLAUDE.md` (project root)

Update the Key Conventions section. Change:
> The animator writes `playground-gen.js` (data + render functions) and `playground-gen.css` (domain styles) into a `playground/` subdirectory

To:
> `playground_init` writes `playground-data.js` (GRAPH + title, deterministic, never edited) and `playground-gen.js` (labels + render functions, rewritten by animator) plus `playground-gen.css` (domain styles) into a `playground/` subdirectory

**File:** `CLAUDE.md`

---

## Change 3: Add violation classification signals to verifier

**Problem:** The verifier's violation classification (spec_error vs requirement_conflict) is the highest-stakes LLM judgment in the system. The current guidance (verifier.md lines 233-258) is sound but relies on relatively abstract instructions. Adding concrete "signals to look for" patterns will improve consistency.

**What to do:**

In `agents/verifier.md`, add a new subsection after line 258 ("When in doubt, lean toward `requirement_conflict`...") and before the example return at line 260.

Insert:

```markdown
### Classification signals

**Strong signals for `spec_error`:**
- A variable changes between states that no action in the structured summary describes changing (missing UNCHANGED)
- An action fires in a state where the summary says it shouldn't be possible (missing or wrong guard)
- The trace's very first state already violates the invariant (Init predicate is wrong)
- The violation disappears when you mentally add an obvious missing guard from the summary
- An action does the opposite of what the summary describes (e.g., increments instead of decrements)

**Strong signals for `requirement_conflict`:**
- Every action in the trace does exactly what the structured summary describes — the spec faithfully encodes the requirements
- The violated property is a liveness property and the loop contains only correctly-implemented actions blocking each other
- Two "should never happen" constraints are individually satisfiable but jointly unsatisfiable in some reachable state
- The only way to fix the violation would require relaxing or removing a stated requirement
- A deadlock where every action's guard is correctly encoded but the guards collectively block all progress
```

**File:** `agents/verifier.md`
