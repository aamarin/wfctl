# Review: working changes on `18-spec-root-manifest-key` (`git diff HEAD` + `tests/test_spec_root.py`)

**Date**: 2026-08-06
**Scope**: `wfctl/_paths.py`, `wfctl/cli.py`, `tests/conftest.py`, `tests/test_paths.py`,
`tests/test_install_skills.py`, `tests/test_spec_root.py`, `README.md`
**Method**: adversarial pass, six lenses. Every finding below was reproduced against a
real scratch repo, not inferred from reading.

---

## Findings

```
WARNING  cli.py:L432 — `spec-root` writes the main checkout's tracked .gitignore, unreported → report it, or drop the call
WARNING  cli.py:L433 — `--unset` on an unset repo prints "✓ wrote <path>" for a file it never writes → report the real outcome
WARNING  cli.py:L1420 — stranded-specs guard compares unresolved paths; false positive under WFCTL_REPO_ROOT → compare .resolve()
WARNING  cli.py:L398-415 — show-branch re-derives the precedence chain `spec_root()` owns → one helper returning (root, source)
WARNING  test_paths.py:L404,L511 — `pytest.raises(Exception)` passes on any error, incl. NameError → raise on json.JSONDecodeError
NIT      cli.py:L1425 — "1 spec directory — they will not be found" → pluralize the pronoun too
NIT      cli.py:L378 — `path: str = typer.Argument(None)` annotates a non-optional str → `str | None`
NIT      cli.py:L390 — literal "WFCTL_SPEC_DIR" duplicates `_paths._SPEC_DIR_OVERRIDE` → export and reuse it
NIT      _paths.py:L246 — `main_checkout()` runs eagerly, ~1 subprocess/call even when unused → evaluate lazily
```

