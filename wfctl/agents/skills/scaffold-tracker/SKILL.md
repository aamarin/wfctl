---
name: scaffold-tracker
description: Author a new issue-tracker backend for `wfctl issue` by generating a `.agents/trackers/<name>.json` verb→command map. Use when a repo uses a tracker other than GitHub (e.g. a private Jira CLI) and needs the session skills to reconcile against it.
---

# Scaffold an issue-tracker backend

`wfctl issue <verb>` delegates issue operations to a per-repo backend defined by
`.agents/trackers/<name>.json`. GitHub ships as `github.json`. This skill authors
a config for any other tracker (a private Jira CLI, Linear, a custom script) so
the session skills work unchanged.

## The verb contract

The session skills speak six standard verbs. A backend implements the subset it
supports — the presence of a verb key is its declaration, so a backend cannot lie
about what it can do.

| Verb      | Meaning                     | Params available for `{...}` substitution |
|-----------|-----------------------------|-------------------------------------------|
| `list`    | list open issues            | (none)                                    |
| `view`    | show one issue              | `{id}`                                     |
| `close`   | close an issue with comment | `{id}`, `{comment}`                        |
| `comment` | comment on an issue         | `{id}`, `{body}`                           |
| `create`  | open a new issue            | `{title}`, `{body}`                        |
| `label`   | add/remove a label          | `{id}`, `{action}` (add\|remove), `{label}`|

Each verb maps to an **argv list** (never a shell string). `{name}` placeholders
are substituted per-token from the CLI options, so free text like a comment body
is always one inert argument — no shell injection, no quoting to get right.
Substitution is within-token, so `"--{action}-label"` becomes `--add-label`.

## Optional: `changes` (PRs / patchsets)

`wfctl change` lists/views code changes through a **parallel `changes` section**,
so PRs (GitHub) and patchsets (Gerrit) share one abstraction. Same argv-list
rules; two verbs:

| Verb   | Meaning              | Params |
|--------|----------------------|--------|
| `list` | list open changes    | (none) |
| `view` | show one change      | `{id}` |

```json
"changes": {
  "list": ["gh", "pr", "list", "--state", "open", "--author", "{me}"],
  "view": ["gh", "pr", "view", "{id}"]
}
```
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

2. **Ask which of the six verbs this backend supports.** Only include verbs the
   backend can actually do — omit the rest; `wfctl issue` skips unsupported verbs.

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
