# Pull Request

## Summary

**Context:** wfctl works out which issue a branch belongs to by matching the
branch name against a regex. Projects that don't number their branches the way
GitHub does can supply their own regex in a tracker config — a small JSON file
someone writes by hand. Everything downstream depends on that lookup producing
an answer, so it is built never to fail: whatever is wrong with the config, it
falls back to the built-in default and carries on.

### Before / After

A tracker config is hand-written JSON, so `key_pattern` arrives as whatever the
author typed. Every wrong value was supposed to land in the fallback. Four of
them did not:

```
key_pattern in the config          before              after
─────────────────────────────────  ──────────────────  ──────────────
absent / null / ""                 default             default
"[unclosed"   (bad regex)          default             default
123           (a number)           TypeError, uncaught default
["a"]         (a list)             TypeError, uncaught default
{"x": 1}      (an object)          TypeError, uncaught default
true          (a boolean)          TypeError, uncaught default
"PROJ-\d+"    (valid)              returned as given   returned as given
```

The four that raised did so from one line. `re.compile` answers a non-string
with `TypeError`, and the guard around it catches only `re.error` — so the
exception went straight out of a function whose callers do not guard it, over a
config a user can write without doing anything unusual.

Review then found the same hole one level up — the config *document*, not the
field in it:

```
the tracker file holds            before                     after
────────────────────────────────  ─────────────────────────  ──────────────
{"verbs": {...}}   (an object)    read normally              read normally
not JSON at all                   treated as no config       treated as no config
[]                 (empty list)   treated as no config       treated as no config
[{"list": [...]}]  (a list)       AttributeError, 3 places   treated as no config
```

The last row is a verb map written without its enclosing object. It parses, so
nothing rejected it, and then three separate call sites called `.get` on a list.
One of them is `wfctl tracker-check` — the command every "config missing or
invalid" message tells you to run.

**What:** A malformed tracker config no longer crashes the commands that read
it — neither a `key_pattern` of the wrong type nor a document that is not an
object. Both degrade the way every other bad value already did.

**Why:** The fallback existed and had two holes in it, and the values that fell
through are the ones easiest to write by hand: a bare number where a string was
meant, or a verb map saved without its enclosing braces.

**Impact:** Anyone authoring a tracker config. A single typo used to take the
command down with a Python traceback — including `wfctl tracker-check`, the
command the error messages send you to. Now the tracker degrades to the default
and `tracker-check` tells you what is wrong with the file.

---

## Type of Change

- [x] Bug fix (non-breaking change that fixes an issue)
- [x] Documentation update

## Issue Links

### Closes
- Closes #249

### Related
- Related: #247 — the stale test count in `AGENTS.md`, the same drift in a
  different line. Not touched here.
- Related: #263 — `resolve_spec_dir` inheriting a foreign feature's spec dir,
  found while running this PR's review panel. Not touched here.

## What Changed?

### Changes Made
- `load_key_pattern` checks `isinstance(pattern, str)` before compiling, so a
  non-string `key_pattern` falls back to `DEFAULT_KEY_PATTERN` instead of raising
  `TypeError`.
- Its docstring names that failure mode alongside the four it already listed.
- A parametrised regression test covers `int`, `list`, `dict` and `bool`.
- `AGENTS.md`'s sentence about strict mypy replaced: it stated three things
  about the deferred findings and all three were wrong.
- `_load_tracker_config` returns `None` for a document that parses but is not an
  object, so a top-level JSON array no longer reaches `.get()` in
  `load_key_pattern` or `dispatch`.
- `validate_config` reports `config must be a JSON object` instead of raising
  `AttributeError` out of `wfctl tracker-check`.
- `pyproject.toml`'s `[tool.mypy]` comment carried a second, contradicting copy
  of the corrected strict-mypy rationale. Same treatment.

### Implementation Details

