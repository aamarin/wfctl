# CLI contract: The design checks match records to the contexts a branch changes

Strings are what a user sees. `<arch-root>` prints as `wfctl arch-root` would show it, relative to the repo when it's inside it.

## `wfctl status`

With a name list, the `architecture` row and #648's `software-design` row can read:

```
architecture  ▶ no architecture record governs session-continuity
software-design  ▶ no software design record governs session-continuity
architecture  ▶ design.md lists no contexts
architecture  ▶ session-continuty is not a context on the domain page
```

The remedy under `next:` for a context with no answer:

```
  Either add a record whose governs field names session-continuity, under:
      docs/architecture/
  or state that it needs none:
      wfctl arch none --context session-continuity --reason "<why>"
```

For the software design check, the location is `docs/architecture/design/` and the command is `wfctl step none brainstorm.software-design --context session-continuity --reason "<why>"`.

The remedy for a missing `Contexts` line:

```
  Add a line under the title of design.md listing the contexts this branch changes:
      Contexts: <names from the domain page>
```

The remedy for an unknown name lists the names:

```
  The domain page lists:
      evidence-and-derivation, architecture-records, design-method, install-and-drift,
      session-continuity, attention, workmux, trackers, spec-kit, agent-host,
      consumer-repo, upstream-projects
```

`wfctl status` and `wfctl status --all`, once every context is answered and at least one by a "no". Several are joined with `; ` on one line:

```
architecture  ●  session-continuity: no — Copy change in the handoff template; workmux: no — No hook changes
```

The row keeps the reasons because the row and the JSON `annotation` are the same field, and a done pass can't move them into `reason`, which would make its step read as held. A reason longer than the console width prints on one line, wrapped by the terminal and not by wfctl, so it doesn't break under the step table and read as a new row.

`wfctl status --json` carries the same text: `state` is `in_progress` with `reason` and `remedy` while paused, and `done` with the lines in `annotation` once answered.

## `wfctl arch none --context <name> --reason "…"`

```
✓ Recorded: session-continuity needs no new boundary — "Copy change in the handoff template"
  Put the reason in the PR body.
```

Refusals, each exiting 1 and writing nothing:

```
✗ --context needs a name list on the domain page, and docs/architecture/domain/ has none.
✗ sesion-continuity is not on the domain page. It lists: evidence-and-derivation, …
✗ This repo checks each context separately, so a branch-wide "no" doesn't answer any of them.
  Run it once per context instead:
      wfctl arch none --context <name> --reason "<why>"
```

The empty-reason and placeholder-reason refusals are #635's, unchanged, and run first.

## `wfctl step none brainstorm.software-design --context <name> --reason "…"`

```
✓ Recorded: brainstorm.software-design does not apply to session-continuity — "No structural choice"
  Put the reason in the PR body.
```

The same three refusals, with `step none brainstorm.software-design` in the command line. `step none brainstorm.architecture` without `--context` gets the branch-wide refusal too, since the claim would otherwise skip the architecture pass. Plus:

```
✗ --context applies only to brainstorm.software-design, the one pass the context check reads.
```

## `wfctl doctor`

```
✗ sample-record: governs sesion-continuity, which isn't on the domain page's name list
```

A malformed entry on the domain page:

```
✗ wfctl: Contexts lists "session continuity", which isn't a lowercase name of letters, digits, and hyphens
```

It exits 1 on either finding, as every other record finding does.

## `wfctl end`

The summary's Boundary line, when the repo has a name list and the branch has a `design.md`. The line reads from `context_gap`, the same function `wfctl status` uses, so the two can't disagree. It doesn't stop at `spec.md`, because the line records whether the question was answered and not whether brainstorm is still paused:

| Branch state | Line |
| --- | --- |
| every listed context has a record or a per-context "no" | `**Boundary**: answered` |
| a listed context has neither, a missing `Contexts` line, or an unknown name | `**Boundary**: unanswered` |
| a listed context has no answer and git can't list the branch's records | `**Boundary**: unknown` |

Without a name list, or without a `design.md`, the line reads as #635 left it.

## Worktree guard: a per-context "no" and a record about the same context

The guard refuses `gh pr create` and `gh pr merge` with exit 2, after the review check finds nothing pending. This refusal comes after #635's branch-wide contradiction and before the unaccepted-record check. It applies when the branch's own spec folder holds `exceptions/<context>/boundary.md` and a level-2 record the branch changes lists that context in its `governs` field:

```
✗ 656-architecture-check-by-context touches docs/architecture/session-handoff.md, which governs session-continuity, but its spec folder says session-continuity needs no new boundary.
  The record answers that context, so delete the exception:
  rm '/Users/andremarin/Development/wfctl-specs/649-design-checks-by-context/exceptions/session-continuity/boundary.md'
```

A "no" for one context and a record that governs a different one is allowed. The check lists the per-context files and doesn't read the name list, so it still runs after the domain page goes back to draft (#653).
