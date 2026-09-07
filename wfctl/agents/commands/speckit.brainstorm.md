---
disable-model-invocation: true
description: Start a brainstorming session. Wraps the design-levels + brainstorming + idea-refine skills, whose output lands in specs/<branch>/design.md for speckit pickup.
handoffs:
  - label: Start Specify
    agent: speckit.specify
    prompt: The design document is ready in specs/<branch>/design.md. Run specify.
    send: true
allowed-tools: Read Glob Write Bash(wfctl feature-paths*) Bash(wfctl status*) Bash(mkdir*) Bash(git log*)
---

Read `AGENTS.md` at the repository root for project overrides. It is optional —
if the file is absent, proceed silently. Then invoke the `design-levels` skill —
it governs which level each question gets answered at, and its gates run
throughout — and follow the `brainstorming` skill exactly.

Read which mode this feature is in before the first gate:

```bash
wfctl status --json      # read `auto_approve`
```

`false` is the default and today's behaviour: every gate stops for a human.
`true` means the gates are answered into the record instead, and the approval
happens at the PR. Both skills below branch on it, and neither one waives a
record — an auto-approving pass documents more than an attended one, not less.

Create the destination directory:

```bash
wfctl feature-paths      # prints FEATURE_DIR='…/specs/<current-branch>'
```

Read `FEATURE_DIR` from that output and `mkdir -p` it. Substitute the real path —
`<branch>` in this file is a placeholder, never a directory name. The design
document is `design.md` inside that directory.

After the brainstorming session concludes, invoke the `idea-refine` skill to
sharpen the chosen direction into an actionable one-pager.

**Output:** `specs/<branch>/design.md`, written by `idea-refine` — once, at final
fidelity. `brainstorming` carries its approved design here in context rather than
saving it first; a second write to that path destroys the approved design.
`/speckit.specify` reads the file from there.
