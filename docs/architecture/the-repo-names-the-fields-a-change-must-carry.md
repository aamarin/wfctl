---
status: proposed
---

# The repository names the fields a change must carry; wfctl decides only whether a blank one is a finding

## Context

`opening-a-change` Step 6 says an open PR is not done until its sidebar is
filled, and that sentence is skipped across several worktrees — #301 was opened
with a body built from the template, `check-body` passing, and no labels,
assignee or milestone. `a-rule-is-expressed-as-a-check` decides that a rule whose
violation is visible in an artifact the work produces ships as a check, and an
open change is that artifact.

Building the check forces a question the prose never had to answer: *which*
blank fields are worth reporting. Labels and milestones are GitHub's vocabulary
and Gerrit has neither, so a check that names them is wrong everywhere else —
the mistake #301 made and had to undo when its label read parsed `gh issue view`
output and silently read every non-GitHub backend as having no labels. And the
answer is not uniform even within one tracker: a solo repository wants every
change assigned, while a repository whose triage someone else controls wants
that requirement to say nothing at all.

## Direct baseline

`wfctl change check <pr>` shells to `gh pr view <id> --json
labels,assignees,milestone,projectItems`, and reports any of those four that is
empty. No new tracker verb, no new config key, roughly forty lines in `cli.py`.

It works today, in this repository, and is wrong in three ways that only appear
elsewhere: a Gerrit or Jira backend has no such command, a repository that uses
no labels is told off on every change, and a repository that does not control
its own triage cannot turn the assignee requirement off.

## Decision

wfctl computes the verdict and nothing else. Which fields exist, what they are
called, and what is set on a given change all arrive from outside it — the
tracker config declares a `fields` verb returning JSON on both the `verbs` and
`changes` sections, and the tracked `wfctl.json` declares `change_check`, the
list of keys this repository requires. The keys are whatever the backend emits,
so wfctl holds no field name of its own.

A key is a finding when it is required by `wfctl.json` and blank on the change,
or set on the branch's issue and missing from the change. Anything else is
silent.

## Owns truth

wfctl owns *"is this blank field a finding?"*. The tracker cannot: a verdict
computed per backend puts the finding/notice split into an unreviewed shell
script, one copy per tracker, and that split is the entire design — a noisy
check is learned around and then ignored, which loses the prose and the check
together.

The repository and its tracker own *"which fields exist, what are they called,
and which of them are required?"*. wfctl cannot: any field name it hardcodes is
one tracker's vocabulary shipped as universal, and no constant can be right for
both a repository that assigns every change and one whose triage is somebody
else's.

## Considered

- **wfctl hardcodes the field names** — the direct baseline. Loses on the
  vocabulary: Gerrit has neither labels nor milestones, so the check would be
  wrong everywhere but GitHub. This is the failure #301 had to undo.
- **The branch's issue is the only source** — sound, and the option this issue
  itself proposed. Loses because an issue bare in every field is triaged by
  nobody rather than triaged to nothing, so the check goes quiet exactly when
  triage was skipped. `opening-a-change` Step 6 already says so about assignees.
- **A hardcoded floor for assignee, everything else inherited from the issue** —
  correct for a repository whose issues its author triages, wrong for one whose
  triage is controlled elsewhere and where the requirement is noise. A floor
  cannot be right in both, and the person running it is the only one who knows
  which they have.
- **Derive the expectation from what the repository's recent merged changes
  carry** — answers the single-collaborator reviewer question for free, which
  none of the others do. Loses on cost and on direction: substantially more
  machinery, and a repository that has been sloppy teaches the check to be
  sloppy.
- **The policy lives in `.agents/trackers/<name>.json`** — the per-repo file that
  already exists, and the one the next person will reach for. Loses silently,
  which is why it is worth recording: that tree is gitignored and rewritten by
  `install-skills`, so a policy written there works for a session and then
  vanishes with no error.
- **The backend ships the whole check as a script wfctl dispatches** — zero
  contract change, and the laziest option on offer. Loses for the same reason as
  the first: it moves the finding/notice split out of review and into shell, once
  per tracker.
- **`changes.view` returns JSON instead of a new verb** — one verb rather than
  two. Loses because `wfctl change view` is a human-readable passthrough that
  `/start-session` and the skills already use, and reshaping it to feed a parser
  breaks the caller it was written for.

## Consequences

- The comparison returns one record per key, carrying which side made the key
  checkable and the issue's value, rather than the flat list of strings
  `check-body` returns. The `✓` lines name why a key was checkable, and a list of
  strings cannot.
- The issue-side fetch is skippable, because a branch carrying no issue key is a
  reachable state. The comparison takes the issue's fields as optional.
- Reading a verb's output must distinguish "the backend declined" from "the
  backend returned nothing". `_tracker.dispatch` cannot — it prints stdout and
  returns an exit code — but `_tracker.read_issue_labels`, added by #301, already
  has the shape: `(value, detail)` where both `None` means nobody was asked.
- `fields` sits beside the `labels` verb #301 added rather than replacing it.
  `labels` feeds the notify grant, which gates outward-facing authority;
  migrating a security path onto a new reader for tidiness buys nothing today.
  The overlap is a follow-up, not this change's problem.
- List-valued keys compare as a set difference, not empty-versus-not. Step 6 says
  *"Copy the set across whole. A label the change earns in its own right is added
  to that set, never swapped in for it"* — and #301 carries `enhancement, P1`
  today while #280 carries `authority:notify`, so an emptiness test would green-
  light the exact change that motivated the issue.

## Log

- 2026-09-09  proposed    — level-2 gate of the #302 design pass, answered while
  the alternatives were still in front of the reader.
