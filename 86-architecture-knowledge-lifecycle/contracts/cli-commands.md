# Contract: CLI Surface

Two commands added, one removed. Rendered as the literal strings a user sees.

## `wfctl arch-root`

Prints the resolved architecture root. Mirrors `wfctl spec-root`.

```
$ wfctl arch-root
/Users/dev/project/docs/architecture
```

Out-of-tree root — honoured, with the cost named (FR-002a):

```
$ wfctl arch-root
/Users/dev/project-architecture
⚠ Root is outside the working tree. Records will not share a commit with the
  code implementing them, and will not reach anyone who clones this repo.
```

Exit 0 in both cases. The warning is a warning, not a finding — it describes a
configured choice, not drift.

## `wfctl arch context`

Prints the in-force set: `accepted` records only.

```
$ wfctl arch context
# Architectural contract — 3 accepted decisions

layer-model
  wfctl/agents/ is source; .agents/ is install output. Edit source, then
  re-run install-skills to try it.

vendor-upstream-skills
  Vendored upstream skills are layered over, never edited.

wfctl-runs-the-check
  wfctl runs the verification and records the result. The agent never
  reports its own completion.

2 records not shown (1 superseded, 1 retired) — docs/architecture/
```

Empty root — an empty set is not an error:

```
$ wfctl arch context
# Architectural contract — no accepted decisions

docs/architecture/ holds no records yet.
```

Unparseable record — excluded, and said so rather than silently dropped:

```
$ wfctl arch context
# Architectural contract — 2 accepted decisions

...

⚠ 1 record has no readable status and was excluded: draft-notes.md
```

Exit 0 in all three cases. This command reports what is in force; it does not
judge whether the set is correct.

## `wfctl promote` — removed

```
$ wfctl promote
Usage: wfctl [OPTIONS] COMMAND [ARGS]...
Try 'wfctl --help' for help.

Error: No such command 'promote'.
```

Removed because it was orphaned: it read `<state-dir>/memory-candidates.md`,
which nothing wrote, and wrote `<state-dir>/promoted/<date>.md`, which nothing
read. `WFCTL_CANDIDATES_FILE` goes with it.

It is **not** renamed into this feature. The architecture lifecycle uses
`accepted` as its in-force status, and records reach that state through the
design gate, not through a promotion command.

## Advance check — the design step

Refuses to advance without a record or an explicit declaration (FR-010, FR-010a):

```
$ wfctl next
✗ design: no architecture record for this change.

  Either record the boundary this change draws:
      docs/architecture/<slug>.md
  or state that it draws none:
      wfctl arch none --reason "<why>"
```

After declaring:

```
$ wfctl arch none --reason "copy edit, no new state"
✓ Recorded: no boundary changed — "copy edit, no new state"
```

The declaration is persisted where it lands in the change under review, so a
reviewer sees the claim. wfctl does not verify it: whether a change draws a
boundary is a judgment with no objective test, unlike completion, which either
exits zero or does not.
