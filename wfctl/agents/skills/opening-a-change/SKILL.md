---
name: opening-a-change
description: 'Write the description before opening a change, from the template the repository already ships. Use when about to open a PR, create a pull request, raise a change, push a merge request or a patchset. Use before reaching for `gh pr create`, `glab mr create`, or `git push` for review. Layers the description step over finishing-a-development-branch, which still owns the integration decision.'
---

# Opening a change

A repository that ships a change-description template wrote it for two authors
and only reaches one. A human opening a pull request in a web UI gets the
template prefilled; `gh pr create --body-file` writes whatever it is handed and
never looks. The template is not optional guidance that an agent may substitute
its own summary for — it is the project's stated answer to *what a reviewer
needs*, and it is on disk.

**Announce at start:** "I'm using the opening-a-change skill to write the
description from this project's template."

## Order

`finishing-a-development-branch` owns the integration decision and everything up
to the push. This skill owns the body. Run that skill first, unmodified —
`.agents/skills/finishing-a-development-branch/SKILL.md`. It verifies the tests,
detects the environment and determines the base branch, and its Option 2 ends at

```bash
git push -u origin <feature-branch>
```

Pick up there. Two notes on running it from here:

- A reader who said "open a PR" has already answered its Step 4 menu. Do not ask
  the four options again — take Option 2 and run the rest.
- Its Step 1 still applies in full. A description written against a failing suite
  describes something that does not work yet.

## Step 1: Run the review panel

A repository has one or more review groups, and every change runs all of them
before its PR opens. List them in the order they run:

```bash
wfctl review groups
```

```text
security  reviewing-security  s1 s2 s3 claude
code      code-review         c1 c2 c3 claude
```

Run each group, in that order, over this branch's whole, unmodified diff, with
`.agents/skills/fanning-out-code-review/SKILL.md`, before
you open the template. Security and code always come first, and a group the
repository adds runs after them.

Run every group on every change, with no condition that skips one, including
the change that looks too small to need it. Skipping a group because this
particular diff seemed trivial is a decision made silently, on each run, by the
only party with an interest in the answer. That is what this step
removes, with no exception for a small diff.

It is a step here rather than a phrase in that skill's description because a
description is matched against what a reader said, and in an unattended run
nobody says anything. A panel is most worth running when a change is about to
be opened, and that is when nobody is there to type "review this". The
discovery mechanism that works for a human can't fire here.

**Commit each group's fixes before the next group starts.** The security group
commits its fixes. The code group reviews the result, so a security fix that
breaks something reaches a reviewer before it reaches `main`. wfctl records
commits, not the working tree. If a group's fixes are still uncommitted, the
next group reviews a tree that its run record doesn't describe.

**wfctl refuses the PR until every group has reviewed the newest commit.** The
worktree guard refuses `gh pr create` and `gh pr merge` while any group has
commits it hasn't reviewed, and lists those commits under each group. A fix the
code group commits is a new commit the security group hasn't reviewed. The
security group then runs again over only that fix, then the code group if the
security group changed anything. The security group's own fixes are new
commits too, so a security run that produced fixes needs another security run
over them. Each of these runs is short, since a group's run covers only the
commits since its last complete run.

**Stop after three complete rounds and ask the person for a sign-off.** A round
is one complete run of every group. If the guard still refuses the PR after the
third round, show the person the commits it lists. Ask them to run
`wfctl review sign-off` in their own terminal, or to say how they want to
proceed. Don't run a fourth round on your own, and don't try to sign off
yourself, since the guard refuses that command from an agent. wfctl numbers the
runs but doesn't count rounds yet (#626), so you track this limit yourself.

**None of the panel's output goes in the description.** That covers every
finding, whether you applied it, accepted it, or rejected it, and it covers the
disposition table, the roster, and any line saying the panel ran. It holds for
the first body and for every push after it.

The disposition table from the panel skill's Step 5 goes to the person you are
working for, in the conversation. Report one table covering every group, one
row per finding, naming each reviewer by its id and model, such as `s3 codex`.
They can overrule a disposition, and they do that in the conversation. A
finding you applied is a commit on this branch, which the diff already shows. A
finding you did not apply was a decision made with that person, and it is
theirs to carry further.

On MarinVentures/pfms#680 a description that carried the panel gained a row
with every review round until it held 15, 12 of them findings already applied,
and the maintainer asked that the body not mention the panel at all. So the
description is for the change, and the panel is not part of the change.

