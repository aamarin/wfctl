---
status: proposed
governs: trackers
---

# The issue edit verb writes one field per backend call

## Context

`wfctl issue edit` changes an issue's title, its body, or both. Each tracker
backend declares the commands it supports in `.agents/trackers/<name>.json`, as
argv templates with `{name}` placeholders. Every placeholder in a template is
required. If a caller leaves one out, wfctl refuses to run the command.

That makes optional fields hard to express. The caller passes `--title`,
`--body`, or both, but a single template naming `{title}` and `{body}` can only
run when both are given. Filling the missing one with an empty string would
make the backend blank that field, which is the worst failure a body edit can
have.

The boundary stays where it is. The tracker owns the write, and wfctl owns the
record of it, as it already does for `label`. Both domain contexts this
change affects have recorded that no boundary moves, so this record covers only
the shape of the verb.

## Verified

- `wfctl/_tracker.py` `_substitute` raises `_MissingParam` when a placeholder's
  value is `None`, and `dispatch` then prints "'<verb>' requires --<key>" and
  returns 1. Every placeholder is required.
- `wfctl/agents/trackers/github.json` declares
  `"label": ["gh", "issue", "edit", "{id}", "--{action}-label", "{label}"]`.
  Substitution happens within a token, so a backend already builds a flag
  name from a placeholder.
- `dispatch` records a successful write as `issue-<verb>` only for verbs in
  `_RECORDED_VERBS`, which is `comment`, `create`, `label`, and `close`.
- `gh issue edit` takes `--title` and `--body` as separate flags, so
  `--{field}` with `field` set to `title` or `body` produces both.
- The `scaffold-tracker` skill asks about every row of its verb table, so
  a new row there is asked about when a backend is authored.

## Assumed

- A tracker whose CLI spells the flags differently, such as Jira's
  `--summary` for the title, can ship a short script that maps `title` and
  `body` to its own flags. If most backends need that script, the field
  names are leaking into the backend contract, and an explicit mapping in the
  config would serve better.
- Two writes that are not atomic are acceptable when both fields are
  given. Nothing we know of depends on a title and body changing together.

## Direct baseline

The backend declares one `edit` template carrying both fields:
`["gh", "issue", "edit", "{id}", "--title", "{title}", "--body", "{body}"]`.
wfctl dispatches it once. A caller who wants to change only one field has to
pass the current value of the other, which means reading the issue first and
writing back the field it did not mean to change.

## Decision

The backend declares one `edit` verb that takes `{id}`, `{field}`, and
`{value}`, following the shape `label` uses:

```json
"edit": ["gh", "issue", "edit", "{id}", "--{field}", "{value}"]
```

wfctl calls it once for each field the caller passes, title first, with
`field` set to `title` or `body`. Each call that succeeds is logged as
`issue-edit`. If the title write succeeds and the body write fails, wfctl
reports that the title changed and the body write failed, and exits non-zero.
A backend that doesn't declare `edit` gets the notice every other missing verb
gets.

## Diagram

```
          baseline                          decision

          ┌──────────────┐                  ┌──────────────┐
          │ wfctl issue  │                  │ wfctl issue  │
          │ edit         │                  │ edit         │
          └──┬────────┬──┘                  └──────┬───────┘
     reads   │        │ calls once                 │ calls once per field (new)
   other     │        │ with title + body          │ with field + value
   field     ▼        ▼                            ▼
════ tracker contract (in force) ═══════════════════════════════════
          ┌──────────────┐                  ┌──────────────┐
          │ backend view │                  │ backend edit │
          └──────────────┘                  └──────────────┘
          ┌──────────────┐
          │ backend edit │
          └──────────────┘
```

The tracker contract is the only divider, and it is already in force.

The change this decision is built to absorb is a third editable field, such
as an assignee. In the baseline, adding it touches every backend's `edit`
template, and every single-field edit gains one more value to read back first,
so it changes two arrows. In the decision, a backend that can set the field
with `--assignee` needs no template change, and wfctl gains one more allowed
field name, so it changes no arrows. The decision also removes the `reads`
arrow, so wfctl no longer reads an issue in order to write it.

## Considered

- Optional placeholders in the template language, such as a token dropped
  when its value is missing. We didn't choose this because it changes the
  config format every backend is written in, for one verb, and `validate_config`
  and `scaffold-tracker` would both have to learn it.
- Two backend verbs, one for the title and one for the body. Each template
  stays plain and needs no field names, so a tracker with different flag
  names needs no script. We didn't choose this because it adds two words to a
  verb list that has no stated naming rule yet (#402). It would also be the
  first time a `wfctl issue` verb name doesn't match the backend verb it runs.
- `edit` for changes (PRs) as well. We left it out because the `changes`
  section has no write verbs at all, and the first one, `create`, is tracked in
  #126. A change `edit` belongs with that work, since recording a change write
  needs the same support.

## Consequences

An agent can change an issue's title or body without naming a vendor, and the
write is recorded where a restarted session reads it. A backend's `edit`
template stays a single plain argv.

The field names `title` and `body` become part of the backend contract. A
backend whose flags use other names needs a script to translate them.

When both fields are given and the second write fails, the issue is left
half-edited. wfctl says which half landed, but it doesn't roll the first
write back.

## Verification

- A test dispatches `edit` with only `--title` and asserts one backend call
  with `field=title`, and one `issue-edit` record.
- A test dispatches both fields with the body call failing, and asserts that
  the output says the title changed and the body write failed, the exit
  code is non-zero, and exactly one `issue-edit` record exists.
- A test with neither field asserts that nothing is dispatched.
- `wfctl tracker-check` accepts the new `github.json` entry and lists `edit`,
  and reports an `edit` template that leaves out `{id}`, `{field}`, or `{value}`.
- One real `wfctl issue edit` against a GitHub issue changes its body and
  logs the `issue-edit` event.

## Log

- 2026-11-09  proposed  — written during the #445 brainstorm, where the user
  agreed to the field-and-value shape over the two alternatives above.
