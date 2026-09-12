# Contract: reading and writing the notify grant

Module boundary is `wfctl/_session.py`, which already owns `mode.json`. The
underscore prefix is the module contract (`the-underscore-is-the-module-contract`):
these are internal to wfctl, and `cli.py` is the only caller.

## Read

```python
def notify_grant(
    agent_dir: Path, repo_root: Path, branch: str, issue: str | None
) -> NotifyGrant: ...
```

**Amended during `implement`.** The two-argument sketch above it could not ask
FR-008's question — *is this the trunk* needs the repo and the branch — and could
not reach the tracker, whose config is per-repo and would otherwise have to be
found by a name this module hardcoded. Both callers already hold all four:
`_resolve_context` computes them together.

Returns the resolved pair. Never raises — every failure shape resolves to a
refused verdict, matching `auto_approve`'s posture and for its stated reason: a
raise here breaks `status`, `start`, `resume` and `end` for that branch at once.

```python
class NotifyGrant(NamedTuple):
    granted: bool          # the verdict every caller gates on
    source: str            # "label" | "local" | "deny" | "unset" | "unreadable"
                           #   | "corrupt" | "trunk" | "unknown-trunk"
    detail: str | None     # why, when source is "unreadable" or "corrupt"
```

**Two sources were added during `implement`, each forced by a requirement this
list did not cover.** `trunk` is FR-008: a grant is refused on the trunk branch
regardless of what any file or label says, and folding that into `unset` would
send a reader hunting for the flag that turns it on — the confusion the last
console line below exists to prevent. `corrupt` is the spec's *grant is
unreadable* edge case, which says the refusal must not print the ordinary line;
sharing `unreadable` with it would mean printing *couldn't reach GitHub* over a
damaged local file, naming a cause that is not the cause.

A third source, `unknown-trunk`, was added after a review panel: a repo whose
trunk cannot be named was filed as `unreadable`, which prints *couldn't reach the
issue tracker* — in a repo that may have no tracker configured at all. Exactly
the false cause the `corrupt` split above was made to avoid, in the one case the
argument had not been applied to.

`granted` is `False` for `unset`, `deny`, `unreadable`, `corrupt`, `trunk` and
`unknown-trunk` alike. `source` is
what separates them, and every rendering that shows a refusal shows the source
with it — the refusals are not one event, and FR-015 turns on saying so.

**`detail` splits by destination.** The console line carries a fixed string —
`couldn't reach GitHub to check` — and never the underlying error. The event log
carries the tracker's full stderr. The reason is that the two are read at
different moments for different purposes: `status` is glanced at and must stay
one line, while the log is opened by someone already debugging, who needs to
know whether it was auth, network, or a missing `gh` scope. A status line
carrying an unbounded stderr wraps and stops being scannable; a log carrying a
fixed string is a log that cannot answer the only question it is opened for.

`issue` is `None` where the branch carries no issue key. The label read is
skipped and resolution falls to the local file alone, as it also does where no
tracker is configured at all (FR-012) — `read_issue_labels` answers "nothing was
asked" there, which is not the same as "the answer did not arrive".

**The label comes from a declared `labels` verb, not from parsing another
command's output.** `read_issue_labels` in `wfctl/_tracker.py` runs the backend's
own `labels` command and reads one label per line, compared whole.

This replaces the first implementation, which ran `view` and looked for the
`labels:` header `gh` prints. Two things were wrong with it, and the second is
the reason this is a verb. Reading the whole output would have let an issue
*about* a label grant that label — #280's body names `authority:notify` several
times. And the header itself is GitHub's: every other backend would have read as
having no labels, with no error and no warning, so the tag surface would simply
never have worked on Jira or Gerrit and nothing would have said why.

Declaring it puts the read where every other tracker operation already lives.
A backend that cannot list labels omits the verb, which is how omission already
works everywhere else in this contract — that repo grants through `wfctl start
--allow-notify`, which needs no tracker (FR-012). Omission is *nothing was
asked*, which is not *the answer did not arrive*: only the second is an
unreadable grant.

## When the answer is read

```python
def resolved_notify(agent_dir: Path) -> NotifyGrant: ...
def action_grant(agent_dir: Path, repo_root: Path) -> NotifyGrant: ...
```

**This is the largest divergence from the original design, and it went
unrecorded until a review panel named it.** `notify_grant` above is called by
`wfctl start` and by nothing else. It records what it resolved as a
`notify-resolved` event, and every later command reads that back rather than
resolving again.

The reason is a number: `gh issue view` costs about 1.4 seconds, `wfctl status`
runs dozens of times in a session, and resolving per command would have spent
most of a minute per session re-reading a label that does not change while a
session runs. `plan.md` states the budget as one tracker round-trip per run, and
the obvious wiring broke it.