**Where the guard goes.** Two shapes close this: widen the `except` to
`(re.error, TypeError)`, or check the type before compiling. Same size once
written. The `except` catches the failure where it surfaces; the isinstance
check rejects the value where it is read, and says what a `key_pattern` has to
be rather than which exception something downstream threw. `validate_config`,
forty lines up in the same file, already states the same rule in the same
shape — so the guard matches a check the file was already making rather than
introducing a second idiom for one field. It also narrows the value, which
removes one of strict mypy's `no-any-return` findings as a side effect.

**What was left alone.** The issue offers two further shapes and neither is
here. Giving the four JSON-parsing boundaries return types they actually honour
(`_manifest.py:32`, `_io.py:64`, `_tracker.py:123`) decides what each parsed
document *is*, which is a boundary being drawn — that needs the spec pipeline,
and none of those three has a demonstrated crash behind it. Enabling `strict`
mypy is refused for the reason `AGENTS.md` already gives about ruff rule sets:
it is its own reviewable diff, not a drive-by.

**The `AGENTS.md` correction, and why it carries no number.** The old sentence
said the strict findings were "26", "one shape", and "tracked separately". They
are 40, two shapes, and tracked nowhere. The replacement names the two shapes —
`type-arg` and `no-any-return` — and points at `uv run mypy --strict wfctl/`
rather than writing down a count. A number here has already drifted once with
nothing watching it, which is #247's complaint about a different line in the
same file; a second cached count would be the same defect written twice. The
deferral itself stands. #249 argued against its stated reasons, not against it.

## How Has This Been Tested?

- [x] Unit tests added/updated
- [x] Manual testing performed
- [x] Edge cases considered and tested
- [ ] Tested across the environments/browsers this affects (if applicable)

### Test Details

The issue's reproduction was run against the unfixed function first, and it
raised:

```
$ uv run python -c "from wfctl._tracker import load_key_pattern; \
                    print(load_key_pattern(Path('/tmp/tb')))"
TypeError: first argument must be string or compiled pattern
```

After the fix, the same command prints `\d+`. Running it only against the fixed
tree would not have shown the test covers anything.

`tests/test_key_pattern.py::test_load_non_string_falls_back` carries the four
non-string shapes. `bool` is the one worth naming: `True` is truthy, so it got
past the old `if not pattern` guard, and it is not a `str`, so it would still
reach `re.compile` under a fix that only special-cased integers.

The two rows a careless guard breaks are covered by tests that already existed:
`test_load_configured` (a valid pattern is returned as given) and
`test_load_uncompilable_falls_back` (the `re.error` path still degrades).

The non-object config has one test per crash site, each confirmed red first:
`test_load_non_object_config_falls_back`, `test_non_object_config_degrades`
(`wfctl issue view` exits 0 with the "missing or invalid" notice) and
`test_tracker_check_reports_a_non_object_document` (exits 1 naming the problem).
They use `[{"list": [...]}]` rather than `[]` — `[]` is falsy, so `(config or
{})` already handled it and a test on it would pass against the unfixed code.

`uv run wfctl verify` records 3 of 3 passed at `1b7252e` — 1054 tests, ruff,
mypy.

## Review Panel

**Panel:** the commits on this branch — 3 local reviewers plus Copilot, 3 code
findings, 2 items raised outside the diff.

| # | Reviewer | Finding | Disposition |
|---|---|---|---|
| 1 | r1 | No findings. Hand-traced every value the function handles, old guard vs. new; confirmed `validate_config` makes the isinstance check the new comment claims it does; re-derived the strict-mypy numbers independently | accepted — the claim in the comment was worth checking, and it holds |
| 2 | r2 | `AGENTS.md`'s "653 tests" line is now stale — the same class of drift this PR fixes one paragraph below it | rejected for this PR — it is #247, already filed and open. Fixing it here would put two unrelated corrections behind one review |
| 3 | r3 | No findings. Confirmed `extract_issue_key` is the only typed caller, so the return type is the whole contract; verified the `no-any-return` claim by diffing strict-mypy output across the fix commit | accepted |
| 4 | r3 | Process, not code: it ran `git stash`/`git stash pop` in this shared repo and collided with a pre-existing entry belonging to another worktree | verified independently rather than taken on report — `git reflog show stash` has one entry, `d161804`, dated 2026-09-02, with no push or drop since. The pop conflicted and therefore dropped nothing. Tree clean, branch diff unchanged, suite re-run green afterwards |

