# Implementation Plan: gitignore glob dedup

**Branch**: `11-gitignore-glob-dedup` | **Date**: 2026-08-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/11-gitignore-glob-dedup/spec.md`

## Summary

Replace the literal-string dedup guard in `_ensure_gitignored` with git's own
ignore evaluation, so an entry already covered by a broader pattern is not
appended. The function gains a boolean return so callers can count what was
skipped and report it once (FR-011/FR-012).

Measured effect in this repository: **84 entries considered, 83 already covered,
1 written** (`.wf-skills-backup/`). Today's guard appends 83 of those 84 — it
catches only the install record, the one path present as a literal.

## Technical Context

**Language/Version**: Python ≥3.11 (`pyproject.toml`), single package `wfctl/`
**Primary Dependencies**: `typer` (CLI), `rich` (console output). No new
dependency — the change shells out to `git`, which `install-skills` already
requires for its clone.
**Storage**: None. The unit of state is `.gitignore` plus
`.wf-skills-manifest.json`, both plain files in the consuming repo.
**Testing**: `pytest` via `uv run pytest`. Fixtures in `tests/conftest.py`
(`agent_dir`) already create a real git repo and point `WFCTL_REPO_ROOT` at it,
so `git check-ignore` works under test with no new scaffolding.
**Target Platform**: Developer workstations, macOS and Linux. Git is a hard
prerequisite of the surrounding command.
**Project Type**: Single-package CLI tool.
**Performance Goals**: SC-006 — coverage checking adds ≤1.5 s to a full install.
Measured: ~12 ms per path, ~1.0 s for 83 entries.
**Constraints**: No behavior change for paths that are not already covered
(FR-003, SC-004). No new terminal noise in the clean case (FR-012).
**Scale/Scope**: One function, four call sites, one test file pair.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

`.specify/memory/constitution.md` does not exist in this repository. The gates
shipped in the plan template target a different project (workspace isolation,
ZenStack policies, `.zmodel` tiers) and none of them apply here — see *Template
deviations* below. The gates used instead are drawn from the conventions this
repository actually enforces, evidenced by its existing code and comments.

- [x] **No new dependency.** The change shells out to `git`, already a hard
      prerequisite of `install-skills`.
- [x] **Complexity is justified.** The chosen per-path form is the smaller of
      two measured options; the cheaper batched form is deferred with its cost,
      trigger, and replacement recorded in a `ponytail:` marker (repo
      convention, greppable, harvested by `/ponytail-debt`).
- [x] **Behavior preserved where not explicitly changed.** FR-003 through
      FR-006 pin today's outcomes; SC-004 requires zero regressions.
- [x] **Validation plan exists.** `uv run pytest`, `uv run ruff check .`, and
      `uv run mypy` (the three CI gates), plus the ten cases named in Phase 1
      and the manual check in `quickstart.md`.
- [x] **Failure mode is safe.** FR-008 fails closed: when the check cannot run,
      the entry is written, which is today's behavior.
- [x] **No silent output changes.** FR-012 keeps the clean case silent; the new
      line appears only when something was skipped.

**Post-Phase 1 re-check**: unchanged — no design step introduced an abstraction,
a dependency, or a new interface.

## Project Structure

### Documentation (this feature)

```text
specs/11-gitignore-glob-dedup/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output — probe findings behind each decision
├── quickstart.md        # Phase 1 output — manual verification
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

`data-model.md` and `contracts/` are intentionally absent — see *Phase 1* below.

### Source Code (repository root)

```text
wfctl/
├── cli.py               # _ensure_gitignored (:633) + call sites (:929-932, :1134)
├── _paths.py            # get_repo_root — unchanged
├── _archive.py          # unchanged
├── _session.py          # unchanged
├── _pipeline.py         # unchanged
└── _tracker.py          # unchanged

tests/
├── conftest.py          # agent_dir fixture — real git repo, unchanged
├── test_install_skills.py   # coverage cases + skip report
└── test_install_config.py   # wt/ no-regression cases
```

**Structure Decision**: No structural change. One function is rewritten in
place, its four call sites in `cli.py` adapt to a boolean return, and two
existing test files gain cases. Nothing new is created and nothing moves.

## Design

### The guard

```python
def _ensure_gitignored(repo_root: Path, line: str) -> bool:
    """Append `line` to .gitignore unless git already ignores it.

    Returns True if a line was written, False if it was already covered — the
    exact-match guard this replaced could not see that a broader pattern
    already ignored the path, so every install re-appended entries no one
    would ever commit.
    """
    import subprocess as sp

    # ponytail: one check-ignore per path, ~12ms each (~1s for a full install).
    # Batch via `check-ignore --stdin` if the clone in #1 ever goes away and
    # this stops being noise against the network.
    #
    # --no-index: a tracked path whose pattern matches reports "not ignored"
    # without it, and we would write a line that does nothing to a tracked file.
    # capture_output: outside a repo this exits 128 and prints `fatal:` — a
    # non-zero exit already means "not covered", which is the safe fallback.
    if sp.run(
        ["git", "check-ignore", "-q", "--no-index", line],
        cwd=repo_root,
        capture_output=True,
    ).returncode == 0:
        return False

    gi = repo_root / ".gitignore"
    text = gi.read_text() if gi.exists() else ""
    if text and not text.endswith("\n"):
        text += "\n"
    gi.write_text(text + f"{line}\n")
    return True
```

