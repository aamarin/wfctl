---
name: worktree-handoff
description: 'Write the handoff before a worktree is created, so the reasoning behind the work arrives with it. Use when creating a worktree, spinning one up, branching off to a new work stream, or handing a task to another session. Use before reaching for `wm add` / `workmux add` or `git worktree add`. Layers over using-wm, which still owns how worktrees are made.'
---

# Worktree handoff

The session that decides to spawn work is the only one that knows why it exists,
what was already argued out, and what the new branch must not touch. The new
branch's session gets the issue text. Everything else — the decisions, their
arguments, the boundaries — stays behind in a conversation that will be cleared.

`workmux add --prompt-file` is the slot that context fits into, and nothing
fills it. Three of nine worktrees in this repo have a prompt because someone
remembered; the other six opened cold and the human re-explained the task by
hand.

**Announce at start:** "I'm using the worktree-handoff skill to write the
handoff before creating the worktree."

## Order

`.agents/skills/using-wm` owns how a worktree gets made — the `--background`
rule, `.workmux.yaml`, the branch-name hooks. Read it and follow it. This skill
owns what the new session is handed, and adds two arguments to the `add` you
were already going to run.

## Step 1: Check you are the one who can write this

The handoff is worth writing only from what this session actually decided. If
you cannot answer these from the conversation you are in, you are transcribing
the issue, and the issue is already in the worktree:

- Why does this work exist *now* — what happened that made it necessary?
- What did this session settle that the issue does not say, and what did it
  reject?
- What is the new branch stacked on, and what does a sibling already own?
- Does this change draw a boundary or move ownership — or is it a fix?

Nothing to answer means the honest handoff is short. Write the short one. Do
not pad it back to the shape below.

## Step 2: The shape

Derived from the three prompts that worked, not invented. Sections 1, 2, 3, 6,
7 and 8 are always present. Sections 4 and 5 are **omitted entirely** when they
have no content — an empty "Boundaries: none" teaches the reader to skim the
heading next time.

1. **One line: what to build.** `Implement issue #N — <the thing, in a
   sentence>.` Not a summary of the issue; the sentence the issue would have
   opened with if it had been written after the fact.

