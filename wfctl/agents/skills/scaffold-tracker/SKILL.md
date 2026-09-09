---
name: scaffold-tracker
description: Author a new issue-tracker backend for `wfctl issue` by generating a `.agents/trackers/NAME.json` verb→command map. Use when a repo uses a tracker other than GitHub (e.g. a private Jira CLI) and needs the session skills to reconcile against it.
---

# Scaffold an issue-tracker backend

`wfctl issue <verb>` delegates issue operations to a per-repo backend defined by
`.agents/trackers/<name>.json`. GitHub ships as `github.json`. This skill authors
a config for any other tracker (a private Jira CLI, Linear, a custom script) so
the session skills work unchanged.

## The verb contract

The session skills speak the standard verbs below. A backend implements the
subset it supports — the presence of a verb key is its declaration, so a backend
cannot lie about what it can do.

The table is the list. Nothing here or in the steps restates how many there are:
a count written beside a table is a second copy of it, and the copy is what goes
stale — which it did, one release after `start` and `stop` were added.

| Verb      | Meaning                     | Params available for `{...}` substitution |
|-----------|-----------------------------|-------------------------------------------|
| `list`    | list open issues            | (none)                                    |
| `view`    | show one issue              | `{id}`                                     |
| `close`   | close an issue with comment | `{id}`, `{comment}`                        |
| `comment` | comment on an issue         | `{id}`, `{body}`                           |
| `create`  | open a new issue            | `{title}`, `{body}`                        |
| `label`   | add/remove a label          | `{id}`, `{action}` (add\|remove), `{label}`|
| `labels`  | list one issue's labels      | `{id}`                                     |
| `fields`  | one issue's attributes, as JSON | `{id}`                                  |
| `start`   | work on an issue has begun  | `{id}`                                     |
| `stop`    | work on an issue has stopped| `{id}`                                     |

Each verb maps to an **argv list** (never a shell string). `{name}` placeholders
are substituted per-token from the CLI options, so free text like a comment body
is always one inert argument — no shell injection, no quoting to get right.
Substitution is within-token, so `"--{action}-label"` becomes `--add-label`.

`labels` must print **one label per line and nothing else** — it is read by
wfctl rather than by a person, and it decides whether a run may notify anyone.
Point it at whatever produces that (`--jq` for `gh`, a script for a backend with
no such flag); do not point it at a command whose human-readable output happens
to contain the labels somewhere. A backend that cannot produce the list leaves
the verb out, and the repo grants through `wfctl start --allow-notify` instead.

`fields` must print **one JSON object and nothing else**, whose values are
scalars or arrays of scalars. The key names are yours — wfctl neither supplies
nor validates them, so a tracker with topics and hashtags reports topics and
hashtags. What it must not return is an object, or an array of them: comparing
two of those means knowing which key inside identifies one, and that key is your
vocabulary living inside wfctl. Flatten before you hand it over (`--jq` for
`gh`), and wfctl reports a payload that did not as a problem with this file.

`fields` and `labels` overlap and are both kept. `labels` decides whether a run
may notify anyone, which is a path worth leaving alone; a backend may declare
either, both, or neither.

`start` and `stop` are events, not values: they say *when*, and the backend
decides what that means. wfctl wires them into worktree creation and removal, so
neither takes a status to write — a board name in the caller would make every
consumer of this contract know one tracker's column vocabulary. Where the
tracker has no board at all, leave both out; the caller carries on.

A verb whose backend needs more than one call is still one argv. Point it at a
script the backend ships beside its config and pass `{id}` as an argument rather
than building a shell string — the GitHub backend's `start` does exactly that,
because setting a Projects v2 column takes a query for the item id and then a
mutation, and `gh` has no by-issue-number form of the write.

`start` and `stop` are also the two verbs whose id defaults to the issue key on
the current branch, since the worktree hooks that call them have no other issue
in mind. Nothing else defaults: `wfctl issue close` with no id would close the
wrong thing.

## Optional: `changes` (PRs / patchsets)

`wfctl change` lists/views code changes through a **parallel `changes` section**,
so PRs (GitHub) and patchsets (Gerrit) share one abstraction. Same argv-list
rules; three verbs:

