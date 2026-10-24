# Research: A security review panel runs before every change opens

The spec and the four design records settle the shape. This file records what
the plan had to settle on top of them, with the reason and the alternatives for
each.

## R1. Command names

- Decision: a `wfctl review` command group with `start`, `check`, `groups`,
  and `sign-off`, plus the top-level `wfctl relay` the spec names.
- Rationale: the four review commands share one subject, and a group keeps
  `wfctl --help` short. `relay` stays top-level because the spec, the design
  record, and the roster line already name it.
- Alternatives considered: top-level `wfctl review-start` and friends, which
  adds four entries to the top-level help. `wfctl review relay`, which renames
  a command three documents already use.

## R2. How a report names its commit and its verdict

- Decision: a report counts when it carries a line `Reviewed: <sha>` naming the
  run's newest commit (seven or more hex digits, as a prefix of the full sha),
  and its last non-blank line holds `Approve` or `Request changes` with a
  verdict anchor on that line or the non-blank line before it. The anchor is
  the one `fanning-out-code-review` already uses, `^[^A-Za-z]*Verdict`, so
  `Verdict: Approve`, `**Verdict: Approve**`, and `## Verdict` followed by
  `Approve` all count.
- Rationale: the spec requires the verdict at the end, so a truncated report
  carries none. Reusing the existing anchor keeps every spelling reviewers
  already write, which the skill's own test pins.
- Alternatives considered: a verdict anywhere in the file, which accepts a
  report cut off after an early "Verdict" mention. A JSON report, which every
  reviewer model would have to produce exactly.

## R3. The commits a run covers

- Decision: `git rev-list --parents <base>..<head> --not <trunk refs> --`,
  keeping every commit with one parent and every merge that has edits of its
  own. A merge has edits of its own when git can't redo it unaided, or when the
  redo differs from it. `git merge-tree --write-tree <parent1> <parent2>` redoes
  the merge, exits 1 on a conflict, and otherwise prints the tree it made,
  which is compared with `<merge>^{tree}`. A merge whose parents share no
  commit, where `git merge-base <parent1> <parent2>` exits 1, is always kept.
  A merged orphan branch makes one. We didn't pass
  `--allow-unrelated-histories` instead, because it redoes the merge against an
  empty base, which can't show that a merge kept a file one side deleted. A
  merge with more than two parents
  is always kept. The base is the group's last reviewed commit when it is an
  ancestor of the head, and otherwise the merge base of the head and the trunk
  branch.
  1. The trunk refs are `refs/remotes/origin/<trunk>` and `refs/heads/<trunk>`,
     each when it exists, in that order. `_paths.trunk_branch` returns either
     one: the remote ref when `origin/HEAD` is set, and the local name when it
     isn't, such as for a remote added with `git remote add`. They are full
     names because git resolves a short `main` to a tag of that name first.
  2. When `_paths.trunk_branch` returns None, `review start` fails and names
     the `trunk` key in `wfctl.json`, and the review check refuses for the
     same reason. Without a trunk there is no merge base to start from.
  3. When the head is the last reviewed commit or one of its ancestors, the
     group has no unreviewed commits. This happens when reviewed commits
     haven't been pushed yet and a merge is judged at the pushed head.
  4. A shallow clone is refused, and the error says to run
     `git fetch --unshallow`. `rev-list` can't list commits past the cut, so a
     completed run would mark them reviewed without anyone seeing them. A cut
     can also leave two merge parents with an older shared commit than the
     real one, and a redo against that base can match a merge that kept a file
     `main` deleted. For the same reason, every git call passes
     `--no-replace-objects`, since a replace ref can graft commits out of the
     history `rev-list` walks.
- Rationale: `--not <trunk>` drops every commit that came in from the trunk
  branch (US2 scenario 4). A clean merge is dropped as well, so merging `main`
  doesn't force a review round. Any conflict counts, whichever side the person
  kept, because keeping the branch's side of a conflict undoes `main`'s change
  to those lines. A clean redo that differs from the merge catches an edit made
  during the merge, and `git merge -s ours`, which records `main` as merged
  while keeping none of it. `_archive.py` already uses `merge-tree`, so it adds
  no new git requirement. The closing `--` stops git reading a bare `main` as a path
  when one exists, which made it refuse the range as ambiguous. Passing the
  remote ref too means a stale local `main` doesn't make merged commits look
  like branch work, whichever of the two `_paths.trunk_branch` returned. A
  last reviewed commit that is no longer an ancestor, after a rebase, falls back
  to the merge base, which costs one larger review and lets nothing through.
  `_paths.trunk_branch` falls back to `origin/HEAD` when `trunk` isn't
  declared, which is `main` here, so FR-006's default is the remote's default
  branch. Item 3 is safe because every ancestor of a reviewed commit was
  covered by an earlier complete run. Without it, the range falls back to the
  merge base and lists every commit on the branch as unreviewed.
