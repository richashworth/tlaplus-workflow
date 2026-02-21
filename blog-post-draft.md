# TLA+ Verification Plugin for Claude Code
## Reference Notes for Blog Series

---

## The Thesis

Formal verification with TLA+ is powerful but nobody uses it — the notation is impenetrable and the tooling is developer-facing. The bet: hide the formalism entirely behind a conversational AI interface and ship it as a Claude Code plugin.

**The contribution isn't the components.** TLA+ generation exists (AgentSkills). Model checking exists (TLC). LLMs already interview well. LLMs already generate UIs. Animation of specs exists (Spectacle). PBT from specs is a known concept.

**The contribution is the assembled workflow and the agent topology that makes it invisible.** Five specialist agents, each with a different mindset, wired into a sequence where the user has a conversation and gets a verified, animated design without ever seeing a formal notation. Packaged as a plugin anyone can install in thirty seconds.

The honest framing: "I didn't build these tools. I assembled them into a workflow, packaged it as a Claude Code plugin, and tested whether it actually finds bugs."

---

## The Workflow

```
User describes system
        │
        ▼
   ┌─────────┐
   │ Elicitor │  Interviews user. Surfaces edge cases.
   │          │  Never mentions TLA+. Speaks domain language.
   └────┬─────┘
        │ structured summary (entities, states, transitions, guards, invariants)
        ▼
   ┌───────────┐
   │ Specifier  │  Writes TLA+ spec + .cfg file.
   │            │  User never sees this agent or its output.
   └────┬───────┘
        │ .tla + .cfg files
        ▼
   ┌──────────┐
   │ Verifier  │  Runs TLC. Translates output.
   │           │  Returns "clean" or plain-language violation scenario.
   └────┬──────┘
        │
        ├── violation ──► present scenario to user ──► user corrects ──► back to Specifier
        │
        ▼ clean
   ┌──────────┐
   │ Animator  │  Generates split-pane HTML: domain prototype
   │           │  + verification sidebar. Self-contained file,
   │           │  user opens in browser.
   └──────────┘
        │
        ▼ (on request)
   ┌─────────────┐
   │ Test Writer  │  Generates property-based tests from spec invariants.
   └──────────────┘
```

---

## The Plugin

### Structure

```
tlaplus-workflow/
  .claude-plugin/
    plugin.json
  agents/
    elicitor.md
    specifier.md
    verifier.md
    animator.md
    test-writer.md
  skills/
    tlaplus-from-interview/SKILL.md
    tlaplus-verify-explain/SKILL.md
    tlaplus-animate/SKILL.md
    tlaplus-to-pbt/SKILL.md
```

### Dependencies

None. The plugin is self-contained. TLC (`tla2tools.jar`) must be available on PATH — the verifier calls it via bash.

The official Anthropic **playground plugin** (`claude-plugins-official`) is prior art and inspiration for our self-contained HTML pattern and copy-prompt-back interaction model. But our interaction model is fundamentally different (state-space exploration with verification feedback vs parameter configuration), so we own the full implementation rather than extending their templates.

### Installation

```
/plugin install richarda/tlaplus-workflow
```

No project-level config needed. The agents' `description` fields handle automatic routing. Optional: teams can add a one-liner to their project CLAUDE.md.

### How It Triggers

The lead agent (main Claude Code session) reads the subagent descriptions and delegates when the task matches. Trigger conditions are encoded in the agent descriptions:

**Activate when the user:**
- Asks to design or specify a stateful system
- Describes concurrent access, shared resources, or state machines
- Mentions booking, scheduling, queues, locks, workflows, lifecycle management
- Says "verify", "check for race conditions", "what could go wrong"

**Don't activate for:**
- CRUD endpoints with no shared state
- UI layout or styling
- Simple data transformations

### Agent Definitions

