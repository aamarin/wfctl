# Design: per-feature authority for outward-facing actions (#280)

Level 2 landed in `docs/architecture/a-human-grants-outward-facing-authority.md`
and is not repeated here. This file carries level 1 (behaviour) and level 3
(structure, and which of its claims were checked).

## Level 1 — the states the grant can be in

Enumerated as reachable states, each judged by whether the string it renders is
true *in that state*. Today's precedent is `auto_approve`: `cli.py:235` prints a
line when the mode is on and nothing when it is off.

Superseded 2026-09-08 by the wording pinned in
`contracts/notify-grant.md`. The class is *notifying*, not *outward-facing*, and
every state prints a line. Kept here in its judged form because the judgement is
what generated the requirements below.

```
granted, by label
  may notify people — you allowed it on issue #280
  true. Names the authority and which of the two places it came from.

granted, locally
  may notify people — you allowed it in this worktree
  true, and it has to differ from the line above — the two places can
  disagree and a reader resolving a surprise needs to know which answered.

not granted  (the default)
  was:  (nothing printed)
  now:  will not notify anyone — nobody has allowed it for this work
  the old silence was FALSE: identical to what a wfctl with no concept of
  a grant prints. Same output, opposite meanings.

denied
  will not notify anyone — you turned it off here
  true. Someone said no; that is not the same as nobody saying anything.

unreadable
  was:  (nothing printed)
  now:  will not notify anyone — couldn't reach GitHub to check
  the old silence was FALSE. Refusing is the safe direction, but the read
  happens once per run, so a failure decides the whole run and must not
  read as a person withholding authority.

granted, agent declined anyway
  may notify people, but skipped creating issues — the delivery plan has
  rows with no issue number
  true. Leads with the permission it held, which is what separates
  "I chose not to" from "nobody let me".

irreversible reached
  will never merge or delete — that is always yours, there is no setting
  true, and the last clause is load-bearing: without it the reader goes
  looking for the flag that turns it on.
```

**Decision: every state prints its own line rather than staying silent.**
The wording is pinned in `contracts/notify-grant.md`; the block above is the
judgement that produced it.

Silence is the wrong default here for a reason that does not apply to
`auto_approve`. This repo runs two wfctls on purpose — the released wheel on
PATH and `uv run` from the tree — and `AGENTS.md` is largely about telling them
apart. A grant-aware wfctl and a grant-unaware one must not print the same thing.

### Level-3 consequences generated at level 1

Stated here because a level-1 decision with no level-3 consequence means level 1
is not finished.

1. **The status payload carries the key present and false, never absent.** A
   `--json` consumer that reads a missing key as false cannot separate "this
   wfctl refused" from "this wfctl is too old to know". `build_report` already
   emits `auto_approve` unconditionally (`cli.py:229`), so the shape exists.
2. **Whatever stores the grant keeps its source, not just a boolean.** The
   granted line names where the grant came from, and a bare `true` cannot print
   it.

## Level 3 — checked and assumed

The split is the finding. Everything in the left column was opened and read this
session; everything in the right was believed and not verified.

| Checked against the code | Assumed |
|---|---|
| `grant_auto_approve` writes `{"auto_approve": granted}` through `write_json_atomic`, which is tempfile + `os.replace` — full-file replacement, so a second key on `mode.json` needs read-merge-write (`_session.py:110`, `_io.py:11`) | A Projects v2 `Status` field write leaves no entry on the issue timeline and notifies no subscriber |
| `start-session`'s `allowed-tools` carries `Bash(wfctl start*)`, a glob that admits any flag | Adding a label *does* reach the issue timeline and notify its subscribers |
| `_STEPS["decompose"]` is `("/speckit.decompose", False)` and untouched by this branch | `gh issue view` returns labels in a form a grant read can parse without a second call |
| The tracker's `label` verb is `gh issue edit {id} --{action}-label {label}`; `view` is `gh issue view {id}` (`.agents/trackers/github.json`) | The tracker is reachable at grant-read time during an unattended run |
| `.workmux.yaml` `post_create` runs `install-skills` then `issue start` — no `wfctl start`, so no worktree-creation moment where a human types a wfctl flag | |
| `wfctl issue start` calls `github-board.sh`, which resolves an item id and runs a Projects v2 field mutation (`gh project item-edit`) | |
| `arch context` projects `accepted` records only, so this feature's record does not reach the contract while `proposed` | |
| `cli.py:235` prints the auto-approve notice only when the mode is on | |

**The two notification assumptions are load-bearing and neither was verified.**
`wfctl-classes-the-action-not-the-command` places an action by *who is
notified*. That criterion is what put `post_create`'s unprompted `wfctl issue
start` outside the gated row, and what puts a label inside it — which is also
what makes the label surface self-bootstrapping, since an ungranted agent then
cannot set its own grant. Both conclusions rest on how GitHub actually notifies,
and "a board column move is quiet, a label is loud" is a belief about a third
party's product, not a fact read out of this repo.

If the label turns out to be quiet, the bootstrap property is gone and the
label is merely convenient. If the board write turns out to be loud, then every
worktree creation is already taking a gated action unprompted, and the record's
`post_create` paragraph is wrong.

**Not verified — declined 2026-09-08 as accepted risk**, after `clarify` put the
local command in every repo, which conceded the bootstrap property on its own.
Neither outcome changes who may grant or where the grant is stored, which is what
made skipping affordable. `spec.md` Assumptions carries it forward.

## Decided downstream of this file

- **Storage** — resolved in `research.md` as a second file, `notify.json`, not a
  second key on `mode.json`. This file had left it to `plan`; the argument that
  settled it is that `mode.json` documents one-writer-one-reader as the property
  it copies, and the grant stopped being a bare boolean once it gained a source.
- **The console wording** — pinned in `contracts/notify-grant.md`, including the
  decline and irreversible lines this file never rendered.
- **Two surfaces, not one** — `clarify` put the local command in every repo, not
  only those without a tracker. That is what turned the checked/assumed split
  above from blocking into carried risk.

The `Assumed` column above is unchanged and still true as a record of what was
believed on 2026-09-07. Nothing in it was later verified.
