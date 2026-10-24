# Config contract: the `review` key in `wfctl.json`

`review` is optional. A repository without it gets three Claude reviewers in
the security group and three in the code group.

```json
{
  "review": {
    "commands": { "codex": "codex exec --sandbox read-only" },
    "groups": [
      { "group": "security",
        "reviewers": [ { "name": "claude", "count": 2 }, { "name": "codex", "count": 2 } ] },
      { "group": "money-rules", "skill": "money-rules-review",
        "reviewers": [ { "name": "claude", "count": 2 } ] }
    ]
  }
}
```

A built-in group gets its default of three Claude reviewers only when the
`reviewers` key is missing, whether the group is left out of the list or
listed without the key. An empty `reviewers` list is a finding, not a way to
run a group with no reviewers.

With this file the run order is `security` (s1 - s4), `code` (c1 - c3, the
default), then `money-rules` (m1, m2).

## `wfctl check config` findings

Each is one `- ` line under `✗ wfctl.json:`, and the command exits 1.

| Problem | Finding |
| --- | --- |
| `review` isn't an object | `review must be an object` |
| `groups` isn't a list | `review.groups must be a list` |
| a group entry has no `group` string | `review.groups[2] has no group name` |
| a group name isn't lowercase letters, digits, and hyphens starting with a letter | `review group '../x': a name is lowercase letters, digits and hyphens, starting with a letter` |
| a custom group has no `reviewers` key, or any group, built-in or custom, lists `reviewers` as an empty list | `review group 'money-rules' has no reviewers` |
| two groups share a first letter | `review groups 'security' and 'storage' both start with 's'; reviewer ids would clash` |
| a reviewer's model has no command | `review group 'security': model 'codex' has no entry in review.commands` |
| a count below 1, or not an integer | `review group 'security': count for 'claude' must be 1 or more` |
| `commands` isn't an object of strings | `review.commands must map each model to a command string` |

`check config` doesn't check that a command is installed, because that is a
fact about the machine running the review, not about the repository. `review
start` checks it and warns (`research.md` R7).