A finding you did not apply can still be something a reviewer of the change
needs to know, and then it is written about the code rather than as a finding.
A rejected one becomes an open question ("Should `resolve` fall back to the main
checkout when the manifest is missing?"). A deferred one becomes a follow-up you
are deliberately leaving, with whether it was filed. Both go where the template
keeps open questions and follow-ups, and neither names the panel or a reviewer.

**The guard checks that the panel ran, and it reads wfctl's records, not
yours.** Before wfctl kept review records, the only trace of a panel was one
report per reviewer, which the coordinating agent filed in a folder outside the
tree. A check that those files existed would have been worthless, since the
same agent wrote them about its own work. Their presence showed only that a
folder was filled, not that a panel ran. Now wfctl decides which commits each
run covers, which reviewers it expects, and whether each report counts, and the
guard reads that record (`review-covers-unreviewed-commits`).

The question that decided whether the rule became a check is
`a-rule-is-expressed-as-a-check`'s. **Keep it a quotation.** A summary of it
drifts into a criterion the record does not have, such as "visible in *any*
artifact" or "an artifact a reader can reach". A drifted summary of this
particular test inverts its verdict rather than blurring it. The record also
doesn't ship with this skill, so its words have to be quoted here, or nobody
reading this skill can see them:

> is a violation of it visible in an artifact the work already produces?

> *Already produces* is the load-bearing half. It excludes a check that needs an
> artifact invented so that it can be checked, and it includes the reply, the PR
> body, the diff and the tree — which is where every violation above was
> observed.

A report the agent wrote about its own work, in a folder outside the tree,
answered no, so the rule stayed prose. A run record that wfctl writes, with
the reports wfctl judges against it, answers yes, so the rule is now the
guard's check.

Findings you apply change the branch. **Commit them**, re-run the verification,
and push again before Step 5 — `git push` moves commits and not a working tree,
so an uncommitted fix leaves the PR opening from the commit that still has the
defect. A recorded verdict binds to the tree it ran against, which your fix has
moved, so the verification is re-run after the commit rather than before it.

## Step 2: Find the template

It is a file in the repository:

```bash
find . -maxdepth 3 -name .git -prune -o -type f \
     \( -ipath '*pull_request_template*' \
        -o -ipath '*merge_request_template*' \) -print
```

Four details, each of which has already produced a wrong answer once:

- **`find`, not a list of paths with globs in it.** Under `zsh` a glob matching
  nothing aborts the whole command line, so the lookup reports *no template* in
  a repository that has one.
- **`-ipath`, not `-iname`.** GitHub's multi-template layout puts the files in
  `.github/PULL_REQUEST_TEMPLATE/`, named `bug.md` and `feature.md` — basenames
  that match nothing. GitLab's `merge_request_templates/` is the same shape.
  Matching the path finds them; matching the name finds the directory instead.
- **`-type f`.** Without it the multi-template *directory* is itself a hit, and
  the next step tries to read a directory as a template.
- **`-name .git -prune`.** `-not -path` filters the output but still walks the
  object store, which is slow and can surface a blob that happens to match.

Case-insensitive throughout: the same file ships as
`pull_request_template.md` and `PULL_REQUEST_TEMPLATE.md` in about equal numbers.

`.github/` wins over `docs/` and the repository root, which win over a match
anywhere else.

Then read it. **All of it, before writing a line of the body.** The sections it
asks for, the order it asks for them in, and the instructions inside its comment
blocks are the specification for what you are about to write.

This skill does not carry a section list of its own, and must never grow one. A
second copy of the project's sections would be a copy to keep in sync, and the
copies that fall behind do not announce themselves — they contradict the file
that is actually installed.

If several templates match, ask which one this change is; a repository with a
`PULL_REQUEST_TEMPLATE/` directory has deliberately made that a choice.

## Step 3: If there is no template

State the shape you are using rather than refusing or improvising:

```
No change-description template in this repo. Using the default shape:
Summary (context, then the drawing, then what / why / impact) · What changed ·
How it was tested · Issue links · Additional context.
```

Then fill those five. The panel's findings went to the person in the
conversation, with or without a template. The one thing from Step 1 that can
land here is a finding already rewritten about the code, as an open question or
a follow-up, and that goes under Additional context like any other.

`wfctl install-config github` seeds a real template — say so once, and do not
block on it.

## Step 4: Fill every section

- **Every section the template has, in its order.** A section you have nothing
  for gets "None" or "N/A" — never silent deletion, which reads as an answer.
- **A `## Review Panel` section is an older template, and it gets "N/A".**
  `install-config` writes a template once and never touches it again, so a
  repository seeded before this skill changed still carries that section, and
  its comment block still asks for the disposition table and refuses "N/A".
  Step 1 overrules that comment. Deleting the section would read as an answer,
  and filling it would put the panel in the description; "N/A" does neither.
  The template is the project's file to change, not yours. The same goes for a
  checklist item or a comment block elsewhere in an older template that asks for
  findings under Additional Context: leave the item unticked and write nothing
  from the panel.
- **A comment naming `conversation-response-shape` as the owner of the
  form-selection table is an older template too.** That skill no longer ships
  with wfctl, and the seed-once rule above means the pointer was never updated.
  The table is in "Choosing a drawing" below, so read it there, and leave the
  template's wording for the project to change.
- **Answer the comment blocks; then delete them.** They are instructions to the
  author, not part of the description. Placeholders in brackets are replaced,
  not left.
- **Tick only what you actually did.** An unticked box is information a reviewer
  can act on. A checklist ticked wholesale is worth less than an empty one,
  because it now has to be verified line by line.
- **Evidence comes from the branch, not from your session.** `git log`, the
  diff, the issue and the test output — the reader has none of your context, and
  the parts of it that mattered are the ones already written down.
- **Render literal output where the template asks for a before/after.** The CLI
  line as it printed, the record as it is shaped, the error as it read. A
  sentence describing a string is longer than the string and less certain.
- **Pick the drawing's form from the table, then read the template for its
  notation.** "Choosing a drawing" below is the single home for which form the
  material calls for. Whether that form ships as ASCII or as mermaid is the
  template's question, and its answer is conditional rather than a default:
  mermaid where the reader is at a desk and a layout engine should do the work,
  ASCII where the drawing has to survive a phone or a terminal, and ASCII where
  placement carries grouping, alignment, or counts positioned to be compared.

  **Position that carries meaning is a reason to stay in ASCII, not something
  to re-draw.** A layout engine assigns position itself, so the distinction is
  not preserved and not recoverable. Where the distinction never rode on
  position — a glyph, an arrowhead, a line style — a class carries it across:

  ```
  classDef terminal stroke-dasharray: 4 3
  class R2,R3 terminal
  ```

  A chain is the case that goes wrong quietly. Where one does render as
  mermaid, it is `flowchart LR` with the chain as edges and **no `subgraph`** —
  grouping the levels reads as the obvious translation of the nesting, and an
  edge leaving a grouped box drags its members out of the group.
- **Name the issue in the form the tracker parses** — GitHub `Closes #123`,
  Jira `Fixes PROJ-45` — not the key written into a sentence. This is the one
  attribute Step 6 cannot set: it lives in the body or nowhere, and it is what
  links the change to its issue in the tracker's own panel. Where the template
  has a section for it, that section's rules govern the details and this bullet
  stops here.

## Choosing a drawing

**Draw when the reader has to hold something to follow the sentence** — a set, a
location, a count, a branch. Not when the prose gets long: a short paragraph can
fail this just as badly, and length was never the signal.

The drawing carries the argument. The line beneath it is a caption — it names
what to look at and says nothing the drawing already says.

**A change that only rewords or reorders text takes no drawing.** A reworded
paragraph has no set, location, count, or branch for the reader to hold, and the
diff already is the before and after. The only thing left to draw is a
paraphrase of the new text, which repeats what What, Why, and Impact already say.
So Before / After reads `N/A`, or at most one high-level line naming the new
order when a document was reorganized. A text edit that changes a rule the text
states, such as a skill's branching instruction, is not this case; the rule has
a before and after, and it is drawn like any other. The test is what the change
does and not how much of it there is, so a one-line code change that flips a
branch still earns a drawing.

**A proposed change is a set.** Naming a fix means naming what the code does
today and what it does once changed, across every input that reaches it — the
*rows against columns* row below, and the one most often missed. The diff is
not that drawing: a branch the reviewer has to run in their head to recover the
states is the holding a drawing exists to prevent.

**Pick the form from what the material is**, before reaching for any of them:

| The material is | Draw |
|---|---|
| a set split in two | two columns, counts in the headers |
| one source, several destinations | a fan-out, annotations hanging right |
| a chain whose destinations fan out again | a nested tree, each level indented under the node it hangs from |
| a value and what it causes | the value, then `└─►` the consequence |
| a sequence with exits | a flow, exits hanging off the step that takes them |
| rows against columns | a table |

Two columns is the most frequent row. *Before / after* is one filling of it —
*can observe / cannot observe*, *checked / assumed*, *mirrored / not mirrored*
are others — and the split is chosen from the material, not defaulted to.

**Tabular content goes in a table.** Columns aligned by hand inside a code block
read as jumbled the moment one cell outgrows its header — this is the rule
`check-body` (Step 5) enforces mechanically; the rest of this section is
judgment a check can't see. Reserve ASCII for flows, trees and timelines, where
arrows and nesting carry what a table cannot.

**Enumerate real states, not every trigger.** A property that varies across
every row is a column, not a row. Two states that leave identical output are
one state reached two ways — collapse them.

## Step 5: Open it

Write the body to a file and pass the file. `--body` on a shell line mangles
newlines, backticks and anything a diagram needs.

Write the description to `/tmp/pr-body-<branch>.md`, with this branch's name
written out, such as `/tmp/pr-body-622-security-review-panel.md`. Then run two
separate commands, and read the first one's output before running the second:

```bash
wfctl check-body /tmp/pr-body-622-security-review-panel.md
```

```bash
gh pr create --title "<subject>" --body-file /tmp/pr-body-622-security-review-panel.md
```

**Run `gh pr create` on its own, exactly in this shape.** The worktree guard
checks the branch before any part of the command runs. It refuses
`gh pr create` chained after another command, such as a commit, a push, or a
`cd`, since that command could change the branch after the guard checked it.
For the same reason, it refuses a command substitution such as
`$(git branch --show-current)` anywhere in the command. It also refuses an
environment prefix such as `NO_COLOR=1`, since the guard's own `git` and `gh`
calls don't see that variable. That's why each command writes the path out in
full rather than building it from the branch name.

**Outside the repository, and the path is not decoration.** A description written
into the worktree is an untracked file, so the tree it describes stops being clean
the moment it exists — and the verification finding below then reports `tree has
uncommitted changes` about the description itself, on a branch that verified clean
a second earlier.

**The branch is in the filename for the same kind of reason.** Two worktrees
cannot be on one branch, so this collides with nobody; a fixed `/tmp/pr-body.md`
is one file every concurrent session writes, and the damage lands in the gap
between the two commands above — yours is checked, theirs overwrites it, and `gh`
uploads a description nothing validated and nobody wrote for this change. Write
the path out in each command rather than carrying it in a shell variable. A
shell doesn't outlive the command it ran, and an empty variable points `gh` at
the current directory.

A scratch directory your harness already gives you is better than either, since
it is unique per session without deriving anything. Use it where you have one,
and write its path out the same way.

### When the guard refuses

The guard prints a `✗` line with the reason, and each kind of refusal has one
response:

- **Commits no review covered.** The guard lists them under each group. Go back
  to Step 1 and run the groups it names, then open the PR again. After three
  complete rounds, ask the person for a sign-off, as Step 1 says.
- **The review check failed.** Something stopped the check from reaching an
  answer, such as a `gh` call that timed out or a record it couldn't read. Stop
  and tell the person, naming the error the refusal printed. Don't retry the
  command in another spelling. The refusal notes that a person can run the
  command in their own terminal, where the hook doesn't run, and that is the
  person's call.
- **Run this from the checkout on the trunk branch.** The command acts on
  another branch's pull request, and a worktree opens and merges only its own.
  Leave that pull request to the checkout on the trunk branch.
- **Any other refusal**, such as a chained command or an environment prefix,
  names the shape it refused. Run the command in the shape this step shows.

`check-body` reads the drawings against "Choosing a drawing" above, this skill's
own home for which drawing to use. It knows one thing and says so: a fenced
block with columns aligned by hand *and* a cell that outgrew its header is
tabular content, and tabular content goes in a table. That combination is the
one the reader rejected on #208 — the fix was replacing the fence with a
markdown table, and the accepted drawings in the same body are hand-aligned too,
which is why alignment alone is not the finding.

**Its other finding is not about the file.** A `verification:` line says the
repository declares a definition of done and no record of it passing covers this
tree — never run, failed, left inconclusive, or taken against a commit the branch
has since moved off:

```
verification: unverified — run `wfctl verify`
verification: failed — 1 of 3 at a1b2c3d: pytest -q
verification: stale — verified at a1b2c3d, HEAD is e4f5a6b
```

Run `wfctl verify`, then read the body check again. It is not a gate and there is
no flag to silence it: a change that should ship unverified ships unverified, and
the line is the record that it did. A repository that declares no definition of
done never prints it.

This is the only check on the road every change takes, which is why it is here.
`wfctl verify` was called from one place — `speckit-implement` step 9c — and that
runs only when the pipeline runs, so the bug fixes and copy edits `design-levels`
sends around the pipeline were certified by nothing but the agent that wrote them
(#236).

It exits 1 when it finds something and gates nothing; the point is that the file
exists before `gh` reads it, so the check is available at all. Outside a wfctl
repo, or with no `wfctl` on `PATH`, skip it — the rule is in the skill either way.

The body only. The sidebar is Step 6 and is deliberately not a flag on this
command: a flag dropped from an invocation cannot be observed as missing, and
this step reports done the moment the PR exists. A step can be observed as
unfinished. That is the whole reason the two are separate.

## Step 6: Fill the sidebar

`gh` sets no attribute on its own. A body can be perfect and the change still be
absent from every board, filter and milestone the issue it closes already sits
on — the description is what a reviewer reads, the attributes are how anyone
finds it to read.

**Read them off the issue rather than inferring them from the diff.** Someone
already made this triage decision; re-deriving it from what the change touches
puts `documentation` on a bug fix, because the fix edited prose.

```bash
gh issue view <issue> --json assignees,labels,milestone,projectItems
gh pr edit <pr> --add-label <name> --milestone <title> \
  --add-assignee <login> --add-project <title>
```

Copy the set across whole. A label the change earns in its own right is added to
that set, never swapped in for it.

**An empty field on the issue is not an answer to copy.** An unassigned issue is
not a decision that the PR has no owner, so that case is `--add-assignee @me`.
An issue bare in every field is the same shape — triaged by nobody rather than
triaged to nothing — and copying it faithfully produces exactly the unfindable
change this step exists to prevent. Treat it as the no-issue case below: decide
the triage rather than inherit it.

**A change that closes nothing still has a source.** Read the set off the issue
it is filed under — the one in `Related` naming the work this belongs to. Falling
back to an empty sidebar because no issue carries a closing keyword is the same
omission this step exists to catch, arriving through a gap in the instruction
rather than through a dropped flag. Where the change answers to no issue at all,
triage is a decision you are making rather than one you are copying: make it, and
say in the description that you did.

`--add-project` takes the project's title and works on a Projects v2 board, but
it only *adds* the item. The board's "item added" workflow then writes the
default status, which is the backlog column — so a PR opened for review lands
behind the issue it closes, which is already in progress. Set it deliberately:

```bash
gh project item-list <project> --owner <owner> --format json --limit 200 \
  --jq '.items[] | select((.content.number//0)==<pr>) | .id'
gh project item-edit --id <item> --project-id <pid> \
  --field-id <status field> --single-select-option-id <option>
```

**Never reshape the Status field to make room for a column.**
`updateProjectV2Field` takes the option list whole rather than appending to it,
and rewriting it regenerates every option id — which silently clears the status
of every item on the board, not only the ones you meant to touch. Add the column
in the project UI. If it has already happened, the values are recoverable: each
item's content carries a `ProjectV2ItemStatusChangedEvent` timeline, and the last
one per item is the status it held.

**Reviewers are the one field with nothing to copy from.** An issue has no
reviewers; a change does, and `gh pr create` requests none. Who a repository
wants reading its changes it has already recorded somewhere — a `CODEOWNERS`
entry, a review bot the org installed, a line in the contributing guide — and
those arrive on their own. Request whoever that leaves out, and nobody the
project has stopped using: a reader dropped for cost is not restored because the
flag still accepts the name.

```bash
gh pr edit <pr> --add-reviewer <login>     # "@copilot" for Copilot
```

`--add-reviewer` takes a user or team login, and a review bot installed as a
GitHub App is neither — it subscribes itself and cannot be requested by name. On
a repository whose readers are all of that kind, an empty reviewer field is the
finished state, and the way to know which kind you have is to look at a PR you
did not touch.

Then read it back — with the check where it is available, and by eye where it
is not:

```bash
wfctl change check <pr>
```

It reports every field the issue carries that the change does not, plus any your
repository named in `change_check` in `wfctl.json`, and stays silent about
everything else. `⚠` is a finding, `✓` a field it verified. Exit 1 means this
step is unfinished.

This exists because the paragraph above it was skipped across several worktrees
(#302). A run that copied the sidebar and a run that did not produced the same
observable state, so nothing disagreed. Now something does.

**`ℹ No \`fields\` verb for changes` is not a pass, and it is the answer you
should expect first.** It means the tracker config in this repo predates the
verb, so the check read nothing and exited 0 — and *no ordinary command tells
you*. A bare `install-skills` fills a missing tracker file and never refreshes a
present one; `doctor` does not look inside `.agents/trackers/`; `tracker-check`
prints the `verbs` section only, never `changes`, which is the half this reads
first. The refresh is explicit:

```bash
wfctl install-skills --tracker <name>     # `github` for the shipped backend
```

Until that has been run, and in any repo whose backend declines the verb, do the
read-back by hand. This is the instruction the check replaces, not one it
retired:

```bash
gh pr view <pr> --json labels,assignees,milestone,projectItems     # copied
```

The copied set is done when it matches the issue's.

Neither form reaches the two below, which are not copied from anywhere:

```bash
gh pr view <pr> --json closingIssuesReferences,reviewRequests,latestReviews
```

**Reviewers: every login you requested appears in one of the two lists.**
`reviewRequests` is the *pending* list and clears the moment a reviewer submits,
so a name missing from it is either done or was never asked; `latestReviews`
tells them apart. Neither list being empty is the check — a bot that reviews
every PR fills `latestReviews` whether your own request landed or not, so the
comparison is against the names you chose, not against zero.

**The linked issue: `closingIssuesReferences` answers only for a GitHub
tracker.** It holds GitHub issue links, so a repository tracking work in Jira or
Gerrit reports it empty for a body that named its issue correctly, and reading
that as unfinished fails the change for doing the right thing. Where the tracker
is something else, the keyword is verified by reading the body — the tracker's
own link, if it draws one, is not this field.

An empty sidebar here is this step unfinished, not a PR that happens to have no
attributes.

## Red flags

- "The description no longer mentions the panel, so Step 1 is optional." The
  step is not reached through the body and never was; what the body stopped
  carrying is the panel's output, not the requirement to run the panel over
  every change.
- Any mention of the review panel in the description, on the first body or on a
  push after it. That includes a status line such as `Review panel: s1 ✓ s2 ✓
  s3 ✓`, a roster, a findings table, and a single finding of any disposition.
  The table goes to the person in the conversation, and a question a reviewer
  needs is asked about the code.
- Skipping a group, or starting the code group before the security group's
  fixes are committed. The guard will refuse the PR either way, and the group
  that ran early reviewed a tree that has since changed.
- Retrying a refused `gh pr create` in another spelling. The `✗` line names why
  the guard refused it, and a spelling that gets past the check opens a PR that
  the review record marks as unreviewed.
- Running the panel after the PR is open, because the diff is easier to point at
  there. The findings then arrive against a change reviewers have already been
  asked to read, and every fix lands as a commit pushed after they started.
- Composing a summary first and checking the template afterwards. By then the
  body exists and the template becomes something to reconcile against rather
  than the thing being filled.
- "The template is boilerplate for this change." The sections a change makes
  look like boilerplate — usually Before / After and the test details — are the
  ones a reviewer cannot reconstruct themselves. A change that only rewords
  text is the one exception for Before / After, and "Choosing a drawing" says so.
- Reporting a green suite as the test evidence. A negative case checked by hand
  — the new check failing when the fix is reverted — is the half that gets
  skipped, and the only half that proves the check works.
- Editing the template because a section did not fit. The template is the
  project's file; a change to it is its own change, argued on its own.
- "The PR is open, so the step is done." The body is what a reviewer reads; the
  attributes are how anyone finds it to read. PR #179 was opened by an agent that
  had read this skill in the same turn and landed with none of the issue's four,
  because the sidebar was an argument on someone else's command rather than a
  step of its own.
