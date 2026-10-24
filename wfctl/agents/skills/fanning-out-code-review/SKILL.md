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

What the fan-out buys is independent context, not coverage. That distinction
decides the whole design, as "The axes are not the split" below explains.

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

Every reviewer in a group runs that group's whole skill. Independence is the
variable, and the rubric is not.

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

Security and code always run first, in that order, and any group the
repository adds runs after them. Run this skill once per group, in that order.
Each group's fixes are committed before the next group starts, so the code
group reviews the security group's fixes and a later group reviews both. The
second column is the skill each of the group's reviewers follows.

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
  Give the path because a host can ship its own command under the same name,
  and a reviewer that reaches for the Skill tool gets the host's command
  instead of this rubric. Claude Code's built-in `/code-review` is a different
  review. It fans out helper agents that report into your session and never
  receive the bullets below, and on two panels an agent running under it
  edited the shared tree. Give the path rather than pasting the rubric, so that
  each reviewer reads all of it and not your summary of it.
- **Review the commits listed in `run.json` in the reports folder,** each with
  `git show <sha>`, and report a finding only if it's still there at the run's
  `head`.
- **Write the report to `<reports folder>/<id>.md`.** It carries a
  `Reviewed: <sha>` line naming the run's head, and its last line is the
  verdict. wfctl counts a report only when its `Reviewed:` line names the head
  with at least seven digits and it ends with `Verdict: Approve` or
  `Verdict: Request changes`. A report cut off partway has no verdict at its
  end, so it doesn't count.
- **Say which passes ran and what each covered,** whether or not it found
  anything. `code-review` Step 5 ends a clean report at the over-engineering
  metric and a verdict, which is enough to show a reviewer worked and not
  enough to say what it looked at. Step 6 gives a reviewer that found nothing a
  row whose Finding cell carries its coverage, and this bullet is where that
  requirement reaches the reviewer.
- **Report only. Change nothing.** Reviewers share a worktree with each other
  and with you. Three agents editing a tree a fourth is reading corrupts all
  four, and you can't recover afterwards, since you can't tell whose
  half-applied edit produced the state you're looking at. Writing its own
  report is not an edit to the tree, and touching anything under review is.
  The boundary is wider than the tree, though. Anything the project reads back
  later as evidence is off limits too. Under wfctl that is `wfctl verify`,
  which writes one record per branch outside the worktree, and a reviewer
  running it replaces the parent's proof of done with one taken mid-review.
- **Report any design decision nothing on the change covers:** new stored
  state, a new file or setting the code reads, a new command or flag, or a
  boundary drawn or moved. A record or spec the change names covers it, and the
  change calling itself a bug fix doesn't. Nothing checks that the author asked
  whether the change needs a spec before writing code, and an agent that
  skipped the question can still answer "No" when the PR opens. A reviewer that
  reads only the diff is the first reader who didn't write it, so it is the one
  placed to notice. The coordinator shows these findings in the table before
  the PR opens, and the author writes the "Needs a spec?" answer after reading
  them.

Dispatch them in parallel, since they are independent by construction. Sharing
one tree is a choice, not a limit to engineer around. A harness that can hand
each reviewer its own worktree lifts the report-only constraint and buys
nothing back, since a reviewer's product is findings and verification stays
with the parent either way.

### A reviewer on another model

A line with a command after the model, such as `s3 codex  codex exec --sandbox
read-only`, is a reviewer you run yourself with that command:

The command comes from the `review.commands` key in the repository's
`wfctl.json`, so in a repository you don't own, read that key before running
it, the same as you would a hook the repository ships.

Use the scratch folder your harness gives you, never a fixed path such as
`/tmp/panel/`. Another session, or another user on the same machine, can write
to a shared path, and a report planted there would be relayed as this run's.

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
line. It refuses a relay with no reason.

**Never put a report in a command's text,** whether in a heredoc, an `echo`, or
an argument. The worktree guard matches command text, and a security report
quotes the commands it refuses, such as `gh pr create`, so a command carrying
the report is refused while the branch is unreviewed, which it always is
during a run. A file keeps the report out of the text the guard reads, and
`wfctl relay` reads the report only from `--from` for that reason.

