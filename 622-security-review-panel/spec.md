# Feature Specification: A security review panel runs before every change opens

**Feature Branch**: `622-security-review-panel`
**Created**: 2026-10-22
**Status**: Draft
**Input**: User description: "From the brainstorm output at design.md (issue #622: run a security review panel before opening a change)"

## Clarifications

### Session 2026-10-22

- Q: When the code group's fixes add commits after the security group has reviewed, does the security group have to review them before the pull request opens? → A: Yes. Every group, custom groups included, has to review the newest commit, and three rounds of that is the cap before a person signs off.
- Q: When the agent merges or opens a pull request for a different branch than the one it's on, whose reviews does the review check read? → A: That pull request's own branch, which the check looks up from GitHub. If the lookup fails, the check refuses.

### Session 2026-10-23 (plan walkthrough)

- Q: Should a `GIT_DIR=` prefix, which points `gh` at another worktree's branch, be blocked or recorded as a known limit? → A: Blocked, the same as `GH_REPO=`. The rule is that a command the check can't read for sure is blocked. A limit is recorded only when the command looks ordinary and the surprise lives outside it.
- Q: Where may an agent open or merge another branch's pull request? → A: Only from the checkout on the trunk branch, which is where Andre orchestrates. A feature branch's worktree opens and merges only its own branch's pull request.
- Q: When a bug in the review check blocks a fully reviewed pull request, how does it get through? → A: A person runs the command in their own terminal, where the hook doesn't run. The refusal says so, because a sign-off doesn't help in that case.

### Session 2026-10-24

- Q: Six plan reviews in a row each found more ways to disguise a merge from the review check. Does the check keep adding a rule for each one? → A: No. The check keeps the rules it has, which catch ordinary commands and most disguised ones. A disguise found from now on is recorded as a known limit. The required CI check in #627 closes those, since GitHub blocks the merge itself however the command was typed. Until #627 ships, they stay open.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Every change gets a security review before the code review (Priority: P1)

A review panel is a set of independent reviewers who read the same change
before a pull request opens. Currently, `opening-a-change` runs one panel, the
`fanning-out-code-review` panel. Its reviewers follow the `code-review` rubric,
and security is one of that rubric's six passes. As a result, a change gets a
security check only as deep as one pass of a general review.

After this change, `opening-a-change` runs two review groups on every change.
A review group is one panel with its own reviewers and its own review skill.
The security group runs first. Each security reviewer runs both security
reviews:

1. The `security-and-hardening` skill, which starts from a threat model.
2. Anthropic's `/security-review` command, which looks for exploitable
   vulnerabilities in the diff.

The security group commits its fixes. The code group then reviews the result
with the full `code-review` rubric. Both groups run whether or not anyone asks
for them, so an agent in an unattended run never decides to skip one.

The findings from both groups reach Andre in chat as one table. Each finding
names the reviewer id and model that raised it, such as `s3 codex`. Nothing
from either group goes in the pull request description.

**Why this priority**: This is the feature. The two security reviews exist
today, and neither one runs unless a person asks for it by name.

**Independent Test**: Run `opening-a-change` on a branch with one commit in a
repository with no `review` key in `wfctl.json`. Three security reviewers
report, then three code reviewers report on a commit that includes the
security group's fixes. One findings table reaches the chat, and the pull
request description holds no finding.

**Acceptance Scenarios**:

1. **Given** a repository with no `review` key, **When** `opening-a-change`
   runs, **Then** the security group runs with reviewers `s1`, `s2`, and `s3`,
   followed by the code group with `c1`, `c2`, and `c3`, all Claude.
2. **Given** the security group has committed fixes, **When** the code group
   starts, **Then** its run covers the fix commits.
3. **Given** both groups have reported, **When** the agent reports to Andre,
   **Then** every finding appears in one table with its reviewer id and model,
   and the pull request description carries none of them.

---

### User Story 2 - wfctl, not the coordinating agent, records whether a review ran (Priority: P1)

The coordinating agent is the agent that launches the reviewers. Currently, it
also reports whether its own panel ran, and nothing records which commits the
panel read. That is the agent grading its own work. It has already gone wrong
once, when all three reviewers reported on an older commit after the pull
request opened.

After this change, wfctl keeps the record. When a group starts, wfctl writes a
run record that lists the expected reviewers and the commits to review. Each
review covers every commit since the group's last reviewed commit, except
commits merged in from the trunk branch. The first review on a branch starts
where the branch left the trunk branch. One complete run of every group over
the new commits is a round, and the next round reviews the fixes the round
before it made.

