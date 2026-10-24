---
status: proposed
---

# The worktree guard hook also runs the review check

## Context

The accepted record on review coverage has an agent hook that wfctl installs.
The hook refuses to open or merge a pull request while the branch has commits
that no review covered. After three rounds, a person can sign off on the
remaining commits, and the hook then allows the pull request. The agent
shouldn't sign off, so the same hook refuses the sign-off command when the agent
runs it.

wfctl already installs a hook that runs before every shell command the agent
runs: the worktree guard. Every one of those commands pays for the guard,
including the many that could never trip it. Its cost has been measured and cut
before.

The proposed record on managed hooks says each wfctl feature on an event gets
its own hook entry. It rejects combining two features into one entry, because
on the `Stop` event the shared `|| true` hid one feature's failure, and the two
features had to merge their output into one JSON object.

## Verified

- `cli.py`, `MANAGED_HOOKS` holds one `PreToolUse` row, `GUARD_HOOK_COMMAND`,
  which runs `wfctl hook worktree-guard`. The comment above it reads "No
  `|| true` here, unlike `Stop`. A non-zero exit on `PreToolUse` is the guard
  refusing the call."
- The `_hook.py` docstring says the guard took 81.7 ms per call before the fast
  path, and that "27.1 ms of interpreter startup ... is the floor for a hook
  spawned per Bash call".
- `_entry.py` sends the exact arguments `hook worktree-guard` to
  `_hook.worktree_guard` without importing `typer` or `rich`.
- `_hook.worktree_guard` returns 0 right away for a command with no `/` in it.
  `gh pr create` has none, so the review check has to run before that line.
- `_hook.worktree_guard` writes its refusal to stderr and returns 2, and it
  prints nothing when it allows a command. Piping an `ls` payload into
  `wfctl hook worktree-guard` printed nothing and exited 0.

## Assumed

- Every pull request in this repository is opened and merged with `gh`. A pull
  request opened through a GitHub plugin or a browser isn't checked. Every pull
  request so far used `gh`, and one opened another way would break this
  assumption.
- Matching each command against a short list of strings adds well under a
  millisecond. Nobody has measured it yet, and the verification below does.

## Direct baseline

The simplest approach adds a second `PreToolUse` row on `Bash` to
`MANAGED_HOOKS`, which runs a new `wfctl hook review-check` subcommand.
`_entry.py` gets a third exact argument list for its fast path. Each feature
has its own entry, its own process, and its own exit code, as the proposed
record on managed hooks describes.

## Decision

The review check runs inside `wfctl hook worktree-guard`, before the worktree
check. It looks for two kinds of command.

The first kind is judged against the branch's reviews:

1. `gh pr create`, and `gh pr new`, which is `gh`'s second name for it.
2. `gh pr merge`.
3. A `gh api` call to a pull request's `merge` or `merge-async` endpoint.

The second kind is refused every time, because the check can't tell which
branch it acts on, or because the agent shouldn't run it at all:

1. A `gh api` call that creates a pull request through the `pulls` endpoint.
2. A `gh api graphql` call naming `createPullRequest`, `mergePullRequest`,
   `enablePullRequestAutoMerge`, or `enqueuePullRequest`. The branch these act
   on sits in a request body the check can't read reliably, so the refusal
   tells the agent to use `gh pr create` or `gh pr merge` instead.
3. `gh pr merge --auto`, since GitHub would later merge a head the check
   never judged.
4. A command that names another repository, through `-R`, a
   `repos/<owner>/<repo>/` path, or an `owner:` prefix on `--head` naming
   another owner, since that repository's reviews aren't kept here.
5. A pull request command that follows another command in the same text, such
   as `git push && gh pr create`, or that holds a command substitution. The
   check reads the branch and its newest commit before any of the text runs,
   so an earlier commit, push, or `cd`, or one inside a substitution, would
   change what the pull request command acts on after the check judged it.
6. A pull request command with an environment prefix, such as `GIT_DIR=` or
   `GH_REPO=`, or run through `env`. The check's own `git` and `gh` calls
   don't see the prefix, so it would judge this branch while `gh` acts on
   another branch or repository.