Check each relay reason against what you saw. If the reviewer wasn't really
blocked, such as a reviewer that said its write was denied when no denial
reached you, tell the person you're working for. A reviewer that could write
and didn't is a gap in the process, and the roster can't show it.

**The trigger you will meet most often is not a sentence.**
`.agents/skills/opening-a-change/SKILL.md` runs this skill for every group
before a PR is opened. That is the path an unattended run takes, where the
description above matches nothing because nobody said anything (#187).

The reconciled table from Step 5 is this skill's own output, and it goes to the
person you're working for, in the conversation. A change description carries
nothing from the panel, and `opening-a-change` says the same from its side: no
finding of any disposition, no table, and no roster or status line.

**Comments already on the change are panel members you didn't pay for,** such as
a bot's review or a person's note. Collect them in the same pass. What
qualifies them is that whoever wrote them never had your session. They read the
change and nothing else, which is what this step hands a dispatched reviewer
and the only thing a panel buys. wfctl doesn't count them, since they aren't
reviewers in the run, so they never move a group's record forward. They are
named on the roster line in Step 5 beside the run's reviewers.

## Step 3: Let wfctl confirm every reviewer reported

**This is the step the skill exists for.** In a fan-out, a reviewer that
returns nothing looks the same as a reviewer that found nothing, and an agent
will report the second. One real run produced the completion message *"this is
the completion notification for the review I already relayed above — same
finding, nothing new. No action needed"* for a review that had never arrived.
Asked again, that reviewer produced the only confirmed correctness defect in
the change.

So you don't count reports from memory, and you don't count them yourself.
wfctl reads the reports folder against the reviewers it expected:

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
count. The last line says `complete: security reviewed through 9f8e7d6` once
every expected report counts, and wfctl then moves the group's last reviewed
commit to the head. Anything else exits 1.

wfctl reads the verdict the way this project's reviewers write it. The four
spellings in this project's own spec root, `Verdict:`, `**Verdict: Approve**`,
`## Verdict`, and `### Verdict`, all count, and prose that only mentions a
verdict doesn't. `test_report_counts_with_each_verdict_spelling_reviewers_use`
holds that list open, so read it before tightening the rule.

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
while a panel works. Reading the roster then is not a mistake, as long as you
don't record it. A reviewer that has finished and left no report is a failure,
not a pass. Whether a reviewer has finished is what the dispatch told you, not
what the reviewer told you. A reviewer's own "I already reported" is the
recollection this step exists to disbelieve, and that its run ended is an
observation nobody has to trust. A `✗ no report` written into the table for a
reviewer that was only slow spends that reviewer's work twice and puts an
untrue sentence in the table (#173).

**A finished reviewer with no counted report gets asked again.** Ask it for its
findings in the format `.agents/skills/code-review/SKILL.md` specifies, or the
format of its group's skill, and repeat that it reads that file rather than
invoking a Skill named `code-review`. A reviewer that wrote nothing may have
reached the host's command the first time, and a re-ask that names the skill
sends it back there. If a reviewer insists it already reported, the report is
the evidence and its recollection is not, so ask again anyway. A reviewer that
still reports nothing after the re-ask didn't run, so dispatch a replacement
under the same id. A file with no verdict is also the likeliest trace of a
reviewer that ran the host's command, since that command's output carries no
verdict line.

Run `wfctl review check` again after each re-ask, until the last line says
`complete`. A group isn't done until then, and the next group doesn't start
before it.

A run where no reviewer could run never completes. `review check` says
`incomplete: no reviewer in security could run`, and the only ways forward are
making a model available or a person signing off. Tell the person, since a
sign-off is theirs to make.

### The roster is the whole panel

wfctl answers one direction of one question: did every reviewer it expected
report? The other direction is yours, and it is the one that lets a stranger
in.

**A report from an agent you didn't dispatch is not a reviewer's, and being
right doesn't make it one.** On one run, two agents this panel never
dispatched finished while all three real reviewers were still working, and
reported on the same diff through the same channel the reviewers use. One of
their findings was a genuine defect. The panel found it independently forty
minutes later and confirmed it by mutation (#205). A session that folded it in
would have taken a true finding from a source with no independence behind it,
and had nothing to tell it so. The rule therefore carries no "unless it is
correct", since at the moment you are reading one, correct is what a
contaminated report looks like.

**The disqualifier is inheriting your context, not the agent's type.** This
skill hands a reviewer the run, the intent, and the project's rules, and never
your session history. An agent that inherited your context has already read
your reasoning, so its agreement with you is evidence about your reasoning
rather than about the diff. Type can't answer this question. Of the two agents
above, `ListAgents` typed one a fork and didn't list the other at all, so a rule
keyed on type catches one of the two. Comparing against the ids you dispatched
answers it for both.

wfctl counts only the files named for the run's ids, so a stranger's file in
the reports folder never counts toward a run. A report that arrives as a
completion notification leaves no file, so read the id it reports under against
the ids `review start` printed, as each report arrives.

A report from outside the panel doesn't enter the roster line, doesn't get a
disposition row, and isn't re-asked, because there is nothing you asked it for.
Name it under the table instead, so a reader can see that five reports arrived
and three of them were the panel.

## Step 4: Reconcile and verify

Read the reports the roster counts, and the comments already on the change.
Read all of them, and only those, then group the findings:

- **Two or more reviewers, same defect** → evidence. Verify it anyway, and
  verify it first.
- **One reviewer only** → a hypothesis, not noise. How often this happens isn't
  worth predicting. One three-reviewer run produced three disjoint sets and no
  overlap, with the most valuable finding coming from one reviewer alone, and
  the next produced unanimous agreement on a single defect. Both are normal. A
  lone finding is verified, not discounted.
- **Reviewers contradicting each other** → they read the same code and
  disagree, which means the code supports two readings. That is a finding in
  itself.

Then verify each finding yourself. This isn't delegable, and it isn't fanned
out, since holding findings from several reviewers against one codebase is
exactly the synthesis a parent can't hand off. Follow `receiving-code-review`:
check each finding against the code before acting on it, and push back with a
demonstration rather than an argument.

This step is not a formality. In the real run it changed the disposition of
half the findings, and two of four would have been wrong to apply as written.

## Step 5: Report a disposition table

Every finding from every reviewer appears, with what you did about it and why.
Silence on a finding isn't an option, since an unmentioned finding reads as one
nobody raised.

Report it to the person in the conversation, not into a change description. On
a change that is already open, that holds for every later round as well. A
description that took one row per round grew to 15 rows, 12 of them already
applied.

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

Three dispositions for a finding, each requiring a reason on the line:
**applied**, **accepted** (with the reason you accepted it for, when it differs
from the one given), and **rejected** (with the reason). A run in which
everything was applied hasn't exercised the reconciliation. It has relayed
three reports. `clean` is the fourth value in that column and not a fourth
disposition, since it disposes of no finding and carries no reason.

**A reviewer that found nothing gets a row, not a tick.** Its `#` carries `—`,
not a number and not an empty cell, since nothing was found to number and a
blank in a pipe table reads as an omission. Its Finding column carries what the
report says it covered. A clean reading is a result the panel paid for, and the
roster line can't carry it. `c3 ✓` says a report counted and stops there, which
is the same mark a reviewer earns for a page of blockers.

**Every name in the Reviewer column is on the roster line.** The line carries
the whole panel: the ids wfctl counted, and the free members named beside them.
A name in the column that the line doesn't carry is a report from outside the
panel, visible to anyone reading the table. The roster line records a re-ask by
its outcome, `c2 ✓ (re-asked once)`, never by its history. A report this skill
excluded is named below the roster and not counted, by id:

```
roster: s1 ✓  s2 ✓  s3 ✓  c1 ✓  c2 ✓  c3 ✓  + codex (review comment on the PR)
not read: correctness-angles, r4 — agents this panel did not dispatch
```

## Red flags

- Recording a reviewer as clean because it said it had nothing to add. That is
  the exact sentence this skill was written after. A `clean` row is earned by a
  report that names what it covered, not by one that declines to.
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
- Reconciling a report from an agent you didn't dispatch. Being correct is what
  makes one of those hard to catch, not what makes it a panel member.
- Applying findings straight from the reports. Half of them changed shape under
  verification.
- A disposition table shorter than the number of findings collected.
