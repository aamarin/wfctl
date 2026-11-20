# Implementation Plan: Auto-approve has its own command

**Branch**: `407-auto-approve-mid-session` | **Date**: 2026-11-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from the feature's `spec.md`

## Summary

A new `wfctl auto-approve [on|off]` command turns the mode on or off at any
point in a session, and with no argument it prints the mode and which session
granted it. `wfctl start --auto-approve` keeps working and shares one grant
helper with the new command. Every mode change a person makes now carries the
identity of the session that made it. Running `on` while the mode is already
on writes nothing, so it can't restart the review count. The `using-wfctl`
skill tells the agent to turn the mode on only when a person asked. Both `.workmux.yaml` files gain a `post_create` line that
grants the mode once at worktree creation when `WFCTL_AUTO_APPROVE` is exactly
`1`. When a repository's `post_create` has no such line, `wfctl auto-approve`
prints a note with the line to add. The skills and reference docs name the new
command.

The design is in the accepted record
`docs/architecture/approval-mode-is-stored-intent.md`. No level-3 record was
written.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `typer`, `rich`. Nothing new.  
**Storage**: `mode.json` and `events.jsonl` in the branch's state dir. No new
files.  
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run
mypy`, then `uv run wfctl install-skills` and a read of the two changed skills,
one manual `WFCTL_AUTO_APPROVE=1 workmux add` on a throwaway issue, and one
manual check that Claude Code prompts when the agent runs `wfctl auto-approve
on` and `uv run wfctl auto-approve on`, in the default mode and in auto mode.  
**Target Platform**: macOS and Linux shells, the same as the rest of wfctl.  
**Project Type**: CLI  
**Performance Goals**: None beyond the existing commands. The new command does
one event-log read and at most one `.workmux.yaml` read.  
**Constraints**: `contexts-are-packages`: the CLI imports `evidence` and
`install` through their packages only, and evidence can't import session
continuity, so the caller's identity reaches the grant as an argument.
Minimal-complexity bias: reuse `_refuse_unless_the_issue_allows_a_session`,
`build_report(...).session_holder`, and `_workmux._live_lines` rather than
writing new versions of them.  
**Scale/Scope**: One command, one evidence function changed and one added, one
install helper added, two YAML files, two skills, one reference doc, and a
release note.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The gates after the
first three come from `AGENTS.md`'s definition of done and its architectural
rules, as recorded under Complexity Tracking.

- [x] Validation plan exists: the three `uv run` commands, the new test files
      named in Project Structure, the shell test of the shipped grant line,
      the `install-skills` read for the two skills, and the manual check that
      Claude Code prompts on the ask rules.
- [x] Complexity is justified: no new abstraction. The grant helper exists so
      `start` and the new command can't drift apart in what they write, and it
      replaces code rather than adding a layer.
- [x] Ownership is stated: see "Ownership" below.
- [x] Imports follow the Context Map: `cli.py` is wiring and may import any
      context's package. `evidence/_mode.py` imports only `wfctl._io`, as it
      does today. No new baseline line, arrow, or shared package, so nothing
      waits on `approve-imports`.
- [x] A change under `wfctl/agents/` is exercised after `uv run wfctl
      install-skills`, not only by the suite.
- [x] The branch commits `changes/407.addition.md`. The change adds a command,
      so `addition` is the category.
- [x] Accepted records are honored: `approval-mode-is-stored-intent`,
      `session-identity-from-named-agent` (the identity is compared, never
      parsed or printed), `no-hardcoded-agent` (the hook line names no agent),
      and `install-modes` (`install-config` stays seed-once).

### Ownership

1. **The mode's value** is owned by wfctl, in `mode.json`, written only by the
   grant helper and the review cap. Nothing on disk implies the mode, so the
   agent can't compute it.
2. **The time and session of each mode change** are owned by wfctl, written
   into the event log when the change happens. The agent shouldn't be the
   witness to its own grant.
3. **The relation shown to the reader** ("this session", "another session", "an
   unknown session") is derived at read time by comparing the last mode
   change's identity with the caller's. It is never stored, per
   `session-state-is-re-derived`.
4. **Whether the repository's `post_create` has a grant line** is derived from
   `.workmux.yaml` on every bare `wfctl auto-approve` run. The repository owns
   the file, and wfctl only reads it.
5. **Whether a person asked for the grant** is visible only in the agent's
   conversation, so wfctl can't check it. The record accepts this as its case
   1. The control is an instruction in `using-wfctl`, in a new paragraph under
   `## Commands` right after the command table. It tells the agent to run
   `wfctl auto-approve on` only when a person in this conversation asked for an
   unattended run, or started the run with `WFCTL_AUTO_APPROVE=1`. It also says
   never to turn the mode on from the agent's own judgment that the work is
   ready, and that `off` is always allowed. The `plan-walkthrough` refusal
   points at the same rule. In Claude Code, a permission prompt backs the
   instruction up (Walkthrough fixes, item 2).

