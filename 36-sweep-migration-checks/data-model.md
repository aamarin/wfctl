# Phase 1 Data Model: Sweep the one-time migration checks

This feature introduces no persistent state and changes no stored format. The
entities below are the filesystem and in-memory structures it reads, and the
rules it applies to them.

## Superseded artifact directory

The per-branch location that held design artifacts before they moved into the
branch's spec directory.

| Property | Value |
|---|---|
| Location | `<worktree>/.agent/` |
| Created by | Nothing, as of the vendoring change (#43/#47) |
| Read by | The rescue plan in `_archive.py`, during teardown only |
| Written by | Never |

**Rules**

- Every regular non-symlink file beneath it is rescued, recursively — not
  `spec.md` alone. Reading one filename out of a directory about to be deleted
  rescues that file and destroys its neighbours.
- `spec.md` maps to `extra/legacy-agent-spec.md`; every other file maps to
  `extra/legacy-agent/<relative path>`.
- Nothing infers pipeline state from it. The read copies bytes out of a directory
  about to be deleted; step inference reads the current location only.
- An absent directory and an empty one are equivalent: no files rescued, no
  report emitted.

**Lifecycle**: exists on worktrees predating the move → contents rescued at
teardown → destroyed with the worktree. The population only shrinks.

## Archive plan entry

The in-memory pairing produced while planning an archive, and the source of the
rescue count.

| Property | Value |
|---|---|
| Shape | `tuple[str, str]` — `(destination_name, source_description)` |
| Container | `mapped: list[tuple[str, str]]`, returned by `_archive.archive` |
| Ordering | Pipeline order; deliberately not sorted |

**Rules**

- An entry is a legacy rescue when its destination begins with
  `extra/legacy-agent`. This covers both the `spec.md` special case and the
  nested form.
- The count reported to the user is the number of such entries, derived at the
  call site. `_archive.py` returns data and prints nothing.

## Teardown hook

The repository-local configuration entry invoked before a worktree is removed.

| Property | Value |
|---|---|
| Location | `<repo>/.workmux.yaml`, key `pre_remove` |
| States | absent · present and archiving · present and not archiving · unreadable |
| Command named | current (`archive-specs`) or retired (`archive-story`) |

**Rules**

- Absent file: not every repository uses the worktree tool. No report.
- Unreadable file: reported once, by the surviving hook check. No second report.
- Present and not archiving: reported, with an offer to wire it. This is ongoing
  drift, not a transition, and is out of scope for removal.
- Naming the retired command still counts as wired — such a repository is
  protected, and is told so by the archive command itself rather than by the
  health check.

## Bundled hook template

The teardown-hook configuration shipped inside the package and copied into
repositories on seeding.

| Property | Value |
|---|---|
| Location | `wfctl/agents/configs/workmux/.workmux.yaml` |
| Consumed by | The seeding command, and the wheel/installed-tree CI checks |
| Distribution | Ships in the wheel; reaches machines by tool upgrade, not by clone |

**Rules**

- The command name appears twice — once in the executable hook line, once in the
  explanatory comment above it. Both must name the current command; a corrected
  hook beside a comment naming the retired command is a contradiction the reader
  has to resolve.
- Seeding refuses to overwrite an existing file, so correcting the template
  reaches newly seeded repositories only. Already-seeded repositories are covered
  by the retained alias and its report.

## Removal-condition signal

Not stored anywhere. This is the observable that replaces the unobservable
comments issue #36 was filed about.

| Property | Value |
|---|---|
| Emitted by | The archive command, during teardown |
| Two forms | legacy rescue performed · invoked under the retired name |
| Emitted when | Only on a machine that predates the corresponding move |
| Recorded | Never — no flag, no state file, no counter |

**Rules**

- Silence is the meaningful state: a teardown that prints neither line is
  evidence that machine is swept.
- The two forms are independent. A single teardown may emit both, and neither
  suppresses the other.
- Neither affects the exit code, and neither can prevent archiving from
  completing. A teardown must never be aborted by a message about a shim.