- Alternatives considered:
  1. Keeping every merge commit in the range. We didn't choose this because it
     forces a round after every `main` merge.
  2. `git rev-list --no-merges`. We didn't choose this because it drops every
     conflict resolution, and a branch whose only new commit was that merge
     reads as up to date.
  3. `git diff-tree --cc`, which prints the hunks that differ from every
     parent. We didn't choose this because it gets two cases wrong. A conflict
     resolved by keeping one side matches that parent, so it prints nothing
     and the merge is dropped. Two clean edits a few lines apart in one file
     share a hunk, so it prints that hunk and a clean merge forces a round.
  4. `git show --remerge-diff`, which gives the same answers as `merge-tree`.
     We didn't choose this because `show` is porcelain and reads user config
     such as an external diff tool, which can print output for a clean merge.
     `git diff-tree --remerge-diff` would avoid that, but it aborts with a git
     bug on git 2.44.

## R4. The branch the review check judges

- Decision:
  1. `gh pr create`, or `gh pr new`, with no `--head` judges the current
     branch at `HEAD`.
     With `-H` or `--head`, it judges the named branch at the commit GitHub
     holds for it, from `git ls-remote origin refs/heads/<branch>`. An
     `owner:` prefix names the repository the head comes from, so it is
     compared like `-R` below. When the owner is this checkout's owner, the
     prefix is dropped and the branch is judged. When it isn't, the check
     refuses, since a fork's branch can share a name with a reviewed branch on
     `origin`.
  2. `gh pr merge` judges the pull request it names, or the current branch's
     pull request when it names none. The check runs
     `gh pr view [<arg>] [-R <repo>] --json headRefName,headRefOid` and judges
     that branch at `headRefOid`, the commit GitHub would merge.
  3. A `gh api` call to `pulls/<n>/merge` or `pulls/<n>/merge-async` judges
     pull request `<n>`, looked up the same way. A `gh api` call that creates a
     pull request, and a GraphQL call naming one of FR-012's mutations, refuse
     every time and tell the agent to use `gh pr create` or `gh pr merge`. The
     branch they act on sits in a request body the check can't read reliably,
     and judging the current branch instead would let another branch's
     unreviewed pull request through.
  4. When the lookup fails or times out, the number can't be found, or the
     judged commit isn't in the local repository, the check refuses.
- Another branch: a worktree opens and merges only its own branch's pull
  request. A command whose judged branch isn't the current branch refuses,
  unless the current branch is the trunk branch from R3. That checkout is the
  one a person orchestrates from, such as the `main` checkout in this
  repository, or a `dev` checkout in a repository that sets `trunk` to `dev`.
  1. The check compares the judged branch with `resolve_branch` after the
     lookup in items 1 to 3, so `gh pr merge 630` run in the `630-x` worktree
     is judged by `630-x`'s records as before.
  2. The trunk checkout is found by branch, not with `is_main_checkout`. In a
     bare layout no checkout is the main one, and the orchestrating worktree is
     the one on the trunk branch.
  3. `_paths.trunk_branch` returns the remote ref, such as `origin/main`, and
     `resolve_branch` returns the local name, such as `main`. The check strips
     `origin/` from the trunk ref before comparing, the same as R3 item 1.
     Without the strip, the two never match, and every merge from the trunk
     checkout refuses.
  4. This rule keys on the branch name, so it is a convention rather than
     enforcement. A feature worktree that runs `git switch main` passes as the
     trunk checkout. The rule keeps an agent from acting on another branch's
     pull request by accident, and #627 covers one that does it on purpose.
  5. The refusal says
     `run this from the checkout on main; a worktree opens and merges only its own branch's pull request`,
     naming the trunk branch.
- Where the check reads from: the check reads the repository, the current
  branch, and `HEAD` from the session's working directory, the `cwd` field of
  the hook payload, and runs every `gh` and `git` call there. The worktree check
  already reads the same field, because the hook process runs in the agent's
  project directory, and that differs from the session's directory once an
  earlier command has run `cd`.
  1. Reading the hook's own directory would let a pull request through
     unreviewed. Take a session started in the `main` checkout. The agent runs
     `cd wt/630-x`, which the worktree check can't see because the path is
     relative, and then `gh pr create --fill`. The check would judge `main`
     while `gh` opens `630-x`'s pull request. The trunk rule above would also
     let `gh pr merge 631` through as if it ran in the trunk checkout.
  2. The check finds the repository with `git -C <cwd> rev-parse
     --show-toplevel`, passes that root to `resolve_branch` and
     `resolve_agent_dir` as `repo_root`, and runs each `gh` call with
     `cwd=<cwd>`.
  3. A matched command whose payload has no `cwd`, or whose `cwd` isn't inside
     a git repository, refuses with the error refusal (Timeouts and errors item
     4). The worktree check falls back to `.` in that case, but the review check
     refuses on any error once a command has matched.
- A matched command that follows another command: the check refuses any
  match of R6's patterns 1 to 4 when the text before the match holds `;`, `&`,
  `|`, or a newline, quoted or not, and tells the agent to run the pull request
  command on its own. It judges every match in the text, and one refusal
  refuses the whole text.
  1. The check reads `HEAD`, GitHub's head, and the current branch before any
     of the text runs. `git commit -am fix && git push && gh pr create`,
     `git switch other && gh pr create`, and `cd ../other && gh pr create`
     each change what the pull request command acts on after the check has
     judged it.
  2. Quoted separators count too, so `bash -c "git push && gh pr create"`
     refuses the same way. A wrong refusal costs one command run on its own.
  3. Text after the match doesn't count. `gh pr create --fill && echo done`
     is judged as `gh pr create --fill`, since nothing after the pull request
     command can change what it already did.
  4. A command substitution or a process substitution, `$(`, a backtick,
     `<(`, or `>(`, anywhere from the start of the text to the end of the
     matched command refuses too, quoted or not. The shell runs a
     substitution before `gh` starts, so `gh pr create --fill --title
     "$(git commit -qam fix && git push -q && echo t)"` opens the pull request
     at a commit the check never saw, with no separator before the match.
     `opening-a-change` writes its body path out in full for this reason
     (`plan.md §What the skill rewrites say` item 1.5).
