# Data model: Session start loads only the branch's own context

Nothing here is stored. Each value is computed on every call to `wfctl status --session`.

## SessionReport

What `status --session` prints. It extends the payload plain `status --json` builds, and every field of that payload stays the same.

| Field | Type | Source | Empty case |
| --- | --- | --- | --- |
| everything in `status --json` | — | `build_report` | unchanged |
| `last_stop` | `"none"`, `"continued"`, `"wrapped"` | `events.jsonl`, the most recent `end` event | `"none"` |
| `handoff` | string | `session-summary.md`, word for word | `null` when the file doesn't exist |
| `commits_ahead` | integer or `null` | git, the count of commits from the merge base with the trunk to `HEAD` | `null` when the trunk can't be found |
| `commits` | list of `Commit` | git, merge base with the trunk to `HEAD` | empty list; the last 20 commits, each with `mentions_issue` `null`, when the trunk can't be found |
| `uncommitted` | list of strings | `git status --short`, one line each | empty list |
| `accepted_records` | integer | the arch root, records whose status is `accepted` | `0` |
| `issue_view` | string | the tracker's `view` verb | `null` on a trunk branch, or when the verb is missing or fails |
| `parent` | string | the tracker's `parent` verb | `null` when there is no parent, or the verb is missing or fails |
| `change` | string | the tracker's `branch` verb | `null` when there is no open PR, or the verb is missing or fails |
| `tracker_status` | object keyed `issue_view`, `parent`, `change` | `read_text()`'s reason code for each read | every value `not-applicable` |

Each `tracker_status` value is `ok` when its field holds the answer, or one of `none`, `unsupported`, `no-tracker`, `bad-config`, `failed`, `timeout`, `not-applicable`, with the field `null`. The console report prints the code in place of the answer, so no tracker line is ever left out (`tracker-reads-report-failure.md`). On a branch whose `issue` is `unknown`, the three tracker fields are always `null`, every status is `not-applicable`, and no tracker call is made.

## Commit

| Field | Type | Meaning |
| --- | --- | --- |
| `sha` | string | Short hash |
| `subject` | string | First line of the message |
| `mentions_issue` | boolean or `null` | Whether the subject or body names the branch's issue key. `null` on a trunk branch, or when the trunk can't be found. |

## ClaimNotice filter

Not a new type. `doctor --session` passes the branch's issue key to `_report_double_claimed_keys`, which prints a notice only when the notice's `key` equals it. With `issue` `unknown`, it prints none.
