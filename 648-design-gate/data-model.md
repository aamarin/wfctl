# Data model: design gate (#648)

The feature adds no stored value and no new file kind. It adds one pass and
reads two things that already exist.

## The `software-design` pass

A built-in `SubStep` under `brainstorm`:

| Field | Value |
| --- | --- |
| name | `software-design` |
| command | `/speckit.brainstorm` |
| on_finish | `_AUTOMATIC` |
| reads | `_evidence.brainstorm_software_design` |
| needs_person | `False` |

States it reads:

1. `done` when `spec.md` exists, or when the branch changed
   `<arch-root>/design/`.
2. `skipped` with `turned off by design_record_checks in wfctl.json` when the
   setting is `"off"`.
3. `in_progress` with reason `git can't see whether this branch wrote a
   record` when git can't answer, with the remedy in `contracts/cli.md`. The
   plan's longer wording wrapped the row at 80 columns, so the shipped text is
   this one.
4. `in_progress` otherwise, with reason `no software design record for this
   change` and the remedy in `contracts/cli.md`.
5. `skipped` with `claimed: <reason>` when a claim exists. `_pass_states` reads
   the claim before the reader runs, so this needs no code in the reader.

## `design_record_checks` in `wfctl.json`

`"on"` or `"off"`, and on when the key is missing. `"off"` turns both
brainstorm checks off, the architecture check and this one. Any other value is
a `check config` finding and reads as on.

## What it reads

1. **Software design record**: any path under `<arch-root>/design/` that the
   branch added or modified, committed or not. The pass doesn't read the
   file's content.
2. **Claim**: `<arch-root>/step-claims/<branch>/brainstorm.software-design.md`,
   written by `wfctl step none`. wfctl owns the read, and the person or agent
   who ran the command owns the reason.

## Ownership

1. wfctl computes whether the pass is answered, from git and the claim file, on
   every read (`session-state-is-re-derived`). The agent shouldn't report it,
   since it's the party the pass checks.
2. The person on the branch, or the agent under auto-approve, decides whether
   the change makes a structural choice. wfctl can't compute that, and only
   reads which of the two answers exists.
3. The human reviewer judges the answer at the PR, where the record or the
   claim is a committed file.
