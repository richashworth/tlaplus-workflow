#!/usr/bin/env python3
"""Convert TLC's DOT state graph dump into structured JSON for the playground template.

Reads a DOT file produced by TLC's `-dump dot,actionlabels,colorize` flag,
an optional CFG file for invariant/property names, and an optional TLC stdout
capture for violation trace extraction.  Outputs a single JSON document that
the playground UI can consume directly.
"""

import argparse
import json
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# TLA+ value recursive-descent parser
# ---------------------------------------------------------------------------

class _ValueParser:
    """Recursive-descent parser for TLA+ values as printed by TLC."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    # -- helpers ------------------------------------------------------------

    def _skip_ws(self):
        while self.pos < len(self.text) and self.text[self.pos] in " \t\n\r":
            self.pos += 1

    def _peek(self) -> Optional[str]:
        self._skip_ws()
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]

    def _match(self, s: str) -> bool:
        self._skip_ws()
        if self.text[self.pos:self.pos + len(s)] == s:
            self.pos += len(s)
            return True
        return False

    def _expect(self, s: str):
        if not self._match(s):
            raise ValueError(
                f"Expected {s!r} at pos {self.pos}: ...{self.text[self.pos:self.pos+20]!r}..."
            )

    # -- grammar ------------------------------------------------------------

    def parse(self) -> Any:
        val = self._parse_value()
        return val

    def _parse_value(self) -> Any:
        self._skip_ws()
        if self.pos >= len(self.text):
            raise ValueError("Unexpected end of input")

        c = self.text[self.pos]

        # String literal (possibly escaped quotes from DOT)
        if c == '"' or (c == '\\' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '"'):
            return self._parse_string()

        # Sequence <<...>>
        if c == '<' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '<':
            return self._parse_sequence()

        # Set {...}
        if c == '{':
            return self._parse_set()

        # Record [field |-> ...]
        if c == '[':
            return self._parse_record()

        # Parenthesized function display (k :> v @@ ...)
        if c == '(':
            return self._parse_function()

        # Boolean
        if self.text[self.pos:self.pos + 4] == "TRUE":
            self.pos += 4
            return True
        if self.text[self.pos:self.pos + 5] == "FALSE":
            self.pos += 5
            return False

        # Number (possibly negative)
        if c == '-' or c.isdigit():
            return self._parse_number()

        # Bare identifier (model value)
        if c.isalpha() or c == '_':
            return self._parse_identifier()

        raise ValueError(
            f"Unexpected char {c!r} at pos {self.pos}: ...{self.text[self.pos:self.pos+20]!r}..."
        )

    def _parse_string(self) -> str:
        # Handle both \" (DOT escaped) and plain " as quote delimiter
        if self.text[self.pos] == '\\' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '"':
            self.pos += 2  # skip \"
            return self._read_string_body(escaped_quote=True)
        else:
            self.pos += 1  # skip "
            return self._read_string_body(escaped_quote=False)

    def _read_string_body(self, escaped_quote: bool) -> str:
        chars: list[str] = []
        while self.pos < len(self.text):
            if escaped_quote:
                if self.text[self.pos] == '\\' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '"':
                    self.pos += 2
                    return "".join(chars)
            else:
                if self.text[self.pos] == '"':
                    self.pos += 1
                    return "".join(chars)
            if self.text[self.pos] == '\\' and not escaped_quote:
                self.pos += 1
                if self.pos < len(self.text):
                    chars.append(self.text[self.pos])
                    self.pos += 1
                continue
            chars.append(self.text[self.pos])
            self.pos += 1
        raise ValueError("Unterminated string")

    def _parse_number(self) -> int:
        start = self.pos
        if self.text[self.pos] == '-':
            self.pos += 1
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        return int(self.text[start:self.pos])

    def _parse_identifier(self) -> str:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        return self.text[start:self.pos]

    def _parse_sequence(self) -> list:
        self._expect("<<")
        self._skip_ws()
        if self._match(">>"):
            return []
        items = [self._parse_value()]
        while self._match(","):
            items.append(self._parse_value())
        self._expect(">>")
        return items

    def _parse_set(self) -> list:
        self._expect("{")
        self._skip_ws()
        if self._match("}"):
            return []
        items = [self._parse_value()]
        while self._match(","):
            items.append(self._parse_value())
        self._expect("}")
        return items

    def _parse_record(self) -> dict:
        self._expect("[")
        self._skip_ws()
        if self._match("]"):
            return {}
        result: dict = {}
        while True:
            self._skip_ws()
            key = self._parse_identifier()
            self._expect("|->")
            val = self._parse_value()
            result[key] = val
            if not self._match(","):
                break
        self._expect("]")
        return result

    def _parse_function(self) -> dict:
        self._expect("(")
        result: dict = {}
        while True:
            self._skip_ws()
            key = self._parse_value()
            self._expect(":>")
            val = self._parse_value()
            result[_json_key(key)] = val
            self._skip_ws()
            if not self._match("@@"):
                break
        self._expect(")")
        return result


def parse_tla_value(text: str) -> Any:
    """Parse a single TLA+ value string into a Python/JSON-compatible object."""
    p = _ValueParser(text.strip())
    return p.parse()


def _json_key(v: Any) -> str:
    """Coerce a parsed value to a JSON object key (string)."""
    if isinstance(v, str):
        return v
    return str(v)


# ---------------------------------------------------------------------------
# State label parsing  (/\ var = value lines)
# ---------------------------------------------------------------------------

def parse_state_label(label: str) -> Dict[str, Any]:
    """Parse a TLC state label into a dict of variable name -> parsed value."""
    variables: Dict[str, Any] = {}
    # Split on /\ (conjunction) — each piece is "var = value"
    parts = re.split(r'/\\', label)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.match(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)', part, re.DOTALL)
        if m:
            var_name = m.group(1)
            raw_value = m.group(2).strip()
            try:
                variables[var_name] = parse_tla_value(raw_value)
            except ValueError:
                variables[var_name] = raw_value  # fallback: keep raw string
    return variables


# ---------------------------------------------------------------------------
# DOT parsing
# ---------------------------------------------------------------------------

_EDGE_RE = re.compile(
    r'(\d+)\s*->\s*(\d+)\s*\[label="((?:[^"\\]|\\.)*)"\s*.*?\]'
)
_NODE_RE = re.compile(
    r'^(\d+)\s*\[label="((?:[^"\\]|\\.)*)"\s*(.*?)\]',
    re.MULTILINE,
)


def parse_dot(path: str) -> Tuple[Dict[str, dict], List[dict], str]:
    """Parse TLC DOT file.

    Returns (states_dict, edges_list, initial_state_id).
    """
    with open(path, "r") as f:
        content = f.read()

    states: Dict[str, dict] = {}
    edges: List[dict] = []
    initial_id: Optional[str] = None

    for m in _NODE_RE.finditer(content):
        nid = m.group(1)
        raw_label = m.group(2)
        attrs = m.group(3)
        # Unescape DOT string escapes: \n -> newline, \\ -> \, \" -> "
        label = raw_label.replace("\\\\", "\\").replace("\\n", "\n").replace('\\"', '"')
        variables = parse_state_label(label)
        states[nid] = {"label": label, "vars": variables}
        if "style = filled" in attrs or "style=filled" in attrs:
            initial_id = nid

    for m in _EDGE_RE.finditer(content):
        src, tgt, action = m.group(1), m.group(2), m.group(3)
        edges.append({"source": src, "target": tgt, "action": action})

    if initial_id is None and states:
        # Fallback: pick smallest numeric id
        initial_id = min(states.keys(), key=int)

    if not states:
        print("Error: Could not parse any states from DOT file.", file=sys.stderr)
        sys.exit(1)

    return states, edges, initial_id  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Action label disambiguation
# ---------------------------------------------------------------------------

def _compact_diff(src_vars: dict, tgt_vars: dict) -> List[Tuple[str, str, str]]:
    """Return list of (key, old_repr, new_repr) for changed variables."""
    diffs = []
    for k in src_vars:
        if k in tgt_vars and src_vars[k] != tgt_vars[k]:
            diffs.append((k, _short(src_vars[k]), _short(tgt_vars[k])))
    return diffs


def _short(v: Any) -> str:
    return v if isinstance(v, str) else str(v)


def disambiguate_actions(
    states: Dict[str, dict], edges: List[dict]
) -> Dict[str, List[dict]]:
    """Build transitions dict with disambiguated labels where needed."""
    # Group edges by source
    by_source: Dict[str, List[dict]] = {}
    for e in edges:
        by_source.setdefault(e["source"], []).append(e)

    transitions: Dict[str, List[dict]] = {}

    for src, src_edges in by_source.items():
        # Group by action name
        action_groups: Dict[str, List[dict]] = {}
        for e in src_edges:
            action_groups.setdefault(e["action"], []).append(e)

        result: List[dict] = []
        for action, group in action_groups.items():
            if len(group) == 1:
                e = group[0]
                result.append({
                    "action": action,
                    "label": action,
                    "target": e["target"],
                })
            else:
                # Need disambiguation
                src_vars = states[src]["vars"]
                edge_diffs = []
                for e in group:
                    tgt_vars = states[e["target"]]["vars"]
                    diffs = _compact_diff(src_vars, tgt_vars)
                    edge_diffs.append((e, diffs))

                # Find the first diff key that distinguishes all edges
                disambiguated = _disambiguate_group(action, edge_diffs)
                result.extend(disambiguated)

        transitions[src] = result

    return transitions


def _disambiguate_group(
    action: str, edge_diffs: List[Tuple[dict, List[Tuple[str, str, str]]]]
) -> List[dict]:
    """Try to find a single diff key that distinguishes all edges; otherwise
    pick the first per-edge diff that is unique across the group."""
    # Collect all diff keys across edges
    all_keys: List[str] = []
    for _, diffs in edge_diffs:
        for k, _, _ in diffs:
            if k not in all_keys:
                all_keys.append(k)

    # Try each key: does it produce unique labels for all edges?
    for key in all_keys:
        labels: List[Optional[str]] = []
        for _, diffs in edge_diffs:
            entry = next((d for d in diffs if d[0] == key), None)
            if entry:
                labels.append(f"{key}: {entry[1]}\u2192{entry[2]}")
            else:
                labels.append(f"{key}: (unchanged)")
        if len(set(labels)) == len(labels):
            result = []
            for (e, _), lbl in zip(edge_diffs, labels):
                result.append({
                    "action": action,
                    "label": f"{action} ({lbl})",
                    "target": e["target"],
                })
            return result

    # Fallback: pick the first diff per edge that differs from at least one
    # other edge's corresponding diff, to avoid identical fallback labels.
    result = []
    used_labels: set = set()
    for e, diffs in edge_diffs:
        lbl = None
        for d in diffs:
            candidate = f"{action} ({d[0]}: {d[1]}\u2192{d[2]})"
            if candidate not in used_labels:
                lbl = candidate
                break
        if lbl is None:
            lbl = f"{action} (\u2192 {e['target']})"
        used_labels.add(lbl)
        result.append({
            "action": action,
            "label": lbl,
            "target": e["target"],
        })
    return result


# ---------------------------------------------------------------------------
# CFG parsing
# ---------------------------------------------------------------------------

def parse_cfg(path: str) -> Tuple[List[str], List[str]]:
    """Return (invariants, properties) from a TLC cfg file.

    Handles both single-line (``INVARIANT Foo``) and multi-line formats::

        INVARIANTS
          Foo
          Bar
    """
    invariants: List[str] = []
    properties: List[str] = []
    try:
        with open(path, "r") as f:
            current_list: Optional[List[str]] = None
            for line in f:
                stripped = line.strip()
                if not stripped or stripped.startswith("\\*"):
                    current_list = None
                    continue
                # Single-line: INVARIANT Foo  or  INVARIANTS Foo Bar
                m = re.match(r'INVARIANT[S]?\s+(.*)', stripped)
                if m:
                    names = m.group(1).split()
                    if names:
                        invariants.extend(names)
                        current_list = None
                    else:
                        # Bare keyword — following indented lines are names
                        current_list = invariants
                    continue
                m = re.match(r'PROPERT(?:Y|IES)\s+(.*)', stripped)
                if m:
                    names = m.group(1).split()
                    if names:
                        properties.extend(names)
                        current_list = None
                    else:
                        current_list = properties
                    continue
                # Bare keyword with no trailing text
                if stripped in ("INVARIANT", "INVARIANTS"):
                    current_list = invariants
                    continue
                if stripped in ("PROPERTY", "PROPERTIES"):
                    current_list = properties
                    continue
                # Indented continuation line
                if current_list is not None and line[0] in (" ", "\t"):
                    current_list.extend(stripped.split())
                    continue
                # Any other keyword resets multi-line accumulation
                current_list = None
    except OSError as exc:
        print(f"Warning: Could not read CFG file: {exc}", file=sys.stderr)
    return invariants, properties


# ---------------------------------------------------------------------------
# TLC output parsing (violations)
# ---------------------------------------------------------------------------

_STATE_HEADER_RE = re.compile(
    r'^State\s+(\d+):\s*(?:<(.+?)>)?'
)
_BACK_TO_STATE_RE = re.compile(r'^Back to state\s+(\d+)')


def parse_tlc_output(
    path: str, graph_states: Dict[str, dict]
) -> List[dict]:
    """Extract violation traces from TLC stdout."""
    violations: List[dict] = []
    try:
        with open(path, "r") as f:
            lines = f.readlines()
    except OSError:
        return violations

    i = 0
    vid = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # Detect violation type
        vtype = None
        vname = None

        inv_m = re.match(r'Error: Invariant (\S+) is violated\.', line)
        if inv_m:
            vtype = "invariant"
            vname = inv_m.group(1)

        if "Deadlock reached" in line:
            vtype = "deadlock"
            vname = None

        if "Temporal properties were violated" in line:
            vtype = "temporal"
            vname = None

        if vtype is None:
            i += 1
            continue

        # Advance to trace
        i += 1
        while i < len(lines) and not _STATE_HEADER_RE.match(lines[i].rstrip()):
            # For temporal violations, try to grab the property name
            if vtype == "temporal" and vname is None:
                pm = re.search(r'is violated', lines[i])
                if pm:
                    pm2 = re.match(r'Error:\s+(\S+)\s+is violated', lines[i].rstrip())
                    if pm2:
                        vname = pm2.group(1)
            i += 1

        # Parse trace states
        trace_states: List[dict] = []
        back_to: Optional[str] = None

        while i < len(lines):
            line = lines[i].rstrip()
            sm = _STATE_HEADER_RE.match(line)
            bm = _BACK_TO_STATE_RE.match(line)

            if bm:
                back_to = bm.group(1)
                i += 1
                break

            if sm:
                action_info = sm.group(2)
                action_name = None
                if action_info:
                    # Extract action name from <ActionName line ...>
                    am = re.match(r'(\w+)', action_info)
                    if am and am.group(1) not in ("Initial",):
                        action_name = am.group(1)

                # Gather variable lines
                var_lines = []
                i += 1
                while i < len(lines):
                    vl = lines[i].rstrip()
                    if (not vl or _STATE_HEADER_RE.match(vl)
                            or _BACK_TO_STATE_RE.match(vl)
                            or vl.startswith("Error:")):
                        break
                    var_lines.append(vl)
                    i += 1

                label = "\n".join(var_lines)
                tvars = parse_state_label(label)
                trace_states.append({
                    "action": action_name,
                    "vars": tvars,
                })
            else:
                if line == "":
                    # Empty line between states — skip and continue
                    i += 1
                    continue
                # Not a state line and not back-to — done with this trace
                break

        # Match trace states to graph states
        trace_entries: List[dict] = []
        for ts in trace_states:
            sid = _find_matching_state(ts["vars"], graph_states)
            if sid is None:
                print(
                    f"Warning: Could not match trace state to graph "
                    f"(vars: {ts['vars']})",
                    file=sys.stderr,
                )
            trace_entries.append({
                "stateId": sid,
                "action": ts["action"],
            })

        if back_to is not None:
            # back_to is a 1-indexed TLC trace number, not a graph state ID.
            # Resolve it through the already-matched trace entries.
            back_idx = int(back_to) - 1
            if 0 <= back_idx < len(trace_entries):
                back_sid = trace_entries[back_idx]["stateId"]
            else:
                print(
                    f"Warning: Back-to-state index {back_to} out of range "
                    f"(trace has {len(trace_entries)} entries)",
                    file=sys.stderr,
                )
                back_sid = None
            trace_entries.append({
                "stateId": back_sid,
                "action": "Back to state",
            })

        # Generate summary
        summary = _violation_summary(vtype, vname, trace_states)

        vid += 1
        violation: dict = {
            "id": f"v{vid}",
            "type": vtype,
            "summary": summary,
            "trace": trace_entries,
        }
        if vtype == "invariant" and vname:
            violation["invariant"] = vname
        if vtype == "temporal" and vname:
            violation["property"] = vname

        violations.append(violation)

    return violations


def _normalize_for_compare(v: Any) -> Any:
    """Normalize a parsed value for order-insensitive comparison.

    TLA+ sets are unordered, but we store them as lists. Sort lists
    recursively so {a, b} and {b, a} compare equal.
    """
    if isinstance(v, list):
        normed = [_normalize_for_compare(x) for x in v]
        try:
            normed.sort(key=str)
        except TypeError:
            pass
        return normed
    if isinstance(v, dict):
        return {k: _normalize_for_compare(val) for k, val in v.items()}
    return v


def _find_matching_state(
    tvars: Dict[str, Any], graph_states: Dict[str, dict]
) -> Optional[str]:
    """Find the graph state whose vars match tvars (order-insensitive for sets)."""
    norm_tvars = _normalize_for_compare(tvars)
    for sid, sdata in graph_states.items():
        if _normalize_for_compare(sdata["vars"]) == norm_tvars:
            return sid
    return None


def _violation_summary(
    vtype: str, vname: Optional[str], trace_states: List[dict]
) -> str:
    if vtype == "deadlock":
        if trace_states:
            last = trace_states[-1]["vars"]
            parts = [f"{k} = {_short(v)}" for k, v in last.items()]
            return f"Deadlock reached with {', '.join(parts[:3])}"
        return "Deadlock reached"

    prefix = vname or vtype
    if len(trace_states) >= 2:
        prev = trace_states[-2]["vars"]
        last = trace_states[-1]["vars"]
        diffs = _compact_diff(prev, last)
        if diffs:
            parts = [f"{k} changed to {nv}" for k, _, nv in diffs[:3]]
            return f"{prefix} violated: {'; '.join(parts)}"
    return f"{prefix} violated"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert TLC DOT state graph to playground JSON"
    )
    parser.add_argument("--dot", required=True, help="Path to TLC DOT file")
    parser.add_argument("--cfg", required=True, help="Path to TLC CFG file")
    parser.add_argument(
        "--tlc-output", default=None, help="Path to TLC stdout capture"
    )
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    # Parse DOT
    states, edges, initial_id = parse_dot(args.dot)

    # Threshold check
    n_states = len(states)
    if n_states > 50_000:
        print(
            f"Warning: State graph has {n_states} states. "
            "The playground may be slow. Consider reducing constants "
            "or using Spectacle for exploration.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Build transitions with disambiguation
    transitions = disambiguate_actions(states, edges)

    # Parse CFG
    invariants, properties = parse_cfg(args.cfg)

    # Parse violations
    violations: List[dict] = []
    if args.tlc_output:
        violations = parse_tlc_output(args.tlc_output, states)

    # Assemble output
    output = {
        "initialStateId": initial_id,
        "states": {
            sid: {"label": s["label"], "vars": s["vars"]}
            for sid, s in states.items()
        },
        "transitions": transitions,
        "invariants": invariants + properties,
        "violations": violations,
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