Function-local `import subprocess as sp` matches the surrounding convention
(`cli.py:295`, `:695`).

### The call sites

`cli.py:929-932` becomes a single loop that counts skips:

```python
skipped = sum(
    not _ensure_gitignored(repo_root, rel)
    for rel in (_MANIFEST_PATH, f"{_BACKUP_DIR}/", *gitignore_targets)
)
if skipped:
    console.print(
        f"[dim]ℹ {skipped} ignore entries already covered by .gitignore — skipped[/dim]"
    )
```

Placed immediately before the existing backup notice at `:934`, so the ignore
story reads in one block.

`cli.py:1134` (`install-config`'s `wt/`) is unchanged — a bool return is
ignorable, and the guard's behavior there is the same.

### Why the return value rather than a counter parameter

The function already knows the answer; returning it is free. A counter passed
in or a module-level accumulator would both add state that only one caller
reads. Callers that do not care ignore the bool, which is why `:1134` needs no
edit at all.

## Phase 0: Research

See [research.md](./research.md). All open questions were resolved by probing
git directly during brainstorming rather than by reading documentation; the
probe scripts and their raw output are recorded there.

No `NEEDS CLARIFICATION` markers remain in the spec.

## Phase 1: Design & Contracts

**`data-model.md` — not generated.** This feature has no entities, no schema,
and no persisted structure. The only data touched is one line of text appended
to a file. Generating a data model here would produce a document with nothing
in it.

**`contracts/` — not generated.** The CLI surface is unchanged: no new command,
no new flag, no changed argument. The only externally visible change is one
conditional line of output, specified by FR-011/FR-012 and asserted in tests.
There is no interface to contract.

**`quickstart.md` — generated.** The manual verification path, which is
meaningful here because the bug's signature is a diff that reappears.

**Agent context** — written to `.agent/brief.md`.

### Test plan

Ten new tests, all asserting on resulting file contents rather than on how
coverage was determined (spec *Validation Strategy* → test altitude):

| # | Story | Case | Asserts |
|---|-------|------|---------|
| 1 | US1 | glob already covers install paths | those lines absent; file byte-identical |
| 2 | US1 | two installs in a row | `.gitignore` byte-identical after the second |
| 3 | US2 | no `.gitignore` exists | file created with expected lines |
| 4 | US2 | nothing covers the paths | every path appended (today's behavior) |
| 5 | US2 | directory-form entries, directory absent from disk | `wt/` and `.wf-skills-backup/` resolve correctly |
| 6 | US2 | repo root is not a git repository | line still written, nothing on stderr (FR-007, FR-008) |
| 7 | US2 | path tracked in the index **and** matched by a pattern | not appended (FR-006) — the only test that defends `--no-index` |
| 8 | US2 | `.gitignore` with no trailing newline | last existing line survives; entry lands on its own line |
| 9 | US3 | some entries skipped | skip count reported |
| 10 | US3 | nothing skipped | no line printed (FR-012) |

Plus `test_install_config.py`'s two existing cases
(`test_seed_writes_workmux_and_gitignores_wt`,
`test_gitignore_no_duplicate_when_present`), which must pass **unedited** — if
either needs a change, the guard altered behavior it should not have.

Case 1 is the regression test for issue #11 and must fail against the current
implementation. Cases 7 and 8 were added at `/speckit.analyze` (findings E1 and
E3); case 7 closed the only requirement with zero test coverage.

`tasks.md` is authoritative for test names and task IDs.

## Complexity Tracking

No Constitution Check violations. One deliberate simplification is recorded
rather than justified as a violation:

| Simplification | Measured cost | Trigger to revisit | Replacement |
| --- | --- | --- | --- |
| One `check-ignore` process per path | ~12 ms/path, ~1.0 s per full install vs ~46 ms batched | Issue #1 removing the runtime clone, making this ~half of install time instead of ~7% | `git check-ignore --stdin` over the already-collected `gitignore_targets` list |

## Template deviations

`.specify/templates/plan-template.md` is vendored from pfms and its defaults
describe a different system. Replaced rather than filled in:

- **Technical Context** — template defaults to TypeScript, Node 20+, Express 5,
  Vue 3, ZenStack, Prisma, PostgreSQL, Vitest, pnpm, and a `client/`+`server/`
  monorepo. wfctl is a single Python package with `typer` and `rich`.
- **Constitution Check** — all six template gates are pfms-specific
  (`workspaceId` boundaries, ZenStack policies, `.zmodel` tiers,
  `bootstrap.zmodel`, `.claude/context/*`, `pnpm type-check`). No
  `.specify/memory/constitution.md` exists here, so repo-appropriate gates were
  substituted and the substitution declared.
- **Project Structure** — the template's three-option placeholder tree was
  replaced with the real layout.

This is the second artifact in this feature to hit the same problem; the spec
template needed equivalent surgery. **Already tracked upstream** as
`aamarin/wf-skills#10` (open) — an umbrella counting 24 foreign-stack references
across 8 files, filed from the same experience while running this pipeline on
`aamarin/wfctl#17`. Its PRs 4-6 cover `spec-template.md`, `plan-template.md`,
and the rest. `aamarin/wf-skills#3` is closed, with the decision recorded as
*delete, do not adapt*. Nothing to file here; the deviations above are recorded
so this feature's artifacts are auditable, not as a bug report.
