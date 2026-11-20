# Implementation Plan: Agent accepts with approval

**Branch**: `833-agent-accept-with-approval` | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/833-agent-accept-with-approval/spec.md`

## Summary

The agent runs `wfctl arch accept`, `wfctl review sign-off`, and the installed
`wfctl arch approve-imports`, and the user approves each run at Claude Code's
permission prompt. One table in evidence and derivation lists the prompted
spellings. `install-skills` builds the Claude Code `ask` rules from it, and a
test holds the Codex rules file to it. The worktree guard lets a command
through only when it is exactly one table entry, the payload comes from Claude
Code, the rule is in `.claude/settings.json`, and wfctl's auto-approve is off.
Each command skips its terminal check when `CLAUDECODE` is set, and then skips
the typed confirmation too. At a terminal, nothing changes.

This builds on #407's managed `ask` rules, so implementation starts once #407
merges and this branch is rebased on `main`.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `typer`, `rich`, no new ones
**Storage**: `.claude/settings.json` (rules), `.wf-skills-manifest.json` (rule receipts), records' frontmatter
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy`, plus a walk in Claude Code
**Target Platform**: macOS and Linux shells under Claude Code, Codex, and Bob Shell
**Project Type**: CLI
**Performance Goals**: the guard adds no cost to a command that names none of the three commands, and two small file reads to one that does
**Constraints**: the import check's Context Map (`contexts-are-packages`), the accepted threat model in `prompt-approves-person-commands.md`, and minimal-complexity bias
**Scale/Scope**: three commands, five prompted spellings, two hosts that ask (Claude Code now, Codex once walked)

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

The repo has no `.specify/memory/constitution.md`. The gates below come from
`AGENTS.md` and the accepted records, as recorded under Complexity Tracking.

- [x] Validation plan exists: the three `uv run` checks, `wfctl doctor`,
      `wfctl check config`, one test per threat-model list entry, and a walk
      in Claude Code are named in Validation below.
- [x] Complexity is justified: the one added structure is the table, and
      `docs/architecture/design/prompted-spellings-one-table.md` records why
      three hand-kept lists lose.
- [x] Ownership is stated: the host decides whether a person agreed, wfctl
      decides whether the prompt will appear, and the user decides the
      threat model's lists (`prompt-approves-person-commands.md`).
- [x] Imports follow the Context Map: the table lives in `evidence`, which the
      guard already imports. `cli.py` is wiring and may import it.
- [x] Every change commits a release note (`change-carries-release-note`).
- [x] A security control change carries an accepted threat model
      (`security-change-needs-threat-model`): `prompt-approves-person-commands`
      is accepted.

Post-design re-check: all pass. Phase 1 adds no import arrow and no package.

## Design

### The table

`wfctl/evidence/_prompted.py` holds `Prompted(command, words)` and the
`PROMPTED` tuple from the level-3 record. `wfctl/evidence/__init__.py` exports
`PROMPTED`, `Prompted`, `prompted_match(text) -> Prompted | None`, and
`prompted_host() -> bool`.
`_review_gate.py` is placed in evidence by the baseline already, so it imports
from the module directly.

### Rules

`cli.py` builds the Claude Code rules from `PROMPTED`: `Bash(<words>:*)` for
each entry. They join #407's `ASK_RULES` as `_ManagedRule(SETTINGS_PATH, rule,
"ask", cost)`, so install, the receipt, `doctor`, and `uninstall-skills` all
reuse #407's path. `wfctl/agents/codex/rules/wfctl.rules` gains one
`prefix_rule` per entry, written by hand, and `tests/test_prompted_rules.py`
builds the expected entries from the table and compares.

### The guard

Two changes in `_review_gate.read()`, one per blocker the first review found.

**Sign-off and approve-imports get the accept's reader (PR-002).** Today
`read()` refuses both on two loose regexes, `_SIGN_OFF` and
`_APPROVE_IMPORTS`, which also refuse a `grep` or a commit message that only
names them. The accept's reader, `_accepts`, already tells a command that runs
the accept from text that names it, and `_reads_text_only` already exempts
`grep`, `git commit -m`, and `towncrier create`. So `_accepts` becomes
`_runs_person_command(text, words)`, taking the command's words (`("arch",
"accept")`, `("review", "sign-off")`, `("arch", "approve-imports")`), and
`read()` calls it once per command. The two regexes are deleted. The
dry-run handling stays specific to the accept. Every form the accept's reader
refuses today is then refused for the other two commands as well, and the
`Must let through` searches and commit messages pass for all three.

**The pass check reads the raw text, not split words (PR-001).** Before
appending a person-command refusal, `read()` asks `_prompt_will_ask(command,
payload, cwd)`, which returns a reason string when it says no and `None` when
the host will ask:

1. The raw command, with leading and trailing whitespace removed, starts with
   one `PROMPTED` entry's words joined by single spaces, followed by a space or
   the end. The comparison is literal and case-sensitive, so `wfctl "arch"
   accept s`, `wfctl ar\ch accept s`, and `WFCTL arch accept s` don't match.
   That is the form Claude Code's rule matches too.
2. The raw command holds none of `$`, a backtick, `\`, `;`, `&`, `|`, `<`,
   `>`, `(`, `)`, or a newline anywhere. A command holding one, including
   inside an `--agreed` citation, is refused, and the refusal lists the
   characters to remove from the command. This keeps the check from having to
   locate the citation or parse quoting.
3. `shlex.split` succeeds on it, so an unclosed quote is refused, and
   `shlex.split(text, comments=True)` gives the same words as
   `shlex.split(text)`. A `#` inside quotes, as in `--agreed "agreed on
   #833"`, gives the same words both ways and passes, and an unquoted comment
   doesn't (PR-018).
