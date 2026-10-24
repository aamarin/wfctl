# A security review panel runs before every change opens

## Problem Statement

How might we give every change a dedicated security review from several
independent reviewers, without the agent grading its own panel?

## Recommended Direction

Before a change opens, `opening-a-change` runs two review groups, security
first and code second. Each security reviewer runs both security reviews: the
`security-and-hardening` skill, which starts from a threat model, and
Anthropic's `/security-review` command, which looks for exploitable
vulnerabilities in the diff. The security group commits its fixes. The code
group then reviews the result with the full `code-review` rubric. Both groups
run on every change, so an agent in an unattended run never decides to skip
one.

The coordinating agent launches the reviewers, and right now it also reports
whether the panel ran. Nothing records which commits the panel read. With this
change, wfctl keeps that record. When a group starts, wfctl writes a run record
listing the expected reviewers and the commits to review. Each review covers
every commit since the last review, except commits merged in from `main`. A
round is one complete run of every group over the new commits, and the next
round reviews that round's fixes. A report counts only when it names the run's newest commit and
ends with a verdict. When every expected reviewer has reported, wfctl moves
the last reviewed commit forward.

A reviewer blocked from writing its report sends it as its reply instead. The
coordinating agent then runs the `wfctl relay` command, which saves the reply as
the reviewer's report with the block reason. After each group, wfctl prints the
roster, a list of every expected reviewer with ✓ for an accepted report and ✗
for a missing one. For example, a relayed report shows as
`s2 claude ✓ relayed: write denied`.

The worktree guard is the hook wfctl installs to check each shell command an
agent runs. Its review check blocks opening or merging a pull request while
the branch has unreviewed commits. After three rounds, the agent asks a person
to sign off on the remaining commits. The person runs wfctl's sign-off command
in their own terminal, which works at any time. The worktree guard blocks that
command when an agent runs it.

Both groups' findings go to Andre in chat as one table. Each finding names its
reviewer id and model, such as `s3 codex`. Nothing from either panel goes in
the pull request description.

A repository sets its reviewers in `wfctl.json`. It can add models such as
Codex, change the security or code reviewers, and add its own review groups,
but it can't remove the security or code group. By default, each group has
three Claude reviewers.

## Key Assumptions to Validate

- [ ] Andre is the only user, and he reviews and opens every pull request from
  one machine. A second machine can't see the review history in the state
  directory. When a second person opens a pull request, the required CI check
  in #627 replaces this assumption. Test: check that Andre opened every pull
  request in this repository.
- [ ] Every pull request is opened and merged with `gh`. The worktree guard sees
  only shell commands, so it misses a pull request opened through a GitHub
  plugin. If another tool can open one, such as a GitHub MCP server, the
  required CI check in #627 closes the gap. Test: list the tools the agent can
  use to open a pull request, and check that `gh` is the only one.
- [ ] A reviewer follows wfctl's note over the vendored `/security-review` file.
  The file tells the reviewer to review the whole branch, and the note tells it
  to review only the new commits. The file also ends by asking for the
  markdown report and nothing else, and says not to write files, while the
  note asks for a report file with a `Reviewed:` line and a verdict. Test: run
  one security reviewer on a branch with an earlier review, and check that its
  findings stay inside the new commits, and that wfctl counts its report.
- [ ] A reviewer blocked from writing can still reply to the coordinating agent.
  Test: deny a reviewer's write in a test run, and check that the relayed report
  reaches wfctl with its block reason.
- [ ] Codex runs as a read-only reviewer with `codex exec --sandbox read-only`
  and writes a report wfctl can read. Test: run one panel with a Codex reviewer,
  and check that wfctl accepts its report.
- [ ] The review check adds well under a millisecond to each shell command.
  Test: time the worktree guard on an `ls` payload before and after the change.

## MVP Scope

In scope:

1. The two security reviews, vendored into `wfctl/agents/skills/`. Each has a
   row in `vendor-upstream-skills.md` and an entry in `NOTICES.md`. The
   `security-and-hardening` skill also ends with the attribution line. The
   `/security-review` file carries no line, so its `NOTICES.md` entry names it
   by path. Both are MIT licensed.
2. A wfctl note beside the vendored `/security-review` file. It tells the
   reviewer to skip the file's git section and review the commit range wfctl
   gives it. The file itself stays unedited.
3. The `review` section in `wfctl.json`, with `commands` and `groups`, and
   `wfctl check config` findings for it.
4. The run record, the last reviewed commit, and the reports, all in the
   branch's state directory.
5. The report check, which accepts a report only when it names the newest
   commit and ends with a verdict.
6. The `wfctl relay` command for a reviewer blocked from writing.
7. The review check in the worktree guard, and the sign-off command it
   protects.
8. `fanning-out-code-review` and `opening-a-change`, updated to start each group
   through wfctl, launch each reviewer, and read the roster wfctl prints.

Everything under Not Doing is out of scope.

## Not Doing (and Why)

- A required CI check that blocks the merge on GitHub. The review records stay
  on the local machine, so CI can't see them. #627 covers pushing them.
- Vendoring the `claude-security` plugin. Its license is "All rights reserved".
- Splitting the security skills by language or framework. Both skills already
  read the diff they're given, and one set is simpler to keep current.
- Having wfctl launch the Claude reviewers itself. wfctl can't start a host's
  own subagents. A reviewer that never launches writes no report, so the run is
  incomplete anyway.
- Detecting a report the agent forged. An agent can still write a report file
  itself. wfctl's test verification has the same limit, since it's a local
  tool.
- Adding plan review, clarify, or analyze as review groups. Plan review can join
  later as one more group.
- Removing the 376 review reports already committed to `specs-trunk`. Andre
  decides that separately.

## Open Questions

- Whether the three-round cap is configurable, and how rounds are counted.
  #626 holds these.

## Software design decisions

- docs/architecture/design/622-review-records-in-state-dir.md — wfctl keeps review reports and run records in the branch's state directory
- docs/architecture/design/622-review-groups-list.md — a repository lists its review groups under `review` in `wfctl.json`
- docs/architecture/design/622-blocked-reviewer-relays-report.md — a reviewer blocked from writing returns its report, and wfctl saves it as relayed
- docs/architecture/design/622-review-check-in-worktree-guard.md — the worktree guard also runs the review check