- An environment prefix or `env`: a `NAME=value` word, or the word `env`,
  anywhere from the start of the text to the match refuses, quoted or not. The
  refusal says `run gh pr create without an environment prefix or env; the check can't see where it points gh`.
  1. The check's own `gh` and `git` calls run in the hook's environment, not
     the command's. `GIT_DIR=` and `GIT_WORK_TREE=` point `gh` at another
     worktree's branch, `GH_REPO=` and `GH_HOST=` point it at another
     repository, and `env -C <dir>` runs it in another directory. In each case
     the check judges this branch while `gh` acts on a different one.
  2. The check refuses every name rather than a list of known ones, since `gh`
     and `git` read more variables than a list would keep up with. A harmless
     prefix such as `NO_COLOR=1` costs one reworded command.
- `gh`'s command words: the word after `gh` has to be one of `gh`'s own
  commands, and for `gh pr` the verb after `pr` has to be written out plainly.
  1. The word after `gh` passes only when it is on a fixed list in wfctl,
     taken from `gh help` in `gh` 2.91, less the two item 2 names. The list is
     `alias`, `api`, `attestation`, `auth`,
     `browse`, `cache`, `codespace`, `completion`, `config`, `extension`,
     `gist`, `gpg-key`, `help`, `issue`, `label`, `licenses`, `org`, `pr`,
     `preview`, `project`, `release`, `repo`, `ruleset`, `run`, `search`,
     `secret`, `skill`, `ssh-key`, `status`, `variable`, `version`, and
     `workflow`. Any other word refuses, which covers an extension such as
     `gh stack`, a one-word shortcut made with `gh alias set`, and a word the
     check can't read, such as `gh "$X" merge 630`. An extension run through
     `gh extension exec` passes, since `extension` is on the list, and is a
     known limit (R6).
  2. `copilot` and `agent-task` are left off the list, since each hands the
     request to another agent that can open or merge a pull request.
  3. `gh stack merge` merges a whole stack of pull requests, and runs without
     a prompt in a shell with no terminal, such as an agent's. Every installed
     extension and every shortcut adds a command word the check has never
     seen, so the check lists the commands it knows instead of the ones it
     refuses, the same move as for flags below. `gh` won't create a one-word
     shortcut whose name is one of its own commands. It does accept a two-word
     shortcut under one, such as `pr ship` for `pr merge`, and that is a known
     limit (R6).
  4. A command a newer `gh` adds refuses until it is added to the list. That
     costs one command run in a person's own terminal, and never lets a pull
     request through.
  5. The verb after `pr` refuses when it holds `$`, a backslash, `*`, `?`,
     `[`, or `{`, or a quote or backtick anywhere but at its end. So
     `gh pr $(git push -q) create`, `gh pr 'merge' 630`, and `gh pr m* 630`
     refuse. The check can't read those words, so it can't tell whether the
     command opens or merges a pull request.
  6. The refusal for an unlisted word says
     `run gh <word> in your own terminal; the check knows only gh's own commands`.
- What sits before a command word: one plain `-R` flag and nothing else. A
  plain `-R` flag is `-R` or `--repo` with its value after a space or `=`, or
  `-R` with its value attached. A plain value is `OWNER/REPO` or
  `HOST/OWNER/REPO`, where each part holds only letters, digits, `.`, `_`, and
  `-`. Pattern 8 refuses any other word starting with `-` before the word after
  `gh`, or before the verb after `gh pr`.
  1. `gh` parses a verb's flags before the verb, so
     `gh pr --squash=true merge 630` merges, and
     `gh pr --squash=true merge --help` prints the merge help. Two `-R` flags
     before `pr` also reach `gh`. Each of the last three plan reviews found one
     more spelling of this kind, so the check lists the one spelling it allows
     rather than the spellings it refuses.
  2. An `-R` value holding a quote, `$(`, or a backtick refuses too, since it
     isn't plain. In `gh -R $(git push -q; echo a/b) pr merge 630`, the shell
     pushes before `gh` starts, and the words after the value aren't the words
     `gh` reads.
  3. `gh --help` and `gh --version` refuse as well. `gh help` and `gh version`
     do the same thing and pass.
  4. The refusal says
     `move flags after the verb, and write -R as OWNER/REPO; the check reads only one plain -R before pr or the verb`.
