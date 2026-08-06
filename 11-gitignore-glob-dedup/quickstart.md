# Quickstart: verifying the gitignore glob dedup

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

The bug's signature is a diff that keeps coming back, so the verification that
matters is "run it twice and look at the file".

## Automated

```bash
uv run pytest tests/test_install_skills.py tests/test_install_config.py
```

Then the full suite, to catch anything the boolean return touched:

```bash
uv run pytest
```

## Manual — the one that proves it

From this worktree, with a clean tree:

```bash
git status --short          # expect: clean (or only your own edits)
wfctl install-skills
git diff .gitignore
```

**Expected**: exactly one added line, `.wf-skills-backup/`, plus a dim notice
reporting that 83 entries were already covered. Skipped plus written should
equal the 84 entries an install considers.

**Before the fix**, the same command adds 83 lines — every entry except the
install record, which is the only one a literal comparison catches. All 83 are
redundant with the `.agents/`, `.claude/`, and `.specify/` patterns already in
the file.

Run it a second time without committing:

```bash
wfctl install-skills
git diff .gitignore
```

**Expected**: still one added line. The second run appends nothing, because
`.wf-skills-backup/` is now present and the exact-match path in the guard
catches it.

## Confirming *why* a path was skipped

No wfctl-specific tooling — git answers directly (SC-005):

```bash
git check-ignore -v --no-index .agents/skills/start-session
```

```
.gitignore:12:.agents/	.agents/skills/start-session
```

Read as `source:line:pattern<TAB>path`. A path that is not covered prints
nothing and exits non-zero.

## Cleanup

`.wf-skills-backup/` is the one legitimate new entry — commit it. That is the
last time this repository's `.gitignore` should change from an install until a
new top-level install root appears.

```bash
git add .gitignore && git commit -m "chore: gitignore the wf-skills backup dir"
```

## Checking the performance budget (SC-006)

Only relevant if you are revisiting the deferred batching decision:

```bash
time wfctl install-skills
```

The coverage check should account for ~1 s of the total. If the clone has been
removed (issue #1) and install is now dominated by this, the `ponytail:` marker
in `_ensure_gitignored` names the replacement.
