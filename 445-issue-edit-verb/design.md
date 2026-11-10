# wfctl issue edit

Contexts: session-continuity, trackers

## Problem Statement

An agent changes an issue's title or body through `wfctl issue edit`, without
naming a vendor, and wfctl records the write as `issue-edit` like every other
`wfctl issue` write.

Currently, `wfctl issue` can't change either field. An agent that needs to
retitle an issue or add scope to its body has two choices. It can call
`gh issue edit` directly, which leaves no record, and the permission layer
can't tell that call apart from a sanctioned write. Or it can leave a comment
instead, as the #739 session did when it needed to add scope to #745.

## Recommended Direction

`wfctl issue edit <id>` takes `--title`, `--body`, or both. The tracker backend
declares one `edit` verb that takes a field name and a value, the same way
`label` builds its flag from `{action}`:

```json
"edit": ["gh", "issue", "edit", "{id}", "--{field}", "{value}"]
```

wfctl calls it once for each field the caller passes, title first. Each call
that succeeds is recorded as `issue-edit`. We chose this shape because a
tracker template treats every placeholder as required. A single template
naming both `{title}` and `{body}` can't run when the caller passes only one,
and filling the missing one with an empty string would blank that field.

The design record listed below explains this choice and the two alternatives
it beat.

### What each case prints

```
$ wfctl issue edit 445 --title "New title"
https://github.com/aamarin/wfctl/issues/445
```
One write, one `issue-edit` record.

```
$ wfctl issue edit 445 --title "T" --body "B"
https://github.com/aamarin/wfctl/issues/445
https://github.com/aamarin/wfctl/issues/445
```
Two writes, two `issue-edit` records.

```
$ wfctl issue edit 445
✗ 'edit' needs --title, --body, or both
```
Nothing is sent, and the exit code is 2.

```
$ wfctl issue edit 445 --title "T" --body "B"     (the body write fails)
https://github.com/aamarin/wfctl/issues/445
<the backend's error>
✗ title changed, body write failed
```
The exit code is the backend's, and only the title write is recorded.

```
$ wfctl issue edit 445 --body "B"                 (the backend has no edit verb)
ℹ Tracker 'jira' does not support 'edit' — skipped
```
This is the notice every other missing verb gets, with exit code 0.

```
$ wfctl issue edit --body "B"                     (no issue id)
✗ 'edit' requires an issue id
```
`edit` is not one of the verbs that defaults to the branch's issue, for
the same reason `close` isn't: a person typing it means a specific issue.

## Boundaries and Ownership

No boundary moves. As with `label`, the tracker makes the write and wfctl
records it.

1. The tracker backend translates `field` and `value` into its own command. Only
   the backend knows its CLI's flag names, so wfctl can't build that command
   itself.
2. wfctl decides which fields to send and in what order, and records each
   write that succeeded. The backend can't record it, since the record lives in
   wfctl's state directory and the backend is a plain command.
3. wfctl reports which field changed when a later one fails. Only wfctl sees
   both calls, so the backend can't say which half landed.

Both contexts declared that no boundary moves (using `wfctl arch none`).
Session continuity also declared that it makes no structural choice, since
recording `issue-edit` adds one name to an existing list.

## Software design decisions

- docs/architecture/design/issue-edit-one-field-per-call.md — the edit verb writes one field per backend call, taking a field name and a value

### Checked and assumed

| Checked | Assumed |
|---|---|
| `_substitute` in `wfctl/_tracker.py` refuses a template with any placeholder missing. | A tracker with differently named flags, such as Jira's `--summary`, can ship a short translating script. |
| `label` in `github.json` already builds its flag name from a placeholder, `--{action}-label`. | Nothing depends on a title and body changing together, so two separate writes are acceptable. |
| `dispatch` records `issue-<verb>` only for verbs in `_RECORDED_VERBS`. | |
| `gh issue edit` takes `--title` and `--body` as separate flags. | |
| `scaffold-tracker` asks about every row of its verb table. | |

## Key Assumptions to Validate

- [ ] `--{field}` works with `gh` for both fields. Test it by running a real
      `wfctl issue edit` against a GitHub issue, once with `--title` and once
      with `--body`.
- [ ] A body passed as one argv token survives multi-line markdown with
      backticks and quotes. Test it with the real edit above, using a body
      containing all three.
- [ ] The `issue-edit` record reaches a restarted session's handoff. Test it by
      checking the session's outward-action log after the real edit.

## MVP Scope

The scope includes these items:

1. `edit` added to `ALLOWED` in `wfctl/_tracker.py`, taking `id`, `field`, and
   `value`, and added to `_RECORDED_VERBS`.
2. `wfctl issue edit` in `wfctl/cli.py`. It checks for an id and at least one
   field before dispatching, then dispatches once per field, title first, and
   stops at the first failure.
3. The `edit` entry in `wfctl/agents/trackers/github.json`.
4. A row for `edit` in the `scaffold-tracker` verb table, saying that a tracker
   with other flag names points the verb at a script.
5. The `wfctl issue` help text listing `edit`.
6. Tests for the single-field, two-field, partial-failure, no-field, no-id, and
   unsupported-backend cases.
7. A release note, `changes/445.addition.md`.

## Not Doing (and Why)

- Folding `label` into `edit`. `label` already ships, and changing how it's
  called breaks every caller for no gain. Verb naming rules are tracked in
  #402, and a merge like this should be settled there first.
- `edit` for changes (PRs). The `changes` section has no write verbs yet, and
  the first one, `create`, is tracked in #126. A change `edit` belongs with that
  work.
- A `--body-file` option. `comment` and `create` take the body as an argument
  too, so adding a file option for one verb would make the three inconsistent.
  If long bodies become a problem, all three should get it together.
- Rolling back the title when the body write fails. wfctl reports which half
  landed, and the agent can rerun the body. A rollback would need the old title,
  which means reading the issue first.
- Optional placeholders in the template language, and separate title and body
  verbs. The design record explains why both lost.

## Open Questions

None. The handoff from #739 settled the verb name and the body's scope, and
this brainstorm settled the backend shape and what an unsupported backend does.
