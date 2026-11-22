---
status: superseded
diagram: data-flow
governs: worktree-guard, evidence-and-derivation, architecture-records
---

# The accept check stops a plain accept, not a hidden one

## Decision

The guard's check on `wfctl arch accept` stops an agent that runs the command
by mistake, by habit, or because a document told it to. It doesn't stop an
agent that hides the command on purpose. Each form listed under "Must keep
catching" below is refused, each form under "Must let through" runs, and each
form under "Accepts" is a known gap that shows in the PR diff instead.

A change to the check is judged against these lists. A change that lets a
"Must keep catching" form through is a regression. A change that lets an
"Accepts" form through is not, and a change that blocks a "Must let through"
form is a regression in the other direction.

## Boundary

![The guard refuses a plain accept, and a hidden accept shows in the PR diff](drawings/accept-check-threat-model-data-flow.svg)

A solid arrow is a command the agent runs and waits on. The dotted arrow is the
record change, which the human reviewer reads later in the PR diff.

## Context

Accepting a record is the user's decision (`a-human-accepts-a-decision.md`). Two
checks keep an agent from running the accept command:

1. The worktree guard reads each shell command's text before it runs and
   refuses one whose words would run `wfctl arch accept` without `--dry-run`.
2. The `arch accept` command refuses to write when stdin or stdout isn't a
   terminal.

A pseudo-terminal, such as one the `script` command provides, satisfies the
second check. That's why the first check exists.

Previously, the only statement of what the text check defends against was
research note R-013 in the #740 spec folder. `wfctl arch context` never prints
a spec folder's research, so neither the session that fixed #792 nor its review
panels read it. The security panel on #792 was told that the guard must not let
any real accept through. R-013 already said no text rule can promise that, so
the panel treated every narrowing of the check as a regression, including forms
R-013 lists as accepted. R-013 also didn't say which forms the check must keep catching, so
neither the panel nor the author could tell a real regression from a form inside
the accepted gap. The review loop ran three rounds before the cap stopped it.

## Threat model

### Defends against

An agent that runs `wfctl arch accept` without meaning to bypass the user. It
might copy the command from a skill, a record, or an issue body, retry a refused
command in a slightly different form, or reach the command through a wrapper
such as `uv run` or `bash -c`. The agent isn't trying to hide what it runs.

The check doesn't defend against an agent that deliberately builds the command
so the text check can't see it. Stopping that agent would need a sign-off an
agent can't produce, and wfctl doesn't have one.

### Must keep catching

The guard refuses each of these. The guard's tests in
`tests/test_review_gate.py` cover more variants of each form, and a test reads
this list and checks that the guard refuses every entry.

1. The command as written: `wfctl arch accept s --agreed x`
2. Behind a runner the guard knows: `uv run wfctl arch accept s --agreed x`
3. The name in another case: `WFCTL arch accept s --agreed x`
4. A quoted word: `wfctl "arch" accept s --agreed x`
5. A backslash inside a word: `wfctl arch acc\ept s --agreed x`
6. An expansion standing in for the name: `"$(command -v wfctl)" arch accept s --agreed x`
7. A variable standing in for one word: `A=accept; wfctl arch $A s --agreed x`
8. Words split by the shell at run time: `bash -c 'wfctl${IFS}arch${IFS}accept s --agreed x'`
9. A glob naming wfctl: `~/.local/bin/wf?tl arch accept s --agreed x`
10. A brace expansion: `wfctl {arch,} accept s --agreed x`
11. Inside a script a shell runs: `bash -c "true; WFCTL arch accept s --agreed x"`
12. Text piped into a shell: `echo 'wfctl arch accept s --agreed x' | sh`
13. An interpreter's system call: `awk 'BEGIN{system("wfctl arch accept s --agreed x")}'`
14. A command substitution inside a quoted message: `git commit -m "see $(wfctl arch accept s --agreed x)"`
15. A dry run on one command beside a real accept: `wfctl arch accept --dry-run -- a; wfctl arch accept b --agreed x`
16. `--dry-run` where wfctl doesn't read it as the flag: `wfctl arch accept b --agreed "after a --dry-run"`
17. `--dry-run` after a comment: `wfctl arch accept s --agreed x # --dry-run`
18. `--dry-run` as a redirect target: `wfctl arch accept s --agreed x > --dry-run`
19. `--dry-run` after `--`: `wfctl arch accept -- --dry-run`
20. A command the shell can't split: `wfctl arch accept x --agreed "unclosed`

### Accepts

These run the accept and pass the text check. Under a pseudo-terminal they pass
the terminal check too. We accept items 1 - 4, 6, and 7 because no rule that
reads the command's text can find them. Item 5 is different: the guard refuses
`nice -n 5` on its own and `bash -c` on its own, and misses only the two
together. That's a gap in the guard rather than a limit of text rules, and
#819 tracks closing it and moving the form to "Must keep catching". The record
change still shows in the PR diff, where the human reviewer sees a `Log` line
nobody asked for. This is the same tamper-evident ceiling `a-human-accepts-a-decision.md` names for the citation.