wfctl accepts a report only when it names the run's newest commit and ends
with a verdict. When every expected reviewer has an accepted report, the run
is complete, and wfctl moves the group's last reviewed commit forward. After
each group, wfctl prints the roster, a list of every expected reviewer with ✓
for an accepted report and ✗ for a missing one. For example:

```
s1 claude ✓
s2 claude ✓ relayed: write denied
s3 claude ✗
```

The run records, the reports, and the last reviewed commit live in the
branch's state directory, beside `verify.json`. So `wfctl store specs` no
longer commits review reports to `specs-trunk`.

**Why this priority**: Without it, a security group fails the same way the
code group already does, and every new group copies the same check into its
own instructions.

**Independent Test**: Start a group run, write two accepted reports and one
report that names an older commit, and read the roster. It shows two ✓ and
one ✗, and the last reviewed commit hasn't moved.

**Acceptance Scenarios**:

1. **Given** a run whose newest commit is `C`, **When** a report names an
   older commit, **Then** wfctl doesn't accept it and the roster marks that
   reviewer ✗.
2. **Given** a report that names `C` but has no verdict at its end, **When**
   wfctl reads it, **Then** wfctl doesn't accept it.
3. **Given** every expected reviewer has an accepted report, **When** the run
   is checked, **Then** the run is complete and the group's last reviewed
   commit moves to `C`.
4. **Given** a branch that merged in the trunk branch since its last review,
   **When** a new run starts, **Then** the run lists only the branch's own
   commits.
5. **Given** a completed review, **When** `wfctl store specs` runs, **Then**
   no review report lands in the spec store's commit.

---

### User Story 3 - A pull request can't open or merge with unreviewed commits (Priority: P2)

The worktree guard is the hook wfctl installs to check each shell command an
agent runs. After this change, it also runs the review check. The review check
blocks `gh pr create`, `gh pr merge`, and a `gh api` call to the `merge-async`
endpoint while any review group hasn't reviewed the branch's newest commit.
Its refusal lists the commits each group hasn't reviewed. As a result, every
group reviews a change's newest commit before it opens. When the code group's
fixes add commits, the security group reviews them too, because a fix for a
code finding can bring in a vulnerability.

After three rounds of fixes, the agent stops and asks a person to sign off on
the remaining commits. For now, the three-round cap is an instruction in the
skill that nothing enforces, and #626 adds the enforcement. The person runs wfctl's sign-off
command in their own terminal, and the review check then allows the pull
request. The agent shouldn't sign off, because that would be grading its own
work again, so the worktree guard blocks the sign-off command when an agent
runs it. A person can sign off at any time, not only after three rounds, since
the worktree guard already keeps the agent from running the command.

**Why this priority**: The record in User Story 2 is only advice until
something reads it before the pull request opens. It comes second because the
record has to exist first.

**Independent Test**: On a branch with one unreviewed commit, pipe a
`gh pr create` payload into `wfctl hook worktree-guard`. It exits 2 and names
the commit. After a complete run, the same payload exits 0 and prints nothing.

**Acceptance Scenarios**:

1. **Given** a branch with unreviewed commits, **When** the agent runs
   `gh pr create`, `gh pr merge`, or the `merge-async` call, **Then** the
   worktree guard refuses it with exit code 2 and lists the unreviewed commits
   on stderr.
2. **Given** a fully reviewed branch, **When** the agent runs `gh pr create`,
   **Then** the worktree guard allows it and prints nothing.
3. **Given** any branch, **When** the agent runs the sign-off command, **Then**
   the worktree guard refuses it.
4. **Given** a person signed off on the remaining commits, **When** the agent
   runs `gh pr create`, **Then** the worktree guard allows it.
5. **Given** a sign-off, **When** the agent adds another commit, **Then** that
   commit is unreviewed and the review check blocks the pull request again.
6. **Given** a review record that can't be read, **When** the agent runs
   `gh pr create`, **Then** the worktree guard refuses it.
7. **Given** the code group committed fixes after the security group's last
   run, **When** the agent runs `gh pr create`, **Then** the worktree guard
   refuses it and lists the fix commits under the security group.
8. **Given** the agent is in the checkout on the trunk branch, **When** it
   runs `gh pr merge` on another branch's pull request that has unreviewed
   commits, **Then** the worktree guard refuses it and lists that branch's
   unreviewed commits.
9. **Given** a command that names another pull request, **When** the review
   check can't look up that pull request's branch, **Then** the worktree guard
   refuses it.
10. **Given** the agent is in a feature branch's worktree, **When** it runs
    `gh pr merge` on another branch's pull request, **Then** the worktree
    guard refuses it and says to run it from the checkout on the trunk branch,
    whether or not that branch is reviewed.
