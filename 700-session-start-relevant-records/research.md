# Research: Session start loads the records for the branch's contexts

No `NEEDS CLARIFICATION` remained after clarify. Each entry below is a choice
the plan rests on, checked against the code.

## Where the branch's contexts come from

- Decision: `_contexts.listed(spec_dir)`, with `spec_dir` from
  `_paths.resolve_spec_dir(branch, repo_root)`.
- Rationale: the design checks read the same line through the same function,
  so a session start and the brainstorm gate agree about what the branch lists.
- Alternatives considered: the files the branch changes, rejected until #671
  moves the modules into their packages; the commit count, rejected because
  commits don't name contexts.

## How `arch context` gets the branch

- Decision: `_resolve_context()`, which `arch_context_cmd` already calls.
- Rationale: it returns the branch with no new call.
- Alternatives considered: none needed.

## How the session report gets the selection

- Decision: `default_readers` gains a `records` reader that calls
  `_evidence.records_for_branch(repo_root, branch)` and returns the accepted
  count and the applying count.
- Rationale: `default_readers` already takes `branch`, and the session report
  may import `_evidence` (`EV --> SC`). `status` in `cli.py` doesn't change.
- Alternatives considered: importing `_contexts` from the session report, which
  needs a new baseline line; passing the selection in from `cli.py`, which
  edits `status` in two places in a file #711 is changing.

## How the payload says "not narrowed"

- Decision: `applying_records` is `null` when the set wasn't narrowed, and an
  integer when it was.
- Rationale: `null` says nothing was left out, whether the branch's contexts
  covered every record or wfctl fell back to printing them all. The `Records`
  line reads the same in both cases, so the payload doesn't tell them apart.
- Alternatives considered: always an integer, equal to the total when not
  narrowed. We didn't choose it because a consumer would have to compare two
  numbers to learn what `null` says directly.

## What counts as narrowed

- Decision: narrowed means at least one accepted record was left out. A branch
  whose contexts cover every governed record prints as it does today.
- Rationale: "28 of 28 apply" adds a line that tells the agent nothing.
