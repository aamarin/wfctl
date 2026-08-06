# Research: gitignore glob dedup

**Date**: 2026-08-04 | **Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Every question below was resolved by running git and reading its exit codes, not
by reading documentation. Git version under test: **2.44.0**. Probes ran with
`GIT_CONFIG_GLOBAL=/dev/null` so the developer's global excludes could not
silently satisfy a case.

---

## D1: How to determine whether a path is already ignored

**Decision**: `git check-ignore -q --no-index <path>`, exit 0 meaning covered.

**Rationale**: It evaluates the repository's whole ignore configuration —
`.gitignore` at any directory level, `.git/info/exclude`, and
`core.excludesFile` — with correct last-match-wins and negation semantics. It
matches patterns rather than probing the filesystem, so it answers for paths
that do not exist yet, which is the situation at install time for everything
being written fresh.

It also produces the attribution a developer needs, which is what lets the skip
report stay a bare count (FR-011) instead of duplicating an explanation:

```
.gitignore:12:.agents/     .agents/skills/start-session
.gitignore:14:.specify/    .specify/templates/spec-template.md
.gitignore:25:wt/          wt/
```

**Alternatives considered**:

- *Parse `.gitignore` and match patterns in Python.* Rejected. Correct gitignore
  semantics include directory-only patterns, `**`, negation, precedence by
  position, and per-directory files. Reimplementing that is a bug farm, and git
  already ships the answer.
- *`pathlib`/`fnmatch` glob comparison.* Rejected for the same reason, more so —
  `fnmatch` does not implement gitignore semantics at all.

---

## D2: `--no-index` or not

**Decision**: Use `--no-index`.

**Rationale**: Without it, a path already tracked in the index reports "not
ignored" even when a pattern matches, because tracking wins over ignoring. We
would then append a line that has no effect on a tracked file — noise that can
never do anything.

**Probe**:

```
== E: path already TRACKED in the index, pattern matches ==
  exit=1 : tracked/file.md                 # without --no-index
  --no-index exit=0 : tracked/file.md
```

Confirmed `--no-index` regresses none of the other cases:

```
no-index exit=1 : .agents/skills/foo        # no .gitignore at all
no-index exit=0 : .specify/templates/spec-template.md   # glob covers
no-index exit=1 : .agents/skills/i-have-adhd            # not covered
no-index exit=0 : wt/                       # dir-form, dir absent from disk
```

---

## D3: Suppressing git's own output

**Decision**: `capture_output=True`; treat any non-zero exit as "not covered".

**Rationale**: Outside a repository — reachable because `WFCTL_REPO_ROOT` can
point anywhere — `check-ignore` exits 128 and writes `fatal:` to stderr. Left
uncaptured that lands in the user's terminal mid-install. Treating non-zero as
"not covered" also gives the safe fallback required by FR-008: when in doubt,
write the line, which is exactly today's behavior.

**Probe**:

```
fatal: ../outside: '../outside' is outside repository at '/private/var/...'
  exit=128 : ../outside
  exit=128 stderr-suppressed        # with capture_output
```

---

## D4: Directory-form entries

**Decision**: No special handling. Every call site already passes the trailing
slash, and the probe confirms that is what makes them resolve.

**Rationale**: `wt/` and `.wf-skills-backup/` are written in directory form. The
trailing slash is load-bearing when the directory does not yet exist on disk:

```
== C: directory-form lines, dir does NOT exist on disk ==
  exit=0 : wt/            exit=1 : wt
  exit=0 : .wf-skills-backup/     exit=1 : .wf-skills-backup

== D: directory-form lines, dir DOES exist on disk ==
  exit=0 : wt/            exit=0 : wt
```

Both call sites (`cli.py:930`, `:1134`) pass the slash. The spec asserts this
rather than assuming it (Assumptions, third bullet).

---

## D5: Where the ignore entries belong

**Decision**: Keep writing `.gitignore`. Do not move to `.git/info/exclude`.

