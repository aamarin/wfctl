---
name: fanning-out-code-review
description: 'Review a change with a panel of independent reviewers instead of one: start each review group with wfctl, dispatch one fresh-context reviewer per id it prints, let wfctl confirm every one of them reported, then reconcile and verify the findings yourself. Use when asked to review this, review the PR, review a diff, check something before merge, and after finishing an implementation. Layers over requesting-code-review (the trigger and the hand-off), code-review (the rubric) and receiving-code-review (verify before implementing); it owns none of those.'
# No `disable-model-invocation`, for #124's reason: the moment a panel is most
# worth running — a change about to be opened or merged — is a moment nobody
# types a command. `install-skills` names this skill among those it mirrors into
# `.claude/skills/`, so the model can reach it without one.
---

# Fanning out a code review

One reviewer gives you one reading of a diff, and no way to tell a real defect
from that reader's blind spot. A panel of reviewers that can't see each other's
findings gives you a second signal for free. Agreement between two of them is
evidence, and a finding only one of them raised is a hypothesis you now have to
test.

The fan-out gives you independent context, not coverage. The design
follows from that distinction, as "The axes are not the split" below explains.

wfctl keeps the record of the panel, not you. It decides which commits each
review group covers, which reviewers it expects, whether each report counts,
and when a run is complete. The coordinator shouldn't decide those, since it
would be grading its own panel (`review-covers-unreviewed-commits`). The
worktree guard reads the same record and refuses `gh pr create` and
`gh pr merge` until every group has reviewed the newest commit.

**Announce at start:** "I'm using the fanning-out-code-review skill to run a
review panel over this change."

## What this skill does not own

| Skill | Owns |
| --- | --- |
| `.agents/skills/requesting-code-review/SKILL.md` | when to request a review, and the hand-off rules for dispatching one |
| `.agents/skills/code-review/SKILL.md` | the rubric: the passes, the severities, the report format |
| `.agents/skills/receiving-code-review/SKILL.md` | verifying feedback before implementing it |

Read them. Don't edit them, and don't restate them here. This skill adds three
things none of them has: the fan-out, reading wfctl's check that every reviewer
reported, and the reconciliation.

### The axes are not the split