- How the check reads the arguments: it takes the text from the matched verb
  to the end of that command, which is the next unquoted `;`, `&&`, `||`, `|`,
  or newline, and splits it with `shlex.split`.
  1. For `merge`, the flags that take a value are `-t`/`--subject`,
     `-b`/`--body`, `-F`/`--body-file`, `-A`/`--author-email`,
     `--match-head-commit`, and `-R`/`--repo`. The flags `-s`/`--squash`,
     `-m`/`--merge`, `-r`/`--rebase`, `-d`/`--delete-branch`, `--admin`, and
     `--disable-auto` take none. `--auto` refuses outright, because GitHub
     would merge a head the check never judged.
  2. For `create`, the flags that take a value are `-H`/`--head`,
     `-B`/`--base`, `-t`/`--title`, `-b`/`--body`, `-F`/`--body-file`,
     `-a`/`--assignee`, `-l`/`--label`, `-m`/`--milestone`, `-p`/`--project`,
     `-r`/`--reviewer`, `-T`/`--template`, `--recover`, and `-R`/`--repo`.
     Every other flag takes none.
  3. Any other word after the verb is the pull request argument: a number, a
     URL, or a branch name, passed to `gh pr view` as given.
  4. A long flag's value can be attached with `=`, as in `--subject=fix`, and
     the check splits it at the first `=`. Short flags can be grouped in one
     word, and the check reads the group letter by letter, the way `gh` does.
     A flag that takes no value stands on its own, so `-sd` reads as `-s -d`.
     A flag that takes a value takes the rest of the word, as in `-tfix`, or
     the next word when nothing is left, as in `-st fix`. A letter neither
     list names refuses.
  5. `-h` or `--help` anywhere after the verb allows the command, since `gh`
     prints its help and does nothing else.
  6. The check refuses when `shlex.split` fails, when it finds more than one
     pull request argument, or when it meets a flag neither list names. A
     command the rule can't read never falls back to the current branch.
- Another repository: a command that names one refuses, because that
  repository's reviews aren't in this checkout's state directories. The check
  compares each of these with `gh repo view --json nameWithOwner` for this
  checkout, which runs only when one of them is present:
  1. `-R` or `--repo`, wherever it sits: before `pr`, before the verb, or
     after the verb, and with its value after a space, after `=`, or attached
     to `-R`. The check reads a value before `pr` or before the verb from the
     words pattern 8 read, which pattern 8 has already required to be plain, so
     those words need no `shlex.split`. It reads a value after the verb from
     the `shlex.split` words above. A value after `=`, in `-R=owner/repo` or
     `--repo=owner/repo`, is read without the `=`, as `gh` reads it. A value
     with three parts, `HOST/OWNER/REPO`, refuses unless the host is
     `github.com`, and is then compared after dropping the host. Dropping any
     other host would compare `ghe.example.com/<this repo>` as this repository
     while `gh` acts on the other server. The check passes the value to
     `gh pr view` as written, so the lookup reads the same pull request `gh`
     acts on. The check counts `-R` and `--repo` across all three places, and a command
     with more than one refuses, since the check would have to guess which one
     `gh` uses.
  2. A `repos/<owner>/<repo>/` path in a `gh api` call. The `{owner}/{repo}`
     placeholders mean this repository and pass.
  3. An `owner:` prefix on `--head`, compared with the owner half of
     `nameWithOwner` (item 1 above).
  A `GH_REPO=` prefix isn't compared. It refuses with every other environment
  prefix, above.
- Timeouts and errors: each `gh` and `git` call the check makes runs with
  `timeout=5`, the same bound `_restart.py` gives its hook subprocesses, and
  well under the host's hook timeout. That includes the calls inside the
  `_paths` helpers R3 and R5 name.
  1. Eight `_paths` helpers gain an optional `timeout` keyword, defaulting to
     none so their other callers don't change, and the check passes 5.
     `trunk_branch` passes it down to `_resolve_declared` and `_bare_head`,
     and `_bare_head` passes it to `is_bare_layout`. `resolve_agent_dir`
     passes it through `project_state_dir` to `project_name`.
     `resolve_branch` takes it directly.
  2. The check reads the current branch with `resolve_branch`, so a
     `WFCTL_BRANCH` override names the same branch here as everywhere else in
     wfctl. When `WFCTL_BRANCH` is set and names a different branch from the
     one checked out in `cwd`, the check refuses and says why, the same as for
     `WFCTL_STATE_DIR` in R5. Otherwise the override would name the branch
     without reading `cwd`, which FR-012c forbids.
  3. An exit code that is an answer is read as an answer.
     `git merge-base --is-ancestor` exits 1 for "not an ancestor", and
     `git show-ref --verify` exits 1 for "no such ref". Neither refuses.
  4. Once a command has matched, a timeout, any other non-zero exit, or any
     exception inside the review check's `try` block refuses with exit 2 and
     names the error. The refusal also says that a person can run the same
     command in their own terminal, where the hook doesn't run. That is the way
     out when the check itself is broken. A sign-off doesn't help there: the
     error stops the check whether or not a sign-off exists, and on a fully
     reviewed branch `review sign-off` has nothing to cover and writes nothing.
  5. The check calls `resolve_agent_dir` with `create=False`, as its
     docstring asks of a hook reader, so judging another branch's pull
     request doesn't leave an empty state directory for that branch.
- Rationale: clarify, 2026-10-22. A merge is judged at the commit GitHub will
  merge, since a local branch can be behind or ahead of what was pushed.
  `--head` is judged at GitHub's copy for the same reason, which is also what
  FR-012a asks for. Refusing on any error after a match keeps a bug in the
  check from turning into a pass. If the host kills the hook at its own
  timeout instead, the hook exits without code 2 and the command runs, which
  is why the `gh` call carries its own shorter bound.
