# Implementation Plan: A security review panel runs before every change opens

**Branch**: `622-security-review-panel` | **Date**: 2026-10-23 | **Spec**: `spec.md` in this feature directory
**Input**: Feature specification from `spec.md` in this feature directory

## Summary

Every change gets a security review group and a code review group before its
pull request opens, and wfctl, not the coordinating agent, records whether each
review ran. wfctl gains a `review` command group that starts a group's run,
checks its reports, and takes a person's sign-off, plus a `wfctl relay`
command for a reviewer that can't write its own report. The records live in
the branch's state directory beside `verify.json`. The worktree guard gains a
review check that refuses `gh pr create`, `gh pr merge`, and the `gh api`
merge calls while any group hasn't reviewed the newest commit of the branch
the command acts on. A worktree acts only on its own branch's pull request,
and only the checkout on the trunk branch acts on another's. The check refuses
the `gh api` and GraphQL calls that create or merge a pull request every time,
and the commands its rules can't read for sure, since it can't tell their
target. Every hole still open on 2026-10-24, and any found later, is a known
limit instead, listed in the spec's Edge Cases, and the required CI check in
#627 closes those. The two
security reviews ship with wfctl, and
`fanning-out-code-review` and `opening-a-change` drive the groups through the
new commands.

The design records fix the shape. Records go in the state directory, groups
are a list under `review` in `wfctl.json`, a blocked reviewer's report is
relayed through wfctl, and the review check runs inside the existing guard
process. This plan settles what those records left open: the command names,
the file layout, how a report names its commit, how the check finds the branch
a command acts on, and how a model that can't run is recorded.

Design records read before this plan (via `reading-design-records`):

```
Design records: 4 listed in design.md
  docs/architecture/design/622-review-records-in-state-dir.md
  docs/architecture/design/622-review-groups-list.md
  docs/architecture/design/622-blocked-reviewer-relays-report.md
  docs/architecture/design/622-review-check-in-worktree-guard.md
```

