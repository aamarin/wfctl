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

- `wfctl/_paths.py:284` `touched_on_this_branch` answers "does the change under
  review add or modify anything under `path`", returning `None` when git cannot
  answer. `wfctl/cli.py:992` already asks it of a level-2 declaration, for the
  same reason this record exists.
- `_trunk_branch` (`wfctl/_paths.py:84`) falls back to a local `main`, `master`
  or `dev` when the remote publishes no `origin/HEAD`, and
  `touched_on_this_branch` reads `git status --porcelain` before any diff. A
  branch with no remote and no commits of its own is answered by both.
- `git ls-files --error-unmatch` on a file staged and never committed exits 0.
  Reproduced in a scratch repository.
- `git cat-file -e HEAD:<path>` on a file committed and then edited exits 0. It
  answers about the path, not about what the tree holds.
- `git diff --quiet HEAD -- <path>` on a file never staged at all exits 0.
  Ordinary diffs omit untracked files, so the record compares equal to nothing.
  Reproduced; the two commands are blind in opposite directions and only their
  conjunction is the property.
- `git commit -m <msg>` writes the whole index, so a path staged before the
  design session began lands in the record's commit. `git commit -- <path>`
  commits that path and leaves the rest staged. Reproduced both ways.
- `git rev-parse --show-toplevel` prints `not a git repository (or any of the
  parent directories)` where there is no repository, `not a git repository:
  /nonexistent` for a `.git` file naming a gitdir that is gone, and `this
  operation must be run in a work tree` in a bare repo. Only the first is the
  absence of a repository; the substring `not a git repository` matches two of
  the three.
- `touched_on_this_branch` returns False for a record committed on the trunk
  itself, because `trunk...HEAD` is empty there. Reproduced.
- `~/Development/wfctl-specs` is a checkout of this repository on `specs-trunk`,
  carrying 46 feature directories that have never been committed.
- `wfctl arch-root` already prints `⚠ Root is outside the working tree` under an
  override. The warning is on the resolver, so it fires whether or not a record
  is being written and says nothing about whether one landed.
- `wfctl/cli.py:303` already claims "#121 item 3 guarantees every such record
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
writing and committing the record. It refuses on one thing only — the record is
outside this working tree, or is not committed as it stands — and reports the
rest.

Two questions in the order a reviewer meets them. Is the file committed and
unmodified here, which is the property itself — `git cat-file -e HEAD:<path>` and
`git diff --quiet HEAD -- <path>`, both, because the first says nothing about
what the tree holds and the second omits untracked files entirely. Then, for the
report
rather than the verdict, does the change under review add it —
`touched_on_this_branch`, its three states honoured as three, per the rule
`design_block` already states: block only on evidence. (Written when that
rule lived in `design_gate`'s caller; `promised-evidence-blocks-on-silence`
now names it and `blocks` applies it.)

A project with no git at all exits 0 and is told so. A repository git cannot
read — a broken gitdir, a bare repo, `safe.directory` refusing the tree — is
refused, with git's own sentence repeated. Telling those apart is the command's
work rather than the reader's, and it is why the exemption keys on git's
parenthetical rather than on the sentence containing it.

It wraps `touched_on_this_branch` rather than reimplementing it. What it adds is
the committed-as-it-stands test, which that function does not carry and should
not: its existing caller writes a declaration and asks immediately, where
uncommitted is the expected state.

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
- `git cat-file -e HEAD:<path>` inside the command — the second shape, and the
  fix for the first. It answers about the path rather than about the tree, so a
  record committed once and edited since passed while `touched_on_this_branch`
  returned True *because* the file was dirty. The two checks cancelled, which is
  the failure a second reviewer is for.
- `git diff --quiet HEAD -- <path>` alone — the third shape, and the fix for the
  second. Diffs omit untracked files, so a record written and never staged
  compared equal to nothing and passed: the plainest form of the failure the
  command exists to catch, reaching a pull request past two panels that had each
  tested a *staged* record and neither an untouched one. The two commands are
  kept together rather than one replacing the other.
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

The exemption for a project without git keys on an English sentence git prints.
A translated git costs a false refusal, never a false pass, which is the
direction chosen deliberately: an unrecognised message is refused.

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
- 2026-09-07  revised   — a second panel, run over the first revision because
  that commit had never been reviewed, found the replacement wrong in three more
  states: a record edited after its commit, a repository git cannot read, and a
  branch that is itself the trunk. Each is now a test.
- 2026-09-08  revised   — an automated reviewer on the pull request found the
  fix for the first of those had opened a fourth: a record never staged at all
  passed, because diffs omit untracked files. Four shapes of this check have now
  been wrong in four directions, and each was found by a different reader. That
  is the argument for it being a command rather than a line of git in a skill,
  and the reason the two git calls are kept together rather than one replacing
  the other.