- Alternatives considered: judging the current branch always, and checking only
  `gh pr create`. Both are in the clarify scan file with the reasons they lost.
  Allowing a command when an error stops the check, the way the worktree check
  does. We didn't choose this because every bug in the review check would then
  let an unreviewed pull request through.
- Rationale for another branch: plan walkthrough, 2026-10-23. Andre
  orchestrates from the trunk checkout, so a feature worktree has no reason to
  open or merge another branch's pull request. Allowing it from any worktree
  means every worktree can act on every branch, and the check would be the
  only thing standing in the way.
- Alternatives considered for another branch: allowing it only from the
  checkout `is_main_checkout` names. We didn't choose this because a bare
  layout has no main checkout, so a person orchestrating there could never
  merge from a worktree.
- Rationale for the environment prefix: plan walkthrough, 2026-10-23, which
  settles plan review PR-031. Comparing only `GH_REPO=` left `GIT_DIR=` open,
  and each new variable found later would be one more hole. Refusing every
  prefix closes the shape at the cost of a reworded command.

## R5. Which state directory holds another branch's reviews

- Decision: `_paths.resolve_agent_dir(repo_root, <branch>)`. When
  `WFCTL_STATE_DIR` is set and the judged branch isn't the current one, the
  check refuses and says why.
- Rationale: `WFCTL_STATE_DIR` names one branch's directory. Reading it for
  another branch would judge that branch against the wrong records.
- Alternatives considered: ignoring the override for other branches, which
  silently reads a directory the user didn't point at.

## R6. Matching a command

- Decision: the guard first tests three substrings, `gh`, `merge`, and `sign`,
  before importing anything. A command holding none goes straight on to the
  worktree check. A command holding one is matched against these patterns over
  the whole text. The program word `gh` matches in any case, both in the
  substring test and in every pattern below that names it, because macOS
  finds programs without regard to case, so `GH pr merge 630` and
  `/opt/homebrew/bin/Gh pr create` run `gh`. Everything after the program word
  stays case-sensitive, since `-R` and `-r` are different flags, and `gh` runs
  `gh pr MERGE` as `gh pr` and prints its help.
  1. `\bgh\s+(?:REPO\s+)?pr\s+(?:REPO\s+)?(create|new|merge)\b`, where
     `REPO` is `(?:(?:-R|--repo)(?:\s+|=)\S+|-R\S+)`. The outer group matters,
     since without it the `\s+` after `REPO` binds only to the attached form.
     This matches `gh pr create`,
     its built-in second name `gh pr new`, and `gh pr merge`. An `-R` or
     `--repo` flag can sit before `pr` or between `pr` and the verb, since `gh`
     accepts both, as `gh -R cli/cli pr merge --help` shows. Its value can
     follow a space or `=`, or be attached to `-R`, as in `-Rowner/repo`.
  2. `pulls/\d+/merge(?:-async)?\b`, for both merge endpoints.
  3. `\bgh\s+api\b` with a path whose last segment is `pulls`, and a body
     flag or a `POST` method, for creating a pull request. A plain
     `gh api .../pulls` read, and `pulls/<n>/comments`, don't match.
     1. The path can end in `/pulls`, `/pulls/`, or `/pulls?<query>`, since
        GitHub accepts a query string on the path. A path ending in a
        fragment, such as `pulls#x`, isn't read, and is a known limit.
     2. A body flag is `-f`, `-F`, `--field`, `--raw-field`, or `--input`, in
        three spellings: as its own word, with its value attached
        (`-fhead=x`), or after `=` (`--field=head=x`). A body flag grouped
        after another short flag, such as `-ifhead=x`, isn't read, and is a
        known limit.
     3. A method is `-X` or `--method` with `POST` after a space, after `=`,
        or attached (`-XPOST`), in any case.
     4. Pattern 6 reads body flags and methods the same way.
  4. `createPullRequest|mergePullRequest|enablePullRequestAutoMerge|enqueuePullRequest`,
     for the GraphQL mutations. `enqueuePullRequest` adds a pull request to a
     merge queue, which merges it.
  5. `\breview\b.*\bsign.?off\b`, for the sign-off command, with any
     character or none between `sign` and `off` and any text between the two
     words.
  6. A `gh api` call whose path holds `$`, a backtick, or a substitution, and
     that carries a body flag or a method other than `GET`. It refuses every
     time, since the check can't read which endpoint it writes to. A read with
     a variable path still passes, because a read can't open or merge a pull
     request.
  7. A `gh api graphql` call that reads its query from a file, through
     `query=@<file>` or `--input`. It refuses every time, since the mutation
     sits in a file the check doesn't read.
  8. `\bgh\s+` followed by words R4 says the check can't read. The check
     splits the text after `gh` at whitespace and reads it word by word. A
     word starting with `-` passes only when it starts one plain `-R` flag
     (R4, What sits before a command word), and the check skips that flag and
     its value. The first word that doesn't start with `-` is the command word.
     When that word is `pr`, the check reads the words after it the same way,
     up to the verb. Pattern 8 refuses when it meets any other word starting
     with `-` there, a second `-R` flag, a command word that isn't on R4's list
     of `gh`'s own commands, or a verb after `pr` that holds `$`, a backslash,
     `*`, `?`, `[`, or `{`, or a quote or backtick anywhere but its last
     character. It refuses every time, on every branch, since the check can't
     read whether the command opens or merges a pull request, or which branch
     it acts on. Patterns 1 to 7 can't catch these commands, since each needs a
     verb or a path written out in the text.
     1. One quote or backtick at the end of a word is dropped before the word
        is read, because it closes an outer quote. So `rg 'gh pr'` and a
        commit message quoting `` `gh pr` `` read `pr` and aren't refused.
        A backtick substitution glued to `pr`, such as
        `` gh pr` git push -q` merge 630 ``, also reads as `pr`, and is a
        known limit.
     2. Text that mentions `gh` followed by any other word is refused too,
        such as `rg 'gh (pr|api)'`, `rg 'gh [a-z]+'`, or a commit message
        saying "the gh CLI". Across this repository's commit history, 8 of 38
        mentions of `gh` are followed by an English word rather than a `gh`
        command, such as "in" or "to". Each costs one reworded command.
     3. A search or a commit message that quotes a flag before the verb, such
        as `rg 'gh -R'` or a message naming `gh pr --squash=true merge`, is
        refused the same way.
