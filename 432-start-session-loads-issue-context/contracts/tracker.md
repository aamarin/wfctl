# Tracker contract: the `parent` and `branch` verbs

Both verbs are optional. A backend that leaves one out passes `wfctl tracker-check`, and the session report prints that line as `unsupported`.

| Section | Verb | Placeholders | Prints on success | Prints when there is nothing |
| --- | --- | --- | --- | --- |
| `verbs` | `parent` | `{id}` | One line naming the parent issue, such as `#348 Epic: wfctl's own docs drift` | Nothing, exit 0 |
| `changes` | `branch` | `{branch}` | One line naming the branch's open change, its check state, and its count of unresolved review threads | Nothing, exit 0 |

An unresolved review thread is one that isn't resolved, whether or not it has a reply.

`branch` prints at most one change. A change counts only when it comes from this repository, not from a fork whose branch has the same name. When more than one counts, the backend prints the most recently updated one.

wfctl prints the line as the backend wrote it and never parses it. wfctl assigns a reason code to every line that has no answer, and the backend never prints one. An exit of 0 with no output is `none`. A non-zero exit is `failed`, and no answer within 15 seconds is `timeout`, both with no error text. Before the backend runs, wfctl assigns `no-tracker` when the manifest names no tracker, `bad-config` when the config can't be read or the verb's entry is malformed or needs a missing value, and `unsupported` when the config has no such verb.

`_read_verb` collapses some of these today: `(None, None)` covers no tracker, an unreadable config, and a missing verb, and `(None, detail)` covers a malformed entry, a timeout, and a non-zero exit. The new `read_text()` returns the answer and its reason code instead, and `_read_verb` keeps its current shape for `fields` and `state`, which already rely on it.

## GitHub

```json
"verbs":   { "parent": ["bash", ".agents/trackers/github-issue-parent.sh", "{id}"] },
"changes": { "branch": ["bash", ".agents/trackers/github-change-branch.sh", "{branch}"] }
```

`install-skills --tracker github` installs both scripts beside the existing ones.