11. **Given** a fully reviewed branch and an error inside the review check,
    **When** the agent runs `gh pr create`, **Then** the worktree guard
    refuses it, names the error, and says that a person can run the command in
    their own terminal.

---

### User Story 4 - A reviewer blocked from writing still gets its report counted (Priority: P2)

The host's permission layer can refuse a reviewer's write. The reviewer then
has its findings and nowhere to put them, and it looks the same as a reviewer
that never ran.

After this change, a blocked reviewer sends its report as its reply instead.
The coordinating agent saves the reply to a file and passes that file to the
`wfctl relay` command with the reviewer's id. The reply never goes in the
command's own text. The guard matches command text, and a security report
quotes the very commands the guard refuses, so a report pasted into the
command would be refused. wfctl saves it as that reviewer's report, marked as relayed and
carrying the reason the reviewer gave for the block. The roster shows the
relay on the reviewer's line, such as `s2 claude ✓ relayed: write denied`.
The coordinating agent checks the reason against what it saw. If the reviewer
wasn't really blocked, it reports a gap to Andre.

**Why this priority**: Permission refusals already happen in unattended runs,
and without a relay they leave a run that can never complete.

**Independent Test**: Relay a report with a block reason and read the roster.
The line reads `✓ relayed:` with that reason, and the run completes.

**Acceptance Scenarios**:

1. **Given** a relayed report with a block reason that names the newest
   commit, **When** wfctl checks the run, **Then** it accepts the report and
   the roster shows the reason.
2. **Given** a relay with no block reason, **When** the coordinating agent
   runs `wfctl relay`, **Then** wfctl refuses it and the run stays incomplete.
3. **Given** a relayed report that names an older commit, **When** wfctl
   checks the run, **Then** it doesn't accept it, the same as a written
   report.

---

### User Story 5 - A repository chooses its reviewers and adds its own groups (Priority: P3)

A repository declares its reviewers in the `review` section of `wfctl.json`.
It lives there rather than under `.agents/`, because `install-skills`
rewrites `.agents/` and a policy written there vanishes with no error.

The section holds two keys. `commands` maps each model other than Claude to
the command that starts it. `groups` is a list, and each entry names its
group, can name a review skill, and lists its reviewers as a model name and an
exact count:

```json
"review": {
  "commands": { "codex": "codex exec --sandbox read-only" },
  "groups": [
    { "group": "security",
      "reviewers": [ { "name": "claude", "count": 2 }, { "name": "codex", "count": 2 } ] },
    { "group": "money-rules", "skill": "money-rules-review",
      "reviewers": [ { "name": "claude", "count": 2 } ] }
  ]
}
```

A repository can add other models, change the reviewers in the security or
code group, and add groups of its own. It can't remove the security or code
group, and those two always run first. A group the list doesn't name gets
three Claude reviewers. Each reviewer id is the group's first letter plus a
number, such as `s1`, `c1`, and `m1`.

**Why this priority**: The default of three Claude reviewers per group
already delivers User Stories 1 - 4. Other models and custom groups add to it.

**Independent Test**: With the example above, start the security group. The
run record lists `s1` - `s4`, two of them Claude and two Codex, and the code
group's run lists `c1` - `c3`, all Claude.

**Acceptance Scenarios**:

1. **Given** a custom group listed before `code`, **When** the panel runs,
   **Then** security and code still run first and the custom group runs
   after them.
2. **Given** two groups whose names start with the same letter, **When**
   `wfctl check config` runs, **Then** it reports the clash.
3. **Given** a reviewer whose model has no entry in `commands`, **When**
   `wfctl check config` runs, **Then** it reports the missing command.
4. **Given** a count below 1, **When** `wfctl check config` runs, **Then** it
   reports the count.
5. **Given** a listed model whose command can't run, **When** the group runs,
   **Then** wfctl prints one `⚠` line saying why, the roster marks those
   reviewers ✗ with the reason, and the other reviewers carry on. The run
   completes without their reports, because otherwise a missing Codex install
   would block every pull request.

---

### User Story 6 - The security reviews ship with wfctl (Priority: P3)

Neither security review ships with wfctl today. `/security-review` is a
Claude Code command, and `security-and-hardening` is a plugin skill. After
this change, both are vendored into `wfctl/agents/skills/`, so every
repository that installs wfctl's skills has them. Both are MIT licensed, and
each one is credited the way `vendor-upstream-skills.md` already credits a
derived file. `security-and-hardening` is a skill, so its `SKILL.md` ends with
the attribution line. The `/security-review` file stays unedited, so it carries
no line. Its credit is a row in the record's table and an entry in `NOTICES.md`
that names the file by path, the same way the Spec Kit templates are credited.
Reviewers read the vendored file by path, because Claude Code's built-in
`/security-review` would otherwise take its place.