The accepted level-2 record `review-covers-unreviewed-commits` is the boundary
this plan implements.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: `typer` and `rich` for the CLI commands; no new
dependency. The guard path imports neither, and the review check keeps it that
way. `git` and `gh` run as subprocesses.
**Storage**: JSON and Markdown files under `<state dir>/reviews/`, written with
`_io.write_atomic`. Events go to the branch's `events.jsonl` through
`_io.append_event`. See `data-model.md`.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`,
`uv run mypy wfctl/`, `uv run wfctl check config`, and `uv run wfctl doctor`
after `uv run wfctl install-skills --agent claude`. New tests are listed under
Project Structure.
**Target Platform**: the `wfctl` CLI on macOS and Linux, run by Claude Code's
`PreToolUse` hook for the guard
**Project Type**: CLI
**Performance Goals**: a command that matches none of the review check's
patterns costs under 1 ms more than today, measured on an `ls` payload
(SC-003). A matching command may spend one `gh` call and a few `git` calls,
since it runs a few times per branch.
**Constraints**: the guard path must not import `typer` or `rich`
(`tests/test_guard_entry.py`). Vendored files are credited the way
`vendor-upstream-skills` requires: the `security-and-hardening` skill ends with
the attribution line and is otherwise unedited, and the `/security-review` file
stays byte-identical, credited by a row in the record's file table and a
`NOTICES.md` entry that names it (`research.md` R10). Every `gh` and `git`
call in the review check runs with a 5-second timeout, including those inside
the `_paths` helpers it calls (R4). Skill source is edited under `wfctl/agents/`, never
`.agents/` or `.claude/` (`layer-model`). Tests pin `NO_COLOR`. And a
minimal-complexity bias.
**Scale/Scope**: three new modules, one CLI command group and one top-level
command, one change to `_hook.worktree_guard`, a timeout keyword on eight `_paths`
helpers, one `check config` reader, two
vendored files, one new wfctl skill, two skill rewrites, and an `AGENTS.md`
section

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. The gates below come
from `AGENTS.md` and the accepted records `wfctl arch context` prints. The
substitution is recorded under Complexity Tracking.

- [x] Validation plan exists: the three commands in `AGENTS.md`'s definition of
      done, `wfctl check config`, the tests named under Project Structure, the
      timing run for SC-003, and one `opening-a-change` run after
      `install-skills`.
- [x] Complexity is justified: the review check runs inside the existing guard
      process instead of a second hook, and each new module has one reader. See
      Complexity Tracking.
- [x] Ownership is stated:
      1. wfctl computes which commits each group has reviewed, whether a run is
         complete, and whether a report counts. The agent shouldn't, because it
         would be grading its own panel (`review-covers-unreviewed-commits`).
      2. wfctl decides whether a listed model can run, by looking its command up
         on `PATH` when a run starts, so the coordinator can't simply declare a
         reviewer unavailable. This is visible rather than enforced: the
         agent's shell sets `PATH`, and the roster and a `⚠` line name any
         model left out. A run where no reviewer can run never completes
         (`research.md` R7).
      3. A person owns the sign-off. The guard refuses the sign-off command when
         an agent runs it, and the command itself runs only at an interactive
         terminal and asks the person to type the head's sha (R9). An agent
         writing `sign-off.json` with a file tool is a recorded limit, the same
         as a forged report.
      4. git owns which commits exist and which came from the trunk branch. The
         unreviewed list is derived from git on every read.
      5. GitHub owns which branch a pull request number names. The review check
         asks `gh` and refuses when it can't answer.
      6. The person owns acting on another branch's pull request. A worktree
         opens and merges only its own branch's, and only the checkout on the
         trunk branch, where the person orchestrates, acts on another's
         (R4, Another branch). This is a convention rather than enforcement:
         the check keys on the branch name, so a worktree switched to the
         trunk branch passes. #627 covers that case.
      7. The person owns the way past a broken check. The review check refuses
         on any error and says that a person can run the command in their own
         terminal, where the hook doesn't run. A sign-off doesn't get past an
         error (R4, Timeouts and errors item 4).
      8. The host owns which directory the session is in, and names it in the
         hook payload's `cwd`. The review check reads the branch there and runs
         its `gh` and `git` calls there, as the worktree check does (R4, Where
         the check reads from).
- [x] `session-state-is-re-derived`: the last reviewed commit, the run records,
      and the sign-off are the only stored values, because no artifact records
      which commits a panel read. The unreviewed commits are never stored.
- [x] `wfctl-runs-the-verification`: completion is read from wfctl's own check
      of the report files, never from the coordinator's word.
- [x] `layer-model` and `vendor-upstream-skills`: `security-and-hardening` gets
      the attribution line as its last line and no other edit. The
      `/security-review` file is copied byte for byte, and its credit is a row
      in the record's file table plus a `NOTICES.md` entry naming it, which is
      how the Spec Kit templates are credited today. That makes it a second
      case where the notice stands in for the line, which changes the
      record's decision text. So the record is amended in place, as it has
      been eight times before: the "one case" sentence names both cases, a
      sentence gives this file's reason, and the Log gains a line (R10 items
      4 and 5). `tests/test_skill_attribution.py` tells the new row apart by
      its path and checks it against the notice (R10 item 6). The wfctl note
      that overrides the vendored `/security-review` git section lives in a
      wfctl-owned skill beside it.
- [x] `install-modes`: no new row in `MANAGED_HOOKS`. The review check runs
      inside `wfctl hook worktree-guard`, as its design record argues.
- [x] `knowledge-placement`: the `review` key gets an `AGENTS.md` section beside
      `change_check` and `steps`, since it is guidance for whoever configures a
      repository. `AGENTS.md`'s Safety section also changes. It says wfctl
      doesn't gate outward actions, and after this change the review check is
      the one refusal wfctl makes, so an agent meeting it should run the review
      groups rather than report a host refusal with `wfctl report-block`.
- [ ] `a-rule-is-expressed-as-a-check`: not met, and recorded under Complexity
      Tracking. The three-round cap is visible in an artifact, since run records
      are numbered, so it belongs in a check. It ships as a skill instruction
      until #626 decides how rounds are counted. Until then, an agent that
      ignores the instruction keeps running rounds, and nothing in wfctl stops
      it. The plan walkthrough deferred this to #626, and the issue carries it.
- [x] `change-carries-release-note`: `changes/622.addition.md`.

Re-checked after Phase 1: `data-model.md` and `contracts/cli.md` add no stored
value beyond the three named above, no hook row, and no dependency. Every gate
passes except the round cap, which is a recorded deviation.

## What the skill rewrites say

The skills carry the requirements no code checks, so each rewrite is listed
here with the requirements it traces.

1. `opening-a-change`:
   1. Run every group from `wfctl review groups`, in its order, with no
      condition that skips one (FR-001).
   2. Commit the security group's fixes before starting the code group
      (FR-003).
   3. Report every group's findings to the person in chat as one table, one row
      per finding, naming the reviewer id and model. Put no finding, table, or
      status line in the pull request description (FR-004).
   4. After three complete rounds, stop and ask the person for a sign-off
      (R11).
   5. Run `gh pr create` on its own, never chained after a commit, a push, or
      a `cd`, and with no command substitution in it, since the review check
      refuses both (R4, FR-012b). Step 5's bash block changes to match. Today
      it sets `BODY` with `$(git branch --show-current)`, runs
      `wfctl check-body`, and runs `gh pr create` in one block of three lines,
      which the check refuses every time. The rewrite shows `wfctl check-body`
      and `gh pr create` as two separate commands, each naming the body file
      by its full path with the branch name written out, such as
      `/tmp/pr-body-622-security-review-panel.md`. A shell variable set in one
      command doesn't reach the next, so the path is written out in each.
      Neither command carries an environment prefix, since the check refuses
      one (R4).
   6. When the review check refuses with an error, stop and tell the person,
      naming the error. Don't retry the command in another spelling. The
      refusal says a person can run it in their own terminal, and that is the
      person's call (FR-015). When it refuses another branch's pull request,
      leave that pull request to the checkout on the trunk branch (FR-012a).
2. `fanning-out-code-review`:
   1. Start the group with `wfctl review start <group>`, and launch one
      reviewer per printed id, giving each the commit range and the reports
      path (FR-026).
   2. Tell each reviewer to write a `Reviewed: <sha>` line and to end with its
      verdict (R2).
   3. Save a blocked reviewer's reply to a file and run
      `wfctl relay <id> --reason "…" --from <file>`. Run another model's
      command with its prompt and output in files, and relay the output file
      the same way. Never put a report in a command's text, since the guard
      matches command text and a security report quotes the commands it
      refuses (R8).
   4. Finish with `wfctl review check <group>`, and read the roster it prints
      rather than counting reports itself.
3. `reviewing-security` (R10 item 7, FR-025):
   1. Run both vendored reviews over the printed commit range, and skip the
      `/security-review` git section.
   2. Read the checklist at
      `security-and-hardening/references/security-checklist.md`.
   3. Write one report covering both reviews, with a `Reviewed: <sha>` line
      and a verdict at the end, to the path `wfctl review start` printed. This
      outranks the vendored file's last line, which asks for the report and
      nothing else, its "Do not use the bash tool or write to any files" line,
      and its sub-task steps when the reviewer can't launch sub-tasks (R2).

## Project Structure

### Documentation (this feature)

```text
622-security-review-panel/
├── plan.md              # This file
├── research.md          # Phase 0: decisions this plan settled
├── data-model.md        # Phase 1: files under <state dir>/reviews/
├── quickstart.md        # Phase 1: one group run, end to end
├── contracts/
│   ├── cli.md           # the review commands, relay, and the guard's refusals
│   └── config.md        # the `review` key in wfctl.json
└── tasks.md             # Phase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
wfctl/
├── _review_config.py    # new: reads `review` from wfctl.json → groups, problems
├── _review.py           # new: run records, reports, last reviewed commit,
│                        #      sign-off, commit ranges, roster
├── _review_gate.py      # new: the guard's review check; no typer or rich
├── _hook.py             # worktree_guard calls the review check first,
│                        #   passing the payload's `cwd`
├── _paths.py            # trunk_branch, _resolve_declared, _bare_head,
│                        #   is_bare_layout, resolve_branch,
│                        #   resolve_agent_dir, project_state_dir, and
│                        #   project_name take an optional timeout
├── cli.py               # `review` group (start, check, groups, sign-off),
│                        #   `relay`, and the `review` reader in check config
└── agents/skills/
    ├── security-and-hardening/              # new, vendored from addyosmani/agent-skills
    │   ├── SKILL.md                         # attribution line added as the last line
    │   └── references/
    │       ├── hardening-patterns.md        # vendored with the skill
    │       └── security-checklist.md        # vendored from upstream's top-level references/
    ├── reviewing-security/                  # new, wfctl-owned
    │   ├── SKILL.md                         # runs both security reviews over
    │   │                                    #   wfctl's commit range
    │   └── references/security-review.md    # vendored from
    │                                        #   anthropics/claude-code-security-review
    ├── NOTICES.md                           # new anthropics/claude-code-security-review
    │                                        #   section naming the file by path
    ├── fanning-out-code-review/SKILL.md     # drives a group through wfctl
    └── opening-a-change/SKILL.md            # runs every group, security first

