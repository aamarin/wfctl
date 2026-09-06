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

The panel is `.agents/skills/fanning-out-code-review/SKILL.md`. Run it over this
branch's diff, whole and unmodified, before the template is opened.

It is a step here rather than a phrase in that skill's description because a
description is matched against what a reader said, and in an unattended run
nobody says anything. The moment a panel is most worth running — a change about
to be opened — is the moment there is no reader to type "review this", so the
discovery mechanism that works for a human is the one that cannot fire here.

**Its reconciled disposition table is content for the body, not a side effect.**
It goes in the description under the section the template gives it. That is the
whole of what makes a skipped panel visible: a body carrying no panel was read by
nobody, and a body carrying no panel is also what a clean pass looks like. The
two are told apart in the description or not at all.

Findings you apply change the branch. Push again before Step 5 — a PR is opened
from what is on the remote, not from what is in your tree.

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
How it was tested · Issue links.
```

Then fill those four. `wfctl install-config github` seeds a real template — say
so once, and do not block on it.

## Step 4: Fill every section

- **Every section the template has, in its order.** A section you have nothing
  for gets "None" or "N/A" — never silent deletion, which reads as an answer.
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
- **Name the issue in the form the tracker parses** — GitHub `Closes #123`,
  Jira `Fixes PROJ-45` — not the key written into a sentence. This is the one
  attribute Step 6 cannot set: it lives in the body or nowhere, and it is what
  links the change to its issue in the tracker's own panel. Where the template
  has a section for it, that section's rules govern the details and this bullet
  stops here.

## Step 5: Open it

Write the body to a file and pass the file. `--body` on a shell line mangles
newlines, backticks and anything a diagram needs:

```bash
wfctl check-body <path>                                   # then read what it says
gh pr create --title "<subject>" --body-file <path>
```

`check-body` reads the drawings against `conversation-response-shape`, which the
template above names as the owner of which drawing to use. It knows one thing and
says so: a fenced block with columns aligned by hand *and* a cell that outgrew its
header is tabular content, and tabular content goes in a table. That combination
is the one the reader rejected on #208 — the fix was replacing the fence with a
markdown table, and the accepted drawings in the same body are hand-aligned too,
which is why alignment alone is not the finding.

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

Then read it back — the whole sidebar, not the part that was copied:

```bash
gh pr view <pr> --json labels,assignees,milestone,projectItems     # copied
gh pr view <pr> --json closingIssuesReferences,reviewRequests,latestReviews
```

The copied set is done when it matches the issue's. The other two are not
copied, so that sentence does not reach them.

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

- "The reviewers had nothing, so there is nothing to write." A panel that ran and
  found nothing is a result and is recorded as one — who reviewed, what each
  checked, no findings. Left out, it is indistinguishable in the body from a panel
  that never ran, which is the failure the step exists to prevent.
- Running the panel after the PR is open, because the diff is easier to point at
  there. The findings then arrive against a change reviewers have already been
  asked to read, and the body they read says nothing was found.
- Composing a summary first and checking the template afterwards. By then the
  body exists and the template becomes something to reconcile against rather
  than the thing being filled.
- "The template is boilerplate for this change." The sections a change makes
  look like boilerplate — usually Before / After and the test details — are the
  ones a reviewer cannot reconstruct themselves.
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
