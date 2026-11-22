# Threat model: controls that read an agent's commands

Read this guide when the control reads a command an agent runs or text an agent
writes, and decides from that text whether to let the action through. In wfctl,
that covers the worktree guard's refusals and the text checks in front of the
person-only commands, `wfctl arch accept`, `wfctl review sign-off`, and `wfctl
arch approve-imports`. It adds the
prompts for step 2 and the principles for step 3 of
[`threat-model.md`](threat-model.md), which you've already read.

The principles come from Saltzer and Schroeder, "The Protection of Information
in Computer Systems" (1975), section I.A.3
(https://web.mit.edu/Saltzer/www/publications/protection/Basic.html). The paper
says they "serve best as warnings" rather than absolute rules, and that's how
this guide uses them.

## Who the control defends against

Name which of these agents the control stops, since a text check can stop the
first two and not the third:

1. An agent that runs the action by mistake, such as copying a command from a
   skill, a record, or an issue body.
2. An agent that retries a refused command in a different form, such as adding
   a runner or a wrapper, without trying to hide what it runs.
3. An agent that builds the command on purpose so the check can't read it.

Stopping the third agent takes a condition the agent can't produce, such as a
terminal it doesn't have. A text check alone can't do it, so say that in
`Defends against` rather than leave a reviewer to assume otherwise.

## Paths to walk in step 2

Walk each of these and write down the forms it allows:

1. The command as written, and in another case or with extra flags.
2. Behind a runner, such as `uv run`, `npx`, `env`, or `nice`.
3. Inside a shell the agent starts, such as `bash -c`, text piped into `sh`, or
   `eval`.
4. Inside another interpreter, such as `awk`'s `system()` or Python's
   `subprocess`.
5. Through shell syntax that changes the words at run time: quoting, a
   backslash inside a word, a variable, a glob, a brace expansion, `$IFS`, or a
   command substitution.
6. Through a file: a script written to disk, then run.
7. Through a different tool that performs the same action. For example,
   `gh pr merge` and a `gh api` call to the merge endpoint both merge a PR.

Then walk the ordinary work an agent does that only names the command: commit
messages, searches, release notes, and comments. Those are the candidates for
`Must let through`.

## Principles for step 3

1. **Complete mediation.** "Every access to every object must be checked for
   authority." Each path from the list above that reaches the action needs a
   check, or a line in `Accepts` saying why it has none. Path 7 is the one most
   often missed, because the check was written for one tool's command.
2. **Fail-safe defaults.** The paper says to "base access decisions on
   permission rather than exclusion." A text check works by exclusion: it
   refuses the forms it recognizes and lets everything else through. That's
   why a text check's `Accepts` list is never empty. If the action can't be
   undone, put a permission-based check behind the text check, such as a
   terminal the agent doesn't have, and name it in `Defends against`.
3. **Separation of privilege.** A mechanism that "requires two keys to unlock
   it" is harder to get past. The text check and the terminal check are two
   keys, so an `Accepts` form that gets past the text check still has to get
   past the terminal check. Say which key stops each form.
4. **Work factor.** "Compare the cost of circumventing the mechanism with the
   resources of a potential attacker." For an agent, the cost is how far a form
   is from a natural mistake. A form one wrapper or one typo away from the plain
   command belongs in `Must keep catching`. A form that takes deliberate
   construction, such as `eval` of text built at run time, can go in `Accepts`.
5. **Compromise recording.** When a form can't be stopped, use a mechanism that
   reliably records that the action happened. For a record acceptance, the PR
   diff shows a `Log` line nobody asked for. Every `Accepts` entry names its
   record. If an accepted form leaves no record, that's a gap, and it should be
   stated in the section.
6. **Psychological acceptability.** The paper asks for a human interface
   "designed for ease of use." A check that refuses ordinary work teaches the
   agent and the user to route around it. That's why a text check carries a
   `Must let through` list with tests.
7. **Open design.** "The design should not be secret." The lists live in a
   committed record the agent can read, so the control can't depend on the
   agent not knowing which forms it misses.

## Example

`prompt-approves-person-commands.md` in wfctl's arch root applies this guide
to the three person-only commands. It names agents 1 and 2 in `Defends
against`, lists forms from paths 1 - 5 in `Must keep catching`, and lets
through the plain spellings Claude Code asks the user about. It accepts the
forms no text rule can read, because the PR diff and the review notes record
what ran, and it says which of the two is the weaker record.
