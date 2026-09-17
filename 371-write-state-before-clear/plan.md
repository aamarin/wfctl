# Implementation Plan: Session restart that writes its handoff first

**Branch**: `371-write-state-before-clear` | **Date**: 2026-09-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/371-write-state-before-clear/spec.md`

## Summary

A fourth managed Claude hook, `wfctl hook session-restart`, runs on every reply end
beside the reply-shape check. Under the threshold it reads one transcript and
returns. Over it, a pure decision over the branch's event log sends
`/end-session restart`, then — once a stop lands after that send — `/clear` and
`/start-session`, from a detached worker that records each send's exit. Holds,
skips and clears that did not take are reported once in the pane via
`systemMessage`. Supporting changes: the installer identifies a managed row by
event plus subcommand so Stop can carry two, `end-session` gains a `restart`
section and its wrapper starts passing arguments, and the threshold comes from
`WFCTL_RESTART_THRESHOLD`.

Design records this plan is written against (from `design.md`):

- `docs/architecture/wfctl-performs-the-session-restart.md` (level 2, proposed)
- `docs/architecture/a-managed-hook-is-owned-by-its-subcommand.md` (level 2, proposed)
- `docs/architecture/design/371-the-session-restart-sends-from-a-detached-worker.md`
- `docs/architecture/design/371-the-session-restart-instruction-lives-in-end-session.md`
- `docs/architecture/design/371-the-session-restart-threshold-is-an-environment-variable.md`

## Technical Context

**Language/Version**: Python 3.11+ (CI on 3.11 and 3.13)
**Primary Dependencies**: stdlib only on the new paths (`json`, `os`, `subprocess`, `sys`, `time`); `typer`/`rich` untouched and not imported on the hook's fast path. External runtime tool: `workmux` (already required by wfctl's worktree flow).
**Storage**: the branch's `events.jsonl` in the XDG state dir (two new event kinds); `.claude/settings.json` (one new managed row)
**Testing**: `uv run pytest -q`; stub `workmux` on `PATH` for the worker; `NO_COLOR` pinned where output is asserted
**Target Platform**: macOS and Linux developer machines running Claude Code in tmux via workmux
**Project Type**: CLI with packaged skills
**Performance Goals**: a reply end that decides nothing under 0.2 s wall time and zero model tokens (SC-004)
**Constraints**: hook exits 0 on every path; never blocks a stop; no state dir created on the nothing path; minimal-complexity bias
**Scale/Scope**: one pane per worktree; a restart a few times a day per pane

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

No `.specify/memory/constitution.md` exists in this repo. Gates below are
substituted from `AGENTS.md` and the accepted records in `wfctl arch context`;
the substitution is recorded under Complexity Tracking.

- [x] Validation plan exists: `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, `uv run mypy wfctl/`, `uv run wfctl doctor`, `uv run wfctl install-skills --agent claude` plus a hand exercise of `end-session restart` (AGENTS.md: a change under `wfctl/agents/` is not verified by the suite alone), and the live pane checks in `quickstart.md`.
- [x] Complexity is justified: one new module for the decision, one for the worker (research R6; level-3 record names the rejected single-shell alternative); the fast-path entry reuses `_entry.py`'s existing pattern (R8). No new dependency.
- [x] Ownership is stated: see `design.md` § Boundaries and Ownership and `data-model.md`; each new event kind is written by exactly one process (hook or worker) and read only by the hook.
- [x] `layer-model`: skill and wrapper edits land in `wfctl/agents/`, never in `.agents/` or `.claude/`.
- [x] `no-hardcoded-agent`: the new hook row is in the claude layer's `MANAGED_HOOKS`, installed only with `--agent claude`; no committed hook names an agent.
- [x] `install-modes`: the row is merge-mode and marked by `wfctl hook `; the subcommand-identity change is the proposed record, and `install-modes` gets a Log line only when that record is accepted (not by this change).
- [x] `a-rule-is-expressed-as-a-check`: the send text and the skill's restart section are tied by a test (FR-018); the single definition of 200000 is a test (FR-015).
- [x] `session-state-is-re-derived`: every restart state is derived from `events.jsonl` on each Stop; no marker files, no cached "restarting" flag.
- [x] `vendor-upstream-skills`: `end-session` is wfctl-authored, not spec-kit-derived, so an in-place section is permitted.
- [x] Code style: ruff rule set unchanged; new functions annotated; comments explain why this shape.
- [x] Releasing: `pyproject.toml` version not bumped.

