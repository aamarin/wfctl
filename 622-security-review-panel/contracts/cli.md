# CLI contract: review commands and the guard's review check

Every command runs from inside the repository and acts on the current branch.
Output below is with `NO_COLOR` set. Paths are shortened to `<state>`.

## `wfctl review groups`

Prints the groups in run order, one per line, with the skill each runs and its
reviewers. Exit 0, or 1 with the `check config` findings when `review` is
invalid.

```text
security  reviewing-security  s1 s2 s3 claude
code      code-review         c1 c2 c3 claude
```

## `wfctl review start <group>`

Writes the next run record for `<group>` and prints what the coordinator needs
to launch the reviewers.

```text
security run 003 · 2 commits since a1b2c3d · head 9f8e7d6
reports: <state>/reviews/security/runs/003/
s1 claude
s2 claude
s3 codex  codex exec --sandbox read-only
s4 codex  codex exec --sandbox read-only
```

When a model's command isn't on `PATH`, its reviewers are left out and one
line says so:

```text
s3 codex  ✗ unavailable
s4 codex  ✗ unavailable
⚠ codex: `codex` not found on PATH; s3 and s4 left out of this run
```

| Case | Output | Exit |
| --- | --- | --- |
| commits to review | the block above | 0 |
| every reviewer unavailable | the block above, then `⚠ no reviewer in security can run; the run can't complete until one can, or a person signs off` | 0 |
| nothing since the last reviewed commit | `security is up to date at 9f8e7d6` | 0 |
| no trunk branch found | `✗ can't find the trunk branch; set trunk in wfctl.json` | 1 |
| the clone is shallow | `✗ this clone is shallow, so wfctl can't see every commit on the branch; run git fetch --unshallow` | 1 |
| unknown group | `✗ no review group named 'x'`, then the group list | 1 |
| invalid `review` config | the `check config` findings | 1 |

## `wfctl review check <group>`

Judges the latest run's reports, prints the roster, and completes the run when
every expected reviewer has a counted report.

```text
security run 003 · head 9f8e7d6
s1 claude ✓
s2 claude ✓ relayed: write denied
s3 codex  ✓ relayed: read-only sandbox
s4 codex  ✗ names 5c4b3a2, not 9f8e7d6
incomplete: 1 of 4 expected reports missing
```

| Case | Last line | Exit |
| --- | --- | --- |
| every expected report counts | `complete: security reviewed through 9f8e7d6` | 0 |
| the run completed earlier, and a report no longer counts | `complete: security reviewed through 9f8e7d6`, then `⚠ 1 report no longer counts since the run completed at <time>` | 0 |
| any expected report missing or not counted | `incomplete: N of M expected reports missing` | 1 |
| no reviewer in the run could run | `incomplete: no reviewer in security could run` | 1 |
| no run started | `✗ security has no run; run wfctl review start security` | 1 |

A run stays complete once it completes. The last reviewed commit has already
moved, so calling the run incomplete again would contradict the record the next
run starts from.

The reason on a ✗ line is one of: `no report`, `names <sha>, not <head>`,
`no Reviewed: line`, `no verdict at the end`, `can't read report: <error>`,
`unavailable: <reason>`.

## `wfctl relay <id> --reason TEXT --from PATH`

Reads a report from the file `--from` names and saves it as `<id>.md` in the
latest run of the group `<id>`'s letter names, with the `Relayed:` header. It
never reads stdin, so a report can't travel in the command's text, where the
guard would match the commands it quotes (`research.md` R8).

| Case | Output | Exit |
| --- | --- | --- |
| saved | `✓ s2 relayed: write denied` | 0 |
| `--reason` missing or blank | `✗ a relay needs --reason saying why the reviewer couldn't write` | 1 |
| `--from` missing | `✗ a relay needs --from naming the file that holds the report` | 1 |
| the file doesn't exist or can't be read | `✗ can't read <path>: <error>` | 1 |
| the file is empty | `✗ <path> is empty; nothing to relay for s2` | 1 |
| id not in the latest run | `✗ s9 isn't a reviewer in security run 003` | 1 |
| a report already exists for the id | `✗ s2 already has a report in run 003` | 1 |

A relayed report is judged like any other. One that names an older commit
doesn't count.

## `wfctl review sign-off`

Records a person's sign-off on the current head and lists what it covers. It
lists the commits first, then asks for the head's short sha.

```text
security  5c4b3a2 fix(release): check the tag body
security  9f8e7d6 test: cover an empty note
code      9f8e7d6 test: cover an empty note
Type 9f8e7d6 to sign off on these commits: 9f8e7d6
✓ signed off through 9f8e7d6
```