2. **Where to start, and how to read it.** Open with `Run /start-session before
   you touch anything`, and say why on the same line — an agent already holding a
   full handoff concludes a session-start step is redundant, and four agents
   concluded exactly that in one afternoon (#206), each running against whatever
   skills its worktree happened to install and never reading the accepted
   records or the pipeline position. Then `Start with <the issue command>`, and
   say which parts of it are settled and which are not, and why. "Written after
   the failure rather than before" and "from a real run, so treat its findings
   as evidence" are the two that carried; a reader who does not know which
   sections bind will negotiate with all of them.

3. **Which route this work takes.** Straight to implementation, or through the
   spec pipeline. `.agents/skills/design-levels` owns where the line falls —
   do not restate its criteria here, state which side *this* change lands on and
   why. A change that draws a boundary, moves who owns a piece of truth, or adds
   new state goes through the pipeline; a bug fix or a copy edit does not.

   This section is always present, because an unstated route is not neutral. A
   handoff that opened with "implement issue #N" and said nothing else was read
   as "start coding": the child implemented, committed and pushed, and its own
   `/start-session` then reported `step: brainstorm` — wfctl's answer arriving
   after the work it was meant to gate. The spawning session is the one that
   read the issue and knows which it is; the child inherits the verb in your
   first line and nothing else.

4. **Branch context** — only when the branch is stacked or overlaps open work.
   The base branch and its change number, what must happen for the base to merge
   safely, the conflicts to expect, and the files the child must not edit. Each
   boundary sits beside the reason it exists. A free-standing "do not touch"
   list is obeyed right up until it is inconvenient.

5. **Open questions** — only when something is genuinely undecided. Name the
   recommendation *and* say it is a recommendation, plus what deciding it costs
   ("run the level-2 gate on it"). An open question buried after a page of
   settled ones gets read as settled.

6. **What is already decided, and why.** One bolded claim per decision, then the
   argument, then what was rejected. A decision without its argument gets obeyed
   blindly or reopened from scratch, and the reader cannot tell which it should
   do. This is the section the whole artifact exists for.

7. **Definition of done.** The project's verification commands, verbatim, plus
   any known flake and its workaround. Then what the suite does *not* cover, as
   a real exercise, phrased so a run that skipped it fails: "an exercise where
   everything was applied has not tested the reconciliation."

8. **How to open the change.** The repository's template and why it is being
   said out loud. `.agents/skills/opening-a-change` owns the rest.

Where the three disagreed: two put branch context before the decisions and one
put it after. Before — a boundary you might cross is worth knowing before you
read what to build, and reading it afterwards means re-reading the decisions
against it.

## Step 3: Write it, then create the worktree

**Write the sections above into a file first.** Not as a step inside the block
below — an agent that runs the block as written ships an empty prompt, which is
the cold start this skill exists to prevent, and Step 4 will not catch it because
it reads back the same empty file.

```bash
HANDOFF=$(mktemp -t handoff)
```

Fill `$HANDOFF`. Then, and only then:

```bash
wm add <branch> --background --prompt-file "$HANDOFF" &&
  cp "$HANDOFF" "$(wfctl state-dir --branch <branch>)/session-summary.md"
```

Chained on purpose. `pre_create` hooks reject branch names — this repo's requires
a leading issue number — and an unchained `cp` runs anyway, creating a state dir
for a branch that does not exist.

Both destinations, and neither is optional:

- `--prompt-file` puts it in the agent pane's first turn, so the child has it
  before it runs anything.
- The state dir is where it survives. `.workmux/` is git-excluded and is deleted
  with the worktree; the state dir outlives `wm rm`.

`session-summary.md` is the filename because
`.agents/skills/start-session` step 4 already reads it and reads it *fully* —
landing there costs the reader no change. What goes in it is the shape above,
not `.agents/skills/end-session`'s template: that template is what a session
writes about a session it just finished, and this is a handoff about a session
that has not started. The filename is the interface; the prose is yours.

Say so in the handoff's first line — the child otherwise reads a
`session-summary.md` as evidence of a previous session on its own branch, and
there wasn't one.

Order matters: `wm add` first. Resolving the state dir creates it, and a branch
whose `pre_create` hook rejected the name should not leave one behind.

One thing landing here does *not* give the reader: `start-session` step 9 offers
the top item of a **Next Session TODO** as the default answer to "what are we
working on today?", and a handoff has no such list — its answer lives in section
2, after `/start-session`. Say that first action plainly enough to be the
default. Do not add a TODO section to get one; it would be a second copy of the
route, and `.agents/skills/end-session` owns that heading.

## Step 4: Confirm it landed

```bash
head -3 "$(wfctl state-dir --branch <branch>)/session-summary.md"
```

The acceptance test is not that the file exists. It is that the child session
starts work without you explaining anything. If you find yourself typing the
context into the new session, the handoff was incomplete — fix the file, not the
conversation.

## Red flags

- Doing the work in the checkout you are standing in. This skill's triggers are
  all phrases a human says, and the failure it was written for is the turn where
  nobody says one: a session on `main` that identified the next piece of work and
  offered to take it there (#241). New work gets a worktree before it gets a
  commit, and the session that spots the work is the one that owes the handoff.
- Opening with "implement issue #N" on work that needed a spec first. The verb
  in line 1 is the route the child takes when nothing else names one, and by the
  time `/start-session` disagrees the code is written.
- Creating the worktree first and writing the prompt after. The prompt is only
  injected at `add` time, so this quietly produces the cold start it was meant
  to prevent.
- A decision stated without its argument. That is a task list, which is the
  thing being replaced.
- Boundaries listed under their own heading with no reason attached. Reasons are
  what make a boundary survive contact with an inconvenience.
- Restating the issue. The child can run the issue command. What it cannot
  recover is the conversation that read it.
- Writing only to `.workmux/`. That file dies with the worktree, and the
  reasoning dies with it.
- A section 2 that never says to run `/start-session`. An agent holding a full
  handoff infers the session start is redundant, and the handoff is why it
  thinks so — four agents inferred it in one afternoon (#206).
