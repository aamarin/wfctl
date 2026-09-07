---
status: proposed
---

# Whether a record reached the reviewer is one command, asked after it is committed

## Context

A level-3 record only works if a reviewer opening the branch reads it. Nothing
enforced that. `arch_root` is overridable — `WFCTL_ARCH_DIR`, then this repo's
manifest, then the main checkout's — so a record can be written to a directory
the branch does not carry, and the session reports success either way.

The pressure is that the question has three independent ways to fail and they do
not share an answer. A record can be outside this working tree, inside it and
ignored, or tracked and never committed. Each is silent, and a check that covers
two of the three is the same defect narrowed.

`a-rule-is-expressed-as-a-check` constrains the form and is not restated here.

## Verified

- `wfctl/_paths.py:283` `touched_on_this_branch` answers "does the change under
  review add or modify anything under `path`", returning `None` when git cannot
  answer. `wfctl/cli.py:992` already asks it of a level-2 declaration, for the
  same reason this record exists.
- `_trunk_branch` (`wfctl/_paths.py:84`) falls back to a local `main`, `master`
  or `dev` when the remote publishes no `origin/HEAD`, and
  `touched_on_this_branch` reads `git status --porcelain` before any diff. A
  branch with no remote and no commits of its own is answered by both.
- `git ls-files --error-unmatch` on a file staged and never committed exits 0.
  Reproduced in a scratch repository; `git cat-file -e HEAD:<path>` exits 128 on
  the same file.
- The same command exits 128 both for a path outside the repository and for a
  directory in no repository at all. Reproduced against
  `~/Development/wfctl-specs` and against a plain directory.
- `~/Development/wfctl-specs` is a checkout of this repository on `specs-trunk`,
  carrying 46 feature directories that have never been committed.
- `wfctl arch-root` already prints `⚠ Root is outside the working tree` under an
  override. The warning is on the resolver, so it fires whether or not a record
  is being written and says nothing about whether one landed.
- `wfctl/cli.py:302` already claims "#121 item 3 guarantees every such record
  lands in the branch diff" while excluding `design/` from the level-2 gate.
  That comment shipped before anything guaranteed it.

## Assumed

- Skill prose is enough to make the command run. Falsified by a session that
  writes a record and never calls it; no test can see that from outside.
- Committing a record before the design is approved is acceptable. Records land
  `proposed` and are superseded rather than deleted, so a rejected direction
  leaves an argument rather than a claim. Falsified by a repo that treats any
  commit as a claim about direction.

## Direct baseline

Resolve `arch_root`, compare it against the repository root, and run
`git check-ignore` on the target. Three string comparisons and one plumbing
command, all before the record is written, all in the skill's prose.

## Decision

`wfctl arch check <path>` answers the question, and the skill calls it after
writing and committing the record. The command asks the three failures
separately: outside this working tree, not part of the change under review, or
never reached a commit. A directory in no git repository at all exits 0 with a
line saying there is no review to reach.

It wraps `touched_on_this_branch` rather than reimplementing it. The one thing it
adds is the commit test, which that function does not carry and should not: its
existing caller writes a declaration and asks immediately, where uncommitted is
the expected state.

## Diagram

```
          baseline                          decision

stable    ┌────────────────┐                ┌────────────────────┐
          │ arch_root      │                │ arch_root          │
          │ resolution     │                │ resolution         │
          └────────────────┘                └────────────────────┘
                 │ reads                      ▲ reads
════ tool / agent ═══════════════════════════ │ ═══════════════════
                 ▼                            │
volatile  ┌────────────────┐                ┌─┴──────────────────┐
          │ path compare   │                │ wfctl arch check   │
          │ ignore check   │                │  in tree?          │
          └────────────────┘                │  on this branch?   │
                 │ permits                  │  in HEAD?          │
                 ▼                          └────────────────────┘
          ┌────────────────┐                         ▲ calls
          │ write record   │                ┌────────┴───────────┐
          └────────────────┘                │ write, then commit │
                                            └────────────────────┘
```

The boundary is the same one and it is already in force: the tool resolves, the
agent acts. The two sides differ in which of them holds the question. The
baseline leaves it in prose on the agent's side, where three proxies have to be
interpreted before the file exists. The decision moves it across to the tool,
where it is asked of the file after it exists — and the arrow reverses, because
the agent now calls the tool rather than reading a value out of it.

## Considered

- A path comparison plus an ignore check, before the write (the baseline) — it
  passes for a second checkout of the same repository on a branch that never
  merges, which is the exact shape this repository has. Reading
  `git check-ignore` as proof a path is untracked is also a mistake with a cost
  already paid here.
- `git ls-files --error-unmatch` in the skill's prose, with no command — the
  first shape of this decision, and rejected by a review panel that found it
  wrong twice. It reads the index, so a staged record passes; and its 128 covers
  both a path outside the repository and no repository at all, so the exemption
  for a project without git could fire for the failure it exempts nothing from.
- `wfctl start` refusing to begin a session — sound, and it buys failure at turn
  zero instead of after the design. Lost on the same predicate as the baseline:
  before the record exists there is nothing to ask git about. Recorded as dropped
  in `declarations/121-level3-records-in-pr.md`.
- A `PreToolUse` hook blocking the write — enforces rather than instructs, which
  is the one thing prose cannot do. Lost on reach: hooks land in one agent's
  config, and `no-hardcoded-agent` is in force because wfctl ships to more than
  one. It remains the only mechanism that would close the gap named in `Assumed`.

## Consequences

Two answers to this question no longer ship. The cost is a command whose name
invites the schema validation #121 puts out of scope — `arch check` reads a
record's *placement* and never its contents, and widening it is where that line
gets crossed.

The check runs on the artifact rather than on the intent, so it cannot be
satisfied by an agent that meant well. It can still be skipped by one that does
not call it, and nothing downstream would say so.

A record is now committed before the design it argues for is approved. That
ordering is deliberate — the record is what the implementation is written
against — and it means a branch carries a docs commit before its first
implementation commit.

## Verification

`tests/test_arch_check.py` covers the four states, two of them written as the
mistakes the rejected command makes: a staged record fails, a record in a second
checkout fails, a directory with no repository passes.

`test_the_design_record_skill_asks_git_whether_the_record_landed` pins that the
skill names the command rather than any line of git.
`test_brainstorm_orders_the_records_before_the_one_pager` and
`test_brainstorm_allows_the_commands_its_records_need` pin the order and the
`allowed-tools` entries without which the prose reads correctly and cannot run.

The check is demonstrated by this record: `wfctl arch check` on this path exits
0, and did so only after the file was committed.

## Log

- 2026-09-07  proposed  — written while deciding it, as the first exercise of
  the path #121 builds.
- 2026-09-07  revised   — a review panel found the first version's check wrong
  in both directions and named an existing function that already answered it.
  The decision now wraps that function; `Considered` carries the rejected shape
  rather than the corrected argument replacing it.
