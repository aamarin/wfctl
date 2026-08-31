# Phase 1 Data Model: deployment key metadata

No database and no serialised schema is introduced. The "entities" here are the
in-memory and on-disk structures the installer already reasons about; this change
alters one of them and leaves the rest untouched.

## Shipped skill

A directory under `wfctl/agents/skills/<name>/` containing a `SKILL.md`.

| Field | Source | Notes |
| --- | --- | --- |
| `name` (identity) | the directory name | The only identifier. Nothing else keys a skill, which is why a renamed directory is a rename of the entity. |
| frontmatter | `SKILL.md`, between the first two `---` lines | Constrained to the Agent Skills allowed set — see `contracts/`. |
| body | `SKILL.md` after the frontmatter | Not read by wfctl. |
| vendored? | derived: `license:` present in frontmatter | One instance today, `i-have-adhd`. Recorded in `vendor-upstream-skills`, not computed at install time. |

**Change**: the frontmatter loses `deployment:` for the six skills that carry it,
and gains nothing. After this change no shipped skill carries a wfctl-specific
key.

**Validation rule (FR-001, FR-010)**: for every skill that is not vendored, the
set of top-level frontmatter keys is a subset of the allowed set.

## Discoverable set

The named subset of shipped skills that an agent's native loader picks up.

| Field | Value |
| --- | --- |
| Representation | an immutable set of skill names, declared once in `wfctl/cli.py` |
| Cardinality | 7 after this change, from 6 before |
| Membership test | by skill directory name |
| Owner | `install-skills`. Not any skill file — see `plan.md`, Constitution Check. |

**Change**: this entity is new *as data*. The same information existed before,
scattered across six files as a frontmatter key; it now exists once, as a value.

**Validation rule (FR-005)**: every name in the set corresponds to a directory
under `wfctl/agents/skills/`. A name that does not is a typo or a rename that
missed the declaration, and fails the suite rather than silently mirroring
nothing.

**Non-rule, stated because it is the obvious wrong assumption**: membership does
not make a skill self-invoking. A skill whose own frontmatter declines
model-initiated invocation is listed and loadable on request but never invoked
unprompted. Membership decides *placement*, not *invocation policy*.

## Install plan entry

The in-memory tuple the installer builds per item before writing anything:
`(layer, kind, relative_destination, destination, source)`.

Unchanged in shape. What changes is which entries exist: the Claude layer gains
one more `skill` entry, for the vendored skill's native copy.

The extra native copy is attributed to the **agent** layer, not the base layer,
even though its source is a base-layer path — so uninstalling the agent removes
it and uninstalling the base does not.

## Install record (`.wf-skills-manifest.json`)

The per-layer list of what wfctl placed in a repo, and the backup of anything it
overwrote. Read by `uninstall-skills` and by `doctor`'s drift and orphan checks.

Unchanged in shape. It gains one item under the `claude` layer. Because uninstall
iterates recorded items rather than recomputing them, the new native copy is
removed with no code change (verified — `research.md` R2 neighbourhood,
`cli.py:1697-1703`).

## State transitions

A skill moves between two states, and only one direction is exercised here.

```
             joins the discoverable set
  reference ─────────────────────────────► reference + native
  copy only                                copy
  (.agents/)   ◄─────────────────────────  (.agents/ + .claude/)
             leaves the discoverable set
                        │
                        └── the native copy stops being installed
                            and stops being recorded, but is not
                            deleted, and doctor never scans for it
                            → tracked as #110, out of scope
```

This change performs the left-to-right transition once, for the vendored skill.
The right-to-left transition is not exercised and is where the known gap lives.
