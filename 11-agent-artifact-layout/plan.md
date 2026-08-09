# Implementation Plan: Agent Artifact Layout

**Branch**: `11-agent-artifact-layout` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/11-agent-artifact-layout/spec.md`

## Summary

Move every per-branch agent artifact into `specs/<branch>/`, delete the `.agent/`
directory, and give project overrides a committed home at `AGENTS.md`. The change
is almost entirely text: 21 path references across 6 skill and command files, and
4 source plus 4 test references in the tooling.

Three things make it more than a rename:

1. **A double writer is removed.** `speckit-plan` step 3 overwrote the agent
   brief with a plan summary. It is deleted rather than repointed — `plan.md`
   already holds that content.
2. **A file is renamed.** `checkpoint.md` becomes `escalation.md`, because the
   tooling already has a `checkpoint` subcommand meaning something unrelated
   (research R3). Consolidating both meanings into one directory would trade this
   feature's fix for a new confusion.
3. **A latent inference defect is repaired.** Step inference short-circuits when
   the spec directory is absent, making the old design-document check unreachable
   during the only phase it served (`_pipeline.py:55-56`).

## Technical Context

**Language/Version**: Markdown skill and command text (skills repository);
Python 3.11+ (tooling repository)
**Primary Dependencies**: None added. Tooling changes stay within `pathlib` and
`shutil`, both already in use
**Storage**: Filesystem only — worktree `specs/<branch>/`, plus the XDG state
directory for archives
**Testing**: `pytest` for the tooling; `git grep` assertions for the text
changes, since a path reference has no runtime to exercise
**Target Platform**: Developer workstations, macOS and Linux, CLI
**Project Type**: Two co-dependent repositories — a markdown skills distribution
and a Python CLI. Neither half delivers the outcome alone
**Performance Goals**: None. No hot path is touched
**Constraints**: Consumer-side (tooling) must land before producer-side (skills);
no dual-path reads; no new dependency
**Scale/Scope**: 21 references across 6 files, plus 4 handoff-destination
references in 2 more (skills); 4 source and 4 test references (tooling)

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

**No constitution file exists.** `.specify/memory/constitution.md` is not present
and the installer does not provision it, so the gates below are derived from this
repository's own recorded decisions rather than read from a constitution. The
substitution is logged in Complexity Tracking.

- [x] **No new dependency.** Nothing is added to either repository's dependency
      set.
- [x] **No new mechanism where an existing one suffices.** The archive already
      preserves artifacts past teardown; the health check already reports both
      skew directions. Neither is reinvented.
- [x] **Delete before adding.** The change removes a double writer, a dead
      special case, and a directory. It adds one diagnostic and one renamed file.
- [x] **Every claim cites a file and line.** Verified through the spec, research,
      and this plan.
- [x] **Ordering is explicit, not implied.** Tooling lands first; the tasks carry
      it as a dependency rather than a note.
- [x] **Verification is executable.** Each success criterion maps to a `git grep`
      or `pytest` invocation in quickstart.md, not to a manual read.
- [x] **Scope holds.** Four adjacent efforts are named and excluded in the spec's
      Assumptions; none is pulled in.

**Post-design re-evaluation**: unchanged. Phase 1 added one rename
(`checkpoint.md` → `escalation.md`) inside the file set already being moved, and
shrank the health-check requirement from a version-negotiation mechanism to a
directory-presence test. Both moved in the direction of less.

## Project Structure

### Documentation (this feature)

```text
specs/11-agent-artifact-layout/
├── design.md            # Phase -1 output — currently at .agent/spec.md, moves with this change
├── spec.md              # /speckit.specify output
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/
│   └── cli.md           # Phase 1 output — path + CLI contract
├── quickstart.md        # Phase 1 output
├── tasks.md             # /speckit.tasks output — NOT created by /speckit.plan
└── checklists/
    └── requirements.md  # /speckit.specify output
```

### Source (two repositories)

```text
wf-skills/                                   # producer side — lands second
├── .agents/
│   ├── commands/
│   │   ├── brainstorm.md                    # 5 refs; also collapses two writes into one
│   │   └── speckit.brief.md                 # 1 ref (description)
│   └── skills/
│       ├── speckit-specify/SKILL.md         # 9 refs — largest single surface
│       ├── agent-brief/SKILL.md             # 3 refs + the checkpoint→escalation rename
│       ├── speckit-delivery-plan/SKILL.md   # 2 refs (diagram + prose)
│       ├── speckit-plan/SKILL.md            # 1 ref — step 3 DELETED, not repointed
│       ├── brainstorming/SKILL.md           # destination + drop "commit it"
│       └── idea-refine/SKILL.md             # destination
└── AGENTS.md                                # NEW — committed project overrides

wfctl/                                       # consumer side — lands FIRST
├── wfctl/
│   ├── _archive.py                          # _DESIGN_DOC → _SPEC_MAP entry; _plan() special case removed
│   ├── _pipeline.py                         # :75 reads the new path
│   └── cli.py                               # doctor: .agent/ presence diagnostic; docstring
└── tests/
    ├── conftest.py                          # 2 fixture refs
    ├── test_archive_story.py                # 1 ref
    └── test_start_atomic.py                 # 1 ref
```

**Structure decision**: no new modules, no new files in either source tree except
`AGENTS.md`. The change is concentrated in path constants and instruction text,
which is why the verification strategy leans on search rather than new tests —
the one genuinely new behaviour (the doctor diagnostic) gets a test.

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --------- | ---------- | ------------------------------------ |
| Constitution gates derived rather than read | `.specify/memory/constitution.md` does not exist and the installer does not provision it, so the template's mandatory gate section has no source | Leaving the section unchecked makes it decorative; filling it with another project's gates would make it false. Deriving from this repo's recorded decisions is the only option that is both complete and true. Tracked as the missing-constitution row on wf-skills#10 |
| A rename inside a move (`checkpoint.md` → `escalation.md`) | The tooling's existing `checkpoint` subcommand claims the word for an unrelated concept; the move would place both meanings in one directory | Keeping the name is free but produces a worse end state than the split this feature removes. Renaming the CLI verb instead has a far larger blast radius — it is public surface with an event type and user habit behind it |

## Template deviations

The shipped `plan-template.md` was used for structure only. Its Technical Context
ships pre-filled with another project's stack (TypeScript, Vue, Express,
ZenStack, Prisma, PostgreSQL, pnpm) and its Constitution Check gates are that
project's (`workspaceId` boundaries, `.zmodel` tier placement, `pnpm type-check`).
Neither has a referent in a Python CLI and a markdown skills repository, so both
were replaced with content true of this feature.

This is the same class of contamination recorded on wf-skills#3 and scheduled as
wf-skills#10 PR 5. Noted here so the deviation is visible rather than silently
absorbed.
