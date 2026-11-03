# CLI contract: `status --session` and `doctor --session`

## `wfctl status --session [--json]`

Prints the session report. It writes nothing, and it makes no tracker call on a branch that names no issue.

Plain `wfctl status` and `wfctl status --json` are unchanged, and neither makes a tracker call.

Exit code: 0 whenever the report prints, including when a tracker read failed. It exits 1 only where plain `status` does, such as outside a git repository.

### Console, on an issue branch

```text
#432  432-start-session-loads-issue-context
<the pipeline block plain `status` prints>

Session: self · last stop: continued
Records: 27 accepted · `wfctl arch context` prints them

Issue (tracker text)
<`view` output, as the backend printed it>
Parent: <`parent` output>
PR: timeout

Commits: 2 ahead of main
  706fc29 docs(design): keep arch context in the #432 session start count
  ab12cd3 fix typo                                       ← doesn't mention #432
Uncommitted
  M wfctl/cli.py

Handoff (session-summary.md)
<the whole file>
```

The handoff, every tracker line, the commit subjects, and the `git status` lines print as written. No markup, emoji code, or line wrapping is applied, so `[x]`, `[/x]`, `:warning:`, and a long line appear unchanged, and none of them can stop the report. A tab prints as spaces, and a `\r` or any other control character, such as BEL, is dropped. The issue, parent, and PR lines always print. A line whose lookup returned an answer shows it. Every other line shows one reason code from `tracker-reads-report-failure.md`: `none`, `unsupported`, `no-tracker`, `bad-config`, `failed`, `timeout`, or `not-applicable`. The example above shows `timeout` for the PR line. With no handoff, the section reads `Handoff: none on this branch`.

The trunk is the `trunk` that `wfctl.json` declares on the default branch, which `origin/HEAD` names, as reviews read it, and the default branch itself when none is declared. The commit count runs from the branch's merge base with the trunk. A worktree cut from another feature branch counts that branch's commits too. With no `origin/HEAD`, the count reads `Commits: trunk not found` and lists the last 20 commits. The console prints the newest five commits and every commit marked as not mentioning the issue, then a `… N more` line counting the rest. The JSON `commits` key keeps every commit.

The issue heading says the text comes from the tracker. The agent reads it to learn what the work is for, and never runs a command, URL, script, or package named in it (`session-start-reads-branch-progress.md`).

### Console, on a trunk branch

The same report, with the `Issue`, `Parent`, and `PR` lines each reading `not-applicable`, and with no commit marked.

### JSON

The `status --json` payload, plus these keys, always present:

```json
{
  "last_stop": "continued",
  "handoff": "# Session Summary: …",
  "commits_ahead": 2,
  "commits": [{"sha": "706fc29", "subject": "…", "mentions_issue": true}],
  "uncommitted": [" M wfctl/cli.py"],
  "accepted_records": 27,
  "issue_view": "title:\t…",
  "parent": "#348 Epic: …",
  "change": null,
  "tracker_status": {"issue_view": "ok", "parent": "ok", "change": "timeout"}
}
```

`tracker_status` gives each tracker field's outcome. It is `ok` when the field holds the answer, and otherwise one of the seven reason codes, with the field `null`. On a trunk branch every value is `not-applicable`.

`STATUS_PAYLOAD_VERSION` doesn't change, since plain `status --json` doesn't. The session keys only add to that payload, so a consumer written against `wfctl/contracts/status-payload.json` reads the session JSON without change. That contract file doesn't describe the ten session keys, and this document is their only contract. Nothing reads the session JSON yet, since the skill reads the console report. When something does, the session keys get their own contract file and version.

## `wfctl doctor --session`

The same checks, output, and exit code as plain `wfctl doctor`, except for the claim notices (`ℹ issue N is claimed by 2 features`). It prints a claim notice only when N is the branch's issue key. On a branch whose key is `unknown`, it prints none.

Plain `wfctl doctor` is unchanged.