- Which holes refuse and which are recorded: plan walkthrough, 2026-10-23,
  changed 2026-10-24. The check refuses a command whose text shows that the
  check can't be sure what the command acts on, such as a variable, a
  substitution, an environment prefix, or a file read in place of a query. It
  records a limit when the text looks like an ordinary command and the
  surprise lives somewhere the check doesn't read: GitHub's merge settings, or
  a file an agent writes with a file tool.
  1. That rule covers the holes fixed up to the 2026-10-24T05:48Z plan
     review. Every hole still open when Andre decided to stop adding rules,
     later that day, and any found since, is recorded as a known limit instead
     of becoming a new rule. `plan.md`'s Summary says "still open on
     2026-10-24" for short, and this item is the exact cutoff. That includes a few that show a variable or a
     substitution, such as PR-035 and PR-042, which the test above would
     otherwise refuse.
  2. We stopped there because six reviews in a row each found more disguised
     commands. The hook only sees a command's text, so its rules can't keep up
     with every spelling `gh` and the shell accept.
  3. The required CI check in #627 closes these holes, since GitHub blocks the
     merge itself however the command was typed. Until #627 ships, they stay
     open.
- Rationale: the spec keeps the plain text match on purpose, so `echo`,
  `bash -c "gh pr create"`, and a full path to `gh` are all caught. The
  substring test keeps a non-matching command under 1 ms (SC-003). Pattern 5
  is loose on purpose, since a wrong refusal of a command that mentions both
  words costs one rewording. It still misses a sign-off spelled through a
  shell variable, which is why the command also requires a terminal (R9).
- Alternatives considered: matching parsed words from `_guard._commands`. That
  parser returns None on substitutions and globs and would fail open on a
  refusal, which the guard's own rule forbids. Matching every `gh api` call to
  a `pulls` path. We didn't choose this because the agent reads and answers
  review comments through `pulls/<n>/comments`, and each of those would be
  refused.
- Known limits, recorded in the spec's Edge Cases and covered by #627:
  1. A `gh pr merge` without `--auto` that `gh` turns into auto-merge because
     checks are pending.
  2. A backtick substitution glued to `pr`, such as
     `` gh pr` git push -q` merge 630 `` (plan review PR-054).
  3. An extension run through `gh extension exec`, such as
     `gh extension exec stack merge` (PR-055).
  4. A two-word shortcut under one of `gh`'s own commands, such as
     `gh alias set 'pr ship' 'pr merge'` followed by `gh pr ship 630`
     (PR-056).
  5. A `gh api` create whose path ends in a fragment, such as `pulls#x`, or
     whose body flag is grouped after another short flag, such as
     `-ifhead=x` (PR-057).
  6. `gh` run through `xargs`, such as
     `printf '%s\n' pr merge 630 | xargs gh` (PR-058).
  7. A merge through a `repositories/<id>/pulls/<n>/merge` path, which names
     another repository by its number rather than its name (PR-059).
  8. A GraphQL mutation built in a variable or a substitution (PR-035).
  9. A wrapper that moves `gh` to another directory or feeds it an argument,
     such as `uv run --directory`, `direnv exec`, or `<<<630 xargs gh pr merge`
     (PR-037).
  10. A quoted or variable program name, such as `"gh" pr merge 630` (PR-042).
  11. A `gh` call inside something the agent runs whose text the command
      doesn't show: a script, such as `release.py` (PR-044), a git alias in
      `.git/config`, or a shell function or alias (PR-063).
  12. A command aimed at another GitHub host through `gh api --hostname`, or
      an `-R` value written as a URL (PR-053).
