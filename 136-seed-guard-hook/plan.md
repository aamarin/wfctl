# Implementation Plan: seed-guard-hook

**Branch**: `136-seed-guard-hook` | **Date**: 2026-09-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/136-seed-guard-hook/spec.md`

## Summary

`install-skills --agent claude` seeds the cross-worktree guard into a
consumer-owned `.claude/settings.json`: a `PreToolUse` hook scoped to `Bash`, and
`permissions.deny: ["Bash(cd:*)"]` as its blunt companion. The hook follows the
merge mode already exercised by two managed events. The deny rule cannot carry
wfctl's marker, so the manifest records whether wfctl added it, and an install
that finds that rule drifted refuses rather than papering over the edit.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `typer`, `rich` — no new dependency; this feature adds none
**Storage**: `.wf-skills-manifest.json` (wfctl's record) and the consumer's `.claude/settings.json` (theirs)
**Testing**: `uv run pytest -q`; new cases in `tests/test_settings_merge.py` (pure merge) and the install/uninstall/doctor suites (I/O and console output)
**Target Platform**: developer machines, macOS and Linux; CI on 3.11 and 3.13
**Project Type**: CLI
**Performance Goals**: none introduced. The guard's own cost was settled by #135 — 33.8 ms/call against a 27.1 ms Python-startup floor
**Constraints**: `_settings.py` stays pure — no `wfctl.*` imports, no I/O (its module docstring); ruff limited to `E4`,`E7`,`E9`,`F`; mypy with `disallow_untyped_defs`
**Scale/Scope**: one settings file, one new hook event, one permission rule

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repo has no `.specify/memory/constitution.md`. Gates below are substituted
from its accepted architecture records and `AGENTS.md`; the substitution is
recorded in Complexity Tracking as the template requires.

- [x] **Validation plan exists** — `uv run pytest -q`, `uv run ruff check wfctl/ tests/`,
      `uv run mypy wfctl/`, `uv run wfctl doctor`, plus the by-hand round trip in
      `quickstart.md` that the suite cannot cover.
- [x] **Complexity is justified** — no new dependency, no new module. One new
      manifest key and two new pure functions; the baseline each beat is recorded
      in `docs/architecture/design/136-the-receipt-is-a-sibling-of-merged.md`.
- [x] **Ownership is stated** — the manifest owns *"did wfctl add this entry?"*;
      the settings file cannot answer it because the rule is matched by exact
      string and so cannot carry a marker. Recorded at
      `docs/architecture/the-manifest-owns-what-carries-no-marker.md`.
- [x] **`the-underscore-is-the-module-contract`** — new pure logic lands in
      `_settings.py` beside `merge_hook`; `cli.py` keeps the I/O.
- [x] **`no-hardcoded-agent`** — nothing here names an agent in committed config.
      `PreToolUse` is Claude Code's schema and installs only in that layer.
- [x] **`a-rule-is-expressed-as-a-check`** — the refusal, the warning tier and the
      declined-removal report are each visible in console output the suite asserts on.
- [x] **`install-modes`** — this is the merge mode's second consumer, which is what
      that record routed #85 to serve.

## Project Structure

### Documentation (this feature)

```text
specs/136-seed-guard-hook/
├── design.md            # the three design levels, written before specify
├── spec.md              # 20 requirements, 4 clarifications
├── plan.md              # this file
├── research.md          # Phase 0 — what was verified in the code
├── data-model.md        # Phase 1 — the manifest and settings shapes
├── quickstart.md        # Phase 1 — the by-hand round trip
└── contracts/
    └── manifest-permissions.md
```

### Source Code (repository root)

```text
wfctl/
├── _settings.py      # merge_hook gains a matcher; merge_permission,
│                     # remove_permission, permission_present added
└── cli.py            # PreToolUse constants, MANAGED_HOOKS, _HOOK_GONE,
                      # _merge_permissions, _unmerge_permissions,
                      # _check_managed_permissions, the refusal, --force