| Agent | User-facing? | Model | Tools | Mindset |
|-------|-------------|-------|-------|---------|
| Elicitor | Yes | Opus | Read | Curious, probing, adversarial about edge cases. Speaks only domain language. |
| Specifier | No (invisible) | Sonnet | Read, Write, Edit, Bash | Precise, completeness-obsessed. Every variable initialised, every guard explicit. |
| Verifier | Indirectly (via lead) | Sonnet | Read, Bash | Adversarial, faithful. Translates TLC output to plain-language scenarios. Never softens. |
| Animator | No (output shown) | Sonnet | Read, Write | UX-minded, creative. Generates the domain prototype panel (left side of split-pane HTML). Only produces the `renderState(state)` function — verification sidebar, trace log, and report-back buttons come from the template in the skill. |
| Test Writer | No (output shown) | Sonnet | Read, Write | Mechanical, thorough. Maps invariants to generators and assertions. |

### Skills

| Skill | New or Existing | Used By | What It Provides |
|-------|----------------|---------|-----------------|
| `tlaplus-from-interview` | **New** | Elicitor | Interview structure, completeness checklists, edge-case question patterns |
| `tlaplus-verify-explain` | **New** | Verifier | TLC invocation via bash, output parsing, counterexample → narrative translation, .cfg generation |
| `tlaplus-animate` | **New** | Animator | Split-pane HTML template: domain prototype (left) + verification sidebar (right). Template provides invariant badges, trace log, report-back buttons with structured clipboard copy. Animator only generates `renderState(state)` for the prototype panel. |
| `tlaplus-to-pbt` | **New** | Test Writer | TLA+ types → generators, actions → transitions, invariants → assertions |
| `tlaplus-from-source` | Existing (AgentSkills) | Specifier (Part 2) | Code → spec extraction patterns |
| `tlaplus-add-variable` | Existing (AgentSkills) | Specifier | Safe iterative spec refinement |
| `tlaplus-split-action` | Existing (AgentSkills) | Specifier (Part 2) | Modelling atomicity bugs |

### Design Principle: Heavyweight vs Lightweight

**Use the heavyweight tool when the LLM can't do it:** TLC model checking (exhaustive state exploration — irreplaceable). SANY parsing (syntax validation).

**Use a lightweight LLM-generated artefact when the LLM does it better:** Domain-themed animation UI. Plain-language explanations. Bespoke test generation. Interview-driven elicitation.

TLC is irreplaceable — you can't approximate exhaustive verification. A throwaway HTML animation themed as a salon booking UI? The LLM nails that and makes it contextual in a way Spectacle never will.

---

## Part 1: Building the Plugin

**~2,500 words. Build log + tutorial.**

**Example:** Salon booking system (deliberately simple enough to show the workflow, complex enough to have real edge cases).

### Section 1: What this is and why (~400 words)

- Formal verification is powerful but nobody uses it
- The bet: hide it behind conversation, ship as a plugin
- "I assembled existing tools into a workflow and packaged it"
- Link to plugin repo — reader can install and follow along

### Section 2: The five agents (~500 words)

- Why agents not just skills: different phases need different mindsets
- Show the agent definitions, explain key design choices:
  - Elicitor never mentions TLA+
  - Specifier is invisible
  - Verifier translates, never softens
- Tool restrictions and model selection rationale

### Section 3: Testing it — the salon booking system (~800 words)

Install the plugin. Start Claude Code. Say "help me design a salon booking system."

**The interview:**
- Show the questions the elicitor asked
- Show how edge-case questions surfaced assumptions:
  "What happens if a hold expires while the client is entering payment details?"
- Show how "should never" statements became invariants

**The bugs TLC found:**
1. Expiry race condition: hold expires during confirmation → double booking
2. Ownership confusion: client A's hold, client B tries to confirm

**Be honest about:**
- Which bugs require TLC's exhaustive search (the race condition)
- Which bugs Claude might spot conversationally (ownership — maybe)
- Where the workflow was slow or awkward

**The refinement loop:**
- TLC finds violation → verifier translates to scenario
- User says "expired holds should be re-assignable"
- Specifier updates spec → verifier re-runs → clean

### Section 4: The animation (~400 words)