The vendored `/security-review` file opens with git commands that review the
whole branch, which contradicts reviewing only the new commits. A wfctl note
beside the file tells the reviewer to skip that section and review the commit
range wfctl gives it. The file itself stays unedited, so an upstream pull
doesn't need a hand merge.

**Why this priority**: Without the vendored copies, User Story 1 works only
where Claude Code and the plugin are installed.

**Independent Test**: Run `uv run wfctl install-skills` in a fresh repository
and find both security reviews in the installed tree, credited as above.

**Acceptance Scenarios**:

1. **Given** a fresh install, **When** a security reviewer starts, **Then** it
   reads both vendored security reviews by path.
2. **Given** a branch with an earlier review, **When** a security reviewer
   runs, **Then** its findings stay inside the new commits.

---

### Edge Cases

- A branch with no review history has no last reviewed commit. Its first run
  starts where the branch left the trunk branch, and until that run completes
  the review check treats every commit as unreviewed.
- The state directory is removed, or `WFCTL_STATE_DIR` points at a new path.
  The next run starts where the branch left the trunk branch. That costs one
  larger review and lets nothing through.
- The agent adds a commit while reviewers are reading. Their reports name the
  older commit, so wfctl doesn't accept them, and the run stays incomplete.
- The configuration changes partway through a run. The run record already
  lists the expected reviewers, so the run can't complete with fewer reports.
- A report is cut off partway. The verdict sits at the end, so a truncated
  report has none and wfctl doesn't accept it.
- A command only mentions `gh pr create`, such as an `echo`, on an unreviewed
  branch. The review check refuses it, and the refusal lists the commits. The
  check matches the text on purpose. A check that matched only a command whose
  first word is `gh` would allow `bash -c "gh pr create"`,
  `env GH_TOKEN=x gh pr create`, and `/opt/homebrew/bin/gh pr create`. A wrong
  refusal costs the agent one reworded command, while a wrong allowance opens a
  pull request with no review.
- A command chains a pull request command after another command, such as
  `git commit -am fix && git push && gh pr create --fill`. The review check
  refuses it and asks for the pull request command on its own. The check reads
  the branch and its newest commit before any of the text runs. A commit, a
  push, a `cd`, or a `git switch` earlier in the same text would change what
  the pull request command acts on after the check has judged it.
- A pull request command holds a command substitution, such as
  `gh pr create --fill --title "$(git commit -qam fix && git push -q && echo t)"`.
  The review check refuses it for the same reason. The shell runs the
  substitution before `gh`, so the pull request would open at a commit the
  check never saw.
- A pull request command carries an environment prefix or runs through `env`,
  such as `GIT_DIR=../630-x/.git gh pr create --fill` or
  `env -C ../630-x gh pr create`. The review check refuses it. The check's own
  `git` and `gh` calls don't see the prefix, so it would judge this branch
  while `gh` opens the pull request for another one.
- A `gh` command word isn't written out plainly, such as
  `gh pr $(git push -q) create`. The review check refuses it, since it can't
  tell whether the command opens or merges a pull request.
- The agent runs a `gh` extension or shortcut, such as `gh stack merge`, which
  merges a stack of pull requests with no prompt. The review check refuses
  any word after `gh` that isn't one of `gh`'s own commands, so a person runs
  extensions in their own terminal. An extension run through
  `gh extension exec` isn't refused, and is a known limit listed below.
- A flag sits before `gh`'s verb, such as `gh pr --squash=true merge 630`,
  which `gh` runs as a merge. The review check refuses it unless the flag is
  one plain `-R` naming `OWNER/REPO` or `github.com/OWNER/REPO`. Each plan
  review found another spelling `gh` accepts there, so the check allows the
  one spelling the agent needs.
- The program name is written in another case, such as `GH pr merge 630`.
  macOS runs that as `gh`, so the review check matches the program name in
  any case.
- The agent merges another branch's pull request. From a feature branch's
  worktree, the review check refuses it, because a worktree opens and merges
  only its own branch's pull request. From the checkout on the trunk branch,
  where a person orchestrates, the check looks up that pull request's branch
  and reads its reviews. Otherwise a reviewed current branch would let an
  unreviewed pull request merge.