Post-design re-check: all gates still hold; Phase 1 added no module beyond the two above.

## Project Structure

### Documentation (this feature)

```text
specs/371-write-state-before-clear/
├── design.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── hook-session-restart.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
wfctl/
├── _restart.py            # NEW: threshold, occupancy reader, event parsing, decide(), messages
├── _restart_send.py       # NEW: detached worker (python -m); waits, sends, records
├── _entry.py              # fast path for ["hook", "session-restart"]
├── _paths.py              # resolve_agent_dir(create=False) for the hook
├── _settings.py           # subcommand-aware merge_hook and managed_command; prune_unshipped
├── cli.py                 # MANAGED_HOOKS as (event, command) pairs; _HOOK_GONE per subcommand;
│                          # _merge_hooks + doctor per subcommand; hook_app registers session-restart
└── agents/
    ├── commands/end-session.md          # $ARGUMENTS block
    └── skills/end-session/SKILL.md      # "When invoked with restart" section

tests/
├── test_restart_decide.py         # NEW: every rule in data-model.md, threshold parsing, messages
├── test_restart_occupancy.py      # NEW: last usage record, unreadable cases
├── test_restart_send.py           # NEW: worker waits for parent, records exits, timeout → -1
├── test_restart_hook_cli.py       # NEW: stdin/stdout contract, exit 0 on error, no state dir created, fast path
├── test_restart_end_session.py    # NEW: send text == "/end-session restart"; skill section names --continued; 200000 once
├── test_settings_merge.py         # subcommand identity, prune_unshipped
└── test_install_hook_merge.py     # two Stop rows survive reinstall; doctor per subcommand; upgrade from one-row Stop
```

**Structure Decision**: Single-package CLI, matching the repo. The decision lives
in its own module rather than in `cli.py` so the fast path can import it without
the CLI (R8) and so it is testable as a function (level-3 record). The worker is a
separate module because it runs as its own process with its own argv (R6).

## Implementation order

1. `_settings.py` + `cli.py` installer identity (FR-019–FR-022). Independently shippable; opens Stop's second slot before anything fills it. Existing hook tests stay green.
2. `_restart.py`: decision, occupancy and threshold, pure and unit-tested (FR-002–FR-004, FR-008–FR-015).
3. `_restart_send.py` worker with stub-`workmux` tests (FR-005, FR-006, FR-012).
4. Hook wiring: `_entry.py` fast path, `hook_app` registration, `resolve_agent_dir(create=False)`, `MANAGED_HOOKS` entry (FR-001, FR-007, FR-011).
5. `end-session` wrapper and skill section, plus the tie test (FR-016–FR-018).
6. `install-skills --agent claude`, doctor, hand exercise of `/end-session restart`, then the live checks in `quickstart.md`.

## Risks

- **Classifier refusal while authoring the send code** (ledger entry 17). If the permission layer refuses writing `_restart_send.py` or the spawn in `_restart.py`, stop and report it with `wfctl blocked`; the person writes those lines. Do not route around it.
- **Live assumptions** (spec § Assumptions): a detached send lands on Claude; trailing text reaches the skill. Both fail loudly — state F reports the first; a non-continued `end` shows the second. The `systemMessage` assumption is settled by research R4.
- **Upgrade path**: a repo installed by an older wfctl has one Stop row. Step 1's test covers the next install adding the second row without collapsing the first.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from `AGENTS.md` and accepted records | This repo has no `.specify/memory/constitution.md` | The template's three generic gates alone check nothing repo-specific; writing a constitution is out of scope |
| Second process (`_restart_send`) | Sends must start after the hook exits and record their exit (R6) | A detached `sh -c` cannot record exits; a synchronous send is refused by the pane (entry 16) |
| Fast-path argv in `_entry.py` | Runs on every Stop | A plain typer command costs ~75 ms per reply end for nothing (R8); the pattern already exists for the guard |
