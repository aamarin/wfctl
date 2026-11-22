# The threat model section

A security control is a check that keeps an action with a person or keeps an
untrusted input out. A change that adds, removes, loosens, or tightens one
writes a threat model before any code, as a `## Threat model` section in the
change's level-2 record. The user accepts it with the record, and the security
reviewers judge the change against it.

A change that leaves what the control refuses and lets through unchanged, such
as a rename or a refactor, doesn't need one.

In wfctl, the security controls are:

1. The worktree guard's refusals, such as the check on `gh pr create` while a
   review group has unreviewed commits, and the checks on git notes.
2. The terminal checks on `wfctl review sign-off`, `wfctl arch accept`, and
   `wfctl arch approve-imports`, the `ask` rules that make Claude Code ask the
   user before each one runs, and the guard's text checks in front of them.
3. The `review` job on GitHub and the import check it runs from `main`.
4. Reading `review.commands` and `review.rounds` from the trunk rather than from
   the branch under review.

Another repository has its own, such as an authorization check, a rate limit, or
a webhook's signature check.

A security control refuses something, and you can write a test that fails when
it lets a form through. Guidance an agent follows, such as the security
reviewer's steps for finding a threat model, isn't a control, even when it
guards the same boundary. It refuses nothing, since the reviewer only reports,
and no test can fail when a reviewer skips a step. A change to that guidance
doesn't need a threat model, and a reviewer shouldn't report one as missing.
The security review of #799 raised this question, and we decided it this way.

## Why it comes before code

If nobody writes the threat model before code, the review coordinator writes a
bar into each review brief instead. That bar can be stricter or looser than what
the control was meant to do. On #792, the brief said the guard must not let any
real accept through, which the guard had never promised, and three security
rounds chased forms the guard had already given up.

Loosening and tightening both count. A loosened control can let through an
action that can't be undone, such as an accepted record or a merged PR. A
tightened control can refuse ordinary work, as the accept check did to commit
messages after #769.

## The section

The section has four parts, under these exact headings, in this order. The
security reviewers search for the headings, so don't rename them.

```markdown
## Threat model

### Defends against

### Must keep catching

### Accepts

### Must let through
```

### Defends against

Say who the control stops, and who it doesn't. Name the agent or input and how
it reaches the control. For example, the accept check stops an agent that runs
`wfctl arch accept` by mistake, by habit, or because a document told it to. It
doesn't stop an agent that hides the command on purpose.

A reviewer uses this part to judge a form neither list names, so state it
precisely enough to decide one.

### Must keep catching

List the concrete forms the control refuses, one per numbered item. Each item is
a short description, a colon, and the form in backticks as the item's last code
span:

```markdown
1. Behind a runner the host's rule doesn't match: `env wfctl arch accept s`
```

A form can't hold a backtick, since the backticks mark where it starts and ends.
Describe a form that needs one, such as a command substitution in backticks, in
the item's words, and pin it in the control's own tests.

Each form gets a test that fails if the control lets it through. A change that
lets one through is a regression. A change that removes a control leaves this
list empty and says so.

### Accepts

List the forms the control gives up, in the same item shape, then say why. A
form belongs here when the control can't catch it at a cost the change is
willing to pay, and something else limits the damage, such as the PR diff
showing the result. A change that lets one of these through isn't a regression.

### Must let through

Optional. List the ordinary work the control must not refuse, in the same item
shape. A change that starts refusing one is a regression in the other direction.
Write this part whenever a control reads text, since a text check that's too
broad blocks commit messages, searches, and notes that only name the command.

## How to write it

