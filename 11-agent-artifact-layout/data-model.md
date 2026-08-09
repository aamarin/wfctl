# Data Model: Agent Artifact Layout

**Branch**: `11-agent-artifact-layout` | **Date**: 2026-08-05

The "data" here is files and their locations. Each entity below is a file with a
producer, a consumer, a lifetime, and a place in the archive sequence.

## Entities

### Design document

| | |
| --- | --- |
| Was | `.agent/spec.md` |
| Now | `specs/<branch>/design.md` |
| Producer | `/brainstorm` (sole writer, after this change) |
| Consumers | `speckit-specify` pre-specify gate; `_pipeline.py` step inference; `_archive.py` |
| Lifetime | Created at brainstorm, read through specify, archived at teardown |
| Archive name | `1-design.md` |
| Committed | No — `specs/` is gitignored |

**Validation**: non-empty file. `_file_exists` treats a zero-byte file as absent
(`_pipeline.py:38`), so an empty design document reads as "brainstorm not done".

### Agent brief

| | |
| --- | --- |
| Was | `.agent/brief.md` |
| Now | `specs/<branch>/brief.md` |
| Producer | `agent-brief` / `/speckit.brief` — **sole writer after this change** |
| Consumers | The scoped agent, at session start |
| Lifetime | Written once per task, never modified during a session |
| Archive name | `extra/brief.md` (catch-all; not in the numbered sequence) |
| Committed | No |

**State transition removed**: `speckit-plan` previously overwrote this file with
a plan summary mid-session, violating the brief's own "never modify during a
session" rule. That write is deleted, not repointed.

### Escalation record

| | |
| --- | --- |
| Was | `.agent/checkpoint.md` |
| Now | `specs/<branch>/escalation.md` — **renamed**, see research R3 |
| Producer | The scoped agent, on hard stop |
| Consumers | A human |
| Lifetime | Written at most once, terminal — the agent stops after writing it |
| Archive name | `extra/escalation.md` |
| Committed | No |

**Renamed** because `wfctl checkpoint` already claims the word for an unrelated
numbered git-diff snapshot in the session state dir.

### Project overrides

| | |
| --- | --- |
| Was | `.agent/AGENT.md` — uncommittable, so effectively nonexistent |
| Now | `AGENTS.md` at repository root |
| Producer | A repository maintainer, by hand. **Never the installer** |
| Consumers | `/brainstorm`; later, an agent-context mechanism owning a fenced region |
| Lifetime | Lives with the repository, outliving every branch |
| Archive | Not archived — it is committed, so git is its history |
| Committed | **Yes** — this is the entity's defining property |

**Validation**: absence is legal and silent (FR-005). Any future writer must
preserve all pre-existing content (FR-006).

**Distinguishing property**: the only entity here whose lifetime is the
repository's rather than the branch's. That is why it lives at the root and not
in `specs/<branch>/`.

### Branch archive

| | |
| --- | --- |
| Location | `<state-dir>/archive/` |
| Producer | `wfctl archive-story`, via the teardown hook |
| Lifetime | Outlives the worktree |
| Committed | No — outside the repository entirely |

Contains the numbered pipeline sequence plus an `extra/` catch-all for files the
map does not name, and a generated `README.md` index.

## Relationships

```
AGENTS.md  (repo root, committed, repo-lifetime)
    │ read by
    ▼
/brainstorm ──writes──> specs/<branch>/design.md
                              │ read by
                              ├──> speckit-specify  (pre-specify gate)
                              ├──> _pipeline.py     (step inference)
                              └──> _archive.py      (1-design.md)

/speckit.brief ──writes──> specs/<branch>/brief.md ──read by──> scoped agent
                                                         │
                                                    on hard stop
                                                         ▼
                                        specs/<branch>/escalation.md ──> human

specs/<branch>/*  ──teardown──>  <state-dir>/archive/
```

## Archive sequence

`_SPEC_MAP` is the numbering — a plain ordered list, iterated rather than sorted,
because lexicographic sort puts `10-delivery.md` before `2-spec.md`.

| # | Source (spec-dir relative) | Archived as |
| --- | --- | --- |
| 1 | `design.md` | `1-design.md` |
| 2 | `spec.md` | `2-spec.md` |
| 3 | `checklists/requirements.md` | `3-requirements-checklist.md` |
| 4 | `plan.md` | `4-plan.md` |
| 5 | `research.md` | `5-research.md` |
| 6 | `data-model.md` | `6-data-model.md` |
| 7 | `contracts/cli.md` | `7-contract-cli.md` |
| 8 | `quickstart.md` | `8-quickstart.md` |
| 9 | `tasks.md` | `9-tasks.md` |
| 10 | `delivery.md` | `10-delivery.md` |
| 11 | `checklists/analysis-report.md` | `11-analysis-report.md` |

**Change**: row 1 moves from a hardcoded worktree-relative constant
(`_DESIGN_DOC`) into this list as an ordinary spec-dir-relative entry. `_plan()`
loses the branch that handled it separately.

**`brief.md` and `escalation.md` stay unmapped** and land under `extra/`. They
are session state, not pipeline stages — giving them numbers would imply a
sequence position they do not occupy, and the catch-all already preserves them.