- The review check itself fails, through a bug or `gh` timing out, on a fully
  reviewed branch. The check refuses the command and names the error, and the
  agent can't get past it. A sign-off doesn't help, because the error stops
  the check either way. The refusal says that a person can run the command in
  their own terminal, where the hook doesn't run.
- A pull request opened without `gh`, such as through a GitHub plugin or the
  browser, isn't checked. Neither is one opened by an agent without hooks.
  The required CI check in #627 covers both.
- A `gh api` call that writes through a variable path, such as
  `gh api "$URL" --input body.json`, or a GraphQL call that reads its query
  from a file, such as `gh api graphql -F query=@mutation.graphql`. The review
  check refuses both every time, since it can't read what they write to.
- Some `gh` commands open or merge a pull request without the review check
  catching them. The required CI check in #627 covers them, since GitHub
  blocks the merge itself however the command was typed. Until #627 ships,
  they stay open. They fall into two groups:
  1. A command that looks ordinary, where what changes it lives outside the
     text. `gh pr merge` without `--auto` while required checks are still
     pending is one. `gh` then turns on auto-merge, and GitHub merges
     whatever the branch head is when the checks pass.
  2. A command disguised in a way the check's rules don't read. Six plan
     reviews in a row each found more of these, so the check stopped adding a
     rule for each one. The known ones are:
     1. A backtick substitution glued to `pr`, such as
        `` gh pr` git push -q` merge 630 ``.
     2. An extension run through `gh extension exec`, such as
        `gh extension exec stack merge`.
     3. A two-word shortcut under one of `gh`'s own commands, such as
        `gh alias set 'pr ship' 'pr merge'` followed by `gh pr ship 630`.
     4. A `gh api` create whose path ends in a fragment, such as `pulls#x`,
        or whose body flag is grouped after another short flag, such as
        `-ifhead=x`.
     5. `gh` run through `xargs`, such as
        `printf '%s\n' pr merge 630 | xargs gh`.
     6. A merge through a `repositories/<id>/pulls/<n>/merge` path, which
        names another repository by its number rather than its name.
     7. A GraphQL mutation built in a variable or a substitution, such as
        `gh api graphql -f query="$(cat m.graphql)"`.
     8. A wrapper that moves `gh` to another directory or feeds it an
        argument, such as `uv run --directory ../630-x gh pr create`,
        `direnv exec ../630-x gh …`, or `<<<630 xargs gh pr merge`.
     9. A quoted or variable program name, such as `"gh" pr merge 630` or
        `$GH pr merge 630`.
     10. A `gh` call inside something the agent runs whose text the command
         doesn't show: a script, such as `.github/scripts/release.py`, which
         runs `gh pr create`, a git alias written into `.git/config`, such as
         `pm = !gh pr merge`, or a shell function or alias from the person's
         profile.
     11. A command aimed at another GitHub host, such as
         `gh api --hostname ghe.example.com` with `{owner}/{repo}`
         placeholders, or an `-R` value written as a URL.
- Some ordinary commands are refused even though they open or merge nothing.
  Each costs the agent one reworded command:
  1. A `gh api` call with `-f merge_method=merge` before the path, which reads
     as an environment prefix. Writing the path first avoids it.
  2. A `gh api` call using the `:owner/:repo` placeholders, which compare as
     another repository. The `{owner}/{repo}` placeholders avoid it.
  3. A `gh api` write through a variable path, such as a reply to a review
     comment. Writing the path out avoids it.
  4. A search that quotes a refused form, such as
     `grep "gh pr create\|gh pr merge"` or `rg 'gh pr.*merge'`. Searching
     without the `gh ` prefix avoids it.
  5. A command that names `gh` as an argument before using it, such as
     `which gh && gh pr view`. Running `which gh` on its own avoids it.
  6. A commit message that quotes a refused form, such as
     `gh "$X" merge 630`. Writing the message to a file and committing with
     `git commit -F <file>` avoids it.
- An agent writes a report file or the sign-off file itself, instead of
  running the command. The check can't tell, the same limit wfctl's test
  verification already has.
- An agent runs the sign-off command through a pseudo-terminal, such as one
  from `script` or Python's `pty` module, with a spelling the guard's pattern
  misses. The command's terminal check passes. That takes no less effort than
  writing the sign-off file directly, so the terminal check is a second
  obstacle for the agent, not enforcement.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: `opening-a-change` MUST run the security group and then the
  code group on every change, with no condition that skips either one.
- **FR-002**: Each security reviewer MUST run both vendored security reviews,
  `security-and-hardening` and `/security-review`, against the commit range
  wfctl gives it.
- **FR-003**: The security group MUST commit its fixes before the code group
  starts.