tests/
├── test_settings_merge.py    # pure: matcher correction, permission merge/remove
├── test_install_skills.py    # records, refusal, --force, console output
├── test_uninstall_skills.py  # declined removal and its report
└── test_doctor.py            # the warning tier, exit code unchanged

README.md             # the guard section stops telling people to hand-wire it
```

**Structure Decision**: no new files. Pure decision logic joins `_settings.py`,
which already holds the merge mode's pure half; everything touching disk or the
console stays in `cli.py`, which already holds the other half.

## Phase 0 — research

See `research.md`. No `NEEDS CLARIFICATION` survived specify: the one genuinely
open question was answered at the level-2 gate before the spec was written.
Phase 0 here is the record of what was read in the code rather than assumed.

## Phase 1 — design artifacts

`data-model.md` fixes the two shapes this touches — the manifest's new
`permissions` list and the settings entries it describes. `contracts/manifest-permissions.md`
states the record contract that install writes and uninstall reads.
`quickstart.md` is the by-hand round trip.

## Implementation order

1. **`_settings.py` — the matcher.** `merge_hook` gains an optional `matcher`.
   Its in-place branch tracks `(group, hook)` pairs rather than flattening to
   hooks, so a replaced entry can have its group's matcher corrected; a new group
   carries the matcher when one is given. `None` leaves every group untouched,
   which is exactly today's behaviour for the two matcher-less events.
2. **`_settings.py` — the permission.** `merge_permission(settings, rule)` returns
   whether it added the rule; `remove_permission(settings, rule)` returns whether
   it removed one; `permission_present(settings, rule)` answers the drift check.
   All three prune upward the way `remove_hooks` does, so a `permissions` key
   wfctl created does not survive as an empty scaffold.
3. **`cli.py` — the constants.** `_PRETOOL_EVENT`, `GUARD_HOOK_COMMAND` built from
   `MANAGED_PREFIX` and the existing `_WORKTREE_GUARD` name, a `_HOOK_MATCHER` map
   holding only `PreToolUse → "Bash"`, the new `MANAGED_HOOKS` entry and its
   `_HOOK_GONE` line, and `DENY_RULE = "Bash(cd:*)"`.
4. **`cli.py` — the refusal.** Before any file is copied, and after the prior
   manifest is read: if a receipt for the rule exists — `added` either way — and
   the file does not carry it exactly, print the refusal naming both ways forward
   and exit 1. `--force` skips the check, re-asserts the rule and records
   `added: true`. A file that will not parse cannot establish drift, so it falls
   to the existing warn-and-continue arm instead of refusing.
5. **`cli.py` — install and uninstall.** `_merge_permissions` mirrors
   `_merge_hooks`' shape, carrying the prior receipt forward rather than
   re-deriving it. `_unmerge_permissions` removes only on `added: true` plus an
   exact text match, and reports what it declined.
6. **`cli.py` — doctor.** `_check_managed_permissions` prints a `⚠` line and
   returns nothing the exit code reads, unlike `_check_managed_hooks`.
7. **README.** The guard section stops instructing people to hand-wire it.
8. **Tests**, then the by-hand round trip.

Steps 1 and 2 are independent of 3–7 and land first because they are the only
part with no I/O to stand up. Step 4 is the one with a placement constraint
worth naming: `_merge_hooks` runs *after* the skill copies, so a refusal raised
there would leave a half-installed tree behind.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from `AGENTS.md` and the accepted records | This repo ships no `.specify/memory/constitution.md`, and the template requires the substitution be recorded rather than silently performed | Borrowing another project's constitution would make the gates false; leaving them blank would make them decorative |
| A second manifest key (`permissions`) beside `merged` | `merged` is read as hooks by three call sites, each reaching for `record["event"]` without a guard | Discriminating inside `merged` was the direct baseline; rejected in `docs/architecture/design/136-the-receipt-is-a-sibling-of-merged.md` |
| A refusal path in `install-skills`, which has never refused before | An unmarked entry the consumer may have authored cannot be silently re-asserted, and the choice belongs at session start where a person is present | Silently re-adding makes removal theatre; silently skipping hides a decision. Both were considered during clarify |