- Animator generates a **split-pane HTML file** that looks like a domain prototype with a verification sidebar
- Left panel: **domain prototype** — the PM sees what looks like their product (salon booking UI with client cards, time slots, booking buttons). They interact naturally. They're not "testing a specification," they're "clicking through a prototype."
- Right panel: **verification sidebar** — invariant badges (✅/❌ with plain English), trace log (narrative of actions taken), and report-back buttons when violations occur

**The layout:**

```
┌─────────────────────────────────┬──────────────────────┐
│                                 │ Invariants           │
│   Domain Prototype              │ ✅ No double booking │
│                                 │ ✅ Owner must confirm│
│   ┌─────────┐ ┌─────────┐      │ ❌ Hold must persist │
│   │ Slot 1  │ │ Slot 2  │      │    during payment    │
│   │ Alice ◉ │ │ (free)  │      ├──────────────────────┤
│   │ Held    │ │  Book → │      │ Trace                │
│   └─────────┘ └─────────┘      │ 1. Alice books S1    │
│                                 │ 2. Time passes (2m)  │
│   ┌─────────┐ ┌─────────┐      │ 3. Alice's hold      │
│   │ Slot 3  │ │ Slot 4  │      │    expires           │
│   │ Bob ◉   │ │ (free)  │      │ 4. Bob books S1      │
│   │ Confirm │ │  Book → │      │ 5. ⚠️ VIOLATION      │
│   └─────────┘ └─────────┘      │                      │
│                                 ├──────────────────────┤
│                                 │ ⚠️ Invariant violated│
│                                 │                      │
│                                 │ [This shouldn't      │
│                                 │  happen → fix in     │
│                                 │  Claude]             │
│                                 │                      │
│                                 │ [This is expected]   │
│                                 │                      │
│                                 │ [I'm not sure]       │
└─────────────────────────────────┴──────────────────────┘
```

- **Specification-backed Figma prototype**: the PM thinks they're reviewing a mockup. They're actually doing formal verification. Every click is a TLA+ action, every invariant is a TLA+ property.
- Actions grey out when guards aren't met (can't confirm an expired hold)
- Pre-built scenarios (presets) replay the counterexample traces TLC found
- **Report-back on violation**: when an invariant goes red, the sidebar shows contextual options:
  - "This shouldn't happen → fix in Claude" — copies structured trace + constraint request to clipboard
  - "This is expected" — copies confirmation with trace context
  - "I'm not sure" — copies trace with request for Claude to explain implications
- User pastes back into Claude Code → feeds directly into the refinement loop
- Compare to Spectacle: "developer state explorer vs PM prototype"
- **For the blog, this is the screenshot.** This split view — PM clicking through what looks like their product, red banner saying "this state shouldn't be reachable" — sells the entire approach in one glance.

### Section 5: What it cost (~400 words)

- Token cost of multi-agent workflow
- Wall-clock time from first question to verified prototype
- Where agent handoffs added friction
- The moment that justified effort: TLC finding the race condition
- "Would I use this for every feature? No. For concurrent state machines? Yes."

---

## Part 2: Does It Work on Real Code?

**~2,500 words. Honest field report.**

**Example:** Known bug in Fidra's drawer state machine. Different entry point — we have code, not a conversation. Uses `tlaplus-from-source` patterns to extract a spec from existing implementation.

### Section 1: From toy to real (~200 words)

- Part 1 was a made-up salon. Now: real bug in real code.
- Install plugin in Fidra project. Can we extract, verify, and test?

### Section 2: Extracting the spec (~600 words)

- Different workflow: code → spec (not conversation → spec)
- Specifier uses `tlaplus-from-source` patterns from AgentSkills
- What the agent got right and wrong in extraction
- Key tension: spec should capture what code *should* do, not what it *does*
- Where `tlaplus-split-action` helped model state machine transitions

### Section 3: TLC finds the bug (~500 words)

- Verifier runs TLC against extracted spec
- Does it find the known drawer bug? Report honestly.
- Does it find anything new? Report honestly.
- Show plain-language violation scenario

### Section 4: From spec to property-based tests (~600 words)