- **FR-004**: The findings from every group MUST reach Andre in chat as one
  table, each finding naming its reviewer id and model. No finding, table, or
  status line from any group may appear in the pull request description.
- **FR-005**: When a group starts, wfctl MUST write a run record listing the
  expected reviewers and the commits to review, from the group's last
  reviewed commit to the current commit.
- **FR-006**: A run MUST leave out commits merged in from the trunk branch
  that `trunk` in `wfctl.json` names, defaulting to the remote's default
  branch, which is `main` in this repository.
- **FR-007**: The first run on a branch MUST start where the branch left the
  trunk branch.
- **FR-008**: wfctl MUST accept a report only when it names the run's newest
  commit and ends with a verdict. wfctl reads the whole report.
- **FR-009**: When every expected reviewer in the run record has an accepted
  report, wfctl MUST mark the run complete and move the group's last reviewed
  commit to the run's newest commit. Otherwise the last reviewed commit MUST
  stay where it was.
- **FR-010**: After each group, wfctl MUST print the roster, one line per
  expected reviewer with its id, model, and ✓ or ✗, and the relay reason
  where there is one.
- **FR-011**: wfctl MUST keep the run records, the reports, and each group's
  last reviewed commit in a `reviews/` folder in the branch's state directory,
  and read them from that one location only. The panel skill MUST ask wfctl
  for that path.