- Known wrong refusals, recorded in the spec's Edge Cases: a `-f` field before
  a `gh api` path, the `:owner/:repo` placeholders, a variable-path write such
  as a review-comment reply (PR-036), a search or commit message quoting a
  refused form, such as `grep "gh pr create\|gh pr merge"`, and a command that
  names `gh` as an argument before using it, such as `which gh && gh pr view`
  (PR-043). Each costs one reworded command, and the
  spec names the rewording for each.

  The walkthrough moved four earlier limits into refusals: a `gh api` path
  from a variable (pattern 6), a GraphQL mutation from a file (pattern 7), a
  substitution between `gh` and the verb (pattern 8), and
  `env -C` (R4, environment prefix). Plan review PR-052 moved a fifth, a
  one-word `gh alias set` shortcut, into pattern 8's list of `gh`'s own
  commands.

## R7. A model that can't run

- Decision: `wfctl review start` looks up the first word of each listed
  model's command with `shutil.which`. When it isn't found, the run record marks
  that model's reviewers `unavailable` with the reason, `start` prints one `⚠`
  line, the roster shows them ✗ with the reason, and `check` completes the run
  without their reports. Claude has no command and is always available.
  1. When no reviewer in the run is available, `start` still writes the run
     record, and `check` keeps it incomplete with the line
     `incomplete: no reviewer in security could run`. A person installs a
     model or signs off.
  2. A model that is on `PATH` but fails when it runs, such as Codex without a
     login, writes no report. Its reviewers read as `no report`, and the run
     stays incomplete.
- Rationale: clarify answer from the specify session. wfctl decides
  availability, so the coordinator can't simply declare a reviewer
  unavailable. The lookup does run on the agent's `PATH`, so an agent that
  changes `PATH` can hide a model. That isn't enforced, but it is visible,
  because the roster and the `⚠` line name the missing model. Item 1 stops a
  group from completing with no review at all, which FR-001 forbids.
- Alternatives considered: letting the coordinator report a model unavailable,
  which is the agent grading its own panel. Running the command with a probe
  flag, which differs per tool and costs a process per model.

## R8. Running a reviewer on another model

- Decision: the coordinator writes the review prompt to a file, runs the
  command `review start` prints with that file as its input, and redirects the
  output to a second file. It then runs
  `wfctl relay <id> --reason "read-only sandbox" --from <that file>`. The same
  goes for a Claude reviewer whose write was denied: the coordinator saves the
  reply to a file with its own file tool, then relays that file.
  1. `wfctl relay` reads the report only from `--from`, never from stdin or an
     argument, and the skill says never to put a report in a command's text.
  2. The files sit in the scratch folder the coordinator already uses, and
     wfctl copies the report into the run's folder with the relayed header.
- Rationale: `codex exec --sandbox read-only` can't write a file, so its report
  arrives on stdout. That is exactly the relay's case, and the roster says so.
  A report travelling in the command's text, through a heredoc or an `echo`,
  meets the guard's text match. A security report quotes `gh pr create` and
  `pulls/630/merge`, which refuse while the branch is unreviewed, as it always
  is during a run. Any report that mentions "review" before "sign-off" refuses
  every time. The guard's accepted cost, one reworded command, doesn't hold
  here, because the report has to arrive word for word. A file keeps the
  report out of the text the guard reads.
- Alternatives considered: reading the report from stdin, with the skill
  telling the coordinator to redirect from a file. We didn't choose this
  because the easy way to feed stdin is a heredoc, which puts the report back
  in the command's text, and nothing would stop it.
- Alternatives considered: wfctl launching other-model reviewers itself. The
  level-2 record leaves that open for later, and it needs a prompt contract
  this feature doesn't define.

## R9. The sign-off

- Decision: `wfctl review sign-off` records the current branch's head commit in
  `<state dir>/reviews/sign-off.json` and lists the commits it covers per
  group. The review check allows a pull request when every group's unreviewed
  commits are ancestors of the signed-off commit or equal to it. It works at
  any time. The guard refuses any command matching R6's pattern 5.
  1. The command refuses unless stdin and stdout are both a terminal, checked
     with `isatty`.
  2. It prints the commits it would cover, then asks the person to type the
     head commit's seven-character sha. Anything else writes nothing.
- Rationale: FR-013 and FR-014, with the clarify answer that it works at any
  time. Covering only commits that existed at signing comes from the ancestor
  test. A commit added later isn't an ancestor of the signed-off commit. The
  terminal check is a second obstacle behind the text match, not enforcement.
  An agent's shell tool has no terminal, so a plain call with a spelling the
  pattern misses still fails. A pseudo-terminal from `script` or Python's
  `pty.spawn` satisfies `isatty`, though, and the sha can be fed through it.
  That takes no less effort than writing `sign-off.json` with a file tool,
  which is the same limit as a forged report. The spec records both limits
  side by side. Typing the sha makes the person read what they're signing off.
- Alternatives considered: a sign-off per group, which makes a person sign
  twice for one decision. Counting rounds before allowing it, which only
  restricts the person (specify clarification).

## R10. Where the security reviews come from

