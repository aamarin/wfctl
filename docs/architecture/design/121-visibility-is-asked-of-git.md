---
status: proposed
---

# Whether a record reached the reviewer is asked of git, once, after it is written

## Context

A level-3 record only works if a reviewer opening the branch reads it. Nothing
enforced that. `arch_root` is overridable — `WFCTL_ARCH_DIR`, then this repo's
manifest, then the main checkout's — so a record can be written to a directory
the branch does not carry, and the session reports success either way.

The pressure is that every property available *before* the write is a proxy.
Where the directory sits, whether an ignore rule matches it, whether it looks
committed: each has to be interpreted, and each can be true while the reviewer
still sees nothing.

`a-rule-is-expressed-as-a-check` constrains the form and is not restated here.

## Verified

- `git ls-files --error-unmatch docs/architecture/design/122-a-record-persists-no-routing-state.md`
  exits 0 in this worktree.
- The same command on a file inside `~/Development/wfctl-specs` exits 128 —
  that directory is a checkout of this same repository, on `specs-trunk`.
- `git -C ~/Development/wfctl-specs rev-parse --show-toplevel` prints that
  directory, and `remote -v` prints this repository's URL. It is a git
  repository, its files are not ignored, and 46 of its feature directories have
  never been committed.
- `git diff --name-only origin/main...HEAD` printed nothing on this branch
  before its first commit, so a diff-membership question is empty for a branch
  that has not committed yet.

## Assumed

- Skill prose is enough to make the check run. Falsified by a session that
  writes a record and does not run it; no test can see that from outside.
- Committing a record mid-design is acceptable in a consumer repo. Falsified by
  a repo whose hooks reject a docs-only commit, or that forbids commits before
  a review.

## Direct baseline

Resolve `arch_root`, compare it against the repository root, and run
`git check-ignore` on the target. Three string comparisons and one plumbing
command, all before the record is written, all in the skill's prose.

## Decision

The skill writes the record, commits it, then runs
`git ls-files --error-unmatch <path>`. Exit 0 is the answer; any other exit
means the record has to move before the design continues. A project with no git
gets the record and a line saying there is no branch to carry it.

## Diagram

```
          baseline                          decision

stable    ┌──────────────┐                  ┌──────────────┐
          │ arch_root    │                  │ arch_root    │
          │ resolution   │                  │ resolution   │
          └──────────────┘                  └──────────────┘
                 │ reads                           │ reads
════ tool / agent ═══════════════════════════════════════════════
                 ▼                                 ▼
volatile  ┌──────────────┐                  ┌──────────────┐
          │ path compare │                  │ write record │
          │ ignore check │                  └──────────────┘
          └──────────────┘                         │ commits
                 │ permits                         ▼
                 ▼                          ┌──────────────┐
          ┌──────────────┐                  │ git ls-files │
          │ write record │                  └──────────────┘
          └──────────────┘
```

Both sides read the same resolved root across the same boundary, which is
already in force — the tool resolves, the agent acts. They differ in what the
agent asks and when. The baseline asks three questions about a path before the
file exists, and each answer is a prediction. The decision asks one question
about the file after it exists, and the answer is the property itself.

## Considered

- A path comparison plus an ignore check, before the write (the baseline) — it
  passes for a second checkout of the same repository on a branch that never
  merges, which is the exact shape this repository already has. Reading
  `git check-ignore` as proof a path is untracked is also a mistake with a cost
  already paid here.
- `wfctl start` refusing to begin a session — sound, and it buys failure at turn
  zero instead of after the design. Lost on the same predicate as the baseline:
  before the record exists there is nothing to ask git about, so it can only
  check a proxy. Recorded as dropped in
  `declarations/121-level3-records-in-pr.md`.
- A `PreToolUse` hook blocking the write — enforces rather than instructs, which
  is the one thing prose cannot do. Lost on reach: hooks land in one agent's
  config, and `no-hardcoded-agent` is in force because wfctl ships to more than
  one.
- Asking whether the record is in the branch's diff against its base — the same
  question, one indirection worse. It needs the base branch, a remote, and a
  branch that is not the base, and it answers empty for a branch with no commits
  of its own.

## Consequences

The check cannot be skipped by accident, because it runs on the artifact rather
than on the intent — but it can be skipped by an agent that does not run it, and
nothing downstream would say so. It also moves a commit earlier than the code it
explains, so a branch carries a docs commit before its first implementation
commit. That ordering is the record being written against the implementation
rather than after it, which is the intent.

## Verification

`test_the_design_record_skill_asks_git_whether_the_record_landed` pins the
literal command in the skill. `test_brainstorm_orders_the_records_before_the_one_pager`
pins that records precede the one-pager that lists them, and
`test_brainstorm_allows_the_commands_its_records_need` pins the `allowed-tools`
entries without which the prose reads correctly and cannot run.

The check itself is demonstrated by this record: it was written, committed, and
`git ls-files --error-unmatch` on this path exits 0.

## Log

- 2026-09-07  proposed  — written while deciding it, as the first exercise of
  the path #121 builds.