| 5 | Copilot | `_load_tracker_config` returns raw `json.loads` output, so a top-level JSON array makes `(config or {}).get(...)` raise `AttributeError` — `load_key_pattern` can still crash | applied — reproduced it first, and it is wider than reported: `dispatch` and `validate_config` fail the same way, and `validate_config` is what `wfctl tracker-check` calls, so the diagnostic crashed on the input it exists to diagnose. Guarded at the parse boundary, which makes `_load_tracker_config`'s declared `dict \| None` true for both callers |
| 6 | Copilot | `pyproject.toml`'s `[tool.mypy]` comment still carries the old rationale — "26 findings", different shapes — and now contradicts the corrected `AGENTS.md` | applied. Not by picking one source of truth, though: a reader in `pyproject.toml` deciding whether to flip `strict` cannot be sent to `AGENTS.md` for the reason it is off. Both keep the rationale, both drop the count |
| 7 | Copilot | Add a regression test for a non-object config, e.g. `[]` | applied, with a different value. `[]` is falsy, so `(config or {})` already handled it — a test on `[]` passes against the unfixed code. The tests use a non-empty list, the shape that actually reaches `.get` |

roster: r1 ✓  r2 ✓  r3 ✓  Copilot ✓ — none re-asked

**Codex did not review this PR.** `chatgpt-codex-connector[bot]` commented that
the account has reached its usage limits for code reviews; it never read the
diff. That is an absent reviewer, not a clean pass, and it was not re-triggered.

## Checklist

- [x] My code follows the project's style guidelines
- [x] I have performed a self-review of my own code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] My changes generate no new warnings or errors
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] New and existing tests pass locally with my changes
- [x] Any dependent changes have been merged and published
- [x] Every fully completed issue is under `Closes` with a closing keyword, not only `Related`
- [x] Anything this change turned up in passing is named under Additional Context, with whether it was filed
- [x] A review panel ran over this diff and its disposition table is under Review Panel

## Documentation

- [x] Code comments added/updated
- [x] README updated (if needed) — not needed; no user-facing surface changed
- [ ] API documentation updated (if applicable)

## Deployment Notes

None. No version bump, no migration, no new dependency.

## Additional Context

Two things this turned up that are not about this change.

**`wfctl feature-paths` resolves this branch to a foreign feature directory.**
On `249-key-pattern-typeerror` it returns
`wfctl-specs/240-decompose-advances-unattended`, which contains nothing but a
leftover `reviews/` from that branch's session. Following it would have
overwritten another feature's review files, so the panel wrote to
`wfctl-specs/249-key-pattern-typeerror/reviews/` instead. This is not new: it is
the case `resolve_spec_dir`'s own docstring leaves open — "a foreign ancestor
that never decomposed has no map to contradict, and is inherited", the remaining
shape of #120. **Filed as #263** — #120 is closed and its second acceptance
criterion is unmet for this shape, so that docstring was the only record.
Reproduced from scratch there: a branch with no artifacts of its own has `wfctl
status` report three steps done and hand the agent `/speckit.analyze`.

**The strict-mypy count is 40, not the 41 the issue states.** Both numbers are
correct — the fix in this PR removes one `no-any-return` finding, and the issue
counted before it. The distinction is worth keeping straight: 41 is a
measurement taken on the old tree, and "the count drifts with the code" is the
claim, which is why the corrected `AGENTS.md` sentence names the command instead
of either number.

**The branch was rebased onto current `main` before opening.** It was cut from
`cef6d5b`, two features back, and carried a `chore(lock)` commit whose one-line
change `main` already had by another route. The rebase dropped that commit as
already applied and left the two commits here. The panel reviewed the same
content under its pre-rebase hashes; `uv run wfctl verify` was re-run afterwards
and records 3 of 3 at the rebased tip.