| Case | Output | Exit |
| --- | --- | --- |
| the person types the sha | the block above | 0 |
| anything else typed | `✗ not signed off; nothing written` | 1 |
| stdin or stdout isn't a terminal | `✗ wfctl review sign-off needs a person at an interactive terminal` | 1 |
| nothing to cover | `nothing unreviewed; no sign-off needed` | 0 |

The guard also refuses this command from an agent. The terminal check is a
second obstacle for a spelling the guard's pattern misses, not enforcement,
since a pseudo-terminal satisfies it (`research.md` R9).

## Guard: `wfctl hook worktree-guard`

The review check runs first, inside the same process, in its own `try` block.

| Command the agent runs | Judged branch | Result |
| --- | --- | --- |
| holds none of `gh`, `merge`, `sign` | none | goes on to the worktree check, no file or git read |
| `gh pr create`, every group reviewed | current at `HEAD` | exit 0, nothing printed by the review check |
| `gh pr create`, a group has unreviewed commits | current at `HEAD` | exit 2, refusal below |
| `gh pr create --head 630-x`, run on `630-x` or on the trunk branch | `630-x` at GitHub's commit for it | exit 0 or 2 by that branch's records |
| `gh pr create --head <this owner>:630-x` | `630-x` at GitHub's commit for it | as `--head 630-x`; the owner matches, so the prefix is dropped |
| `gh pr create --head forkowner:630-x` | none | exit 2, `--head names another owner's branch; its reviews aren't here` |
| `gh pr merge 630`, `gh pr merge --squash 630`, run on PR 630's head branch or on the trunk branch | PR 630's head branch at `headRefOid` | exit 0 or 2 by that branch's records |
| `gh pr merge 630` or `gh pr create --head 630-x`, run on any other branch | PR 630's head branch, or `630-x` | exit 2, `run this from the checkout on main; a worktree opens and merges only its own branch's pull request` |
| `gh pr new --fill` | current at `HEAD` | as `gh pr create` |
| `gh pr merge -s 630`, `gh pr merge --subject=fix 630`, `gh pr merge -tfix 630` | PR 630's head branch at `headRefOid` | as `gh pr merge 630` |
| `gh pr merge -sd 630`, `gh pr merge -st fix 630` | PR 630's head branch at `headRefOid` | as `gh pr merge 630`; a group is read letter by letter |
| `gh pr merge -sx 630` | none | exit 2, `can't read the pull request this command names` |
| `gh pr merge --help` | as `gh pr merge` | judged like any other flag; allowing help let a `--help` the shell drops carry a merge past the check (#638's panel) |
| `git push && gh pr create --fill`, `cd ../x && gh pr create` | none | exit 2, `run gh pr create on its own; the check judges the branch before anything earlier in the command runs` |
| `gh pr create --fill && gh pr merge 630` | none | exit 2, the same message for the second match |
| `gh pr create --title "$(git push -q && echo t)"`, a backtick, `<(…)`, or `>(…)` in the matched command | none | exit 2, `run gh pr create without a substitution; the shell runs it after the check has judged the branch` |
| `gh pr create --fill && echo done` | current at `HEAD` | judged as `gh pr create --fill` |
| `gh pr -R owner/other merge 630`, `-R github.com/owner/other`, `-R ghe.example.com/<this repo>` | none | exit 2, `-R names another repository; its reviews aren't here` |
| `GH pr merge 630`, `/opt/homebrew/bin/Gh pr create --fill` | as `gh pr merge 630`, `gh pr create --fill` | judged the same; the program name matches in any case |
| `gh pr -R github.com/<this repo> merge 630` | PR 630's head branch | as `gh pr merge 630`; the host is dropped before comparing |
| `gh -R <this repo> pr merge 630`, `gh --repo=<this repo> pr merge 630`, `gh pr -R<this repo> merge 630` | PR 630's head branch | as `gh pr merge 630`; `-R` can sit before `pr` or the verb, attached or not |
| `gh -R owner/other pr merge 630`, `gh pr -Rowner/other merge 630` | none | exit 2, `-R names another repository; its reviews aren't here` |
| `gh -R <this repo> pr merge -R owner/other 630` | none | exit 2, `name the repository once; the check can't tell which -R gh uses` |
| `GH_REPO=owner/other gh pr merge 630`, `GIT_DIR=../630-x/.git gh pr create`, `NO_COLOR=1 gh pr create`, `env -C ../630-x gh pr create` | none | exit 2, `run gh pr create without an environment prefix or env; the check can't see where it points gh` |
| `gh pr $(git push -q) create`, `gh pr 'merge' 630`, `gh pr m* 630` | none | exit 2, always: `write gh's command words out plainly; the check can't read them` |
| `gh stack merge`, `gh stack submit`, `gh co 630`, `gh copilot`, `gh "$X" merge 630`, `rg 'gh (pr\|api)' wfctl/`, `git commit -m "the gh CLI"` | none | exit 2, always: `run gh <word> in your own terminal; the check knows only gh's own commands` |
| `gh pr --squash=true merge 630`, `gh -R <this repo> -R owner/other pr merge 630`, `gh -R $(git push -q; echo a/b) pr merge 630`, `gh -R 'owner/repo' pr merge 630`, `gh --version` | none | exit 2, always: `move flags after the verb, and write -R as OWNER/REPO; the check reads only one plain -R before pr or the verb` |
| `gh -R=<this repo> pr merge 630` | PR 630's head branch | as `gh pr merge 630`; the value is read without the `=` |
| `gh version`, `gh help pr` | none | not matched |
| `rg 'gh pr' wfctl/`, `` git commit -m "run `gh pr` first" `` | none | not matched; one quote or backtick at the end of the word is dropped before it is read |
| `gh pr create --fill`, payload `cwd` in the `630-x` worktree while the hook runs in the `main` checkout | `630-x` at its `HEAD` | exit 0 or 2 by `630-x`'s records; the check reads the payload's `cwd` |
| a matched command, payload with no `cwd` | none | exit 2, naming the missing working directory, error refusal below |
| `gh api "$URL" --input body.json`, `gh api "repos/{owner}/{repo}/pulls/$N/merge" -X PUT` | none | exit 2, always: `write the gh api path out plainly; the check can't read where it writes` |
| `gh api "repos/{owner}/{repo}/pulls/$N/comments"` | none | not matched; a read with a variable path can't open or merge |
| `gh api graphql -F query=@mutation.graphql`, `gh api graphql --input q.json` | none | exit 2, always: `put the GraphQL query in the command; the check doesn't read files` |
| `gh api -X PUT repos/owner/other/pulls/630/merge` | none | exit 2, `the path names another repository; its reviews aren't here` |
| `gh api -X PUT repos/{owner}/{repo}/pulls/630/merge` | PR 630's head branch | as `gh pr merge 630` |
| `gh pr merge --auto` | none | exit 2, `auto-merge would merge a head this check never judged` |
| `gh pr merge`, lookup fails or times out | none | exit 2, error refusal below, naming the failed lookup |
| `gh pr merge` with arguments the check can't read | none | exit 2, `can't read the pull request this command names` |
| `gh api …/pulls/630/merge` or `…/merge-async` | PR 630's head branch | as `gh pr merge 630` |
| `gh api …/pulls -f head=… -f base=…`, `gh api …/pulls -fhead=… -fbase=…`, `gh api "…/pulls?x=1" --field=head=…`, `gh api -XPOST …/pulls/` | none | exit 2, always: `open the pull request with gh pr create so the review check can judge its branch` |
| `gh api graphql` naming `mergePullRequest` or `enqueuePullRequest` | none | exit 2, always, with the same message naming `gh pr merge` |
| `wfctl relay s2 --reason "write denied" --from <file>`, the file quoting `gh pr create` | none | not matched; the report's text isn't in the command |
| `gh api …/pulls/630/comments` | none | not matched; goes on to the worktree check |
| any command matching the sign-off pattern | none | exit 2, always |
| `echo "gh pr create"` on an unreviewed branch | current | exit 2; the match is on the text by design |
| review record or config can't be read | none | exit 2, error refusal below, naming the file |
| no trunk branch found | none | exit 2, error refusal below: `can't find the trunk branch; set trunk in wfctl.json` |
| any other error after a match | none | exit 2, naming the error, error refusal below |
| `WFCTL_STATE_DIR` set, judged branch isn't current | none | exit 2, saying the override names one branch |
| `WFCTL_BRANCH` set to a branch other than the one checked out in `cwd` | none | exit 2, saying the override names a different branch from the session's directory |
| `gh pr merge 630` in the checkout on `main`, where `trunk_branch` returns `origin/main` | PR 630's head branch | judged by that branch's records; `origin/` is stripped before comparing |

Refusal on stderr, exit 2:

```text
✗ 604-release-note-fixes has commits no review covered:
  security  5c4b3a2 fix(release): check the tag body
  security  9f8e7d6 test: cover an empty note
  code      9f8e7d6 test: cover an empty note
  Run the review groups (wfctl review start <group>), or ask a person to run
  `wfctl review sign-off` in their own terminal.
```

Error refusal, exit 2. Every refusal where the check couldn't reach an answer
uses this block: a lookup that fails or times out, a record or config that
can't be read, no trunk branch, a payload with no `cwd`, and any other error
after a match. A refusal that judged the command, such as unreviewed commits
or another repository, doesn't carry the last sentence.

```text
✗ the review check failed: gh pr view timed out after 5s
  The check blocks a pull request when it can't reach an answer. A sign-off
  won't get past this. A person can run the same command in their own
  terminal, where this hook doesn't run.
```

Sign-off refusal:

```text
✗ wfctl review sign-off is for a person to run in their own terminal, not an agent.
```