1. Arguments fed through `xargs` from stdin: `printf 'arch\naccept\ns\n' | xargs wfctl`
2. `eval` of text built at run time: `eval "$(printf 'wfctl ar%s acc%spt s' ch e)"`
3. A name built from a variable, with the words in another: `W=wf; A='arch accept s'; ${W}ctl $A`
4. A glob name with the words in a variable: `A='arch accept s'; wf?tl $A`
5. A runner with an option, inside a quoted script: `bash -c "nice -n 5 wfctl arch accept s"`
6. An interpreter that builds the words as a list: `python -c "import subprocess; subprocess.run(['wfctl', 'arch', 'accept', 's'])"`
7. Words written in ANSI-C escapes: `$'w\146ctl' $'\141rch' $'\141ccept' s`

### Must let through

The guard lets each of these run, since each one only names the command or
runs the dry run agents are told to use. A test reads this list too.

1. The dry run: `wfctl arch accept --dry-run -- s`
2. The dry run flag at the end: `wfctl arch accept s --agreed x --dry-run`
3. A commit message naming the command: `git commit -m "To sign off, run wfctl arch accept on the record again"`
4. A commit message with the two words apart: `git commit -m 'arch: accept the record'`
5. A search for the command: `grep -rn "wfctl arch accept" wfctl/`
6. A search for the name: `grep -n wfctl "$f"`
7. A release note naming the command: `uv run towncrier create 769.change.md --content 'run wfctl arch accept on it again'`
8. Another `arch` command with a comment: `wfctl arch context # then accept`

The guard still refuses some commands that don't run the accept, such as a
commit message holding a backticked `wfctl doctor` and a `cp` whose source path
holds the word `wfctl`. Those are tracked in #792, and its fix adds each one to
this list. A change that lets them through fixes a known false refusal and
isn't a regression, as long as every form in "Must keep catching" is still
refused. That includes a backticked accept inside a double-quoted message,
which the shell runs the same way it runs item 14's `$(...)`.

## Direct baseline

Leave R-013 where it is and add a line to the review brief pointing at it. That
draws no new structure. It fails for the same reason the #792 loop happened:
the coordinator has to remember the note exists, and nothing a session loads at
start names it.

## Owns truth

The user decides which forms the check must keep catching and which it gives
up, by accepting this record. The guard decides whether one command's text runs
the accept the way the shell would read it.

The guard shouldn't decide the lists, because the lists set what counts as a
regression in the guard's own code. If the author of a guard change wrote them,
they would be grading their own change. The review coordinator shouldn't write
them either, since a bar written for each run is what led #792's panels to flag
forms R-013 had already accepted.

The guard can't decide whether a command eventually runs the accept. A command
can build its words at run time in ways no text rule can follow, such as
`eval`, `xargs`, or an interpreter's list of arguments.

## Considered

- Keep R-013 as research and cite it from the review skills. We didn't choose
  this because research in one feature's spec folder isn't printed at session
  start, and the next guard change starts from the same blank page.
- One record covering every command the guard keeps for a person, which today
  is `review sign-off`, `arch approve-imports`, and `arch accept`. This is
  equally sound in principle, since all three checks have the same shape. We
  didn't choose it because only the accept check has a stated gap and a list
  of forms, and writing lists for the other two would be a design pass of its
  own.
- Only the "Defends against" and "Accepts" parts, as R-013 had them. We didn't
  choose this because the missing "Must keep catching" list is what left the
  #792 panel unable to tell a regression from an accepted gap.

## Consequences

- `wfctl arch context` prints this record on any branch whose `design.md` lists
  the worktree guard, evidence and derivation, or architecture records, so a
  session changing the check reads it before writing code.
- The security group judges a change to the check against these lists, and says
  so in its report (`security-change-needs-threat-model.md`).
- A test reads the "Must keep catching" and "Must let through" lists and runs
  each entry through the guard. Adding a form to either list adds a test case.
- The `review sign-off` and `arch approve-imports` checks have no threat model
  yet. A change that loosens or tightens either one writes its own, as
  `security-change-needs-threat-model.md` requires.

## Log

- 2026-11-18  proposed    — #799 level 2. Moves R-013 from the #740 research
  note into a record and adds the lists of forms the check must keep catching
  and must let through.
- 2026-11-19  accepted    — agreed by the maintainer on #799, with Accepts item 5 tracked as a guard gap in #819 · drawing drawings/accept-check-threat-model-data-flow.svg sha256:c7c2f192a4e7
- 2026-11-20  superseded  — by prompt-approves-person-commands (#833): the user approves the three commands at the agent host's prompt, and the guard lets the plain spellings through