### Review-plan fixes

These three changes answer the MAJOR findings of the first plan review:

1. **The holder refusal is worded for both meanings of `"other"`.** That value
   covers a different conversation holding the branch and this conversation
   having ended its own session with `wfctl end`. The refusal says that no
   session is open for this conversation and names `/start-session`, which
   fixes both (research.md §1, contracts/cli.md).
2. **`on` while the mode is already on writes nothing.** The grant helper reads
   `mode.json` first and skips both the file and the event, so `review_count`
   doesn't restart. `start --auto-approve` shares the helper and the rule. A
   revoked mode reads as off, so `on` after a revocation is a new grant and
   gives three more reviews, as the record says (research.md §3a). The data
   model separates a grant from a mode change in general.
3. **The rule against an unasked grant has a named home.** It's the
   `using-wfctl` paragraph in Ownership item 5. A test in
   `tests/test_skills_reference_auto_approve.py` checks that the shipped
   `using-wfctl` carries `auto-approve on` next to the words "only when", so
   deleting the rule fails the suite.

### Walkthrough fixes

These two changes answer the gaps the plan walkthrough found:

1. **`on` skips only when a grant is on record.** The skip in Review-plan fix
   2 checks two things: `mode.json` reads on, and the newest `mode` event, the
   review cap's revocation included, is a grant (`newest_is_grant`). If
   someone wrote `mode.json` by hand, the newest event isn't a grant, so `on`
   writes the file and appends the event as usual. That event gives the review
   cap its starting point. Without this, a hand-written mode file followed by
   `on` leaves `review_count` at 0, and the cap never turns the mode off.
   Checking the newest event, not the last grant, also covers a hand edit made
   after a revocation, where the last grant is older than the revocation.