docs/architecture/vendor-upstream-skills.md  # amended in place: a `security-and-hardening`
                                             #   row, a `/security-review` row in the
                                             #   file table, the "one case" sentence
                                             #   naming two, and a Log line (R10)
AGENTS.md                                    # "Declaring reviewers" section, and the
                                             #   Safety section naming the review check
changes/622.addition.md

tests/
├── test_review_config.py   # each check-config finding, including a bad group
│                           #   name and an empty `reviewers` on a built-in
│                           #   and a custom group; defaults, ordering
├── test_review.py          # range, report acceptance, completion, relay,
│                           #   sign-off, unavailable models, every reviewer
│                           #   unavailable, a head behind the last reviewed
│                           #   commit, no trunk, state-dir reset
├── test_review_gate.py     # guard payloads: reviewed, unreviewed, unreadable,
│                           #   every group, other branch, failed lookup, a
│                           #   lookup that times out, an error after a match,
│                           #   every pattern in R6 including `-R` before
│                           #   `pr` and before the verb, spaced, with `=`,
│                           #   and attached as `-R<repo>`; two `-R` values
│                           #   refused; `gh pr new`, and `enqueuePullRequest`;
│                           #   the argument spellings in R4, short flags,
│                           #   `--flag=value`, attached short values,
│                           #   grouped short flags (`-sd`, `-st fix`),
│                           #   `--help`, `--auto`; another repository by
│                           #   `-R`, `HOST/OWNER/REPO`, a
│                           #   `repos/<o>/<r>/` path, and a `--head` owner
│                           #   other than this checkout's; this checkout's
│                           #   own owner on `--head` judged; another
│                           #   branch's pull request refused from a feature
│                           #   worktree and judged from the trunk checkout;
│                           #   chained forms
│                           #   after a commit, push, `cd`, or second match;
│                           #   `$(`, a backtick, `<(`, and `>(` in the
│                           #   matched command refused; `GIT_DIR=`,
│                           #   `GIT_WORK_TREE=`, `GH_REPO=`, `NO_COLOR=1`,
│                           #   and `env -C` before the match refused; a
│                           #   substitution, quote, glob, or variable in
│                           #   `gh`'s command words refused on a reviewed
│                           #   branch; a verb's flag before the verb
│                           #   (`gh pr --squash=true merge`), two `-R`
│                           #   before `pr`, an `-R` value holding `$(`,
│                           #   and `gh --version` refused on a reviewed
│                           #   branch; `-R=<repo>` read without the `=`;
│                           #   one `-R` before `pr` and one after the verb
│                           #   counted as two; `GH pr merge`, `Gh pr create`,
│                           #   and `GH api …/pulls` with a body matched;
│                           #   a `-R` host other than `github.com` refused;
│                           #   `gh stack merge`, `gh co`, `gh copilot`, and
│                           #   `rg 'gh (pr|api)'` refused as words off the
│                           #   list of `gh`'s own commands; a `gh api`
│                           #   create with `-fhead=x`, `--field=head=x`,
│                           #   `-XPOST`, `/pulls/`, or `/pulls?x=1` refused;
│                           #   `rg 'gh pr'` and a message
│                           #   quoting `` `gh pr` `` not matched; a payload
│                           #   `cwd` in a different worktree from the
│                           #   hook's own directory judged by the `cwd`'s
│                           #   branch;
│                           #   a matched command with no `cwd` refused;
│                           #   a variable `gh api`
│                           #   path refused with a body or `-X PUT` and
│                           #   allowed as a read; a GraphQL query from a
│                           #   file refused; an error refusal naming the
│                           #   person's own terminal; an
│                           #   ancestor test answering "no" not refused; no
│                           #   state directory created for another branch;
│                           #   the `gh api` and GraphQL forms,
│                           #   `pulls/<n>/comments` not matched, sign-off
│                           #   spellings refused, `echo` refused; a relay
│                           #   whose report quotes `gh pr create` allowed;
│                           #   `WFCTL_STATE_DIR` set while another branch
│                           #   is judged refused; `WFCTL_BRANCH` naming a
│                           #   branch other than the `cwd`'s refused. Every
│                           #   other gate test clears `WFCTL_BRANCH` or sets
│                           #   it to the `cwd`'s branch, since fixtures in
│                           #   `tests/conftest.py` set it, and a test would
│                           #   otherwise refuse for the wrong reason
├── test_review_cli.py      # command output and exit codes, NO_COLOR pinned;
│                           #   sign-off without a terminal, and with a wrong
│                           #   sha typed
├── test_review_store.py    # runs a group, then `wfctl store specs`, and finds
│                           #   nothing under reviews/ in the commit (SC-004)
├── test_skill_attribution.py  # extended: a new `_NOTICED_ROWS` tuple that
│                           #   `_listed()` drops, `_TEMPLATE_ROW` unchanged;
│                           #   a row under
│                           #   `agents/skills/reviewing-security/references/`
│                           #   exists, carries no line, and is named in
│                           #   NOTICES.md; the new path-claim reader joins
│                           #   `_declaration_sources`
└── test_guard_entry.py     # extended: the review check imports no typer/rich
```

**Structure Decision**: one CLI project. The three modules split by reader.
`_review_config` is read by `check config`, `review start`, and the guard.
`_review` holds the records and is read by the commands and the guard.
`_review_gate` holds only what the guard needs, so the guard's import cost
stays at one small module on a matching command and nothing on any other.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| No constitution; gates drawn from `AGENTS.md` and accepted records | The repository records its constraints as architecture records | Borrowing another project's constitution would make the gates false |
| Two checks share one hook process | Each guard process costs about 27 ms of interpreter startup, on every shell command | A second hook row doubles that cost; `622-review-check-in-worktree-guard` |
| A `gh` subprocess inside the guard | The branch a pull request number names is GitHub's to say | Judging the current branch lets an unreviewed pull request merge from another worktree (clarify, 2026-10-22) |
| The three-round cap ships as a skill instruction, against `a-rule-is-expressed-as-a-check` | #626 decides how rounds are counted and whether the cap is configurable | Counting rounds here would decide #626's questions without its brainstorm (R11) |
