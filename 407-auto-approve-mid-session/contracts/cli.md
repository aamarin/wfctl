# CLI contract: `wfctl auto-approve`

## Synopsis

```
wfctl auto-approve [on|off]
```

Any other argument is a usage error (exit 2, from typer).

## `wfctl auto-approve on`

Checks run in this order, and a refusal writes nothing:

1. The issue check `start` runs. When it refuses, its lines print verbatim with
   their fix command, and the exit code is 1.
2. The holder check. When `session_holder` is `"other"`, it prints the
   following and exits 1. That value covers both another conversation holding
   the branch and this conversation having run `wfctl end`, so the message is
   worded to be true for both (research.md §1):

   ```
   ✗ No session is open for this conversation on this branch, so it can't turn auto-approve on.
     Run /start-session first.
   ```

Then wfctl appends a `mode` event with `session` when the caller has an
identity, writes `{"auto_approve": true}` to `mode.json`, prints the following,
and exits 0:

```
✓ auto-approve — design gates answered into the record, review stops run through, approval moves to the PR
```

If the mode is already on and the newest `mode` event is a grant, both checks
still run, and then wfctl writes no file and appends no event. It prints the
same notice and exits 0. This keeps a repeated `on` from restarting the review
count (research.md §3a).

"Newest" counts every `mode` event, the review cap's revocation included. If
`mode.json` reads on and the newest event isn't a grant, as after a hand edit,
`on` writes as usual. A revoked mode reads as off, so `on` after a revocation
writes as above.

If a write fails, `on` and `off` both print the following and exit 1. wfctl
appends the event before it writes `mode.json`, so a failed append changes
nothing (research.md §3a):

```
✗ Couldn't record the auto-approve change: <error>
```

## `wfctl auto-approve off`

No check runs, so `off` works on a branch that names no issue too. wfctl
appends a `mode` event with `session` when the caller has an identity, writes
`{"auto_approve": false}`, prints the following, and exits 0:

```
✓ auto-approve off — design gates and review stops wait for a human
```

## `wfctl auto-approve`

Reads only, and always exits 0. It looks up the state dir without creating
it, and skips the cleanup of old files that the other commands run. As a
result, a branch wfctl has never used gets no state dir from it. On a branch
that names no issue, it reads that branch's state dir the same way, which
usually prints `auto-approve off` and `no grant on record`.

The first line is the mode:

```
auto-approve on — design gates answered into the record, review stops run through, approval moves to the PR
auto-approve off
auto-approve off — <revocation reason>
```

The revoked line matches what `_revocation_line` prints for `status` and
`resume`. The reason is wfctl's own sentence, such as "wfctl turned it off
after 3 plan reviews or sign-offs since it was granted".

The second line is the last mode change a person made, when one is on record
and it matches `mode.json`. That is the last `mode` event with no `by` field,
whether it turned the mode on or off. After the review cap revokes the mode,
the line shows that change too, which is the grant the cap ended, so the
reader sees who turned the mode on. `<relation>` is
`this session`, `another session`, or `an unknown session` (research.md §4):

```
  turned on 2026-11-19 14:02 UTC by <relation>
  turned off 2026-11-19 15:40 UTC by <relation>
```

In every other case the line keeps the wording spec User Story 4 shows:

```
  no grant on record
```

That covers two states:

1. No mode change is on record.
2. The mode reads on and the newest `mode` event isn't a grant, as after a
   hand edit, including one made after the review cap's revocation.

If the mode reads off, wasn't revoked, and the last mode change turned it on,
the file and the log disagree. That happens after a hand edit, or after a file
write that failed once `on` had appended its event (research.md §3a). The line
says so, and the next `on` or `off` brings the two back in line:

```
  turned off outside wfctl
```

The earlier change isn't shown in any of these states, since it doesn't
explain the mode the file holds now.

When `.workmux.yaml` exists and its `post_create` has no live grant line, a note
follows:

```
  ℹ .workmux.yaml has no auto-approve line, so `WFCTL_AUTO_APPROVE=1 workmux add` won't start a worktree unattended.
    Add this entry to post_create:
      - cd "$WM_WORKTREE_PATH" && [ "$WFCTL_AUTO_APPROVE" = 1 ] && wfctl auto-approve on || true
```

The entry line is printed with `soft_wrap`, so it pastes into YAML unbroken.
Nothing in the output prints a session ID.

## `wfctl start --auto-approve` / `--no-auto-approve` (changed)

Unchanged output and placement. The grant now goes through the shared helper,
so its `mode` event carries `session` the same way, and `--auto-approve` on a
mode that is already on writes nothing. `start` doesn't run the
holder check, since it takes the branch over.

## `.claude/settings.json` `permissions.ask` (added rules)

`install-skills --agent claude` adds these two rules, and records each in the
manifest with the kind `ask`:

```json
"permissions": { "ask": ["Bash(wfctl auto-approve on:*)", "Bash(uv run wfctl auto-approve on:*)"] }
```

Claude Code prompts the person before the agent runs either command.
`uninstall-skills` removes them, and `doctor` and `install-skills` treat a
deleted one the way they treat a deleted `Bash(cd:*)` today.

Each managed rule carries its own explanation. As a result, the lines that
print today for the deny rule don't mention `cd` when the rule is an ask rule:

```
⚠ claude: Bash(wfctl auto-approve on:*) is gone from .claude/settings.json
  without it, the agent can turn auto-approve on without Claude Code asking you
```

The install refusal lists related rules under the list they sit in, as `it now
denies:` or `it now asks for:`. The install announcement names only the rules
this run added, each with its explanation. An existing install that gains the
two ask rules at upgrade prints the following, and doesn't announce
`Bash(cd:*)` again:

```
  It also now asks before Bash(wfctl auto-approve on:*) and Bash(uv run wfctl auto-approve on:*)
  — the agent can't turn auto-approve on without you saying yes.
```

## `.workmux.yaml` `post_create` (added entry)

Last in the list, after `wfctl issue start`:

```yaml
  - cd "$WM_WORKTREE_PATH" && [ "$WFCTL_AUTO_APPROVE" = 1 ] && wfctl auto-approve on || true
```

This repository's copy runs `uv run wfctl` instead.