The obvious panel is one reviewer per axis, such as correctness,
simplification, and over-engineering. Don't build that one. `code-review`
already folds those into a single pass on purpose ("*one* review instead of
four overlapping ones"), and simplification and over-engineering are each one
of its own passes. A panel by axis contradicts a skill this project ships, and
it gives each reviewer a narrower brief than a single reviewer would have had.

Every reviewer in a group runs that group's whole skill. Independence is what
varies between reviewers, and the rubric stays the same.

## Step 1: Start the group

A repository has one or more review groups, and each group has its own
reviewers and its own skill. List them in the order they run:

```bash
wfctl review groups
```

```text
security  reviewing-security  s1 s2 s3 claude
code      code-review         c1 c2 c3 claude
```

The second column is the skill each of the group's reviewers follows. Security
and code always run first, in that order, and any group the repository adds
runs after them. Run this skill once per group, in that order. Commit each
group's fixes before the next group starts, so the code group reviews the
security group's fixes and a later group reviews both.

Start the group:

```bash
wfctl review start security
```

```text
security run 003 · 2 commits since a1b2c3d · head 9f8e7d6
reports: <state>/reviews/security/runs/003/
s1 claude
s2 claude
s3 codex  codex exec --sandbox read-only
```

wfctl writes a run record, `run.json`, into the reports folder. It lists the
reviewers it expects, the run's head, and the commits the run covers, which
are every commit since the group last completed a run. Each reviewer reads the
commits from that file, so every reviewer reviews the same commits and wfctl
counts the same ones.

When the group has nothing new to review, `review start` prints
`security is up to date at 9f8e7d6` and writes nothing. Go on to the next group.

A line with `✗ unavailable` names a reviewer whose model's command isn't on
`PATH`. wfctl leaves it out of the run and prints a `⚠` line saying so. Pass
that line on to the person you're working for, since a group with a model left
out is a smaller panel than the repository asked for.

## Step 2: Dispatch

Launch one reviewer per id `review start` printed, and give each one only two
values: its id and the reports folder. Don't give a reviewer a commit range or a
trunk branch to build one from. `run.json` already holds the commits, and a
range built with `git diff` or `git log` includes merge commits and the commits
a merge brought in from the trunk, which wfctl leaves out.

Per `requesting-code-review`'s hand-off rules, each reviewer also gets what the
change is supposed to do and the project's rules. Never give it your session
history, and never another reviewer's findings. A reviewer primed with the
first reviewer's report is not a second opinion.

Every dispatch instruction carries these six:

- **Read the group's skill by its path and follow it,** such as
  `.agents/skills/code-review/SKILL.md` for the code group or
  `.agents/skills/reviewing-security/SKILL.md` for the security group. Don't
  invoke a Skill named `code-review`, or a Skill with any group's skill name.
  The path matters because a host can ship its own command under the same
  name, and a reviewer that uses the Skill tool gets the host's command
  instead of this rubric. Claude Code's built-in `/code-review` is a different
  review. It fans out helper agents that report into your session and never
  receive the bullets below, and on two panels an agent running under it
  edited the shared tree. Give the path rather than pasting the rubric, so that
  each reviewer reads all of it and not your summary of it.
- **Review the commits listed in `run.json` in the reports folder,** each with
  `git show <sha>`, and report a finding only if it's still there at the run's
  `head`.
- **Write the report to `<reports folder>/<id>.md`.** The report includes a
  `Reviewed: <sha>` line naming the run's head, and its last line is the
  verdict. wfctl counts a report only when its `Reviewed:` line names the head
  with at least seven digits and it ends with `Verdict: Approve` or
  `Verdict: Request changes`. A report cut off partway has no verdict at its
  end, so it doesn't count.
- **Say which passes ran and what each covered,** whether or not it found
  anything. `code-review` Step 5 ends a clean report at the over-engineering
  metric and a verdict. That shows a reviewer worked, but not what it looked
  at. This skill's Step 5 gives a reviewer that found nothing a row whose
  Finding cell carries its coverage, and this bullet is how that requirement
  reaches the reviewer.
- **Report only. Change nothing.** Reviewers share a worktree with each other
  and with you. Three agents editing a tree a fourth is reading corrupts all
  four, and you can't recover afterwards, since you can't tell whose
  half-applied edit produced the state you're looking at. A reviewer writing
  its own report isn't editing the tree, but touching anything under review
  is. Anything the project later reads back as evidence is off limits too,
  including files outside the tree. Under wfctl, that means `wfctl verify`. It writes one
  record per branch outside the worktree, so a reviewer that runs it replaces
  the parent's proof of done with one taken mid-review.
- **Report any design decision nothing on the change covers:** new stored
  state, a new file or setting the code reads, a new command or flag, or a
  boundary drawn or moved. A record or spec that the change names covers the
  decision. The change calling itself a bug fix doesn't. No check confirms that
  the author asked, before writing code, whether the change needs a spec, and
  an agent that skipped the question can still answer "No" when the PR opens.
  A reviewer that reads only the diff is the first reader who didn't write it,
  so it is best placed to notice. The coordinator shows these findings in the
  table before the PR opens, and the author writes the "Needs a spec?" answer
  after reading them.

Dispatch them in parallel, since they are independent by design. Sharing one
tree is a deliberate choice, not a limitation to work around. A harness that
gives each reviewer its own worktree removes the need for the report-only rule
but gains nothing, since a reviewer produces findings and the parent does the
verification either way.

### A reviewer on another model

A line with a command after the model, such as `s3 codex  codex exec --sandbox
read-only`, is a reviewer you run yourself. The command comes from the
`review.commands` key in the repository's `wfctl.json`. In a repository you
don't own, read that key before running the command, as you would read a hook
the repository ships.

Use the scratch folder your harness gives you, never a fixed path such as
`/tmp/panel/`. Another session, or another user on the same machine, can write
to a shared path, and a report planted there would be relayed as this run's.

To run the reviewer:

1. Write the reviewer's whole prompt, with the six instructions above, to a
   file in your scratch folder.
2. Run the printed command with that file as its input, and redirect its output
   to a second file:

   ```bash
   codex exec --sandbox read-only < <scratch folder>/s3-prompt.md > <scratch folder>/s3-report.md
   ```

3. Relay the output file, as the next section describes, with the reason
   `read-only sandbox`.

### A reviewer that couldn't write its report

A reviewer whose write was denied, or one on a read-only model, returns its
report to you instead of writing it. Save the reply to a file in your scratch
folder with your own file tool, then relay it:

```bash
wfctl relay s2 --reason "write denied" --from <scratch folder>/s2-report.md
```

wfctl saves the report under that id in the group's latest run, marked as
relayed with the reason, and the roster shows the reason on that reviewer's
line. wfctl refuses a relay with no reason.

**Never put a report in a command's text,** whether in a heredoc, an `echo`, or
an argument. The worktree guard matches command text, and a security report
quotes the commands the guard refuses, such as `gh pr create`. The guard then
refuses any command carrying the report while the branch is unreviewed, and the
branch is always unreviewed during a run. A file keeps the report out of the
text the guard reads, which is why `wfctl relay` reads the report only from
`--from`.

Check each relay reason against what you saw. If the reviewer wasn't really
blocked, such as a reviewer that said its write was denied when no denial
reached you, tell the person you're working for. A reviewer that could write
and didn't is a gap in the process that the roster can't show.

**Most often, another skill triggers this one, not something a person said.**
`.agents/skills/opening-a-change/SKILL.md` runs this skill for every group
before a PR opens. An unattended run takes that path, since nobody says
anything and the description above matches nothing (#187).

The reconciled table from Step 5 is this skill's output, and it goes to the
person you're working for, in the conversation. A change description carries
nothing from the panel. `opening-a-change` says the same: no finding of any
disposition, no table, and no roster or status line.

**Comments already on the change are panel members you didn't pay for,** such as
a bot's review or a person's note. Collect them in the same pass. They qualify
because whoever wrote them never had your session. They read the change and
nothing else, which is what this step hands a dispatched reviewer and the only
thing a panel buys. wfctl doesn't count them, since they aren't reviewers in
the run. As a result, they never move a group's record forward. Name them on
the roster line in Step 5, beside the run's reviewers.

## Step 3: Let wfctl confirm every reviewer reported

**This is the step the skill exists for.** In a fan-out, a reviewer that
returns nothing looks the same as a reviewer that found nothing, and an agent
will report the second. One real run produced the completion message *"this is
the completion notification for the review I already relayed above — same
finding, nothing new. No action needed"* for a review that had never arrived.
Asked again, that reviewer produced the only confirmed correctness defect in
the change.

That's why you don't count reports from memory, and you don't count them
yourself. wfctl checks the reports folder against the reviewers it expected:

```bash
wfctl review check security
```

```text
security run 003 · head 9f8e7d6
s1 claude ✓
s2 claude ✓ relayed: write denied
s3 codex  ✗ no report
incomplete: 1 of 3 expected reports missing
```

The roster comes from `run.json`, never from the files on disk, so a reviewer
that never wrote a file shows as `✗ no report` rather than dropping out of the
count. Once every expected report counts, the last line reads
`complete: security reviewed through 9f8e7d6`, and wfctl moves the group's last
reviewed commit to the head. Any other result exits 1.

wfctl accepts a verdict in each form this project's reviewers write it. The
four forms in this project's own spec root all count: `Verdict:`,
`**Verdict: Approve**`, `## Verdict`, and `### Verdict`. Prose that only
mentions a verdict doesn't count.
`test_report_counts_with_each_verdict_spelling_reviewers_use` fails if any of
those forms stops counting, so read it before tightening the rule.

A `✗` line carries one of these reasons:

| Reason | What it means | What to do |
| --- | --- | --- |
| `no report` | nothing on disk for that id | wait if the reviewer is still running, otherwise re-ask it |
| `names <sha>, not <head>` | it reviewed another commit | re-ask it, naming the head |
| `no Reviewed: line` | it didn't say which commit it reviewed | re-ask it |
| `no verdict at the end` | the report has no verdict as its last line | re-ask it |
| `can't read report: <error>` | the file is there and unreadable | re-ask it |
| `unavailable: <reason>` | its model couldn't run | nothing; the run doesn't wait for it |

**`no report` is two different states, and only one of them is a failure.** A
reviewer still running has written nothing yet, and that is the normal state
while a panel works. You can read the roster then, as long as you don't record
the result. A reviewer that has finished and left no report is a failure, not a
pass. Judge whether a reviewer has finished by what the dispatch tells you, not
by what the reviewer says. A reviewer's own "I already reported" is the
recollection this step exists to doubt, while the end of its run is an
observation, so nobody has to trust it. If you write `✗ no report` into the
table for a reviewer that was only slow, you pay for that reviewer's work twice
and put a false statement in the table (#173).

**A finished reviewer with no counted report gets asked again.** Ask it for its
findings in the format `.agents/skills/code-review/SKILL.md` specifies, or the
format of its group's skill, and remind it to read that file rather than invoke
a Skill named `code-review`. A reviewer that wrote nothing may have run the
host's command the first time, and a re-ask that names the skill sends it back
to that command. If a reviewer insists it already reported, ask again,
since the report is the evidence and its recollection is not. A reviewer that
still reports nothing after the re-ask didn't run, so dispatch a replacement
under the same id. A file with no verdict is also the most likely sign that a
reviewer ran the host's command, since that command's output has no verdict
line.

Run `wfctl review check` again after each re-ask, until the last line reads
`complete`. A group isn't done until then, and don't start the next group
before it is.

A run where no reviewer could run never completes. `review check` prints
`incomplete: no reviewer in security could run`. The only ways forward are to
make a model available or to have a person sign off. Tell the person, since the
sign-off is their decision.

### The roster is the whole panel

wfctl checks that every reviewer it expected reported. You check the reverse,
that every report came from a reviewer you dispatched, and skipping that check
lets a stranger's report in.

**A report from an agent you didn't dispatch is not a reviewer's, and being
right doesn't make it one.** On one run, two agents this panel never
dispatched finished while all three real reviewers were still working, and
reported on the same diff through the same channel the reviewers use. One of
their findings was a genuine defect. The panel found it independently forty
minutes later and confirmed it by mutation (#205). A session that folded it in
would have taken a true finding from a source with no independence behind it,
and nothing would have told it so. That's why the rule has no "unless it is
correct" exception: when you read a contaminated report, it looks correct.

**The disqualifier is inheriting your context, not the agent's type.** This
skill hands a reviewer the run, the intent, and the project's rules, and never
your session history. An agent that inherited your context has already read
your reasoning, so its agreement with you is evidence about your reasoning
rather than about the diff. An agent's type can't tell you whether it inherited
your context. Of the two agents above, `ListAgents` listed one as a fork and
didn't list the other, so a rule keyed on type catches one of the two.
Comparing against the ids you dispatched catches both.

wfctl counts only the files named for the run's ids, so a stranger's file in
the reports folder never counts toward a run. A report that arrives as a
completion notification leaves no file, so as each one arrives, check the id it
reports under against the ids `review start` printed.

A report from outside the panel doesn't enter the roster line, doesn't get a
disposition row, and isn't re-asked, because you never asked it for anything.
Name it under the table instead, so a reader can see that five reports arrived
and three of them came from the panel.

## Step 4: Reconcile and verify

Read the reports the roster counts and the comments already on the change, all
of them and nothing else. Then group the findings:

- **Two or more reviewers, same defect** → evidence. Verify it anyway, and
  verify it first.
- **One reviewer only** → a hypothesis, not noise. Don't try to predict how
  often this happens. One three-reviewer run produced three separate sets of
  findings with no overlap, and the most valuable finding came from one
  reviewer alone. The next run produced unanimous agreement on a single defect.
  Both are normal. Verify a lone finding, and don't discount it.
- **Reviewers contradicting each other** → they read the same code and
  disagree, which means the code supports two readings. That is a finding in
  itself.

Then verify each finding yourself. Don't delegate this or fan it out, since
checking findings from several reviewers against one codebase is the
synthesis a parent can't hand off. Follow `receiving-code-review`: check each
finding against the code before acting on it, and push back with a
demonstration rather than an argument.

In the real run, this step changed the disposition of half the findings, and
two of the four would have been wrong to apply as written.

## Step 5: Report a disposition table

List every finding from every reviewer, with what you did about it and why.
Don't leave one out, since an unmentioned finding looks like one nobody raised.

Report the table to the person in the conversation, not in a change
description. That holds for every later round on a change that is already open,
too. One description that gained a row each round grew to 15 rows, 12 of them
already applied.

When several groups ran, report one table covering all of them, and name each
reviewer by its id and model, such as `s3 codex`.

```
## Review panel: <target> — security and code, 6 reviewers, 4 findings

| # | Reviewer | Finding | Disposition |
|---|---|---|---|
| 1 | s2 claude | the guard reads the hook's own directory, not the payload's `cwd` | applied — reproduced it first |
| 2 | s3 codex | `--auto` merges a head the check never judged | applied — confirmed `gh` accepts it |
| 3 | c1 claude | the mirror-membership test is near-tautological | accepted — for a sharper reason than the one given (see below) |
| 4 | c2 claude | the `_MIRRORED_SKILLS` comment rationale doesn't apply here | rejected — the rationale is about #124's failure mode, which this entry has |
| — | s1 claude | no findings — both security reviews over the 2 commits in run 003 | clean |
| — | c3 claude | no findings — six passes over the installer, the fence, and its tests | clean |

roster: s1 ✓  s2 ✓  s3 ✓ relayed: read-only sandbox  c1 ✓  c2 ✓  c3 ✓ (c2 re-asked once)
```

A finding gets one of three dispositions, each with a reason on its line:
**applied**, **accepted** (with the reason you accepted it for, when it differs
from the one given), and **rejected** (with the reason). A run where every
finding was applied hasn't exercised the reconciliation, and it has only
relayed three reports. `clean` is a fourth value in that column but not a
fourth disposition, since it disposes of no finding and carries no reason.

**A reviewer that found nothing gets a row, not a tick.** Its `#` cell holds
`—`, not a number or an empty cell, since there is nothing to number and a
blank cell in a pipe table looks like an omission. Its Finding cell holds what
the report says it covered. A clean review is a result the panel paid for, and
the roster line can't show it. `c3 ✓` only shows that a report counted, and a
reviewer gets the same mark for a page of blockers.

**Every name in the Reviewer column is on the roster line.** The line carries
the whole panel: the ids wfctl counted, and the free members named beside them.
If a name in the column isn't on the line, it is a report from outside the
panel, and anyone reading the table can see that. The roster line records a
re-ask by its outcome, `c2 ✓ (re-asked once)`, never by its history. Name a
report this skill excluded below the roster, by id, without counting it:

```
roster: s1 ✓  s2 ✓  s3 ✓  c1 ✓  c2 ✓  c3 ✓  + codex (review comment on the PR)
not read: correctness-angles, r4 — agents this panel did not dispatch
```

## Red flags

- Recording a reviewer as clean because it said it had nothing to add. This
  skill was written after that sentence. A report earns a `clean` row
  by naming what it covered, not by declining to.
- Counting reports yourself instead of reading `wfctl review check`, or
  starting the next group before the last line says `complete`.
- Giving a reviewer a commit range or a trunk branch instead of the reports
  folder. Its review then covers commits wfctl doesn't count.
- Putting a report in a command's text instead of relaying it from a file.
- Giving each reviewer a different lens. That is a coverage split, and
  `code-review` already covers those axes in one pass.
- Letting a reviewer edit the tree, or fixing findings while reviewers are
  still running. Both corrupt the diff the others are reading.
- Handing reviewer 2 what reviewer 1 found, or handing any of them your session
  history. Both destroy the independence that is the only thing a panel buys.
- Reconciling a report from an agent you didn't dispatch. A correct one is hard
  to catch, but being correct doesn't make it a panel member.
- Applying findings straight from the reports. Half of them changed shape under
  verification.
- A disposition table with fewer rows than the findings collected.
