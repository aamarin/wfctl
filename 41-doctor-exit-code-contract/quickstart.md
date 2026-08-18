# Quickstart: verifying the doctor exit-code contract

How to run this feature's checks and confirm each user story. Everything here runs
offline.

## Gates

```bash
uv run --frozen --extra dev pytest -q      # suite
uv run --frozen --extra dev ruff check .   # lint
uv run --frozen --extra dev mypy           # types
```

Baseline on this branch before implementation: **395 passing, ruff clean, mypy
clean over 11 source files.**

> Bare `python3 -m pytest` is not a valid run. It reports dozens of failures on a
> green tree, all `PackageNotFoundError('wfctl')` — the package is not installed in
> that interpreter, and the failures look like real assertion errors rather than an
> environment problem.

## Story 1 — the exit code

Per-check, in both states:

```bash
uv run --frozen --extra dev pytest tests/test_install_skills.py -q -k doctor
```

The existing `test_doctor_exit_code_is_unchanged_by_the_spec_root_warning`
asserts the convention being replaced. It is expected to be **rewritten**, not
preserved — if it still passes unchanged after the contract lands, the contract
was not applied to that check.

Interactive fix path, all three branches:

| Branch | Expected exit |
| --- | --- |
| Fix offered, accepted, applied | `0` |
| Fix offered, declined | `1` |
| No terminal, offer skipped | `1` |

Offline behaviour is already covered by the autouse fixture in `tests/conftest.py`,
which stubs the only network call for the whole suite. Two tests marked
`real_version_check` opt out and stub `ls-remote` themselves.

## Story 2 — a freshly configured repository reports clean

Unit level:

```bash
uv run --frozen --extra dev pytest tests/test_bundle.py -q -k stale
```

This asserts the shipped template through `_workmux.pre_remove_uses_former_name` —
the same function `doctor` calls — rather than against a copied literal, so the two
cannot disagree about what counts as stale.

End to end, which is the only way to observe the loop this story fixes:

```bash
git init /tmp/probe
cd /tmp/probe
uv run --frozen --project <repo> wfctl install-config workmux
uv run --frozen --project <repo> wfctl doctor
```

**Expected**: no finding mentions `.workmux.yaml`. Before the fix, `doctor`
reported the just-seeded file as stale and prescribed re-running the command that
wrote it.

## Story 3 — abandoned entries

```bash
uv run --frozen --extra dev pytest -q -k abandoned
```

To reproduce by hand: install, rename a source file in the bundle, install again,
then run `doctor`. The old path is on disk and absent from the record.

Confirm the granularity rule (SC-007) — an abandoned directory holding N files is
one finding for any N — and the exclusion: a file hand-written into
`.claude/commands/` is never reported.

## Story 4 — the step-to-command table

```bash
uv run --frozen --extra dev pytest tests/test_pipeline_commands.py -q
```

To confirm it actually catches the drift, point a table entry at a name that is not
shipped and re-run. Expected: failure naming the entry and suggesting the nearest
shipped name.

Current state of the invariant, for reference — all eight resolve:

```
brainstorm  /speckit.brainstorm    specify   /speckit.specify
clarify     /speckit.clarify       plan      /speckit.plan
tasks       /speckit.tasks         analyze   /speckit.analyze
decompose   /speckit.decompose     implement /speckit.implement
```

## Whole-feature check

```bash
uv run --frozen --project <repo> wfctl doctor ; echo "exit=$?"
```

Run in this repository. **Expected**: `exit=0` — it carries none of the drift these
checks look for. Run in a repository with a `.agent/` directory: `exit=1`, and the
finding names it.