7. A command the check can't read for sure: a `gh` command word that isn't
   written out plainly, such as `gh pr $(…) create` or `gh "$X" merge 630`, a
   `gh api` call that writes through a variable path, and a GraphQL query read
   from a file. An unplain command word is refused on its own, without one of
   the first kind matching, since a command like `gh "$X" merge 630` holds no
   verb the check can match. So is any flag before `gh`'s verb other than one
   plain `-R` naming `OWNER/REPO` or `github.com/OWNER/REPO`, such as
   `gh pr --squash=true merge 630`. `gh` accepts more spellings there than a
   list of refused ones keeps up with, so the check lists the one spelling it
   allows instead. The check matches the program name `gh` in any case, since
   macOS runs `GH pr merge 630` as `gh`. The word after `gh` has to be one of
   `gh`'s own commands, on a fixed list wfctl keeps, for the same reason: an
   extension such as `gh stack merge` merges pull requests, and every
   extension or shortcut a person installs adds a word the check has never
   seen. `copilot` and `agent-task` are left off the list, since each hands
   the request to another agent.
8. A command that acts on another branch's pull request, unless it runs in the
   checkout on the trunk branch. A worktree opens and merges only its own
   branch's pull request, and the person orchestrates from the trunk checkout.
9. The sign-off command.

The rule behind items 5 to 7 is that the check refuses a command whose text
shows it can't be sure what the command acts on. A gap is recorded as a known
limit instead when the command looks ordinary and what changes it lives
outside the text, such as GitHub's auto-merge when checks are pending.

A disguised command found after the fifth plan review is recorded as a known
limit too, such as `gh extension exec stack merge` or a two-word shortcut like
`gh pr ship 630`. We stopped adding rules there because six reviews in a row
each found more disguises, and the hook only sees a command's text. The
required CI check in #627 closes these gaps, since GitHub blocks the merge
itself however the command was typed. Until #627 ships, they stay open.

If a command matches none of them, it goes on to the worktree check with no
file read and no git call.

If a command matches the first kind, the review check reads each
group's last reviewed commit from the state directory and asks git for the
commits after it. Every group has to have reviewed the newest commit, so a fix
the code group commits after the security group's run is unreviewed for the
security group. If any group has unreviewed commits and no sign-off covers
them, the review check prints those commits to stderr, grouped by review group,
and returns 2.

The branch the review check judges is the one the command acts on, which isn't
always the branch the agent is on. When the command names another pull request
or branch, such as `gh pr merge 630`, the review check asks `gh` for that pull
request's branch. In the checkout on the trunk branch, it reads that branch's
state directory. Anywhere else, it refuses (item 8 above). It refuses when the
lookup fails, for the same reason it refuses an unreadable record. The
sign-off command is refused every time because the hook exists to stop the
agent from signing off.

The review check reads the branch, its newest commit, and the repository from
the session's working directory, which the hook payload names in `cwd`. The
worktree check already reads that field. The hook process itself runs in the
agent's project directory, and that differs from the session's directory once
an earlier command has run `cd`. If the review check read its own directory, a
session started in the `main` checkout could `cd` into another worktree and run
`gh pr create` there, and the check would judge `main` instead. A matched
command whose payload names no working directory is refused.

Each check runs in its own `try` block, so an error in one doesn't skip the
other. The worktree check allows a command when it can't decide, as it does
today. The review check refuses a pull request when it can't read the record,
or when any other error stops it once a command has matched, such as a failed
`git` call or a `gh` lookup that times out. We chose this because those
commands run only a few times per branch, and a wrong refusal costs one retry.
A sign-off doesn't get past an error, since the error stops the check either
way. So the refusal names the error and says that a person can run the same
command in their own terminal, where the hook doesn't run. A branch with no review history isn't this case. No review has
run on it, so the branch is unreviewed, and the review check refuses it for that
reason. The record is unreadable only when a file was half-written, which is
rare enough that the choice costs almost nothing.

## Diagram

```
             baseline                                  decision

          ┌──────────────┐                          ┌──────────────┐
          │ Claude Code  │                          │ Claude Code  │
          └──┬────────┬──┘                          └──────┬───────┘
     spawns  │        │ spawns                     spawns  │
═══ install-modes: wfctl owns its rows in settings.json ═══╪═══════════════
             │        │                                    │
   ┌─────────▼───┐ ┌──▼────────────┐            ┌──────────▼──────────┐
   │ worktree-   │ │ review-check  │ (new)      │ worktree-guard      │
   │ guard       │ │               │            │  review check (new) │
   └─────────────┘ └──────┬────────┘            │  worktree check     │
                          │ reads               └──────────┬──────────┘
                   ┌──────▼────────┐                       │ reads, on a match
                   │ state dir     │            ┌──────────▼──────────┐
                   └───────────────┘            │ state dir           │
                                                └─────────────────────┘
```

The line marks the existing rule that wfctl owns only the rows it writes into
`settings.json`. In the baseline, Claude Code starts two processes before every
shell command, so every command pays the 27 ms startup cost twice. In the
decision, Claude Code starts one process, and the review check adds a string
match. The decision has one row and one process fewer. Adding a fifth command
to check means changing one list in either graph.

