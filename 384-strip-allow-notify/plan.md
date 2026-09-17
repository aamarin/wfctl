# Implementation Plan: Strip allow-notify

**Branch**: `384-strip-allow-notify` | **Date**: 2026-09-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/384-strip-allow-notify/spec.md`

## Summary

This removes wfctl's own permission check on tracker writes, and keeps the part
of it that records what happened. The grant lives in four places: the
`--allow-notify` flag and label read in `wfctl start`, the refusal inside
`wfctl issue`, the "outward actions authorized" fact in `wfctl status`, and the
prose in five skills and three docs. All four go in one change, because
`pipeline-state-is-one-payload` doesn't allow the JSON and its views to
disagree.

The two recording verbs are renamed and made simpler. `report-action` is
`notify` with the grant check and `--declined` removed, and it now reports the
hold it lifted. `report-block` is `blocked` with `--clear` removed. What they
write to the event log stays exactly the same. The one behaviour change
underneath is in `wfctl issue`. It records `issue-<verb>` instead of the bare
verb, and it records `close`, so a successful retry lifts the hold its own
failure put in place.

Nothing new is stored. This change deletes code and renames things. It adds no
module, no event type, and no dependency.

## Technical Context

**Language/Version**: Python 3.11+ (CI runs 3.11 and 3.13)
**Primary Dependencies**: typer, rich. Nothing is added.
**Storage**: the per-branch `events.jsonl` in the XDG state dir. Its event names don't change. `notify.json` (the local grant file) is no longer read or written.
**Testing**: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, then `uv run wfctl install-skills --agent claude` and `uv run wfctl doctor`
**Target Platform**: macOS and Linux developer machines, anywhere the CLI runs
**Project Type**: CLI, with the skills it ships as package data
**Performance Goals**: `wfctl start` makes no tracker call. Today it makes one per session, to read labels.
**Constraints**: event names stay the same so old logs keep reading. No aliases. Stay biased towards the least complexity.
**Scale/Scope**: 8 modules, 6 skill or command files, 3 docs, about 26 test files, and log lines on 6 records

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

There is no `.specify/memory/constitution.md` in this repo. The gates below come
from `AGENTS.md` and the accepted records in `wfctl arch context`. The
substitution is noted under Complexity Tracking.

- [x] Validation plan exists: the three `uv run` commands, `doctor` after
      `install-skills`, the SC-003 search, and the new tests listed in
      `quickstart.md`.
- [x] Complexity is justified: nothing is added. The only new surface is two
      command names, and they replace two that are removed.
- [x] Ownership is stated: this feature adds no state or derived value. It
      takes one away (the grant). The two values that stay have the owners
      level 2 gave them. The host decides whether a command may run. wfctl
      records what ran and what was refused, because it's the only one of the
      two that writes somewhere the next session reads.
- [x] `pipeline-state-is-one-payload`: `notify`, `notify_source` and the fourth
      fact are removed from `PipelineReport`. No view drops them on its own.
      The JSON, the plain status and the facts block all change in one commit.
- [x] `a-rule-is-expressed-as-a-check`: "no skill calls a removed verb" can be
      seen in the installed tree, so it gets a check. The existing
      `test_skill_cross_references` is extended to fail on `wfctl notify` or
      `wfctl blocked` anywhere under `wfctl/agents/`.
- [x] `vendor-upstream-skills`: none of the files touched are copied from
      spec-kit. `speckit-delivery-plan`, `end-session` and `scaffold-tracker`
      are wfctl's own skills. `speckit.analyze.md`, `speckit.decompose.md`,
      `speckit.implement.md` and `end-session.md` are wfctl's command wrappers.
- [x] `session-state-is-re-derived`: holds are still worked out from the log
      every time it's read. Nothing gets cached.
- [x] `wfctl-runs-the-verification`: unchanged. The definition of done is
      still `wfctl verify` plus the three commands.
- [x] Records land `proposed`. The agent accepts none of them.

## Project Structure

### Documentation (this feature)

```text
specs/384-strip-allow-notify/
├── design.md
├── spec.md
├── plan.md              # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md           # the two new verbs, and what is removed
│   └── status-payload.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
wfctl/
├── cli.py            # remove notify_cmd, blocked_cmd, --allow/--deny-notify,
│                     #   _GRANT_LINES/_notify_line, notify keys in status;
│                     #   add report_action_cmd, report_block_cmd;
│                     #   reword _HOST_AUTHORITY_NOTICE
├── _session.py       # remove the grant (NotifyGrant, notify_grant, action_grant,
│                     #   grant_notify, record_notify_resolved, resolved_notify,
│                     #   _read_notify_file, NOTIFY_NAME, NOTIFY_LABEL,
│                     #   record_notify_declined, record_notify_refused,
│                     #   record_block_cleared); keep record_notify_action,
│                     #   record_blocked, standing_blocks (still reads block-cleared)
├── _tracker.py       # remove _refuse_notifying and read_issue_labels;
│                     #   _NOTIFYING_VERBS → _RECORDED_VERBS incl. close;
│                     #   record "issue-<verb>"
├── _pipeline.py      # remove notify/notify_source fields, _corrected_grant;
│                     #   _block_remedy names `report-action`
├── _predicates.py    # remove fact_outward_actions_authorized, _GRANT_DETAIL,
│                     #   _UNREADABLE_GRANT; facts() returns three;
│                     #   update the two comments that name the grant
├── _paths.py         # remove on_trunk
├── _restart.py       # _LATE_EVENTS = ("notify-action",)
└── _stall.py         # comment only

wfctl/agents/
├── skills/end-session/SKILL.md           # step 5 rewritten; step 7 report-block
├── skills/speckit-delivery-plan/SKILL.md # step 6 rewritten; report-block
├── skills/scaffold-tracker/SKILL.md      # labels verb prose
├── commands/end-session.md               # allowed-tools
├── commands/speckit.analyze.md           # Filing section, allowed-tools
├── commands/speckit.decompose.md         # allowed-tools
└── commands/speckit.implement.md         # report-block, allowed-tools

README.md, docs/reference.md, AGENTS.md (§ Safety)

docs/architecture/                        # log lines only, see research R6

tests/
├── deleted: test_notify_{dispatch,flag,declined,grant,status}.py
├── renamed/rewritten: test_blocked_{cli,holds_step,events}.py → test_report_{block,action}*.py
├── new: test_report_verbs.py, test_tracker_records_issue_verbs.py
└── edited: test_tracker, test_four_facts (→ three), test_restart_hook_cli,
    test_pipeline_payload_snapshot, test_skill_cross_references, and the
    single-mention files listed in research R7
```

**Structure Decision**: this is one project and the layout doesn't change. No
file or module is added under `wfctl/`. Only test files are added or renamed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Gates come from `AGENTS.md` and the accepted records, not a constitution | This repo has no `.specify/memory/constitution.md` | Leaving the check empty would make it a gate with no source behind it. Borrowing another project's constitution would state gates this repo never agreed to. |
