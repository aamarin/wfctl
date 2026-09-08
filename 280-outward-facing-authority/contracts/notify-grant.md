# Contract: reading and writing the notify grant

Module boundary is `wfctl/_session.py`, which already owns `mode.json`. The
underscore prefix is the module contract (`the-underscore-is-the-module-contract`):
these are internal to wfctl, and `cli.py` is the only caller.

## Read

```python
def notify_grant(agent_dir: Path, issue: str | None) -> NotifyGrant: ...
```

Returns the resolved pair. Never raises — every failure shape resolves to a
refused verdict, matching `auto_approve`'s posture and for its stated reason: a
raise here breaks `status`, `start`, `resume` and `end` for that branch at once.

```python
class NotifyGrant(NamedTuple):
    granted: bool          # the verdict every caller gates on
    source: str            # "label" | "local" | "deny" | "unset" | "unreadable"
    detail: str | None     # why, when source is "unreadable"
```

`granted` is `False` for `unset`, `deny` and `unreadable` alike. `source` is
what separates them, and every rendering that shows a refusal shows the source
with it — the three refusals are not the same event and FR-015 turns on saying so.

**`detail` splits by destination.** The console line carries a fixed string —
`couldn't reach GitHub to check` — and never the underlying error. The event log
carries the tracker's full stderr. The reason is that the two are read at
different moments for different purposes: `status` is glanced at and must stay
one line, while the log is opened by someone already debugging, who needs to
know whether it was auth, network, or a missing `gh` scope. A status line
carrying an unbounded stderr wraps and stops being scannable; a log carrying a
fixed string is a log that cannot answer the only question it is opened for.

`issue` is `None` where no tracker is configured (FR-012). The label read is
skipped and resolution falls to the local file alone.

## Write

```python
def grant_notify(agent_dir: Path, state: str) -> None: ...
```

`state` is `"granted"` or `"denied"`. There is no call that writes *unset* —
returning to unset is deleting the file, and no code path does that today.

Two writes, two questions, copied deliberately from `grant_auto_approve`:
`notify.json` answers *what is the state now*, the `notify-grant` event answers
*when was it set*. The file is overwritten and cannot hold the second.

## Report

```python
def record_notify_action(agent_dir: Path, action: str, count: int = 1) -> None: ...
```

Appends `notify-action`. Called by whatever took the action, after it succeeded.
FR-010's required destination; the summary and PR body are renderings and are
not this contract's business.

## Console

`wfctl status` prints one line in every state, never silence:

```
may notify people — you allowed it on issue #280
may notify people — you allowed it in this worktree
may notify people, but skipped creating issues — the delivery plan has rows
  with no issue number
will not notify anyone — nobody has allowed it for this work
will not notify anyone — you turned it off here
will not notify anyone — couldn't reach GitHub to check
will never merge or delete — that is always yours, there is no setting for it
```

**These are the wording, not a paraphrase of it.** They are pinned here so the
implementation does not invent them and a test does not then protect whatever
was invented. Three properties they were written against:

- **Plain, not terse.** `notify — refused; denied locally` is shorter and needs
  the reader to already hold the vocabulary. These read to someone who has never
  seen the feature.
- **Every refusal names which kind.** *Nobody allowed it*, *you turned it off*,
  and *couldn't reach GitHub* resolve identically and are different events —
  FR-015 exists because a failed read decides a whole run and must not be filed
  as a person withholding authority.
- **The decline line leads with the permission it had.** *"may notify people,
  but skipped"* is what separates the agent choosing not to act from the agent
  not being allowed to (FR-011). Without that clause the two are
  indistinguishable, which is the failure the requirement is about.

**No count in the decline line.** An earlier draft read *"declined 6 issue
writes"*. The number contradicts the reason: the agent declined because it could
not read the plan confidently, so claiming it knew there were exactly six asserts
a precision the decline itself denies.

**The last line answers the question it provokes.** *"there is no setting for
it"* exists because a reader hitting that line will otherwise go hunting for the
flag that turns it on (FR-013).

The refused lines are the point of FR-003. `auto_approve` prints nothing when
off, and copying that here would make a grant-aware wfctl indistinguishable from
one too old to know — which is the exact confusion this repo already lives with
between its two installed wfctls.

## JSON

`build_report` carries the key **present and false**, never absent (FR-004):

```json
{ "notify": false, "notify_source": "unset" }
```

A consumer reading a missing key as false cannot tell a refusal from an old
wfctl. Both fields are always present.

## Not in this contract

- Deciding whether an action *is* notifying. That is the classification, and it
  lives in `wfctl-classes-the-action-not-the-command` on `main`.
- Refusing the action. The caller gates on `granted`; this boundary answers the
  question and takes no action of its own.
- Anything touching the irreversible class (FR-013). No grant reaches it, so no
  contract here mentions it.