2. **Claude Code asks the person before the agent turns the mode on.**
   `install-skills --agent claude` adds two rules to the `permissions.ask`
   list in `.claude/settings.json`: `Bash(wfctl auto-approve on:*)` and
   `Bash(uv run wfctl auto-approve on:*)`. Claude Code then prompts the person
   every time the agent runs the command, even when a broader `allow` rule
   covers wfctl. Claude Code honors an ask rule in every permission mode,
   `bypassPermissions` and auto mode included. In `dontAsk` mode and in a
   headless `claude -p` run with no permission host, Claude Code denies the
   call instead of asking, which still leaves the mode off. The ask rules
   don't cover the creation hook. A person who runs `WFCTL_AUTO_APPROVE=1
   workmux add` isn't prompted, and neither is an agent that runs it, since
   the command it types is `workmux add`. The record lists the agent's case as
   accepted. Other agents rely on their own permission settings and the
   `using-wfctl` instruction.

   The rules go through the same path as today's managed deny rule
   `Bash(cd:*)`. `_managed_permissions` returns a list kind with each rule
   (`deny` or `ask`). The `_settings.py` helpers take the list name instead of
   assuming `deny`. The manifest receipt records the kind with the rule. As a result, install, uninstall, and `doctor` keep, remove, and check an
   ask rule the same way as the deny rule, including the refusal when a repo
   deletes a rule wfctl installed. The printed lines differ. Each managed rule
   carries its own explanation, so `doctor` and the install refusal don't
   mention `cd` for an ask rule. The install announcement names the rules this
   run added rather than `DENY_RULE`, so an upgrade that adds only the ask
   rules doesn't announce `Bash(cd:*)` again (contracts/cli.md). A receipt with no kind reads as `deny`, so manifests written
   before this change still match.

   This narrows the accepted record's case 1, an agent granting itself the
   mode without being asked. The record isn't edited. A new level-2 record,
   `auto-approve-grant-asks-first`, states the prompt and its limits: Claude
   Code only, matched by the typed command, and a deliberate wrapper still gets
   past it.

### Second review fixes

The second plan review found one MAJOR and nine MINOR gaps, and all of them
are folded in here or in the files named:

1. **Claude Code's prompt is checked by hand, not only by tests (PR-009).**
   Claude Code's docs say an ask rule prompts in every permission mode,
   including `bypassPermissions` and auto mode. They also say `dontAsk` mode
   and a headless `claude -p` run deny the call instead. The record now states
   both. The validation plan adds a manual check: after `uv run wfctl
   install-skills --agent claude`, the agent runs `wfctl auto-approve on` and
   `uv run wfctl auto-approve on` in the default mode and in auto mode, and the
   check records that each one prompted.
2. **The grant writes the event first (PR-004).** A failed append leaves the
   mode as it was, and the command prints `✗ Couldn't record the auto-approve
   change: <error>` and exits 1 (research.md §3a).
3. **The bare command's second line matches the mode file (PR-005).** It shows
   the last mode change only when the newest `mode` event agrees with
   `mode.json`. Otherwise it prints `no grant on record`, or `turned off
   outside wfctl` (contracts/cli.md).
4. **The revoked line is `_revocation_line`'s (PR-006).**
5. **The bare command creates nothing (PR-007).** It resolves the state dir
   with `create=False` and skips the old-file cleanup. `off` and the bare
   command both work on a branch that names no issue.
6. **A creation-hook grant shows the session that ran `workmux add` (PR-008).**
   The spec's edge cases state it, and the hook line stays unchanged.
7. **Each managed rule carries its own explanation (PR-010).** See Walkthrough
   fix 2.
8. **The ask rules get end-to-end tests (PR-011).** They go in
   `tests/test_install_hook_merge.py`, beside the deny rule's tests.
9. **The creation hook is an accepted path around the prompt (PR-012).** See
   Walkthrough fix 2 and the record's Accepts list.
10. **data-model.md states the grant rule from Walkthrough fix 1 (PR-013).**

## Project Structure

### Documentation (this feature)

```text
<FEATURE_DIR>/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
└── tasks.md          # /speckit.tasks writes this, not /speckit.plan
```

### Source Code (repository root)

```text
wfctl/
├── cli.py                              # new `auto-approve` command; `start` calls the shared grant helper; `_managed_permissions` gains the two ask rules and a list kind
├── evidence/
│   ├── __init__.py                     # export `last_change`, `newest_is_grant`, and `ModeChange`
│   └── _mode.py                        # `grant_auto_approve(..., session=)` appends first and skips a repeat `on`; new `last_change` and `newest_is_grant`
├── install/
│   ├── __init__.py                     # export `post_create_grants` and `GRANT_LINE`
│   ├── _settings.py                    # permission helpers take the list name (`deny` or `ask`)
│   └── _workmux.py                     # `post_create_grants(text)`; `GRANT_LINE`
└── agents/
    ├── configs/workmux/.workmux.yaml   # grant line, last in post_create
    └── skills/
        ├── using-wfctl/SKILL.md        # new command row; "only when a person asked" rule; install-config writes once
        └── plan-walkthrough/SKILL.md   # refusal names `wfctl auto-approve off`

.workmux.yaml                           # this repo's copy, with `uv run wfctl`
docs/reference.md                       # three mentions of `start --auto-approve`, plus a command row
changes/407.addition.md

tests/
├── test_auto_approve_command.py        # new: User Stories 1, 2, 4 and FR-008, FR-009
├── test_auto_approve_mode.py           # existing: the session field on start's grant; a repeat `on` doesn't reset review_count
├── test_skills_reference_auto_approve.py  # new: using-wfctl carries the "only when" rule
├── test_settings_merge.py              # existing: ask-list merge and removal; a kind-less receipt reads as deny
├── test_install_hook_merge.py          # existing: install refusal, doctor warning, and uninstall for a deleted ask rule; the upgrade announcement names only added rules
└── test_workmux.py                     # post_create_grants cases; shipped line in a shell
```

**Structure Decision**: Single project. The command lives in `cli.py` beside
`start`, since that is where every command is registered and the two share a
helper. The mode's storage stays in `evidence/_mode.py`, and the YAML reading
stays in `install/_workmux.py`, beside `post_create_wired`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates borrowed from `AGENTS.md` | The repository has no constitution | A gate with no source is decorative, so each borrowed gate names the `AGENTS.md` rule or record it comes from |
