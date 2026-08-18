# Implementation Plan: version check — default branch and fork

**Branch**: `21-version-check-master-and-fork` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/21-version-check-master-and-fork/spec.md`

## Summary

`wfctl doctor` compares the installed version against release tags only, so a
build installed from the default branch — the install the README prescribes —
reports `✓ latest` while missing merged work. Since #47/#49 vendored the skills
tree into the package, such a build also ships stale skills that the skills check
cannot see, because a bundle always matches itself.

The fix reads the build's origin commit from PEP 610 `direct_url.json`, resolves
the origin's default branch tip through the `ls-remote` call the check already
makes, and reports drift as a second verdict with its own remedy. No packaging
change, no new dependency, no extra network round trip for an upstream install.

## Technical Context

**Language/Version**: Python 3.11+ (`requires-python = ">=3.11"`)
**Primary Dependencies**: none added. Uses `importlib.metadata` (stdlib), `json`
(stdlib), `re` (stdlib), and the `git` binary already invoked by this function.
**Storage**: N/A — every value is derived per invocation; nothing is cached or
persisted (data-model.md, "State transitions").
**Testing**: `pytest`, offline. New cases carry the existing
`real_version_check` marker so conftest's autouse stub steps aside. Plus
`ruff check` and `mypy` as configured in `pyproject.toml`.
**Target Platform**: developer machines, macOS and Linux; also CI, where the
check must remain offline-safe.
**Project Type**: single-package CLI.
**Performance Goals**: no additional network round trip for an upstream install;
at most one more for a fork install (SC-005).
**Constraints**: doctor must never raise on third-party metadata, must retain a
single warning line per report, and must keep the `✓ … — latest` string
byte-identical for the unchanged case. Minimal-complexity bias throughout.
**Scale/Scope**: one function in one file, plus tests and two documentation
lines.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This repository has no `.specify/memory/constitution.md`. Gates below are
substituted from the repository's own documented conventions —
`pyproject.toml`'s annotated lint/type configuration, `tests/conftest.py`'s
offline-and-deterministic rule, and the `ponytail:` shortcut-marking convention
in `wfctl/cli.py`. The substitution is recorded in Complexity Tracking.

- [x] **Validation plan exists.** `pytest` (offline, whole suite), `ruff check`,
      `mypy`, plus the manual end-to-end in `quickstart.md` against this
      machine's live stale build. Per-state coverage is enumerated in
      `data-model.md` E3.
- [x] **Complexity is justified.** No new abstraction, dependency, or file. One
      helper function is added because the parsing has four distinct skip rules
      that would otherwise inline into an already-branching function.
- [x] **No new network dependency.** The branch tip rides the existing
      `ls-remote` invocation for upstream installs.
- [x] **Tests run offline and do not depend on the machine's state.** New cases
      stub both the metadata read and the `ls-remote` output — the rule
      `tests/conftest.py` was written to enforce after three tests went red on a
      release.
- [x] **Type-annotated.** `disallow_untyped_defs = true` applies; the new helper
      is annotated.
- [x] **Deliberate shortcuts are marked.** Any accepted ceiling carries a
      `ponytail:` comment naming it, per the convention already in `cli.py`.

_Post-Phase-1 re-check_: still passing. Phase 0 research **removed** three
planned code paths (research.md, "Resulting simplifications"), so the design got
smaller after investigation, not larger.

## Project Structure

### Documentation (this feature)

```text
specs/21-version-check-master-and-fork/
├── plan.md              # This file
├── spec.md              # /speckit.specify + /speckit.clarify output
├── design.md            # /speckit.brainstorm output
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── doctor-tool-freshness.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit.tasks output — not created here
```

### Source Code (repository root)

```text
wfctl/
└── cli.py               # _WFCTL_REPO (1616), _check_wfctl_version (1626)
                         # + new _installed_build() helper alongside them

tests/
├── conftest.py          # autouse stub — unchanged, relied upon
└── test_install_skills.py   # new cases under @pytest.mark.real_version_check