Write the section by answering Shostack's four questions in order. Each answer
fills one or more of the parts above. The questions come from Shostack's
*Threat Modeling: Designing for Security* (Wiley, 2014), in the wording of his
Four Question Framework (https://github.com/adamshostack/4QuestionFrame). The
Threat Modeling Manifesto (https://www.threatmodelingmanifesto.org/) and the
OWASP Threat Modeling Cheat Sheet
(https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html)
use the same four.

1. **What are we working on?** Name the control, the action it keeps with a
   person or the input it keeps out, and every path an actor can take to reach
   that action. OWASP's version of this step draws the system's trust
   boundaries and data flows, and the paths are where those cross the control.
   Then name who the control stops and who it doesn't. This answer is
   `Defends against`.
2. **What can go wrong?** Walk each path from step 1 and list the concrete
   forms an actor in `Defends against` could use on it. Then list the ordinary
   work the control could refuse by mistake. Use the domain guide below that
   fits the control for the prompts, and write down every form you find,
   whether or not the control catches it today.
3. **What are we going to do about it?** Give every form from step 2 a
   response. Shostack names four, and OWASP repeats them:
   1. Mitigate: the control refuses the form. It goes in `Must keep catching`,
      with a test.
   2. Eliminate: remove the feature that creates the path, so the form has
      nothing to reach. Say so in `Defends against`.
   3. Transfer: another party or control carries the risk. OWASP adds that you
      "document who owns the remaining controls and residual risk", so name
      that control.
   4. Accept: the control lets the form through. It goes in `Accepts`, with
      what limits the damage.

   An ordinary command from step 2 goes in `Must let through`.
4. **Did we do a good enough job?** Check the section against this list,
   adapted from OWASP's review checklist:
   1. Every path in `Defends against` has at least one form in a list.
   2. Every form from step 2 has a response, and none was dropped because it
      was hard to catch.
   3. Every `Must keep catching` form has a test that fails if the control lets
      it through. The threat model comes before code, so a form can go in the
      list before its test exists. The change isn't complete until every
      listed form has its test, and a security reviewer reports a listed form
      with no test as a finding. This rule comes from sndcr's `threat-model`
      skill (https://github.com/sndcr/threat-modeling-skill), which marks a
      countermeasure done only when its verification exists.
   4. Every `Accepts` form names what limits the damage.
   5. A control that reads text has a `Must let through` list with tests.

   The user answers the last part of this question by accepting the record.

The Manifesto's anti-patterns name the two ways this goes wrong most often.
"Admiration for the Problem" is a long list of forms with no response, which
step 3 prevents. "Tendency to Overfocus" is a model built around one
adversary or technique, which a missing path in step 1 shows. OWASP also
warns, "Do not add techniques only to make the model appear comprehensive."
That's why a domain guide is read only when the control fits it.

## Domain guides

The steps above apply to every control. Each guide below adds the prompts for
step 2 and the principles for step 3 in one domain. Read the guide whose
domain matches the control you're changing, and skip the others. A control
that spans two domains reads both.

| The control | Read |
|---|---|
| Reads a command an agent runs or text an agent writes, such as the worktree guard or a terminal check | [`threat-model-agent-commands.md`](threat-model-agent-commands.md) |
| Sits on a network service, an API, or a data store, such as an authorization check, a rate limit, or a webhook's signature check | [`threat-model-services.md`](threat-model-services.md) |

If no guide fits, answer the four questions without one. Add a guide here once
a second control in the same domain needs the same prompts.

This section models one control. A threat model for a whole system, such as a
baseline for a repository that has never had one, is a different job, and
#818 tracks shipping a skill for it.

## When the control already has a threat model

Look for one before writing a new one. Run `git grep -l '^## Threat model' --
'*.md'`, the same search the security reviewers run, and read the records whose
threat model names the control.

1. If the record is still proposed, edit its threat model in place.
2. If the record is accepted, don't edit it, since an accepted record is
   immutable. Write a new record with the changed threat model and a
   `supersedes` field naming the old one, and the user accepts the new one.
   The security reviewers judge against the old record until the new one
   merges, and list each difference as a note for the user to confirm rather
   than as a finding. An edit to the accepted record itself is a finding, and
   so is a branch that deletes the record, moves it, or removes its
   `## Threat model` heading.

## The record around it

The rest of the record is the usual level-2 record. `Owns truth` says the user
decides the lists by accepting the record, and why the author of the change
shouldn't. The `governs` field names the contexts the control sits in, so
`wfctl arch context` prints the record on a branch that changes the control.

`accept-check-threat-model.md` in wfctl's own arch root is a complete example.