- Test writer generates PBTs from spec invariants
- Mapping: TLA+ types → generators, invariants → assertions
- Run the tests — do they catch the bug?
- Show shrunk counterexample

### Section 5: The fix (~300 words)

- Verified spec defines target behaviour
- Claude implements fix with spec as contract
- Re-verify: both TLC and PBTs pass

### Section 6: Verdict (~300 words)

- Time: plugin workflow vs "just fix the bug"
- What persists: PBTs, spec as documentation, verified design
- Where it breaks: extraction from messy real code is harder than greenfield
- Recommendation: strongest for greenfield design (Part 1), useful but harder for retrofit (Part 2)
- Link to plugin — "try it on your own state machines"

---

## Prior Art

What exists and how we relate to it:

| Tool / Paper | What it does | Our relationship |
|-------------|-------------|-----------------|
| AgentSkills (tlaplus/AgentSkills) | 3 skills for agents writing TLA+: from-source, add-variable, split-action | Reference patterns from our skills. Use from-source in Part 2. |
| Spectacle (will62794/spectacle) | Full TLA+ interpreter in JS, interactive state exploration | Developer-facing state explorer. We build a PM-facing domain prototype instead. |
| Playground plugin (claude-plugins-official) | Official Anthropic plugin: self-contained HTML explorers with controls, preview, copy-prompt-back | **Inspiration, not dependency.** Proved the copy-prompt-back pattern works. Our interaction model is different (state-space exploration with verification feedback vs parameter configuration), so we own the implementation. |
| vscode-tlaplus MCP server | Exposes TLA+ tooling via MCP tools | We use bash for TLC invocation. MCP is upgrade path if bash proves fragile. |
| Self-Spec paper | "FMInterviewer" role for formal-methods-guided questions | Targets function-level code gen with invented DSL. We do system design with TLA+. No iterative refinement loop. |
| LLMREI / LEIA | LLM-driven requirements elicitation | Produces prose, not formal specs. No exhaustive verification. |
| Amazon ARc | NL → SMT-LIB → verification → NL for policy compliance | Batch mode, internal tool. No conversational refinement. |
| TLAiBench | Benchmarks for NL → TLA+ translation quality | Benchmarks, not workflow. |

**What's genuinely new in our workflow:**
1. Conversational refinement loop (violation → scenario → correction → re-verify)
2. Interview-driven spec generation where the spec is invisible
3. **Specification-backed domain prototype** — PM sees their product, not a state explorer. Verification sidebar docked alongside like devtools.
4. **Structured copy-prompt-back** connecting prototype exploration to spec refinement (inspired by playground plugin pattern, adapted for verification context)
5. Agent topology where the formalism hides behind specialist roles
6. Hybrid template architecture — animator only generates domain prototype, everything else (invariants, trace, report-back) is generic
7. Packaged as an installable Claude Code plugin

---

## Playground Architecture

### The Split-Pane Model

The playground looks like a product prototype with devtools docked to the side. The PM cares about the left panel. The verification layer is visible but secondary.

**Left panel (domain prototype):** Generated by the animator agent per domain. Salon booking shows client cards, time slots, booking buttons. Distributed lock would show nodes, lock holders, message queues. Payment flow shows accounts, balances, transaction states. This is the only bespoke piece — everything else is templated.

**Right panel (verification sidebar):** Invariant badges (plain English, ✅/❌), trace log (narrative of actions), and report-back buttons when violations occur. Same for every domain.

### v1: Clipboard Loop (No Server Required)

The animator generates a self-contained HTML file. Claude Code writes it to `.tlaplus/playground.html`. User opens it in their browser. That's the entire integration — there's no embedded browser in Claude Code, no special rendering surface.

The HTML does all the work:
- Renders the split-pane layout
- Tracks every click in an internal action log
- Evaluates guards, greys out unavailable actions
- Monitors invariants, shows ✅/❌ status
- On violation, shows contextual report-back buttons
- Report-back buttons serialize the full structured trace to clipboard