| Verb     | Meaning                          | Params |
|----------|----------------------------------|--------|
| `list`   | list open changes                | (none) |
| `view`   | show one change                  | `{id}` |
| `fields` | one change's attributes, as JSON | `{id}` |

```json
"changes": {
  "list": ["gh", "pr", "list", "--state", "open", "--author", "{me}"],
  "view": ["gh", "pr", "view", "{id}"],
  "fields": ["gh", "pr", "view", "{id}", "--json", "labels,assignees,milestone",
             "--jq", "{labels:[.labels[].name],assignees:[.assignees[].login],milestone:(.milestone.title//null)}"]
}
```

`view` and `fields` answer different readers. `view` prints whatever your client
shows a person; `fields` is parsed by `wfctl change check`, which compares a
change's attributes against the issue it answers to. Declare `fields` on both
sections or on neither — a check with only one side has nothing to compare.

`check` is **not** a verb you declare. `wfctl change check` is wfctl's own, and a
config naming it is rejected.
Gerrit example — `"list": ["ssh","gerrit","gerrit","query","status:open","owner:{me}"]`.
Omit the whole section if the backend has no change concept.

## Optional: `identity` and `{me}`

To scope a `list` (issues or changes) to the current user, set a top-level
`identity` string and use `{me}` in the command. wfctl fills `{me}` from
`identity` for every verb. Each backend keys on what it needs:

```json
"identity": "@me"        // GitHub: @me · Gerrit: "self" or your email
```
`"--author", "{me}"` → `--author @me`; `"owner:{me}"` → `owner:self`. A command
that uses `{me}` with no `identity` set errors — so set it whenever any command
references `{me}`.

## Optional: `key_pattern`

wfctl derives the issue key from the branch name (`{key}-{slug}`) to label the
session and find the branch's spec folder. The default shape is `\d+` — a plain
GitHub issue number. If this tracker's keys are **not** plain numbers (e.g. Jira
`PROJ-123`, Linear `ENG-42`), add a top-level `key_pattern` — a regex, anchored
at the start of the branch, matching just the key:

```json
"key_pattern": "[A-Z]+-\\d+"
```

The slug is optional and may follow with a `-` or `_`. Omit `key_pattern` for a
numeric tracker; an invalid or missing value falls back to `\d+`.

## Steps

1. **Ask for the tracker name** (lowercase, e.g. `jira`, `linear`). The file will
   be `.agents/trackers/<name>.json`.

2. **Ask which of the verbs in the table above this backend supports** — every
   row, not the ones that look familiar. Only include verbs the backend can
   actually do; omit the rest, and `wfctl issue` skips what is unsupported.

   `start` and `stop` are the two most often skipped, because they are the two
   that describe an event rather than an operation the tracker's CLI names. Ask
   for them anyway: a backend that leaves them out gets worktree hooks that
   no-op, on a tracker that may well have had a board all along.

3. **For each supported verb, ask for the concrete command** as an argv list,
   using the `{...}` placeholders from the table above where the backend needs
   them. Example, for a Jira CLI invoked as `jiractl`:
   - `view`  → `["jiractl", "show", "{id}"]`
   - `comment` → `["jiractl", "comment", "{id}", "--message", "{body}"]`
   - (a tracker may map `{id}` onto its own key format, e.g. `PROJ-{id}`)

4. **Write** `.agents/trackers/<name>.json`:
   ```json
   {
     "verbs": {
       "view": ["jiractl", "show", "{id}"],
       "comment": ["jiractl", "comment", "{id}", "--message", "{body}"]
     }
   }
   ```

5. **Validate before finishing.** A malformed config does not crash `wfctl issue`
   — it *silently disables the tracker* (the loader treats invalid JSON as "no
   config" and every verb no-ops). So catch problems here:

   ```bash
   wfctl tracker-check <name>
   ```

   It prints `OK: <verbs>` on success, or `INVALID:` with the specific problems
   and a non-zero exit. Fix any reported issue and re-run until it passes. Do not
   silently "fix" a deliberately omitted verb — omission is how a backend declares
   it doesn't support that operation.

6. **Point the repo at it:** run `wfctl install-skills --tracker <name>` (or edit
   the `"tracker"` key in `.wf-skills-manifest.json`) so `wfctl issue` uses this
   backend. Verify with a read-only call, e.g. `wfctl issue view <some-id>`.
