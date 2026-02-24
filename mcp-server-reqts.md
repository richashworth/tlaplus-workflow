# MCP Server Requirements: `tlaplus`

Requirements for an MCP server that wraps the TLA+ toolchain (`tla2tools.jar`) to support the [tlaplus-workflow](https://github.com/) Claude Code plugin. This document is derived from analysis of the plugin's agent prompts, skill orchestration, hooks, and configuration.

---

## 1. Overview

The server provides MCP tools that wrap Java-based TLA+ tooling (SANY parser, TLC model checker, PlusCal translator, TLATeX typesetter). It is the **sole interface** between the plugin's agents and the TLA+ toolchain — agents are explicitly instructed never to invoke `java`, `tla2sany.SANY`, TLC, or any CLI command directly.

**Server name in MCP config:** `tlaplus`
**Transport:** stdio (launched as a child process via `node <path>/dist/index.js`)

---

## 2. Toolchain Management

The server must manage `tla2tools.jar` automatically:

- **Auto-download** on first use if not present locally.
- **Store at** `$HOME/.tlaplus-mcp/lib/tla2tools.jar` — the plugin's post-write hook (`hooks/check-tla-syntax.sh`) hard-codes this path to run SANY outside the MCP server for instant syntax feedback after file edits.
- The hook invokes: `java -cp $HOME/.tlaplus-mcp/lib/tla2tools.jar tla2sany.SANY "$FILE_PATH"` — so the jar must be a complete `tla2tools.jar` containing `tla2sany.SANY` on the classpath.

---

## 3. MCP Tools — Critical Path

These three tools are on the primary pipeline path. Every verification run uses them. Their input/output contracts are tightly coupled to agent prompts.

### 3.1 `tla_parse` — SANY Syntax Check

**Used by:** specifier agent (after writing `.tla`), verifier agent (pre-check before TLC)

**Purpose:** Fast syntax validation via SANY. Does not run TLC.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `tla_file` | string | yes | Absolute path to the `.tla` file to parse |

**Expected return shape:**

```json
{
  "valid": true | false,
  "errors": [
    {
      "message": "string — the SANY error message",
      "location": {
        "file": "string — path to the file",
        "line": 42,
        "col": 10
      }
    }
  ]
}
```

**Behavioral notes:**
- The specifier loops on this tool until `valid` is `true`, silently fixing parse errors.
- The verifier treats parse failure as a hard stop — it will not proceed to TLC.
- Errors must include structured location info (`file`, `line`, `col`), not just raw SANY output.

---

### 3.2 `tlc_check` — TLC Exhaustive Model Checking

**Used by:** verifier agent exclusively

**Purpose:** Run TLC in exhaustive breadth-first mode. Check invariants, liveness properties, and (by default) deadlock freedom.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `tla_file` | string | yes | — | Absolute path to the `.tla` spec file |
| `cfg_file` | string | no | same basename as `tla_file` with `.cfg` | Path to the TLC configuration file |
| `continue` | boolean | no | `false` | If `true`, find all violations (don't stop at first). The verifier always passes `true`. |
| `generate_states` | boolean | no | `false` | If `true`, dump the state graph in DOT format. The verifier always passes `true`. |
| `dump_path` | string | no | — | Directory path for the DOT state graph file. The verifier sets this to `<spec_dir>/<ModuleName>/states`. Parent directories should be created if needed. |
| `deadlock` | boolean | no | `true` | Check for deadlocks. Only set `false` for intentionally terminating systems. |
| `workers` | integer or `"auto"` | no | — | Number of worker threads |
| `max_set_size` | integer | no | TLC default (1000000) | Override TLC's max set size |
| `dfid` | integer | no | — | Use depth-first iterative deepening with given depth |
| `extra_args` | string[] | no | — | Additional raw TLC arguments |

**Expected return shape:**

```json
{
  "status": "success" | "violation" | "error",
  "states_found": 2847,
  "distinct_states": 1523,
  "violations": [
    {
      "type": "invariant" | "deadlock" | "temporal",
      "name": "MutualExclusion",
      "summary": "brief description of the violation"
    }
  ],
  "errors": [
    { "message": "string" }
  ],
  "dump_file": "/absolute/path/to/states.dot",
  "raw_output": "full TLC stdout+stderr as a single string"
}
```

**Behavioral notes:**
- `status` must clearly distinguish three outcomes: clean run (`"success"`), property violations found (`"violation"`), and TLC errors/crashes (`"error"`).
- `violations` is an array — with `continue: true`, TLC may find multiple violations in a single run.
- `raw_output` is critical — the verifier parses counterexample traces from it (see section 5 below). It must contain the full TLC output including `State N:` blocks with `/\ var = value` lines.
- `dump_file` should contain the absolute path to the generated `.dot` file when `generate_states` is `true`. If TLC errored before producing the dump, this field should be absent/null.
- The verifier uses `dump_file` to feed into `tla_state_graph`.
- Common TLC errors the verifier handles:
  - `OutOfMemoryError` — state space too large
  - `EvalException` — missing CONSTANT or evaluation failure
  - Undefined identifier errors — missing EXTENDS or CONSTANT
  - Type mismatch errors (integer vs model value)

---

### 3.3 `tla_state_graph` — Parse DOT State Graph

**Used by:** verifier agent (passes result to animator agent)

**Purpose:** Parse a TLC-generated DOT state graph file into structured JSON suitable for the interactive playground.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dot_file` | string | yes | Absolute path to the `.dot` file (from `tlc_check`'s `dump_file`) |
| `cfg_file` | string | no | Path to `.cfg` file — used to extract invariant/property names |
| `tlc_output` | string | no | Raw TLC output string (from `tlc_check`'s `raw_output`) — used to extract violation traces |
| `tlc_output_file` | string | no | Alternative: path to a file containing TLC output |
| `format` | string | no | `"playground"` (the verifier always uses this), `"dot"` (raw), or `"structured"` (adjacency list) |

**Expected return shape (format = `"playground"`):**

```json
{
  "initialStateId": "1",
  "states": {
    "1": {
      "label": "/\\ x = 0 /\\ y = \"idle\"",
      "vars": { "x": 0, "y": "idle" }
    },
    "2": {
      "label": "/\\ x = 1 /\\ y = \"active\"",
      "vars": { "x": 1, "y": "active" }
    }
  },
  "transitions": {
    "1": [
      {
        "action": "Acquire",
        "label": "Acquire (n1: idle→holding)",
        "target": "2"
      }
    ]
  },
  "invariants": ["TypeOK", "MutualExclusion"],
  "violations": [
    {
      "id": "v1",
      "type": "invariant",
      "name": "MutualExclusion",
      "trace": [
        { "stateId": "1", "action": null },
        { "stateId": "3", "action": "Acquire" },
        { "stateId": "7", "action": "Acquire" }
      ]
    }
  ]
}
```

**Behavioral notes:**
- `states[id].vars` must contain **parsed** variable values as native JSON types (numbers, strings, booleans, objects, arrays) — not raw TLA+ syntax strings. The animator's `renderState(vars)` function directly accesses these as JavaScript values.
- `transitions[id]` is an array of edges from each state, with `action` (the TLA+ action name), `label` (human-readable transition description including parameter values), and `target` (destination state ID).
- `invariants` is the list of property names being checked (from the `.cfg`).
- `violations` must have stable IDs (`v1`, `v2`, ...) — the animator maps these to scenario labels.
- Each violation `trace` is an ordered array of `{ stateId, action }` entries. The first entry's `action` is `null` (initial state).
- If the state graph is too large to return (e.g., millions of states), the response should indicate this — the verifier checks for a `too_large` condition and reports `state_graph: too_large` to skip playground generation.

---

## 4. MCP Tools — Secondary

These tools are available to agents via the `mcp__tlaplus__*` wildcard but are not on the primary verification pipeline. They support advanced use cases.

### 4.1 `tlc_simulate` — Simulation Mode

**Purpose:** Random trace exploration. Faster than exhaustive checking for large state spaces or quick smoke tests.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `tla_file` | string | yes | — | Path to `.tla` file |
| `cfg_file` | string | no | same basename `.cfg` | Config file |
| `num_traces` | integer | no | — | Number of traces to generate |
| `depth` | integer | no | 100 | Max depth of each trace |
| `seed` | integer | no | — | Random seed for reproducibility |
| `aril` | integer | no | — | Adjusts random seed |
| `deadlock` | boolean | no | `true` | Check for deadlocks |
| `workers` | integer or `"auto"` | no | — | Worker threads |
| `extra_args` | string[] | no | — | Additional TLC args |

### 4.2 `pcal_translate` — PlusCal to TLA+

**Purpose:** Translate PlusCal algorithm embedded in a `.tla` file into TLA+. Modifies the file in-place.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `tla_file` | string | yes | — | Path to `.tla` file containing PlusCal |
| `fairness` | `"wf"` \| `"sf"` \| `"wfNext"` \| `"nof"` | no | `"nof"` | Fairness condition |
| `label` | boolean | no | `true` | Auto-add missing labels |
| `termination` | boolean | no | `false` | Add termination detection |
| `no_cfg` | boolean | no | `false` | Don't generate `.cfg` file |
| `line_width` | integer | no | 78 | Line width for output |

### 4.3 `tla_evaluate` — Expression Evaluation

**Purpose:** Evaluate a constant TLA+ expression using TLC. Useful for testing/debugging expressions.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `expression` | string | yes | TLA+ expression (e.g., `1 + 2`, `{1,2,3} \\union {4,5}`) |
| `imports` | string[] | no | Modules to EXTEND. Defaults to `["Integers", "Sequences", "FiniteSets", "TLC"]` |

### 4.4 `tlc_coverage` — Action Coverage

**Purpose:** Run TLC with action coverage reporting.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `tla_file` | string | yes | — | Path to `.tla` file |
| `cfg_file` | string | no | — | Config file |
| `interval_minutes` | number | no | 1 | Reporting interval |
| `workers` | integer or `"auto"` | no | — | Worker threads |
| `extra_args` | string[] | no | — | Additional args |

### 4.5 `tla_tex` — LaTeX Typesetting

**Purpose:** Typeset a TLA+ spec into PDF or DVI.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `tla_file` | string | yes | — | Path to `.tla` file |
| `output_format` | `"pdf"` \| `"dvi"` | no | `"pdf"` | Output format |
| `number` | boolean | no | `false` | Add line numbers |
| `shade` | boolean | no | `false` | Shade comments |
| `no_pcal_shade` | boolean | no | `false` | Don't shade PlusCal code |
| `gray_level` | number | no | 0.85 | Gray level (0=black, 1=white) |

**Note:** Requires `pdflatex` or `latex` to be installed on the system.

### 4.6 `tlc_generate_trace_spec` — Trace Explorer Spec

**Purpose:** Run TLC with `-generateSpecTE` to produce a standalone spec that replays an error trace.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `tla_file` | string | yes | — | Path to `.tla` file |
| `cfg_file` | string | no | — | Config file |
| `monolith` | boolean | no | `true` | Generate single-file SpecTE |
| `extra_args` | string[] | no | — | Additional args |

---

## 5. TLC Raw Output Parsing Contract

The verifier agent parses `raw_output` from `tlc_check` to extract counterexample traces. The server must return **unmodified TLC stdout+stderr** so the following patterns are intact:

### Counterexample trace format

```
Error: Invariant MutualExclusion is violated.
Error: The behavior up to this point is:
State 1: <Initial predicate>
/\ var1 = value1
/\ var2 = value2

State 2: <ActionName line 42, col 5 to line 50, col 20 of module ModuleName>
/\ var1 = new_value1
/\ var2 = value2
```

### Liveness violation (lasso) format

```
State 5: <ActionName ...>
/\ ...
Back to state 3.
```

### Statistics format

The verifier extracts `states_found`, `distinct_states`, and `depth` from TLC's summary output. The structured response fields should match these, but the raw output must also be preserved for the verifier's own trace parsing.

---

## 6. State Graph JSON Contract

The `tla_state_graph` tool's `playground` format output is saved as `state-graph.json` and consumed directly by the animator agent. The contract is critical because the animator generates JavaScript code that accesses this structure.

### Variable parsing requirements

TLA+ values in state labels must be parsed to native JSON types:

| TLA+ Value | JSON Type | Example |
|------------|-----------|---------|
| Integer `42` | `number` | `42` |
| String `"idle"` | `string` | `"idle"` |
| Boolean `TRUE` / `FALSE` | `boolean` | `true` / `false` |
| Set `{1, 2, 3}` | `array` | `[1, 2, 3]` |
| Function `(a1 :> "idle" @@ a2 :> "busy")` | `object` | `{"a1": "idle", "a2": "busy"}` |
| Sequence `<<1, 2, 3>>` | `array` | `[1, 2, 3]` |
| Record `[field1 |-> val1, field2 |-> val2]` | `object` | `{"field1": "val1", "field2": "val2"}` |
| Model value `a1` | `string` | `"a1"` |

### Transition label generation

Edge labels should be human-readable and include parameter values where applicable:
- `"Acquire (n1: idle→holding)"` — shows which entity changed and how
- The `action` field should contain just the action name (`"Acquire"`)
- The `label` field should contain the descriptive label with parameters

### Violation trace extraction

Violation traces are extracted from TLC's counterexample output (`tlc_output` parameter) and correlated with state IDs from the DOT graph. Each violation gets a stable ID (`v1`, `v2`, ...) and its trace as an array of `{ stateId, action }` entries.

---

## 7. Artifact Directory Conventions

The plugin expects this directory structure for derived artifacts:

```
<spec_dir>/
  ModuleName.tla              # Specification (specifier writes)
  ModuleName.cfg              # TLC config (specifier writes)
  ModuleName/                 # Artifact directory (verifier creates)
    states/                   # dump_path target — TLC writes DOT here
      states.dot              # State graph in DOT format
    tlc-output.txt            # Raw TLC output (verifier saves)
    state-graph.json          # Parsed graph JSON (verifier saves)
    playground/               # Playground subdirectory (animator creates)
      playground.html         # Interactive playground (copied from template)
      playground-gen.js       # Generated data + render functions
      playground-gen.css      # Generated domain styles
```

The `dump_path` parameter in `tlc_check` tells TLC where to write the DOT file. The server should create parent directories if they don't exist. The actual filename within that directory is TLC's default (`states.dot` or similar).

---

## 8. Error Handling Expectations

### Parse errors (`tla_parse`)
- Return `valid: false` with structured `errors` array.
- Each error must have a `message` and `location` with `file`, `line`, `col`.
- Do not crash or throw — always return the structured response.

### TLC errors (`tlc_check`)
- Return `status: "error"` with `errors` array.
- Common errors to handle gracefully:
  - `OutOfMemoryError` — state space too large
  - `EvalException` — expression evaluation failure
  - Undefined identifier — missing EXTENDS or CONSTANT
  - Type mismatch — model value vs integer confusion
- Always include `raw_output` even on error — the verifier needs it for diagnostics.

### State graph errors (`tla_state_graph`)
- If the DOT file is too large to parse into the playground format, indicate this (e.g., `too_large: true` in the response).
- If parsing fails, return an error rather than a malformed graph.

---

## 9. Non-Functional Requirements

### Performance
- `tla_parse` should complete in under 5 seconds for typical specs.
- `tlc_check` may run for minutes on large state spaces — the server should not impose artificial timeouts.
- `tla_state_graph` parsing should handle graphs with up to ~100K states for playground generation.

### Reliability
- The server must not crash on malformed `.tla` files — SANY and TLC errors should be caught and returned as structured responses.
- Java process management: TLC runs as a subprocess; the server must handle JVM crashes gracefully.

### Jar location
- The jar **must** be stored at `$HOME/.tlaplus-mcp/lib/tla2tools.jar` — this path is hard-coded in the plugin's post-write hook for direct SANY invocation outside the MCP server.
- The server should auto-download the jar on first use and verify its integrity.

---

## 10. Summary of Tool Priority

| Tool | Pipeline Stage | Frequency | Priority |
|------|---------------|-----------|----------|
| `tla_parse` | Specify, Verify | Every run (2+ calls) | Critical |
| `tlc_check` | Verify | Every run (1+ calls) | Critical |
| `tla_state_graph` | Verify | Every run (1 call) | Critical |
| `tlc_simulate` | Ad-hoc exploration | Occasional | Secondary |
| `pcal_translate` | PlusCal workflows | Occasional | Secondary |
| `tla_evaluate` | Debugging | Occasional | Secondary |
| `tlc_coverage` | Analysis | Rare | Secondary |
| `tla_tex` | Documentation | Rare | Low |
| `tlc_generate_trace_spec` | Debugging | Rare | Low |