**The interaction loop** (same pattern the playground plugin proved works):
1. User clicks through prototype naturally
2. Invariant goes red → report-back buttons appear
3. User clicks "This shouldn't happen → fix in Claude"
4. Clipboard gets structured trace — not prose, machine-generated context from every click
5. User pastes into Claude Code
6. Specifier updates spec, verifier confirms fix
7. Animator regenerates HTML with updated guards
8. User refreshes browser, continues exploring

Two manual steps: paste and refresh. The structured trace means the user isn't writing anything — they're copying machine-generated context that the verifier can parse directly.

### Hybrid Template Architecture

```
tlaplus-animate/SKILL.md contains:

playground-template.html    ← generic, ships with plugin
  ├── split-pane layout     ← always the same
  ├── action buttons        ← generated from spec actions
  ├── guard logic           ← generated from spec guards
  ├── invariant badges      ← generated from spec invariants
  ├── report-back buttons   ← always the same (clipboard copy)
  ├── trace log             ← always the same
  └── state preview         ← BESPOKE, generated by animator per domain
```

Template the chrome. Let animator only generate the state visualization component.

**Animator's job:** "Given spec's variables and domain context, generate a `renderState(state)` function that returns HTML for the prototype panel. Everything else handled by template."

Much smaller job for LLM per domain — generating one rendering function, not entire application. Guard handling, trace logging, report-back buttons all come free from template.

### Generic Applicability

State machine logic is domain-agnostic. Every TLA+ spec has same structure:
- Variables → displayed state (prototype panel)
- Actions → buttons
- Guards → enabled/disabled states
- Invariants → status indicators

Works for salon booking, distributed locks, payment flows, queue processors, insurance claim workflows. Only the visual prototype changes per domain.

**Blog approach:** Part 1 shows salon booking playground with full experience. Then note: "Action buttons, invariant badges, trace log, and report-back are templated. Only bespoke piece is the domain prototype — which the animator agent generates for each new domain."

### v1.1: WebSocket Bridge (Bidirectional)

The clipboard loop works but has two manual steps (paste + refresh). A WebSocket bridge removes both, turning the playground into a **live collaborative editing surface** for the spec.

**What changes:** Report-back buttons send structured JSON over WebSocket instead of copying to clipboard. Plugin receives messages, routes to verifier/specifier, then pushes updated guards back to the playground. HTML refreshes in place.

**Flow:**
1. User explores playground, hits double-booking state
2. Clicks "This shouldn't happen" → message goes to plugin via WebSocket
3. Verifier sees violation, specifier updates spec, verifier confirms fix
4. Plugin pushes updated guards back to playground
5. Playground refreshes in place — action greyed out, invariant goes green
6. User keeps exploring from new state

**Protocol (domain-agnostic JSON messages):**
```
Playground → Plugin:
  {type: "report", kind: "shouldnt_happen", trace: [...], state: {...}}
  {type: "report", kind: "expected", trace: [...], state: {...}}
  {type: "report", kind: "unsure", trace: [...], state: {...}}

Plugin → Playground:
  {type: "update_guards", actions: {book_slot: {enabled: false, reason: "slot held"}}}
  {type: "invariant_status", invariants: [{name: "no_double_booking", status: "pass"}]}
```

**Cost:** ~100 lines across three files (Node server, HTML client, hook to start/stop server). Becomes ~200 with edge case handling (port management, disconnection recovery). Requires Node.js.

**Upgrade path is clean:** Report-back buttons already generate the same structured JSON in v1 (for clipboard). v1.1 swaps `navigator.clipboard.writeText(trace)` for `ws.send(trace)`. Same data, different transport. Template barely changes.

**Demo sentence for blog:** "PM clicked through scenarios in playground. When she found a bug, clicked 'this shouldn't happen.' Thirty seconds later, the action greyed out."

---

## Distribution & Portability

### Distribution Strategy

**Two-path approach:**

1. **Own marketplace (immediate, fast iteration):** `.claude-plugin/marketplace.json` in GitHub repo.
   ```
   /plugin marketplace add richarda/tlaplus-workflow
   /plugin install tlaplus-workflow@richarda-tlaplus-workflow
   ```

