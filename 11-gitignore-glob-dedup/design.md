# Glob-aware `.gitignore` dedup for `install-skills`

Issue: #11 — *install-skills appends .gitignore lines already covered by an existing glob*

## Problem Statement

How might we stop `install-skills` from re-dirtying `.gitignore` on every run,
without giving up the review gate that a tracked `.gitignore` provides?

## Context

`install-skills` copies dozens of files into the repo (`.agents/`, `.specify/`,
and optionally an agent's own root). The README calls these regenerable install
artifacts, not project source, so each one gets an ignore rule —
`_ensure_gitignored` at `wfctl/cli.py:633`.

That guard is a literal string comparison:

```python
if line in text.splitlines():
    return
```

It cannot see that a glob already covers the path. This repo's committed
`.gitignore` has `.agents/`, `.claude/`, `.specify/`, and
`.wf-skills-manifest.json` — yet an install still enumerates every path beneath
them, one line each.

Measured against the committed `.gitignore` in this worktree:

| | lines appended |
|---|---|
| base install (`.agents/` 48 + `.specify/` 8 + backup dir) | 57 |
| after a second run with `--agent claude` (`.claude/` 26 more) | **83** |
| of those, already covered by an existing glob | **82** |
| genuinely uncovered | **1** (`.wf-skills-backup/`) |

The 57 → 83 growth happened *during the session that wrote this spec*, with no
install invoked by hand — the `post_create` hook did it. That is the failure
mode in one line: the file grows on its own, and none of the growth is worth
committing.

The mechanism built to keep the working tree clean is now the only thing
dirtying it. `.workmux.yaml`'s `post_create` hook runs `install-skills` on every
worktree creation, so each new worktree starts with a modified `.gitignore`
before any work begins. The redundant lines are never worth committing, so they
are never committed, so the next worktree re-appends them.

The exact-match guard is not useless — it stops a literal repeat, which is why
`.wf-skills-manifest.json` (present in the committed file) is the one path that
was *not* re-appended. It just cannot see a glob.

## Recommended Direction

Replace the string comparison with git's own evaluation, and keep writing to
`.gitignore`.

```python
def _ensure_gitignored(repo_root: Path, line: str) -> None:
    """Append `line` to .gitignore unless git already ignores it (glob or literal)."""
    if subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", line],
        cwd=repo_root, capture_output=True,
    ).returncode == 0:
        return
    gi = repo_root / ".gitignore"
    text = gi.read_text() if gi.exists() else ""
    if text and not text.endswith("\n"):
        text += "\n"
    gi.write_text(text + f"{line}\n")
```

`check-ignore` matches patterns rather than probing the filesystem, so it works
for paths that do not exist yet — which is the case at install time for
everything being written fresh.

Three details beyond the snippet in issue #11, each found by probing real git
(2.44.0) rather than reasoning about the docs:

- **`--no-index`** — for a path tracked in the index, plain `check-ignore`
  returns 1 even when a pattern matches, because tracking wins over ignoring.
  Without the flag we would append a line that has no effect on a tracked file.
- **`capture_output=True`** — outside a git repo (or for a path above the root)
  `check-ignore` exits 128 and prints `fatal:` to stderr. Suppress it; a
  non-zero exit already means "not ignored", which is the correct fallback.
- **Non-zero means append** — this preserves today's behavior for a repo with
  no `.gitignore` at all: the file still gets created.

### Why `.gitignore` and not `.git/info/exclude`

The alternative considered — and rejected — was to stop writing to `.gitignore`
entirely and record the rules in `.git/info/exclude`, which is never committed
and shared by every linked worktree (verified: the common exclude applies across
all `wt/*`).

It was rejected because `.gitignore` being tracked is a feature, not the bug. A
change to it appears in `git status` and forces a decision. The problem was
never that the decision was surfaced — it was that the same worthless decision
was surfaced every single time.

With the guard in place, the steady state is:

| Event | Outcome |
|---|---|
| This repo, next install | one line: `.wf-skills-backup/` |
| Every worktree after that | clean — the existing globs cover all 82 paths |
| A new skill ships | covered by `.agents/` → nothing appended |
| A new top-level install root appears | one visible line, reviewed once |

That last row is a real change worth seeing. `.git/info/exclude` would have
suppressed exactly the notification worth keeping — and cost ~35 changed lines
instead of ~6.

Concretely, the uncovered roots today are `.wf-skills-backup/`, `.bob/`
(`--agent bob`), and `.github/skills/` (`--agent copilot`). Running
`--agent copilot` against this repo would append 25 lines, one per skill,
because `.github/skills/` matches nothing and `.github/` cannot be globbed
wholesale without swallowing the workflows. The guard surfaces that as a
decision instead of silently enumerating.

## Key Assumptions to Validate

- [ ] `git check-ignore -q --no-index <path>` returns 0 for a glob-covered
      non-existent path on every git in use. **Test:** verified manually on
      2.44.0; the new test suite pins it in CI.
- [ ] No caller depends on `_ensure_gitignored` appending unconditionally.
      **Test:** the four call sites (`cli.py:929`, `:930`, `:931-932`, `:1134`)
      all want "ensure ignored", not "ensure present in the file" — confirm by
      reading each, and by `test_gitignore_no_duplicate_when_present` still
      passing unchanged.
- [ ] Directory-form lines keep working. **Test:** `wt/` and
      `.wf-skills-backup/` return 0 with the trailing slash even when the
      directory does not exist on disk; without the slash they return 1. All
      call sites already pass the slash — assert this, do not assume it.

## MVP Scope

**In:**

- Swap the guard in `_ensure_gitignored` (`wfctl/cli.py:633`).
- Revert this worktree's `.gitignore` (`git checkout .gitignore`) in the same
  commit, so the 83 redundant lines go away with the code that produced them.
- Tests, replacing/extending `tests/test_install_skills.py:60` and keeping
  `tests/test_install_config.py:54` green:
  1. a path covered by an existing glob is not appended
  2. a path covered by nothing is still appended
  3. a repo with no `.gitignore` still gets one created
  4. `wt/` behaves as it does today (`install-config`)
  5. two installs against a clean tree leave `.gitignore` byte-identical

**Out:** everything below.

## Not Doing (and Why)

- **`.git/info/exclude`** — loses the review gate that makes a tracked
  `.gitignore` worth having. Fully explored and rejected above; recorded here so
  the reasoning is not re-derived later.
- **Pruning redundant lines already committed in consuming repos** — the
  manifest knows every path so it could, but rewriting someone's committed
  `.gitignore` can clobber a line a human wrote deliberately. Once the guard
  lands they are inert. A one-time manual trim, same call issue #11 made.
- **Adding broad globs to consuming repos' `.gitignore`** — that enumeration is
  deliberate where PFMS-authored files must stay tracked. Not wfctl's decision
  to make.
- **Making `uninstall-skills` remove ignore lines** — it does not today. The
  asymmetry is pre-existing, not a regression this change introduces, and
  removing a line a user may have since edited is worse than leaving it.
- **Touching `install-config`'s `wt/` call site** — same function, same file,
  and the guard's behavior there is unchanged. Note that `wt/` is currently in
  neither `.gitignore` nor any exclude file: the root checkout shows `?? wt/`
  untracked. That is a separate papercut, not this issue.

## Open Questions

- None blocking. `wt/` being untracked at the root checkout is worth a follow-up
  issue, but it is independent of this change.

## Verification

- **Automated:** `uv run pytest tests/test_install_skills.py tests/test_install_config.py`
- **Manual:** `wfctl install-skills` in this worktree, then `git diff .gitignore`
  — expect exactly one added line, `.wf-skills-backup/`, and none of the other 82.
- **Evidence:** `git check-ignore -v .agents/skills/start-session` resolves to
  the `.agents/` glob.

## Estimate

20–30 minutes. Six lines of implementation; the rest is tests.