4. The payload's `tool_name` is `Bash`. Bob Shell sends `execute_command` or
   `run_shell_command`, and a payload with no `tool_name` is refused.
5. The repo's `.claude/settings.json` parses and carries that entry's `ask`
   rule. A missing or malformed file counts as the rule missing.
6. `evidence.auto_approve(agent_dir)` is false. An agent dir that can't be
   resolved counts as auto-approve on, so the check fails closed.

When it returns `None`, the refusal for that command is skipped. Every other
refusal in `read()` still runs. When it returns a reason, the refusal line
gains it. When several apply, the first of these prints: auto-approve is on,
the host is Bob Shell, the rule is missing, the form isn't plain. `contracts/cli.md` holds the exact wording.

The refusal's first line changes with the reason, so it never tells the agent
the command is off limits and then tells it to rerun the command (PR-017).
For auto-approve and Bob Shell, it keeps today's "is for a person to run in
their own terminal". For a missing rule or a form that isn't plain, it reads
"needs your approval at Claude Code's prompt", and the reason line says what
to change. `contracts/cli.md` holds the lines.

`refusal(command, cwd)` becomes `refusal(command, cwd, payload=None)`, and
`read(command)` becomes `read(command, cwd=None, payload=None)`, since the
pass check needs both (PR-008). `guard/_hook.py` passes the decoded payload. A caller that passes no payload
gets today's behavior, every person command refused. The settings file and the
mode file are read only after a command has matched a person command, so a
command naming none of them pays nothing new. A matching one pays two small
file reads.

### The commands

A new function, `prompted_host() -> bool`, returns true when `CLAUDECODE` is
set to a non-blank value. Claude Code sets it to `1`, and a non-blank test
doesn't break if that value changes (PR-009). It lives in
`wfctl/evidence/_prompted.py`, and the `evidence` package exports it under that
public name, so both `cli.py` and `_review_notes.py` call one function without
reaching into a private module (PR-009).

`CLAUDECODE` is inherited by every child process, including another agent
started from Claude Code's shell, such as a `codex exec` reviewer (PR-004).
That agent runs no guard and shows no prompt, so it passes this check. We
accept this: the review commands run with `--sandbox read-only`, so the
command's write fails there, and an accept that did land shows in the PR diff.
The record's Accepts item 8 says the check stops a mistake, and this is a
mistake it doesn't stop, so the PR body names it for the user to confirm.

1. `arch accept`: the terminal check becomes `if not _at_terminal() and not
   prompted_host()`. `--agreed` becomes optional, and a blank `--agreed ""`
   counts as absent. With no terminal and no citation, the `Log` line is
   "accepted — approved at the permission prompt". At a terminal with no
   citation, it refuses as today, naming `--agreed`. A redraw follows the same
   rule, with "drawing signed off — approved at the permission prompt"
   (PR-011).
2. A new subcommand, `wfctl arch check-accept <slug>`, runs exactly what `arch
   accept --dry-run` runs. It's outside every `ask` rule's prefix, so an
   unattended run can use it without a prompt nobody answers (PR-007). The
   design gate's fix line in `_evidence.py`, the refusal text in
   `_review_gate.py` and `cli.py`, `speckit-brainstorm/SKILL.md`,
   `commands/speckit.brainstorm.md` and its `allowed-tools` grant, and
   `design-levels/references/drawing-style.md` switch to it (PR-016). `--dry-run` keeps working, and prompts.
3. `review sign-off`: same check. With no terminal, it prints the pending
   commits and signs off without `input()`. At a terminal, it asks for the
   short sha as today.
4. `arch approve-imports`: same check in both `cli.py` and
   `_review_notes.approve_imports` / `run_approve_imports`. With no terminal,
   it prints the additions and approves without asking for the digest.
   `_inside_a_worktree` stays.

### Records

