# Agent Brief: 11-gitignore-glob-dedup

**Issue**: #11 · **Step**: plan complete → `/speckit.tasks`
**Spec**: `specs/11-gitignore-glob-dedup/spec.md`

## What we're doing

`_ensure_gitignored` (`wfctl/cli.py:633`) dedups on an exact string match, so it
appends `.gitignore` lines a broader pattern already covers. Every worktree
creation runs `install-skills` via `post_create`, so every worktree starts with
a dirty `.gitignore` nobody wants to commit.

Swap the guard for `git check-ignore -q --no-index`. Add a boolean return so
the caller can report how many entries were skipped.

Measured: **84 entries considered, 83 already covered, 1 written**
(`.wf-skills-backup/`). Today's guard appends 83 of the 84 — it catches only the
install record, the sole path present as a literal. Do not confuse the 83
(today's diff size) with the 84 (the consideration set); an earlier draft did,
and SC-007's self-check did not sum.

## The change

- `wfctl/cli.py:633` — new guard, returns `True` if written
- `wfctl/cli.py:929-932` — loop the three call groups, count skips, print once
- `wfctl/cli.py:1134` — untouched (`install-config`'s `wt/`; bool is ignorable)
- `tests/test_install_skills.py` — 10 new tests
- `tests/test_install_config.py` — asserted unchanged; if it needs an edit, the
  guard broke something it shouldn't have

**T012 is the one test that defends `--no-index`.** If someone "simplifies" that
flag away, T012 is the only thing that fails. Do not delete it.

## Decisions already made — do not re-litigate

- **`.gitignore`, not `.git/info/exclude`.** Considered and rejected: a tracked
  ignore file is the review gate. Full reasoning in `research.md` §D5.
- **Per-path checking, not batched.** ~1.0 s vs ~46 ms, deliberate. Recorded as
  a `ponytail:` marker naming issue #1 as the trigger. `research.md` §D6.
- **`--no-index` and `capture_output` are load-bearing**, not stylistic.
  `research.md` §D2, §D3.
- **Skip report is a bare count**, no path list — git already attributes each
  one. Spec FR-011/FR-012.

## Constraints

- Tests assert on resulting `.gitignore` contents, never on how coverage was
  determined or how many subprocesses ran. A test that would break when
  switching to the batched form is testing the mechanism — rewrite it.
- Fail closed: if the check cannot run, write the line (FR-008).
- No output in the clean case (FR-012).

## Gotchas found by probing

- A tracked path whose pattern matches reports "not ignored" without
  `--no-index`.
- Outside a repo, `check-ignore` exits 128 and prints `fatal:` to stderr.
- Directory-form entries need their trailing slash: `wt/` resolves, `wt` does
  not, when the directory is absent from disk.
- `import subprocess as sp` goes inside the function — repo convention
  (`cli.py:295`, `:695`).

## Open, not blocking

- `wt/` was in neither `.gitignore` nor any exclude file. Fixed on this branch
  in commit `7cc1005`, separate from #11's code change.
- The shipped speckit templates assume the pfms stack (TypeScript, ZenStack,
  Prisma, pnpm). Both `spec.md` and `plan.md` needed sections replaced rather
  than filled. Worth an issue against wf-skills.
