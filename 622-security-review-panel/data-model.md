# Data model: review records

Everything lives in the branch's state directory, under `reviews/`. The
directory is outside every worktree and outside the spec directory, so
`wfctl store specs` never commits it, and removing a worktree keeps it. A
`reviews/` folder an earlier panel left in a spec directory is not read or
moved. Whether to remove those is the same decision as the 376 reports already
on `specs-trunk` (spec, Assumptions).

```text
<state dir>/                          # _paths.resolve_agent_dir(repo, branch)
├── verify.json                       # existing
├── events.jsonl                      # existing; four new event names
└── reviews/
    ├── sign-off.json                 # the latest sign-off on this branch
    └── <group>/                      # one per review group, such as security
        ├── last-reviewed.json        # this group's last reviewed commit
        └── runs/
            └── <NNN>/                # 001, 002, … in start order
                ├── run.json          # the run record
                └── <id>.md           # one report per reviewer, such as s1.md
```

## Review group (from `wfctl.json`)

| Field | Type | Rule |
| --- | --- | --- |
| `group` | string | Required. Lowercase letters, digits, and hyphens, starting with a letter (`^[a-z][a-z0-9-]*$`), so it is always safe as a directory name under `reviews/`. Its first letter is the reviewer id prefix, and no two groups share one. |
| `skill` | string | Optional. Defaults to `reviewing-security` for `security` and to `code-review` for every other group. |
| `reviewers` | list | Required for a custom group. Optional for a built-in group, which gets the default when the key is missing. When present on any group, at least one entry long. Each entry is `{name, count}`. `count` is an integer of 1 or more. A `name` other than `claude` needs an entry in `commands`. |

Run order is `security`, then `code`, then every other group in list order. A
built-in group the list doesn't name, or names without a `reviewers` key, gets
`[{name: claude, count: 3}]`.

## Run record: `run.json`

```json
{
  "group": "security",
  "run": 3,
  "base": "a1b2c3d…",
  "head": "9f8e7d6…",
  "commits": ["9f8e7d6…", "5c4b3a2…"],
  "reviewers": [
    {"id": "s1", "model": "claude", "state": "expected"},
    {"id": "s3", "model": "codex", "state": "expected", "command": "codex exec --sandbox read-only"},
    {"id": "s4", "model": "codex", "state": "expected", "command": "codex exec --sandbox read-only"}
  ],
  "started_at": "2026-10-23T14:02:11Z",
  "completed_at": null
}
```

- Written once by `review start`. `review check` sets `completed_at` and
  changes nothing else.
- Reviewer ids are numbered across the group's whole reviewer list in order,
  so `s1`, `s2` are Claude and `s3`, `s4` are Codex in the example.
- When a model's command isn't on `PATH`, each of its reviewers is written
  with `"state": "unavailable"` and a `reason`, such as
  ``"`codex` not found on PATH"``. `check` doesn't expect a report from them.
  When every reviewer in the run is unavailable, `check` never completes the
  run (R7).
- `commits` is the list R3 in `research.md` defines, newest first. A run is
  never started with an empty list. `start` prints that the group is up to
  date and writes nothing.

## Report: `<id>.md`

Free Markdown with two required lines (R2): `Reviewed: <sha>` naming `head`,
and a verdict at the end. A relayed report starts with a header wfctl writes:

```text
Relayed: write denied
Relayed-at: 2026-10-23T14:09:40Z

<the reviewer's reply, verbatim>
```

A report counts when it names `head` and ends with a verdict. A relayed report
counts the same way, and the roster shows the relay reason.

## Last reviewed commit: `last-reviewed.json`

```json
{"sha": "9f8e7d6…", "run": 3, "at": "2026-10-23T14:12:03Z"}
```

Written only when a run completes, set to that run's `head`. A missing file
means the group has never completed a run on this branch, so its base is the
merge base with the trunk branch.

## Sign-off: `sign-off.json`

```json
{"sha": "9f8e7d6…", "at": "2026-10-23T15:30:00Z"}
```

Overwritten by each sign-off. It covers a commit when that commit is the
signed-off commit or one of its ancestors. Only `wfctl review sign-off` writes
it, at an interactive terminal (R9).

## State a run moves through

```text
start ──► incomplete ──(at least one expected reviewer, and each has a counted report)──► complete
             │                                                             │
             └── stays incomplete; a new `start` opens the next run        └─► last-reviewed.json = head
```

A run that never completes is left in place. The next `start` opens run N+1
from the same base, so the earlier run's reports stay on disk for reading but
never count toward the new run.

## Events (in `events.jsonl`)

| Event | Fields |
| --- | --- |
| `review-start` | `group`, `run`, `head`, `reviewers` (count expected) |
| `review-complete` | `group`, `run`, `head` |
| `review-relay` | `group`, `run`, `id`, `reason` |
| `review-sign-off` | `sha` |

## Derived on every read, never stored

- A group's unreviewed commits: R3's range from `last-reviewed.json` (or the
  merge base) to the judged head, and none when the judged head is the last
  reviewed commit or one of its ancestors.
- Whether the sign-off covers them: an ancestor test against `sign-off.json`.
- The roster: each expected reviewer's report, read and judged when `check`
  runs.