**net: −12 lines possible** (mostly W4's duplicate chain)
**Verdict: Request changes** — 0 blockers, 5 warnings.

---

## Resolution (2026-08-06)

All five warnings and all four nits fixed. `pytest` 299 passed (was 297; +3 new
regression tests, −1 replaced), `ruff` clean, `mypy` clean.

Each behavioral fix was re-verified against the same scratch repo that
demonstrated the defect:

| # | Before | After |
|---|--------|-------|
| W1 | `✓ wrote …manifest.json` only; main checkout left ` M .gitignore` | both writes reported: `✓ wrote …` + `✓ gitignored it in …/.gitignore` |
| W2 | `✓ wrote <path>` for a file that did not exist; created a `.gitignore` | `nothing to unset — no spec_root was recorded`; no files created |
| W3 | "Move them to /private/tmp/…/specs" from `/tmp/…/specs` — same dir | silent; true positives still fire, singular/plural correct |

W3's regression test was confirmed to fail against the pre-fix comparison before
being kept — it is testing the bug, not passing by construction.

`_ensure_gitignored` now returns whether it wrote. Existing callers ignore the
value, so install/uninstall behavior is unchanged; the suite confirms it.

Two of these (W1, W2) were caught only because the review re-ran the commands
rather than trusting the tests — `test_unset_on_a_repo_with_no_manifest_is_not_an_error`
asserted `exit_code == 0` and passed while the command reported a write it never
made. It has been replaced with one that asserts the message and the filesystem.

---

## W1 — `spec-root` silently dirties the main checkout's tracked `.gitignore`

`wfctl/cli.py:432` calls `_ensure_gitignored(target, _MANIFEST_PATH)`, where `target`
is the **main checkout** — a directory the user is not standing in. `.gitignore` is
tracked in most repos, so a config command leaves a clean checkout dirty, and reports
only that it wrote the manifest.

**Reproduced** (repo with a tracked `.gitignore`, command run from a worktree):

```
$ cd demo/wt/9-x && wfctl spec-root /tmp/some-specs
✓ wrote /…/demo/.wf-skills-manifest.json      ← says nothing about .gitignore

$ cd demo && git status --short
 M .gitignore                                  ← main checkout now dirty
```

The write itself is defensible (an untracked manifest is noise). Doing it to another
directory without saying so is not — it can land in an unrelated commit.

**Fix**: print the `.gitignore` path when the line was actually added, or drop the call
and let `install-skills` keep owning it.

## W2 — `--unset` reports writing a file it does not write

`_save_manifest` deletes (or never creates) a manifest that is empty. So on a repo with
nothing recorded, `spec-root --unset` empties the dict, writes nothing — and prints a
success line naming a path that does not exist. It also creates a `.gitignore` in a repo
that had none, via W1.

**Reproduced** on a fresh `git init`:

```
$ ls -a
.  ..  .git
$ wfctl spec-root --unset
✓ wrote /private/tmp/rvnoop/e/.wf-skills-manifest.json   ← no such file afterwards
$ ls -a
.  ..  .git  .gitignore                                   ← and a new file appeared
```

My own test `test_unset_on_a_repo_with_no_manifest_is_not_an_error` asserted only
`exit_code == 0`, so it passed while the command lied. That is the test's fault as much
as the code's.

**Fix**: branch the message on what happened — `✓ wrote <path>` when a manifest exists
after the call, `nothing to unset` when it does not. Extend the test to assert the
message, not just the exit code.

## W3 — Stranded-specs guard false-positives on unresolved paths

`_check_spec_root_migration` (`cli.py:1420`) guards with `root == in_repo`, where `root`
comes back **resolved** (`_manifest_spec_root` calls `.resolve()` on relative values) and
`in_repo` is the raw `repo_root / "specs"`. When `repo_root` is unresolved — which
`WFCTL_REPO_ROOT`, a documented override, produces — the two differ by symlink and the
guard misses.

**Reproduced** (`/tmp` → `/private/tmp` on macOS), `spec_root` set to `specs`:

```
$ WFCTL_REPO_ROOT=/tmp/rvsym/d wfctl doctor
⚠ spec_root is set, but /tmp/rvsym/d/specs still holds 1 spec directory —
  they will not be found.
  Move them to /private/tmp/rvsym/d/specs, or remove them.
```

Source and destination are **the same directory**. The advice is not merely noisy, it is
wrong — and this is `doctor`, whose entire job is to be trusted about repo state.

**Fix**: compare `root.resolve() == in_repo.resolve()`.

## W4 — The show-branch re-implements the precedence chain

`spec_root()`'s docstring calls itself "the single decision point", but
`spec_root_cmd`'s show path (`cli.py:398-415`) walks `(repo_root, main_checkout(...))`
and re-tests `_load_manifest(base).get("spec_root")` itself, to name a source. Two copies
of one rule: they agree today, and nothing keeps them agreeing. Adding a fourth source
means editing both, and a mismatch here misreports where a value came from — the one
thing this output exists to answer.

**Fix**: a single `_spec_root_with_source(repo_root) -> tuple[Path, str]`, with
`spec_root()` returning its first element.

## W5 — `pytest.raises(Exception)` proves almost nothing

`tests/test_paths.py:404` and `:511` assert only that *some* exception escapes, then
exclude `AssertionError`. A typo raising `NameError`, or an `OSError` from a permission
problem, satisfies them just as well as the intended `json.JSONDecodeError`. FR-015 is
specifically about *how* a malformed manifest fails, so the test should pin the type.

**Fix**: `with pytest.raises(json.JSONDecodeError):` in both.

---

## Passes with nothing to report

- **Security** — no new input crosses a trust boundary. The manifest was already
  read by this process; `spec_root` is used as a path, never as a command argument or
  in a shell string. `feature-paths` output stays `eval`-safe: no line was added, and
  the single-quoted `NAME='value'` form is unchanged (a path containing `'` was
  already able to break this before the change, and is no worse now).
- **Architecture** — `spec_root()` lives beside every other path decision in `_paths.py`;
  the lazy `_load_manifest` import matches `_tracker.py:129` and keeps the existing
  one-way `cli → _paths` edge intact. `_check_spec_root_migration` mirrors
  `_check_workmux_hook`'s contract exactly (reports, never mutates, never changes the
  exit code) and is called at the same point, before the layers gate — verified, the
  warning fires in a repo with no layers installed.
- **Over-engineering** — no speculative abstraction, no new dependency, no config nobody
  sets. Both deliberate shortcuts carry `ponytail:` comments naming their ceiling and
  upgrade path. The docstrings are long but carry *why*, not *what*.

## Note on scope

`tests/conftest.py`'s `NO_COLOR` line fixes a pre-existing, unrelated test bug. It is
correct and was explicitly requested, but it does not belong to #18 — worth calling out
in the PR body so a reviewer is not left guessing why it is here.