## Considered

- A second hook entry and subcommand, as the direct baseline describes. We
  didn't choose this because it doubles the startup cost on every shell command
  the agent runs. The proposed record on managed hooks argues for one entry per
  feature, but neither of its two problems applies here:
  1. Neither check swallows the other's exit code, since `PreToolUse` uses no
     `|| true`. Both refuse with exit code 2 and a message on stderr.
  2. Neither check writes JSON to stdout, so there is no output to merge.
- A git `pre-push` hook. The accepted record already rejects this, because an
  agent can skip it with `--no-verify`.
- An instruction in the `opening-a-change` skill. The accepted record already
  rejects this, because it runs only when the agent follows it.

## Consequences

- The hook's name, `worktree-guard`, no longer describes everything it checks.
  The name is written into every consumer's `settings.json`, so renaming it
  would break those files, and the name stays.
- The two checks share a process. A crash outside both `try` blocks, such as a
  payload that isn't valid JSON, skips both. The guard already reads every
  payload field defensively for that reason.
- A pull request opened without `gh` isn't checked, and neither is one opened
  by an agent without hooks or through a disguised command the review check
  doesn't read. The follow-up issue on a required CI check covers all three.
- A command that only mentions `gh pr create`, such as an `echo`, is refused on
  an unreviewed branch. The refusal lists the commits, so the cost is one
  confusing message.

## Verification

- A test pipes a `gh pr create` payload into the guard on a branch with an
  unreviewed commit, and checks for exit code 2 and the commit on stderr. The
  same test on a fully reviewed branch checks for exit code 0 and no output.
- A test pipes the sign-off command into the guard and checks for exit code 2.
- A test pipes a `gh pr create` payload whose `cwd` is a different worktree
  from the hook's own directory, and checks that the `cwd`'s branch is judged.
- A test pipes a `gh pr create` payload into the guard with an unreadable
  record, and checks for exit code 2.
- A measurement of the guard on an `ls` payload, before and after this change,
  shows the added cost per call. The `_hook.py` docstring has the earlier
  numbers to compare against.

## Log

- 2026-10-21  proposed  — #622 level 3. Andre asked whether this added a hook on
  every prompt and cost tokens, and approved it once it ran inside the existing
  guard. He then approved refusing a pull request when the record can't be read.
- 2026-10-22  proposed  — #622 clarify. Andre chose that every group has to
  review the newest commit, and that a command naming another pull request is
  judged against that pull request's branch.
- 2026-10-23  proposed  — #622 plan review. The command list now matches the
  plan: `gh pr new`, the `merge` endpoint, and a second kind refused every
  time, which adds the create and GraphQL calls, `--auto`, another
  repository, and a chained pull request command. Andre approved folding in
  the second review's findings.
- 2026-10-23  proposed  — #622 plan review. A command substitution in a pull
  request command, and a `--head` owner other than this checkout's, join the
  second kind. Andre approved fixing the third review's findings without a
  fourth review.
- 2026-10-23  proposed  — #622 plan walkthrough. An environment prefix, a
  command the check can't read for sure, and another branch's pull request
  outside the trunk checkout join the second kind. The error refusal names the
  person's own terminal as the way past a broken check. Andre set the rule
  that a command the check can't read is refused rather than recorded.
- 2026-10-23  proposed  — #622 plan review. The review check reads the
  session's working directory from the payload, and an unplain `gh` command
  word is refused without another match. Andre approved fixing the review's two
  MAJOR findings.
- 2026-10-23  proposed  — #622 plan review. A flag before `gh`'s verb is
  refused unless it is one plain `-R`. Andre approved allowing that one
  spelling rather than refusing a list, after three reviews in a row each
  found one more spelling the list missed.
- 2026-10-23  proposed  — #622 plan review. The program name `gh` matches in
  any case, and an `-R` host other than `github.com` refuses. Andre approved
  fixing the fourth review's two findings.
- 2026-10-24  proposed  — #622 plan review. The word after `gh` has to be one
  of `gh`'s own commands, which refuses extensions and shortcuts, and a
  `gh api` create is read in every body-flag spelling `gh` accepts. Andre
  approved allowing a fixed list of commands, at the cost of running
  extensions in his own terminal.
- 2026-10-24  proposed  — #622 plan review. The review check stops adding
  rules. The sixth review's findings are recorded as known limits that the
  required CI check in #627 closes, including a two-word `gh alias set`
  shortcut. Andre approved this after six reviews in a row each found more
  disguised commands.