- **FR-012**: The worktree guard MUST refuse `gh pr create`, `gh pr new`
  (`gh`'s built-in second name for `gh pr create`), `gh pr merge`
  (including with `-R` or `--repo` before `pr` or before the verb, with its
  value after a space, after `=`, or attached to `-R`), a `gh api` call to a
  pull request's `merge` or `merge-async` endpoint, a `gh api` call that
  creates a pull request through the `pulls` endpoint, and a `gh api graphql`
  call naming `createPullRequest`, `mergePullRequest`,
  `enablePullRequestAutoMerge`, or `enqueuePullRequest`, with exit code 2, while
  any review group, custom groups included, has commits after its last
  reviewed commit that no sign-off covers. The refusal MUST list those commits
  on stderr, grouped by review group. The `gh api` create call and the
  GraphQL calls MUST be refused every time, naming `gh pr create` or
  `gh pr merge` instead, because the branch they act on is in a request body
  the check can't read reliably. `gh pr merge --auto` MUST also be refused
  every time, because GitHub would later merge a head the check never judged.
- **FR-012a**: When a command names a pull request or branch other than the
  current one, such as `gh pr merge 630`, `gh pr create --head <branch>`, or a
  `merge-async` call with a pull request number, the review check MUST judge
  that pull request's branch. It MUST look the branch up from GitHub, and MUST
  refuse when the lookup fails. When the judged branch isn't the current
  branch, the review check MUST refuse the command unless the current branch
  is the trunk branch FR-006 names. A command that names another repository,
  with `-R`, a `repos/<owner>/<repo>/` path in a `gh api` call, or an
  `owner:` prefix on `--head` naming another owner, MUST be refused, since
  that repository's reviews aren't kept here.
- **FR-012b**: The review check MUST refuse a matched pull request command
  that follows any other command in the same text, and ask for it on its own.
  It MUST also refuse one that holds a command substitution or a process
  substitution, since the shell runs it before the pull request command. It
  MUST refuse one preceded by a `NAME=value` word or by `env`. It MUST judge
  every match in the text, and one refusal MUST refuse the whole text. It MUST
  also refuse, every time, three kinds of `gh` command it can't read. The
  check can't tell what such a command does, so these refusals don't wait for
  one of FR-012's commands to match:
  1. A word after `gh` that isn't one of `gh`'s own commands, on a fixed list
     wfctl keeps. That covers an extension such as `gh stack merge`, a
     one-word shortcut made with `gh alias set`, and `gh "$X" merge 630`. The list
     leaves out `copilot` and `agent-task`, which hand the request to another
     agent.
  2. A verb after `gh pr` that holds a shell expansion, a glob character, or a
     quote inside the word, such as `gh pr 'merge' 630`.
  3. Any word starting with `-` before the word after `gh` or before the verb
     after `gh pr`, other than one `-R` or `--repo` flag whose value is
     `OWNER/REPO` or `HOST/OWNER/REPO` in letters, digits, `.`, `_`, and `-`.
     So `gh pr --squash=true merge 630`,
     `gh -R <this repo> -R owner/other pr merge 630`, and
     `gh -R $(git push -q; echo a/b) pr merge 630` refuse.

  A host other than `github.com` MUST refuse as another repository. The review
  check MUST match the program name `gh` in any case, since macOS runs `GH` as
  `gh`. It MUST read a `gh api` body flag or `POST` method as its own word,
  with its value attached, or after `=`, such as `-fhead=x` or `-XPOST`. The
  disguised commands listed under Edge Cases are known limits, which these
  requirements don't cover.
- **FR-012c**: The review check MUST read the repository, the current branch,
  and `HEAD` from the session's working directory that the hook payload names,
  and MUST run its `gh` and `git` calls there, as the worktree check does. It
  MUST refuse a matched command whose payload names no working directory.
- **FR-013**: The worktree guard MUST refuse the sign-off command every time
  an agent runs it. The sign-off command MUST also refuse to run without an
  interactive terminal. That is a second obstacle for a spelling the guard
  misses, not enforcement, because a pseudo-terminal satisfies it (Edge
  Cases).
- **FR-014**: A person MUST be able to sign off on the remaining commits with
  the sign-off command in their own terminal, after which the review check
  allows the pull request. The command MUST work at any time, not only after
  three rounds. A sign-off MUST cover only the commits that exist when it is
  made.
- **FR-015**: The review check MUST refuse a pull request when it can't read
  the review record, and when any other error stops it from reaching an
  answer once a command has matched. The refusal MUST name the error and say
  that a person can run the command in their own terminal, where the hook
  doesn't run.
- **FR-016**: The review check MUST run inside the existing worktree guard, in
  its own `try` block, before the worktree check. A command that matches none
  of the commands FR-012 and FR-013 name, and holds none of FR-012b's unreadable
  `gh` command words or flags before the verb, MUST go on to the worktree check
  with no file read and no git call.
- **FR-017**: `wfctl relay` MUST take a reviewer id and read the report from
  the file its `--from` option names. It MUST save the report under that id, marked as relayed and
  carrying the block reason, and MUST refuse a relay with no block reason.
- **FR-018**: wfctl MUST read the `review` section of `wfctl.json`: `commands`
  mapping each model other than Claude to its command, and `groups` as a list
  of entries with `group`, an optional `skill`, and `reviewers` of `name` and
  `count`.
- **FR-019**: Security and code MUST run first whether or not `groups` names
  them. A built-in group the list doesn't name, or names without a
  `reviewers` key, MUST get three Claude reviewers. Other groups MUST run in
  list order.
- **FR-020**: Each reviewer id MUST be the group's first letter plus a number.
  A group name MUST be lowercase letters, digits, and hyphens, starting with a
  letter.
- **FR-021**: `wfctl check config` MUST report two groups that start with the
  same letter, a group name that breaks FR-020's rule, a group whose
  `reviewers` list is empty, built-in or custom, a custom group with no
  `reviewers` key, a reviewer whose model has no command, a count below 1, and a
  `groups` value that isn't a list.
- **FR-022**: A repository with no `review` key MUST get three Claude
  reviewers in each built-in group, and the report MUST not mention other
  models.
- **FR-023**: A listed model that can't run MUST produce one `⚠` line saying
  why, and the other reviewers MUST carry on. The run MUST complete without
  that model's reports. A run in which no reviewer can run MUST stay
  incomplete, so a group never completes with no review at all.
- **FR-024**: Both security reviews MUST ship under `wfctl/agents/skills/`,
  each with a row in `vendor-upstream-skills.md` and an entry in `NOTICES.md`.
  The `security-and-hardening` skill MUST end with the attribution line. The
  vendored `/security-review` file carries no line, so its `NOTICES.md` entry
  MUST name it by path.
- **FR-025**: The vendored `/security-review` file MUST stay unedited. A wfctl
  note beside it MUST tell the reviewer to skip its git section and review the
  commit range wfctl gives it. The note MUST also tell the reviewer to write
  one report covering both reviews, in the shape wfctl counts, to the path
  wfctl printed, and say that this outranks the file's own instructions about
  the reply and about writing files.
- **FR-026**: `fanning-out-code-review` and `opening-a-change` MUST start each
  group through wfctl, launch each reviewer, relay a blocked reviewer's report
  through `wfctl relay`, and read the roster wfctl prints.

## Key Entities _(include if feature involves data)_

- **Review group**: One panel with a name, an optional review skill, and its
  reviewers. Security and code are built in, and a repository can add more.
- **Reviewer**: One model running one review in a group, identified by the
  group's first letter plus a number, such as `s2`.
- **Run record**: What one run of one group expects: the reviewer ids and the
  commit range, ending at the run's newest commit.
- **Report**: One reviewer's findings for one run. It names the commit it
  reviewed and ends with a verdict. A relayed report also carries the block
  reason.
- **Last reviewed commit**: Per group, the newest commit a complete run
  covered. The next run starts after it.
- **Roster**: The per-run list of expected reviewers with ✓ or ✗, printed
  after each group.
- **Sign-off**: A person's statement, made outside the agent, that the
  branch's unreviewed commits may go ahead without another review.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Every pull request opened or merged with one of FR-012's
  commands in this repository after the change has a complete run of every
  group covering its newest commit, or a person's sign-off. Zero exceptions.
  The known limits under Edge Cases are outside this count, and #627 covers
  them.
- **SC-002**: A missing report, a report with no verdict, or a report about
  another commit never completes a run, in every test that exercises those
  cases.
- **SC-003**: The review check adds under 1 ms per shell command that matches
  none of its commands, measured on an `ls` payload before and after the
  change.
- **SC-004**: Zero review reports land on `specs-trunk` from a branch that
  stores its specs after the change.
- **SC-005**: A repository with no `review` key runs 6 reviewers, 3 per
  built-in group, with no configuration added.

## Validation Strategy _(mandatory)_

- `uv run pytest -q`, `uv run ruff check wfctl/ tests/`, and
  `uv run mypy wfctl/` all pass.
- Tests cover each `wfctl check config` finding for `review`, the default
  roster with no `review` key, and built-in groups running before a custom
  group listed first.
- Tests cover a report that names an older commit, a report with no verdict,
  and a missing report, and check that none of them moves the last reviewed
  commit.
- Tests pipe every command FR-012 and FR-013 name, including `-R` before `pr`
  and before the verb, and the `gh api` and GraphQL forms, into `wfctl hook worktree-guard` on
  reviewed, unreviewed, and unreadable-record branches, and check the exit
  code and stderr. Tests also cover a `gh` lookup that times out and an
  unexpected error after a match, and check that both refuse.
- Tests pipe a verb's flag before the verb, two `-R` flags before `pr`, an
  `-R` value holding a substitution, `gh --version`, `gh stack merge`, and a
  `gh api` create with attached `-fhead=x` fields, and check that each refuses
  on a reviewed branch. Tests also pipe one plain `-R` before `pr` and
  before the verb, and check that each is judged.
- Tests pipe chained forms, such as `git push && gh pr create` and
  `gh pr create --fill && gh pr merge 630`, and check that both refuse.
- A test relays a report from a file that quotes `gh pr create` and
  "review sign-off", and checks that the guard allows the relay command.
- Tests pipe a merge of another branch's pull request from the checkout on the
  trunk branch, with that branch reviewed, unreviewed, and impossible to look
  up, and check that the review check judges that branch rather than the
  current one. A test pipes the same merge from a feature branch's worktree and
  checks that it refuses.
- Tests check that a fix commit from the code group blocks the pull request
  until the security group reviews it.
- Tests relay a report with a reason, with no reason, and naming an older
  commit.
- A test runs a review group, then `wfctl store specs`, and checks that no
  file under `reviews/` lands in the spec store's commit.
- A timing run of the worktree guard on an `ls` payload, before and after the
  change, compared with the numbers in the `_hook.py` docstring.
- `uv run wfctl install-skills`, then one `opening-a-change` run on a real
  branch, to exercise the updated skills end to end.
- `uv run wfctl check config` passes on this repository's `wfctl.json`.

## Assumptions

- Pre-specify design context loaded from `design.md` in this feature's
  directory.
- Andre is the only user, and he opens every pull request from one machine.
  A second machine can't see the review history in the state directory. The
  required CI check in #627 replaces this assumption.
- Every pull request is opened and merged with `gh`.
- A round is one complete run of every group. The cap stays at three, and
  #626 decides whether it becomes configurable and how rounds are counted.
- The sign-off command's name is chosen in the plan.
- Codex runs as a read-only reviewer with `codex exec --sandbox read-only` and
  still produces a report wfctl can read.
- The 376 review reports already on `specs-trunk` stay there. Removing them is
  a separate decision for Andre. The same goes for a `reviews/` folder an
  earlier panel left in a branch's spec directory. SC-004 counts reports
  written after the change, not those folders.
- A listed model is available when its command is on `PATH`. The agent's
  shell sets `PATH`, so an agent could hide a model. That stays visible,
  because the roster marks the model ✗ with a `⚠` line. A model that is on
  `PATH` but fails when it runs, such as Codex without a login, writes no
  report, so its run stays incomplete until it is fixed or a person signs off.
- Every design record for this feature stays proposed. Andre accepts them
  later, after end-to-end validation.