README.md                # line 247-ish: doctor's description
```

**Structure Decision**: Single-package CLI with a flat module layout. The change
is confined to the freshness-check region of `wfctl/cli.py` (roughly lines
1616-1651) and its existing test file. No new module: the helper is used by one
caller, and a file per function is the kind of structure this repo's conventions
argue against.

## Implementation Approach

**1. `_installed_build() -> tuple[str, str] | None`**

Reads `direct_url.json` via `importlib.metadata.distribution("wfctl")
.read_text(...)`, which returns `None` when absent rather than raising. Returns
`(url, commit_id)` only when `vcs_info` is present and `requested_revision` is
absent; `None` otherwise, including on malformed JSON. The four skip rules are
E1 R-1 through R-4 in `data-model.md`.

**2. Extend the existing `ls-remote` invocation**

From `["git", "ls-remote", "--tags", "--refs", _WFCTL_REPO]` to a call taking
`--symref`, `HEAD`, and `refs/tags/v*`. The symref line yields both the default
branch name and its tip, so no branch name is hardcoded and a rename to `main`
needs no change (FR-003). A fork install issues a second call for its own
`HEAD`, with tags still read from `_WFCTL_REPO` (FR-009).

**3. Render per the decision table**

`data-model.md` E3 is the table; `contracts/doctor-tool-freshness.md` is the
exact line shape. The release verdict is computed first and suppresses the
branch line when an upgrade is already being prescribed.

**4. Failure handling**

Track which comparisons could not run and emit exactly one `⚠` line naming them
(FR-009a). A comparison that failed is never silently dropped — its absence would
read as a pass, which is the class of defect this feature exists to remove.

## Cross-Issue Scope

This branch is **PR B** in issue #41's coordination plan, and covers **#21 plus
#35 B1** (the fork-targeting half). That was established before this feature was
planned; the branch name `21-version-check-master-and-fork` already encodes it.

| Obligation | Source | Where handled |
| --- | --- | --- |
| `_check_wfctl_version` returns `bool`, OR'd into the exit code | #41, "PR B converts it to `bool` as the last step of its own rewrite" | FR-013, T024 |
| Do not touch the other four checks or their call sites | #41, the scoping line that keeps PR A and PR B parallel | stated in tasks.md |
| Let a fork point the version check at its own repo | #35 B1 | FR-009 (branch tip) + **FR-012** (remedy URLs) |

**How B1 was resolved.** #35 B1 frames the fork case as "a fork cannot point
doctor's version check at its own *releases*", which contradicts FR-009's rule
that tags always come from canonical upstream. Both readings serve a different
fork: a contributor's fork carries upstream's tags frozen at fork time, so
FR-009 protects them from a silent "latest"; a maintained hard fork cuts its own
releases, so B1 protects them. Resolved at `/speckit.clarify` in favour of
FR-009, because its failure mode is loud (a visibly wrong version pair) while
B1's is silent (the exact false-negative this feature exists to remove). B1's
real harm — being told to reinstall from someone else's repository — is
addressed instead by **FR-012**, which makes every printed remedy name the
recorded origin.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Constitution gates substituted from repo conventions rather than a constitution file | No `.specify/memory/constitution.md` exists; the template requires recording the substitution rather than inventing or borrowing gates | Copying another project's gates would make the check decorative; skipping the gate entirely would leave the offline-tests and no-new-dependency rules — both already enforced in this repo — unstated |
| Second `ls-remote` call for fork installs | A fork is authoritative about its own branch but its tag list freezes at fork time; one query cannot answer both correctly | Querying only the fork (option A at `/speckit.clarify`) reintroduces this exact bug for fork users; skipping tags for forks (option C) removes release visibility entirely |
| New helper function rather than inlining | Four distinct skip rules plus JSON parsing inside an already-branching function | Inlining pushes `_check_wfctl_version` past the point where its branches can be read at a glance |

## Next

`/speckit.tasks` — break this into ordered, verifiable tasks.
