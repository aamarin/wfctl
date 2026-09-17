# Remove the outward-action grant (#384)

## Problem Statement

How might we let a run file issues, push and comment without wfctl adding a
permission check of its own, while still keeping a record of what the run did
and what it was stopped from doing?

## Recommended Direction

Today a run can't comment on, create or label an issue until someone has run
`wfctl start --allow-notify` or put the `authority:notify` label on the issue.
That was built so unattended runs would stop less often. In practice it added a
stop. On #371 it refused an attended session right after the maintainer had
said "file it", and nothing the maintainer could do from where they sat would
lift it. Filing this issue needed the grant too. And with the grant switched
on, Claude Code's own permission check refused the same command anyway. So the
host was already guarding these commands, and wfctl's grant was a second
refusal stacked on top of the host's. The name doesn't help either. It is
called "notify", but a push notifies nobody here, moving a board card notifies
nobody and isn't gated, and this repository has no watchers.

So the grant goes completely. From now on, whether a command may run is decided
only by the host's permission layer. An attended session still asks before
reaching outside the repo, exactly as its skills already say. An unattended run
simply tries. If the host refuses, the run records the refusal instead of
finding another way to do the same thing. `wfctl status` keeps saying that
merging, force-pushing, closing and deleting stay with the human. The line
about the host's permission rules gets reworded, because "rules *of its own*"
implies wfctl has rules as well, and after this it doesn't.

wfctl keeps the half of the job the host can't do, which is remembering. The
host keeps no record that survives `/clear` or an automatic restart, and #371's
restart hook already writes recorded actions into the next session's summary.
That is why the recorder stays, even though the issue proposed deleting
`wfctl notify` outright. Two verbs remain. One records that the run took an
action, and the other records that the host refused one, which holds the
pipeline step. Recording the action later lifts the hold. For that to work,
both verbs have to use the same name for the action. So `wfctl issue` records
its own verbs under the names the skills already use: `issue-create`,
`issue-comment`, `issue-label`, and now `issue-close` too.

## Key Assumptions to Validate

- [ ] **The host is enough of a gate by itself.** Before #280 it was the only
      gate, and it refused a command during this design pass. Test: run
      `wfctl issue label` on a throwaway issue with no grant in place, and see
      that the host asks and wfctl stays quiet. Ask the maintainer before
      doing this, because it writes to the tracker.
- [ ] **A repo refreshes its skills before calling a verb that has been
      removed.** `/start-session` runs `doctor` and then `install-skills`.
      Test: a skill installed from an older wheel fails loudly with `No such
      command` and has no side effects.
- [ ] **No existing log has a block that only the old bare name would lift.**
      Every block filed so far came from skill text that already used the
      `issue-…` names. Test: grep the state dirs in use for a `blocked` event
      whose action has no prefix.

## MVP Scope

**In:**

- Remove `--allow-notify`, `--deny-notify`, the `authority:notify` label check,
  `wfctl notify` (and its `--declined`), and `wfctl blocked` (and its `--clear`).
- Add `wfctl report-action <action>` and `wfctl report-block <action> --reason
  "…"`. These are plain top-level commands with no aliases. The events they
  store keep their current names, `notify-action` and `blocked`.
- `wfctl issue` records every write verb that succeeds as `issue-<verb>`,
  including `close`. It never records `start` or `stop`.
- `wfctl status` stops showing the fourth fact ("outward actions authorized")
  and the `notify` and `notify_source` keys, in the JSON and in every other
  view, all in the same change.
- Delete the code that only the grant used: `_paths.on_trunk` and
  `_tracker.read_issue_labels`. As a result, `wfctl start` stops calling GitHub
  on every session.
- Rewrite the parts of skills and docs that read or explain the grant:
  `end-session`, `speckit-delivery-plan`, `scaffold-tracker`,
  `speckit.analyze.md`, `speckit.decompose.md` and `end-session.md` (including
  their allowed-tools lines), `README.md`, `docs/reference.md`, and the Safety
  section of `AGENTS.md`.
- Tests that checked the refusal are deleted rather than flipped, because what
  they checked no longer exists. New tests cover the two verbs, a successful
  retry lifting its own hold, and an old `block-cleared` entry still reading
  as cleared.

**Out:** anything that changes what the host permits.

## Not Doing (and Why)

- **Keeping the grant and switching it on by default.** A default doesn't
  remove it. The second permission system stays, its misleading name stays, and
  `--deny-notify` brings the deadlock back.
- **Deleting the recorder along with the grant.** Since #371, a recorded push
  is the only trace a restarted session has of it.
- **Aliases for `notify` and `blocked`.** A `notify` alias would quietly change
  from gated to ungated. `doctor` already closes the gap on the next session.
- **A `wfctl report action | block` group.** Two members don't need an extra
  level in `--help`. The maintainer chose the flat pair.
- **Renaming the stored events.** It would break the restart hook's reader and
  every existing log, only to rename something nobody types.
- **Checking action names against a fixed list.** That would make wfctl
  responsible for listing every outward action, and that list was the grant's
  mistake.
- **Installing host permission rules so both layers agree.** It rests on an
  unverified claim that a hook's "allow" beats the host's classifier. Writing
  into the host's permission layer is also a person's decision.

## Open Questions

- The exact new wording of the host-permission line in `wfctl status`. Today
  it reads "the agent has permission rules of its own — wfctl can't see them
  and says nothing about them". This is left to the spec.

## Software design decisions

- docs/architecture/design/384-an-action-is-named-by-the-verb-that-takes-it.md — `wfctl issue` records each write verb as `issue-<verb>`, `close` included, so a successful retry lifts its own hold
- docs/architecture/design/384-the-agent-reports-through-two-flat-verbs.md — `report-action` and `report-block` replace `notify` and `blocked`, with no aliases and unchanged event names

Level 2 is answered by `docs/architecture/wfctl-records-outward-actions-and-never-gates-them.md`
(proposed, supersedes `a-human-grants-outward-facing-authority`).
