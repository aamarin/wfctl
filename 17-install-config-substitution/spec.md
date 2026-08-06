# Feature Specification: install-config substitution

**Feature Branch**: `17-install-config-substitution`
**Created**: 2026-08-02
**Status**: Draft
**Input**: User description: "install-config: ship pre_remove wired and substitute the <project> placeholder" (issue #17)

## Clarifications

### Session 2026-08-02

- Q: What should happen if the copied config still contains the `<project>` placeholder after substitution? → A: Warn, naming the problem and the exact remediation line. Check for the surviving placeholder rather than for a missing key, so a renamed or reformatted key cannot slip past.
- Q: How should the retrofit be reachable — prompt only, a non-interactive flag, or its own command? → A: Prompt only. A flag relocates the reachability problem rather than solving it; revisit only if the warning is demonstrably ignored.
- Q: Should the retrofit prompt state where archives will be written? → A: Yes. The developer is being asked to consent to a change whose entire value is a destination they cannot otherwise see.
- Q: Should the health check also lint the session-name prefix while it has the file open? → A: No — `pre_remove` only. A cosmetic warning beside a data-loss warning trains the reader to skim past both, and the data-loss warning is the one whose job is to be noticed.

## Dependencies

- **wf-skills#8** — *"workmux template: wire pre_remove to `wfctl archive-story`"* — owns the
  template edit behind User Story 1. It specifies the identical hook this
  feature assumes, and its stated blocker (`wfctl#10`, the archiving subcommand)
  has shipped, so it is ready to land independently of this branch.
- **wf-skills#3** — *"spec-template.md mandates PFMS-specific sections"* — unrelated to
  this feature's behavior, but it is why this spec omits the template's
  mandatory project-impact section.

## Delivery ownership

This feature spans two repositories. User Story 1 is delivered **upstream**;
Stories 2 and 3 are delivered on this branch.

| Story | Delivered by |
| ----- | ------------ |
| US1 — new repos protect their artifacts | wf-skills#8 (template edit) |
| US2 — existing repos are warned and offered a fix | this branch |
| US3 — session names carry the project | this branch |

This branch's automated tests construct their own template fixtures, so they do
not block on wf-skills#8. Manual verification of US1 does.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - A newly configured repo protects its planning artifacts (Priority: P1)

A developer runs the config-seeding command in a fresh project. From that moment,
tearing down a worktree preserves the story's spec, plan, tasks, and analysis
into durable storage — without the developer knowing the archive step exists or
editing the seeded file.

Today the seeded config explicitly disables the pre-removal hook, so the archive
step never runs and those artifacts are destroyed silently along with the
worktree.

**Why this priority**: This is silent, unrecoverable data loss. It is the failure
that caused four stories' artifacts to be lost in a downstream project, and at
least one project is exposed right now. Every other part of this feature is
cosmetic next to it.

**Delivered by wf-skills#8**, not by this branch — the fix is a template edit in
a separate repository, and that issue already specifies the identical hook. This
branch depends on it and verifies against it; it does not re-implement it.

**Independent Test**: Seed a scratch repo, create a worktree, put a spec
directory in it, remove the worktree, and confirm the artifacts appear in
durable storage. Delivers the entire protective value on its own.

**Acceptance Scenarios**:

1. **Given** a repo seeded with the standard config, **When** a worktree holding
   planning artifacts is removed, **Then** those artifacts are recoverable from
   durable storage afterward.
2. **Given** a checkout where the archiving tool is not installed, **When** a
   worktree is removed, **Then** removal completes successfully and no worktree
   is left stranded.
3. **Given** the archiving step fails internally, **When** a worktree is removed,
   **Then** removal still completes and the failure does not block teardown.

---

### User Story 2 - An already-configured repo learns it is unprotected (Priority: P2)

A developer runs the health check in a project configured before this change.
The check reports that teardown protection is missing and offers to wire it. On
confirmation, only the hook is modified; every other line the project has
customized is left exactly as it was.

Seeding is a one-time operation that refuses to overwrite an existing config, and
overwriting wholesale would destroy the customizations a mature project has
accumulated. Without this, the fix reaches new projects only, and existing ones
stay silently exposed indefinitely.

**Why this priority**: This is the only path by which an already-configured
project ever becomes protected. It is a painkiller, not a convenience — but it
depends on the hook definition from Story 1 being settled first.

**Independent Test**: Point the health check at a project whose pre-removal hook
is disabled, confirm the prompt, and verify the resulting change is limited to
the hook.

**Acceptance Scenarios**:

1. **Given** a project whose pre-removal hook does not invoke archiving,
   **When** the health check runs, **Then** it reports the gap and names the
   consequence.
2. **Given** that report and an interactive session, **When** the developer
   confirms, **Then** the hook is wired and the rest of the file is unchanged.
3. **Given** a non-interactive session, **When** the health check runs, **Then**
   it reports the gap, prompts for nothing, and modifies nothing.
4. **Given** a project whose pre-removal hook holds its own custom steps,
   **When** the health check runs, **Then** it reports the gap with manual
   instructions and leaves the file untouched.
5. **Given** a project with no such config file, **When** the health check runs,
   **Then** it says nothing about this condition.

---

### User Story 3 - Session names carry the project, not a placeholder (Priority: P3)

A developer seeds a project and its terminal sessions are immediately named after
the project, distinguishing them from every other project's sessions. The seeded
file contains no placeholder text awaiting a human.

**Why this priority**: A vitamin, not a painkiller. It saves one hand-edit that
every existing project already made once. It is in scope because the value is
derived inside work being done anyway, not because it would justify its own
change.

**Independent Test**: Seed a scratch repo and confirm the prefix holds the real
project name, then repeat from inside a linked worktree and confirm the name is
still the project's — not the worktree's.

**Acceptance Scenarios**:

1. **Given** a seed run from a project's main checkout, **When** it completes,
   **Then** the session prefix holds the project's name and no placeholder text
   remains.
2. **Given** a seed run from inside a linked worktree, **When** it completes,
   **Then** the prefix still holds the project's name, not the worktree's
   directory name.
3. **Given** a project whose name contains a character the terminal multiplexer
   rewrites in session names, **When** it completes, **Then** the written value
   matches what the multiplexer will actually create, and the substitution is
   reported once.

---

### Edge Cases

- **Project name contains `.` or `:`** — the multiplexer silently rewrites these
  to `_` and then cannot be targeted by the original string, reporting the
  failure as a missing pane rather than a bad name. Measured behavior; these two
  characters and no others (spaces, `$`, `-`, `_` survive verbatim).
- **Project name contains an apostrophe** — must not produce a malformed config
  file.
- **Seeding from inside a linked worktree** — the worktree's own directory is
  named after the branch, so naive derivation writes a branch handle into a
  committed file.
- **Template is missing an expected key** — seeding must still succeed rather
  than crash or append a stray key.
- **Pre-removal hook holds custom steps** — the automated fix must decline rather
  than guess at ordering or intent.
- **Config file is not writable** — the health check must report and continue,
  not abort.
- **No config file at all** — not every project uses worktree tooling; the health
  check must stay silent.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: A newly seeded config MUST invoke story archiving before worktree
  removal, with no hand-editing required.
- **FR-002**: The archive invocation MUST NOT prevent worktree removal when the
  archiving tool is absent from the environment or fails internally.
- **FR-003**: A newly seeded config MUST NOT contain the literal placeholder
  `<project>`.
- **FR-004**: The session-name prefix MUST be written with the project's real
  name, active rather than commented out.
- **FR-005**: The project name MUST be derived without reference to the current
  checkout's own directory name, so that seeding from a linked worktree yields
  the project rather than the branch handle.
- **FR-006**: Characters the terminal multiplexer rewrites in session names
  (`.` and `:`) MUST be substituted before the value is written.
- **FR-007**: When that substitution changes the name, the command MUST report
  the original and final values exactly once; when it changes nothing, it MUST
  report nothing.
- **FR-008**: A project name containing an apostrophe MUST produce a valid config
  file.
- **FR-009**: Seeding MUST succeed when an expected key is absent from the source
  template, leaving that key alone rather than failing or inserting one.
- **FR-009a**: After writing, seeding MUST check whether the literal `<project>`
  survives anywhere in the file, and warn if it does. The check MUST target the
  surviving placeholder rather than the presence of a named key, so that a key
  renamed or reformatted upstream cannot defeat it.
- **FR-009b**: That warning MUST state what went wrong and the exact remediation
  line, including the resolved project name — which is already known at that
  point. For example:

  > `⚠ .workmux.yaml still contains '<project>' — the prefix was not substituted.`
  > `  The template's window_prefix key may have been renamed or reformatted upstream.`
  > `  Fix: set window_prefix: 'wfctl__'`

- **FR-009c**: The check MUST NOT flag `<agent>`, which is the worktree tool's
  own runtime placeholder and is resolved by that tool rather than by seeding.
- **FR-010**: The health check MUST report a config whose pre-removal hook does
  not invoke story archiving, naming the consequence.
- **FR-011**: Archiving MUST be counted as wired only when it is invoked from
  within the pre-removal hook itself, by a line that is not a comment. A mention
  anywhere else in the file — another section's command, or a comment — MUST NOT
  count. Erring the other way makes the check report an unprotected repo as
  protected, which is the precise failure it exists to prevent.
- **FR-012**: When interactive, the health check MUST offer to wire the hook and
  apply it on confirmation.
- **FR-012a**: Before asking, the health check MUST state the resolved
  destination that archives would be written to, so the developer can see what
  they are consenting to. For example:

  > `⚠ .workmux.yaml: pre_remove does not call archiving — removing a worktree`
  > `  will discard its specs, plan, and tasks.`
  > `  Archives would be written to: ~/.local/state/wfctl/pfms/<branch>/archive/`
  > `Wire it now? [Y/n]`

- **FR-012b**: The retrofit MUST be reachable only through that prompt. No
  non-interactive flag and no dedicated command in this iteration.
- **FR-013**: When not interactive, the health check MUST report only — no
  prompt, no modification.
- **FR-013a**: In that non-interactive report, it MUST name how to reach the fix
  (running the health check from a terminal), since the prompt is otherwise
  unreachable from automation.
- **FR-013b**: The health check MUST report only the pre-removal hook. It MUST
  NOT warn about an unsubstituted session prefix, which is cosmetic and would
  dilute the warning that prevents data loss.
- **FR-014**: An applied fix MUST modify only the pre-removal hook, leaving every
  other line of the file byte-identical.
- **FR-015**: When the pre-removal hook is anything other than a bare disabled
  list on its own line, the health check MUST report manual instructions and leave
  the file unchanged. "Anything other than" covers a hook holding its own steps and
  a hook that is absent entirely — in both cases the correct insertion point and
  ordering are unknowable, so the health check MUST NOT guess.
- **FR-016**: The health check MUST NOT change its exit status on account of this
  condition, matching how it treats its other warnings.
- **FR-017**: The health check MUST stay silent about this condition when no
  config file is present.
- **FR-018**: Declining the offered fix MUST NOT be recorded; the condition is
  ongoing drift and MUST be reported again on the next run.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: A freshly seeded project requires **zero** hand-edits before
  worktree teardown preserves planning artifacts.
- **SC-002**: Removing a worktree from a freshly seeded project preserves
  **100%** of that story's planning artifacts.
- **SC-003**: Worktree removal succeeds in **100%** of cases where the archiving
  tool is missing or failing — no teardown is ever blocked by this feature.
- **SC-004**: A project missing teardown protection is surfaced within **one**
  health-check run, rather than discovered after work is already lost.
- **SC-005**: Applying the automated fix to an existing project replaces **one**
  line with **two**, and alters no other line in the file. Verified against a
  326-line real-world config: net +1 line, every other byte identical.
- **SC-006**: The written session prefix matches what the terminal multiplexer
  actually creates in **100%** of project names, including those containing
  reserved characters.
- **SC-007**: Seeding produces an identical project name whether run from a main
  checkout or from a linked worktree.
- **SC-008**: **Zero** placeholder literals remain in a seeded config — and if one
  ever does, the developer is told at seed time rather than discovering it in a
  session name, with a remediation line they can paste directly.

## Validation Strategy _(mandatory)_

- `uv run pytest -q` — full suite, including new coverage for the text
  transforms, the project-name derivation under a real linked worktree, and both
  interactive and non-interactive health-check paths.
- `uv run ruff check .` — lint.
- `uv run mypy` — type check.
- **Manual**: seed a scratch repo, confirm both keys land with real values; then
  remove a worktree holding a spec directory and confirm the archive appears in
  durable storage with an index listing the artifacts.
- **Manual (retrofit)**: run the health check against an already-configured
  project, accept the prompt, and confirm the resulting change is a two-line
  diff (SC-005).

## Assumptions

- Pre-specify design context loaded from `.agent/spec.md`. That document records
  three settled decisions this spec reflects: the prefix ships active rather than
  commented (D1); retrofit is surfaced by the health check and applied only on
  confirmation (D2); reserved characters are substituted with a conditional
  notice (D3). No open questions remain, so this spec carries **no** unresolved
  clarification markers.
- The disabled pre-removal hook in the shipped template is an explicit opt-out of
  the tooling's own default behavior, not an absence of configuration. Replacing
  it therefore forfeits nothing that today's seeded projects still have.
- Configs whose pre-removal hook is disabled outright are the only shape observed
  in practice (two projects examined). Projects with custom hooks degrade to
  manual instructions rather than an automated fix, so this assumption is a
  convenience bet rather than a correctness one.
- The template change lives in a **separate repository** from the tool. The
  tool's automated tests construct their own template fixtures and so do not
  depend on that change landing; manual verification does.
- The health check's offered fix reaches a developer only in an interactive
  terminal. Session-startup automation runs it without a terminal and will report
  the warning without ever prompting.