**It needs writing down as a deliberate exception to
`session-state-is-re-derived`, not argued past.** That record says nothing is
carried forward from an earlier write, and the defence that the log is an
artifact rather than a cache is too convenient: the value *can* be recomputed
from `notify.json` plus the label, so re-derivation can reach it. What it cannot
reach is the budget. The exception is FR-014's own words — read once when the run
begins, and that answer holds — and the cost is a label added mid-run being seen
at the next `wfctl start` rather than the next command.

`action_grant` is the read every *write* path uses, and it is not the same read.
It re-asks the branch before consulting the record, because the record cannot
answer FR-008: the state dir is per-branch only while `WFCTL_STATE_DIR` is unset,
and under a shared one a grant made on a feature branch reached the trunk. That
was reproduced, not theorised — the comment sitting beside the resolve-time check
claimed it "survives the state dir changing shape", and it did not.

`status` asks the same question directly for the same reason, and because the
recorded answer does not exist at all on a fresh trunk: it rendered as *nobody
has allowed it for this work*, sending the reader after a flag that would not
have helped. `on_trunk` is a local git call, so the round-trip argument that
keeps the label read out of `status` does not reach it.

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

```python
def record_notify_unread(agent_dir: Path, detail: str) -> None: ...
def record_notify_declined(agent_dir: Path, action: str, reason: str) -> None: ...
def record_notify_refused(agent_dir: Path, action: str, source: str) -> None: ...
```

`notify-unread` is the other half of the `detail` split above: the console line
for a failed read is fixed, so this is the only place the cause survives.

The last two are FR-011, and they are two functions rather than one flag because
they are written from different places — the refusal by the dispatcher, at the
moment it declines to build argv; the decline by whatever held the authority and
chose not to use it. Both leave the same empty tracker, and only one of them says
the grant should be wider.

**`wfctl notify <action>` is the surface for actions wfctl does not perform.**
`wfctl issue` records its own writes, and a push is in the same class with no
wfctl verb behind it — without this command FR-010 covers only the actions that
happen to go through the tracker dispatcher. `--declined --reason` writes the
other event. Recording an action on an ungranted run is refused: the log is the
report, so a line there claiming people were told is a false report.

## Console

`wfctl status` prints one line in every state, never silence:

```
may notify people — you allowed it on issue #280
may notify people — you allowed it in this worktree
may notify people, but skipped creating issues — the delivery plan has rows
  with no issue number
will not notify anyone — nobody has allowed it for this work
will not notify anyone — you turned it off here
will not notify anyone — couldn't reach the issue tracker to check
will not notify anyone — couldn't read the setting for this work
will not notify anyone — only feature branches can be granted this
will never merge or delete — that is always yours, there is no setting for it
```

The last two refusals were added with their sources, above. Both follow the
property the rest were written against: every refusal names which kind it is.

**Two of the lines above were rewritten during `implement`, both because the
first draft broke a property this section states about itself.**

*Couldn't reach GitHub* named one backend in a tool that talks to whichever the
repo configured, so it printed a false cause on every other — the same mistake
the label read made before it became a declared verb.

The trunk line first read *"this is the trunk branch, and authority is granted
per feature branch"*, which is 93 characters and wrapped at 80. Half a sentence
on its own line is not a line a reader can glance at, so the wording that
survived is the one that fits. A test now pins every line at 72 characters,
because the wrapping was invisible until an assertion went looking for the whole
string.

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

  **One caller was added during `implement` and is worth naming here, because it
  is where the rule stopped being advisory.** `_tracker.dispatch` refuses
  `comment`, `create` and `label` when the run resolved to refused, before it
  builds argv. Until then the refusal existed only as prose in two skills, so it
  held exactly as long as every agent read them — and `a-rule-is-expressed-as-a-check`
  says a rule ships as a check when a violation is visible in an artifact the
  work produces, which this one is: the tracker changed.

  It reads the answer `start` recorded and asks the tracker nothing, so it costs
  no round-trip. It returns 1 rather than the 0 a missing backend returns: that 0
  means *nothing was configured to do this*, and a caller reading a refusal as a
  completed write would report the tracker updated when nobody was told anything.

  `close` is deliberately outside the gated set. It is the irreversible row, no
  grant reaches it, and consulting a grant there would refuse the only actor
  allowed to do it — wfctl cannot tell a human from an agent
  (`approval-mode-is-stored-intent`). What keeps that row safe is that nothing
  ever grants it.
- Anything touching the irreversible class (FR-013). No grant reaches it, so no
  contract here mentions it.

  **How that is enforced turned out to matter, and `implement` settled it the
  other way from how T024 reads.** "Refused regardless of the grant" would mean
  `wfctl issue close` refusing every caller, including the human who is the only
  actor allowed to close anything — and wfctl cannot tell a human from an agent
  (`approval-mode-is-stored-intent`), so the refusal would land on the wrong one.

  What keeps the row safe instead is that nothing ever consults a grant for it:
  `close` is outside the gated verb set, and the status line says *there is no
  setting for it* in every state, granted included. The test asserts from the
  granted side that no value of the setting changes either — which is the
  property FR-013 actually states, rather than a refusal that would have to be
  bypassed on the first real use.
