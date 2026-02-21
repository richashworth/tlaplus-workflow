---
name: tlaplus-to-pbt
description: Translate a TLA+ specification into property-based tests that enforce the same invariants
user-invocable: true
---

# TLA+ to Property-Based Tests

You are a TLA+ expert and testing engineer. Given a TLA+ specification, generate property-based tests that verify the same invariants in executable code.

Read the TLA+ file at `$ARGUMENTS`. If no path is given, look for .tla files in the current directory.

## Step 1: Analyze the Spec

Read the .tla file. Identify:
- **Variables** — these become your test state
- **Init** — this becomes your state generator
- **Next / Actions** — these become transition functions
- **Guards** (preconditions on actions) — these become `assume()` / filters
- **Invariants** — these become property assertions
- **CONSTANTS** — these become parameterized test inputs (try several values)

## Step 2: Map TLA+ Types to Generators

| TLA+ | Generator |
|------|-----------|
| `1..N` | integer in range `[1, N]` |
| `{"a", "b", "c"}` | `one_of("a", "b", "c")` |
| `[S -> T]` | dictionary mapping each element of S to a generated T |
| `SUBSET S` | arbitrary subset of S |
| `Seq(S)` | list of elements drawn from S |
| `BOOLEAN` | boolean |
| `Nat` | non-negative integer (cap at a reasonable bound, e.g. 100) |
| `[field1: S, field2: T]` | record/struct with field generators |

## Step 3: Generate Tests

For each invariant in the spec, produce a property test following this structure:

```
property("InvariantName holds under arbitrary action sequences"):
    state = generate(initial_state)          // from Init
    actions = generate(list_of(all_actions)) // from Next disjuncts
    for action in actions:
        if guard(action, state):             // action's enabling condition
            state = apply(action, state)
        assert invariant(state)              // check after EVERY step
```

Each action's guard filters out inapplicable transitions — do NOT generate invalid transitions, use assume/filter to skip them.

## Step 4: Translate Invariants to Assertions

TLA+ quantifiers and predicates map directly to loops and checks:

- `\A x \in S: P(x)` → assert P(x) for every x in S
- `\E x \in S: P(x)` → assert any(P(x) for x in S)
- `\A x \in S: \A y \in S: x /= y => ~(both_hold(x, y))` → for every distinct pair, assert they don't both hold
- `status[s] = "booked" => holder[s] /= "none"` → if booked then holder must be set
- `Cardinality({x \in S: P(x)}) <= N` → count matching elements, assert <= N

Read the quantifiers outside-in, translate each to a loop or filter, then translate the body to an assertion.

## Step 5: Pick the Framework

Use whatever PBT framework the project already has. If none is present, use the standard one for the language:

- **JavaScript/TypeScript**: fast-check
- **Python**: Hypothesis (use `@given` + stateful testing via `RuleBasedStateMachine` for multi-step)
- **Java/Kotlin**: jqwik (`@Property` + `@ForAll`)
- **Swift**: SwiftCheck
- **Rust**: proptest
- **Go**: rapid

## Step 6: Write the Output

- Place test files in the project's existing test directory (follow its conventions)
- Comment each property with the original TLA+ invariant it tests, e.g.:
  ```
  // Invariant: \A s \in Slots: status[s] = "booked" => holder[s] /= "none"
  ```
- Add shrinking hints where the framework supports them — smaller counterexamples are far easier to debug
- If the spec has CONSTANTS, parameterize tests to run with multiple constant values
- Include any necessary setup (state initialization, helper types/classes for the state)
- Run the tests after generating them to confirm they pass