The accepted `prompt-approves-person-commands.md` names only
`accept-check-threat-model` in `supersedes`, and an accepted record isn't
edited. So a `supersedes` list wouldn't clear the warning on
`guard-catches-literal-accept`. Instead, the orphan check in `_records.py`
also counts a superseded record as claimed when its last `superseded` Log line
names a record that exists. `guard-catches-literal-accept.md` already carries
that line, so the warning clears with no edit to an accepted body. The
successor is the first word after `by ` on that line, with trailing
punctuation removed, and it counts only when a record with that slug exists.
The accepted record's Consequences said `supersedes` would take a list, and
this replaces that, so the PR body says so for the reviewer (PR-012). See
research R-005.

### Skills and docs

The skills that say these commands are for the user's own terminal change to
say the agent runs them only when the user asks, and Claude Code asks the user
first: `opening-a-change`, `architecture-decisions`, `fanning-out-code-review`,
`design-passes`, `speckit-brainstorm`, `design-levels/references/drawing-style.md`,
`architecture-decisions/references/threat-model.md` and
`threat-model-agent-commands.md`, and `reviewing-security`. `AGENTS.md`'s
Safety and Releasing sections change the same way. `speckit-brainstorm`'s
rule that an agent never accepts under auto-approve stays, since the guard
refuses there.

### Tests

1. `tests/test_accept_check_threat_model.py` reads the lists in
   `prompt-approves-person-commands.md` and runs every entry through the
   guard with a Claude Code payload and the rule present. It also keeps
   reading items 1 - 20 of `accept-check-threat-model.md`'s "Must keep
   catching", since the new record keeps them (PR-005). Items 1, 2, 16, and 19
   are a plain spelling with arguments, so under those conditions they pass,
   and the test asserts that. Every other item stays refused. That reading of
   items 16 and 19 is the user's to confirm, since the record leaves it to
   them, so the PR body names it (PR-019).
   The same test runs each of those items again with the accept's words
   replaced by sign-off's and by approve-imports', where the item has a
   meaning for them, so the generalized reader is tested for all three
   (PR-020). `_runs_person_command` takes the words as a parameter in every
   place `_review_gate.py` names `arch` and `accept` today, about seven.
2. A test for each of items 13 - 16 of "Must keep catching" builds the
   condition: a `uv run` approve-imports, auto-approve on, a Bob payload, a
   settings file with the rule removed.
3. `tests/test_prompted_rules.py`: install writes every rule, `doctor` reports
   each one removed, and the Codex file matches the table.
4. Command tests: each command with `_at_terminal` false and `CLAUDECODE` set
   runs and writes; with neither, it refuses; at a terminal, sign-off and
   approve-imports still ask, and accept still needs `--agreed`.
5. `tests/test_review_gate.py` updates the cases that expected a plain
   spelling refused, and adds the sign-off and approve-imports forms the
   accept's reader now catches for them.
6. `tests/conftest.py`'s autouse fixture also removes `CLAUDECODE`, so the
   terminal-refusal tests behave the same inside and outside Claude Code
   (PR-006). A test sets it on purpose where it needs it.
7. A test sets `WFCTL_AGENT=claude` with no `CLAUDECODE` and no terminal, and
   checks all three commands still refuse (PR-013).
8. `wfctl arch check-accept` gives the same output and exit code as `arch
   accept --dry-run` on a passing record and on a refused one.

## Validation

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy
uv run wfctl doctor
uv run wfctl check config
```

Then the walk in `quickstart.md`. Claude Code's guard hook runs the installed
`wfctl`, not the branch's, so the walk starts with the user installing the
branch build as the tool and ends with reinstalling from `main` (PR-003). That
install is the user's to run.

## Project Structure

### Documentation (this feature)

```text
specs/833-agent-accept-with-approval/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
└── tasks.md             # /speckit.tasks
```

### Source Code (repository root)

```text
wfctl/
├── evidence/
│   ├── __init__.py          # exports PROMPTED, Prompted, prompted_match, prompted_host
│   └── _prompted.py         # new: the table and the host check
├── _review_gate.py          # one reader for all three commands; pass check
├── _evidence.py             # the design gate's fix line names check-accept
├── _review_notes.py         # approve-imports without a terminal
├── guard/_hook.py           # passes the payload to the review check
├── arch/_records.py         # a superseded Log line naming its successor counts
├── cli.py                   # rules from the table; accept and sign-off changes
└── agents/
    ├── codex/rules/wfctl.rules
    └── skills/…             # wording in the skills listed above

tests/
├── test_prompted_rules.py   # new
├── test_accept_check_threat_model.py
├── test_review_gate.py
├── test_review_notes.py
└── test_arch_accept_dry_run.py

changes/833.change.md
```

**Structure Decision**: the single wfctl package, with the new module inside
the `evidence` context, since `_review_gate.py` is placed there and the guard
already imports it.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates taken from `AGENTS.md` and accepted records | The repo has no constitution file | A gate with no source is decorative |