**Rationale**: `.git/info/exclude` was the initial recommendation — never
committed, invisible to `git status`, shared across every linked worktree
(verified: the common `.git/info/exclude` applies to all `wt/*`, and a linked
worktree's own git dir has no `info/`). It would make the churn structurally
impossible instead of merely rare.

It was rejected on the grounds that a tracked `.gitignore` **is** the review
gate. A change to it surfaces in `git status` and forces a decision. The defect
was never that the decision was surfaced; it was that the same worthless
decision was surfaced on every worktree creation.

The measurement that settled it: this repository's committed `.gitignore`
already carries `.agents/`, `.claude/`, `.specify/`, and
`.wf-skills-manifest.json`. Simulating the new guard against it, over the full
set of paths an install considers:

```
considered=84  skipped=83  written=1
  WOULD WRITE: .wf-skills-backup/
--- old guard (exact match) ---
old guard would append: 83
```

Per-path, on a representative sample:

```
  SKIP   .wf-skills-manifest.json             covered by  .wf-skills-manifest.json
  SKIP   .agents/skills/start-session         covered by  .agents/
  SKIP   .agents/commands/speckit.plan.md     covered by  .agents/
  SKIP   .claude/commands/brainstorm.md       covered by  .claude/
  SKIP   .specify/templates/spec-template.md  covered by  .specify/
  SKIP   .specify/scripts/bash                covered by  .specify/
  WRITE  .wf-skills-backup/                   no pattern matches
```

The first row is the only one today's guard catches — a literal match, which is
why the old guard appends 83 of 84 rather than all 84. The four glob-covered
rows are the defect.

So the guard alone reduces churn to one visible line per genuinely-new ignore
root — which is a change worth reviewing. Confirmed against two hypothetical
future roots: `.github/skills/start-session` (from `--agent copilot`) and
`.cursor/rules` both report WRITE, since nothing covers them. `.git/info/exclude` would have
suppressed precisely that notification, and cost roughly 35 changed lines
against the guard's 6.

**Alternatives considered**: a hybrid (`--shared-ignore` flag selecting the
target) was raised and dropped — two code paths and a flag to document, for a
choice with one right answer per repository.

---

## D6: Per-path versus batched checking

**Decision**: One `check-ignore` process per path, with the batched form
recorded as a deferred upgrade.

**Rationale**: Measured, not assumed:

```
paths=57
sequential subprocess total: 684 ms  (12.0 ms/call)
batched (--stdin) single call: 46 ms
```

Extrapolating to a full `--agent claude` install (83 entries): ~1.0 s versus
~46 ms. That 1 s sits inside `post_create`, but on top of a ~15 s network clone
the hook already performs — roughly 7% of the wait.

The deferral is recorded in the code as a `ponytail:` marker naming the cost,
the trigger, and the replacement, so it is auditable rather than rediscovered.

**Trigger**: issue #1 (*vendoring wf-skills instead of cloning at install
time*). If it lands, the clone disappears and this becomes roughly half of
install time rather than a small fraction. The batched form is cheap to reach
because `gitignore_targets` is already collected as a list at `cli.py:789`.

**Alternatives considered**: batching now. Rejected as premature against the
current cost profile, but the tests are written at behavior altitude so the
switch requires no test changes.

---

## D7: Does a line written mid-run affect later checks in the same run?

**Decision**: Yes, and the loop depends on it. No caching or in-memory tracking
is needed.

**Rationale**: Each `check-ignore` is a fresh process that reads `.gitignore`
from disk, so an entry written during iteration *N* is visible at iteration
*N+1*. This is what makes a duplicate inside the target list self-limiting — the
second encounter reports covered and writes nothing — and what makes the
repeated-install case byte-identical without any extra bookkeeping.

**Probe**:

```
== no .gitignore yet ==
  exit=1                                  # .wf-skills-backup/
== immediately after writing the line ==
  exit=0
== a second line appended, prior line still seen ==
  backup exit=0    agents exit=0
== duplicate path encountered again ==
  exit=0                                  # skipped, no duplicate written
```

**Alternatives considered**: tracking written lines in a Python set alongside the
file. Rejected — it would duplicate state git already holds, and would drift the
moment anything else touched the file.

---

## Evidence index

Probe scripts were written to the session scratchpad, not the repository. Their
outputs are transcribed above in full. To reproduce:

| Finding | Reproduce with |
| --- | --- |
| D1, D2, D4 | `git check-ignore -v --no-index <path>` in a repo with a covering pattern |
| D3 | `git check-ignore -q --no-index ../outside` from inside a repo |
| D5 | `git show HEAD:.gitignore` into a scratch repo, then check each installed path |
| D6 | time a loop of per-path calls against one `--stdin` call |
| D7 | write a line to `.gitignore`, then check the same path again |