- Decision:
  1. `security-and-hardening` is vendored as a skill from
     `addyosmani/agent-skills` (MIT), with its `references/hardening-patterns.md`.
     That upstream already has a `NOTICES.md` section. The skill's `SKILL.md`
     ends with the attribution line, as `idea-refine` from the same upstream
     does, and is otherwise unedited.
  2. The upstream's repository-level `references/security-checklist.md`, which
     the skill cites as `../../references/security-checklist.md`, is vendored
     to `wfctl/agents/skills/security-and-hardening/references/security-checklist.md`.
     The cited path resolves outside the installed skill folder, so
     `reviewing-security` tells the reviewer where the checklist really is.
  3. `/security-review` is vendored from
     `anthropics/claude-code-security-review` (MIT), file
     `.claude/commands/security-review.md`, to
     `wfctl/agents/skills/reviewing-security/references/security-review.md`,
     byte for byte. It carries no attribution line. Its credit is a row in the
     record's existing file table, the one that lists `specify/` files by
     their path under `wfctl/`, and a new
     `anthropics/claude-code-security-review` section in
     `wfctl/agents/skills/NOTICES.md` that names the file by path. This is how
     the Spec Kit templates are already credited.
  4. `vendor-upstream-skills.md` is amended in place, the way its Log shows it
     has been amended eight times before. Three edits change it:
     1. The sentence "The templates are the one case where the notice stands
        in for the line" names this file as the second case.
     2. The paragraph on `wfctl/specify/` gains a sentence giving this file's
        reason, which the next item states.
     3. The Log gains a line, `amended — anthropics/claude-code-security-review's
        /security-review file credited by NOTICES.md, as the templates are
        (#622)`.
  5. The reason this file carries no line, when every derived `SKILL.md` does:
     the file ends on the instruction that defines the reviewer's whole reply,
     "Your final reply must contain the markdown report and nothing else." A
     line after it is the last thing the reviewer reads before it answers. A
     derived `SKILL.md` ends on guidance the agent applies while it works, and
     nothing in it sets the agent's output.
  6. `tests/test_skill_attribution.py` still tells rows apart by path, as its
     comment on `_TEMPLATE_ROW` requires.
     1. `_TEMPLATE_ROW` stays `specify/templates/`, so `_listed_templates()`
        and the template tests that read it don't change. Turning it into a
        tuple would fail one of them, since `str.startswith` takes a tuple and
        the new row would join the template set.
     2. A new constant, `_NOTICED_ROWS`, holds both prefixes whose files a
        notice covers, `specify/templates/` and
        `agents/skills/reviewing-security/references/`. `_listed()` drops rows
        under either one, so the existing line test doesn't fail on the new
        row.
     3. A new test checks that each row under the second prefix names a file
        that exists, carries no attribution line, and is named under its
        upstream's section in `wfctl/agents/skills/NOTICES.md`, the way the
        template rows are checked against their notice today.
     4. The new test's reader of path claims in `wfctl/agents/skills/NOTICES.md`
        joins `_declaration_sources`, as that function's docstring asks of any
        new list of claims, so a path named twice in the notice fails.
  7. `reviewing-security` is a wfctl-owned skill. It tells a security reviewer
     to do four things:
     1. Run both reviews.
     2. Skip the vendored command's git section, and review the commit range
        `wfctl review start` printed.
     3. Read the checklist at the path in item 2.
     4. Write one report covering both reviews, in the shape R2 requires, to
        the path `wfctl review start` printed. This instruction outranks the
        vendored file wherever they conflict: its last line, which asks for
        the markdown report and nothing else, its false-positive block's "Do
        not use the bash tool or write to any files", and its sub-task steps
        when the reviewer can't launch sub-tasks. The file's `allowed-tools`
        frontmatter restricts nothing here, since the file is read as a
        reference and never runs as a command.

     Without item 4, a reviewer that follows the vendored file writes no
     verdict, so wfctl doesn't count its report, and the security group can't
     complete on any change. A reviewer that also declines to write would be
     relayed with a block reason that never came from the host. Item 5's
     argument still holds for the attribution line, since an appended line
     would be read as part of the prompt whichever instruction governs the
     reply.
- Rationale: both licenses were confirmed with `gh api` on 2026-10-23. Keeping
  the command file as a reference under another name stops it installing as a
  skill or command called `security-review`, which Claude Code's built-in
  command would shadow or collide with.
- Alternatives considered: vendoring the command into `wfctl/agents/commands/`,
  which installs it where the built-in takes its place. Editing the vendored
  file's git section, which the next upstream pull reverts silently. Adding the
  attribution line to the end of the `/security-review` file. We didn't choose
  this because the file is a Claude Code command prompt, and a line appended
  after its instructions becomes part of what the reviewer reads. Putting the
  line in `reviewing-security/SKILL.md`. We didn't choose this because the
  test reads a skill's last line as a claim that the whole skill is derived,
  and that skill is wfctl's own. A third table in the record for files that
  carry no line. We didn't choose this because the test would then tell rows
  apart by which table they sit in, and its comment keeps that to the path. A
  new record superseding `vendor-upstream-skills`. We didn't choose this
  because the record's practice is to amend in place, and a second record
  would split one rule across two files.

## R11. The three-round cap

- Decision: the skills tell the coordinator to stop after three complete rounds
  and ask for a sign-off. wfctl numbers runs but doesn't count rounds yet.
- Rationale: #626 owns how rounds are counted and whether the cap is
  configurable. `a-rule-is-expressed-as-a-check` says this rule belongs in a
  check, since run records make a violation visible, so the prose is a stopgap
  and the plan says so.
- Alternatives considered: counting rounds here, which decides #626's questions
  without its brainstorm.
