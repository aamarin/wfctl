# Research: issue edit verb

## 1. How the backend verb is shaped

- Decision: one `edit` verb taking `{id}`, `{field}`, and `{value}`, called once
  per field.
- Rationale: every placeholder in a template is required (`_substitute` raises
  `_MissingParam`), so one template naming both `{title}` and `{body}` can't run
  with only one of them. `label` already builds a flag name from a placeholder.
- Alternatives considered: optional placeholders, and two verbs. Both are in
  `docs/architecture/design/issue-edit-one-field-per-call.md`.

## 2. Checking the tracker once

- Decision: pull the first half of `dispatch` into a helper that resolves the
  tracker name and config, checks that the verb is declared, and prints the
  existing notice when it isn't. It returns the verb map and tracker name, or an
  exit code to stop with. `dispatch` calls the helper and then runs its write as
  before. The new edit function calls the helper once, then runs one write per
  field.
- Rationale: clarify Q1 requires one notice however many fields were given.
  The helper keeps the notice text in one place, so `dispatch` and the edit
  can't drift apart on what a missing verb prints.
- Alternatives considered: calling `dispatch` once per field, which prints the
  notice twice. A support check that only answers yes or no was also considered.
  We didn't choose it because the caller would then have to print each notice
  itself, which is a second copy of three messages.

## 3. Running and recording each write

- Decision: the second half of `dispatch` (substitute, run, print stdout and
  stderr, append the `issue` event, record the outward action) becomes a second
  helper, which both `dispatch` and the edit call. The edit adds `edit` to
  `_RECORDED_VERBS` and gets `issue-edit` recorded through the same line.
- Rationale: recording happens only where wfctl knows the write succeeded,
  which is the reason `dispatch` records it today.
- Alternatives considered: the edit recording its own writes. We didn't choose
  this because it would be a second place deciding success.

## 4. What prints on partial failure

- Decision: after the backend's error, print `✗ title changed, body write
  failed` when the title landed and the body failed, or `✗ title write failed,
  body was not sent` when the title failed with a body still to send. A
  single-field failure prints the backend's error alone. The exit code is the
  backend's.
- Rationale: these are the spec's FR-005 and FR-005a. Only the edit function
  sees both calls, so it prints the line. Each line says which call failed
  rather than what the issue holds, because a write that times out can still
  land, and wfctl knows only the backend's exit code.

## 5. Usage errors

- Decision: `cli.py` checks for an id and at least one field before calling
  `_tracker`, printing `✗ 'edit' requires an issue id` or `✗ 'edit' needs
  --title, --body, or both` and exiting 2. `edit` is not added to
  `_BRANCH_SCOPED_VERBS`.
- Rationale: nothing reaches the tracker on a usage error, and exit code 2 is
  the usage-error code `typer` already uses. The branch's issue isn't used
  because a person typing `edit` means a specific issue, the same reason given
  for `close` in the comment above `_BRANCH_SCOPED_VERBS`.

## 6. Where an existing message is wrong

- Finding: `dispatch` prints `'<verb>' requires --id` when `{id}` is missing,
  although the id is a positional argument. The edit avoids this by checking
  the id itself (Research 5). Fixing the message for every verb is out of scope.