2. **Official Anthropic marketplace (credibility):** Submit PR to `anthropics/claude-plugins-official` under `/external_plugins`. "Anthropic Verified" badge for plugins passing additional review.
   ```
   /plugin install tlaplus-workflow@claude-plugin-directory
   ```

Start with own marketplace while building. Once solid and blog published, submit to official directory.

### Three-Tier Portability

1. **Claude Code plugin (flagship):** Full experience — five agents, orchestration, hooks, split-pane playground
2. **Standalone skills:** Extract four SKILL.md files in universal format. Works in Cursor (`.cursor/rules/`), Copilot (`.github/copilot-instructions.md`), Gemini CLI (`.gemini/skills/`). No automated workflow — invoke skills manually.
3. **MCP server (optional, later):** Wrap TLC invocation as MCP tool. MCP supported by Cursor, Copilot, Claude Code, Windsurf. Gives everyone verification engine regardless of IDE.

Blog mention: "Full orchestrated workflow is Claude Code plugin. But skills work anywhere, and MCP server means any tool can run TLC."

### Contribution to tlaplus/AgentSkills

Skills to submit upstream (complementary to existing write-focused skills):
- **tlaplus-from-interview**: Elicitation patterns, completeness checklists
- **tlaplus-verify-explain**: TLC invocation, output parsing, counterexample-to-narrative
- **tlaplus-to-pbt**: Invariants → property-based test generators

Hold back **tlaplus-animate** initially — more opinionated, tightly coupled to our template approach.

Approach: Build plugin, write blog, then open issue showing working code + published blog. Submit PR adapting three skills to their format.

### Monetization

Plugin is calling card, not product. Ship open-source.

Better value paths:
- **Internal value at hx:** If plugin catches real bugs in Fidra or Monte Carlo, ROI argument writes itself
- **Consulting/workshops:** "Formal verification in AI-native engineering orgs" for insurance/fintech
- **Content/speaking:** Strange Loop, QCon — "I built a plugin that hides TLA+ behind conversation"
- **Paid course/template library:** Plugin free (top of funnel), charge for expanded guide with video walkthroughs, pre-built TLA+ specs for common patterns

---

## Execution Order

1. Build plugin skeleton: plugin.json + five agent definition files
2. Write the four new skills (including HTML template in tlaplus-animate)
3. Install tla2tools.jar, test TLC invocation via bash
4. Run salon example end-to-end through the plugin
5. Write Part 1 from the session transcript
6. Install plugin in Fidra project, run against drawer component
7. Write Part 2 from that session
8. Publish plugin to GitHub
9. Publish blog posts

---

## Open Questions

- **~~Spectacle as fallback?~~** Resolved: we build our own split-pane prototype. Spectacle is a developer state explorer; we need a PM-facing domain prototype.
- **~~Playground plugin as dependency?~~** Resolved: inspiration, not dependency. Our interaction model (state-space exploration with verification feedback) is different enough from theirs (parameter configuration) that extending their templates would fight the design. We credit the copy-prompt-back pattern as prior art.
- **~~WebSocket vs clipboard for v1?~~** Resolved: v1 uses clipboard (proven pattern, two manual steps: paste + refresh). v1.1 adds WebSocket for live feedback loop. Template architecture supports both — same structured JSON, different transport.
- **AgentSkills as dependency?** If tlaplus/AgentSkills ships as a Claude Code plugin, we could declare a dependency rather than inlining patterns. For now, inline.
- **MCP vs bash for TLC?** Bash is simpler and works in Claude Code today. The headless MCP server (PR #1296 on vscode-tlaplus) is the upgrade path for editors without bash access (Cursor, Copilot). Note in the blog as future work.
- **Agent teams (swarms) vs subagents?** Subagents are the right fit — our phases are sequential, not parallel. Agent teams add coordination overhead for no benefit here. Mention briefly in the post as an alternative for parallel verification workflows.
- **How far to push Part 2?** If the Fidra drawer spec extraction is messy, that's honest and valuable. Don't clean it up. The real cost/benefit assessment is the whole point of Part 2.
