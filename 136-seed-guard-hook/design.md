# Seed the cross-worktree guard into a consumer's settings file

**Issue:** #136 · **Branch:** `136-seed-guard-hook` · **Mode:** `auto_approve`

## The idea in one line

`install-skills --agent claude` turns the cross-worktree guard on for the
consumer, instead of the README telling them to turn it on by hand.

## Why now

The guard shipped in #129/#132 as a working subcommand with no way to reach a
consumer's config. Every user who wants it edits `.claude/settings.json`
themselves — four lines that are not reviewable, not versioned with wfctl, and
gone the next time someone sets up a fresh checkout. #85 landed the merge install
mode that makes seeding possible, and it is already exercised: a managed
`UserPromptSubmit` hook merges into that same consumer-owned file today.

The perf objection recorded on the issue is spent. #135 measured the guard at
81.7 → 33.8 ms per Bash call once it stopped importing `wfctl.cli` and stopped
shelling out to git twice, against a 27.1 ms floor of bare Python startup.

## Level 1 — behavior

Two entries reach the consumer's `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "wfctl hook worktree-guard" }] }
    ]
  },
  "permissions": { "deny": ["Bash(cd:*)"] }
}
```

Every state a consumer can be in, and what wfctl does:

| Their settings file | After `install-skills --agent claude` |
|---|---|
| absent | created: three managed hooks and the deny rule |
| exists, no `PreToolUse` | wfctl's group appended; their keys untouched |
| has their own `PreToolUse`/Bash hook | theirs survives; wfctl's is a separate group |
| already has the guard, added by hand | adopted in place — the command prefix marks it as wfctl's |
| already has `Bash(cd:*)` in `deny` | nothing added, and the receipt records that wfctl did not add it |
| re-install | nothing written, file not reflowed |
| uninstall | wfctl's hook removed; their `PreToolUse` hook survives |
| guard hook deleted by hand | `doctor` reports it gone |

**Two of those states render a line that is not true today**, and both are
requirements this level generates:

*The hand-added guard.* `merge_hook` replaces `command` and `type` and never
reads `matcher`. A consumer who pasted the README block but wrote
`"matcher": "*"` gets `✓ Merged wfctl's managed hooks into .claude/settings.json`
while the entry still fires on every tool. The ✓ is a false success, not a silent
no-op, which is the worse of the two failures.

*The deny rule.* `Bash(cd:*)` carries no marker and cannot carry one. Uninstall
either deletes a rule the consumer wrote themselves, or leaves wfctl's own entry
behind. Neither is acceptable without a record of who added it — which is the
level-2 question, generated here.

`doctor`'s existing vocabulary does not cover the second entry either. A rule
carries no version, so it is present or gone and never *behind this wfctl*.

## Level 2 — architecture

The manifest owns *"did wfctl add this entry, or was it already the
consumer's?"*, recorded at install time and read back at uninstall. Absence of a
receipt reads as *not wfctl's* — the safe side, costing a leftover entry rather
than a consumer's rule.

Full argument, the baseline it beat and the three rejected alternatives:

- `docs/architecture/the-manifest-owns-what-carries-no-marker.md`

## Level 3 — design

The receipt is a sibling list, `manifest[agent]["permissions"]`, rather than a
second record shape inside `merged` — `merged` is read as hooks by three call
sites, and a permission entry has no event.

- `docs/architecture/design/136-the-receipt-is-a-sibling-of-merged.md`

The matcher fix threads an expected matcher through `merge_hook` rather than
removing and re-appending the group: the function's docstring commits to keeping
a replaced entry in its original array position, and re-appending breaks that for
a consumer who ordered their hooks deliberately. No credible alternative, so no
record.

## Software design decisions

- `docs/architecture/design/136-the-receipt-is-a-sibling-of-merged.md` — the
  permission receipt is a sibling of `merged`, not a second shape inside it

## Architecture decisions

- `docs/architecture/the-manifest-owns-what-carries-no-marker.md` — the manifest
  owns whether wfctl added an entry that cannot carry a marker

## Out of scope

- Teaching the guard to resolve relative paths. It closes one of the three gaps
  `_guard.py` names and leaves `cd $VAR` and `cd $(…)`, so it narrows the deny
  rule's job without removing it.
- Making the pipeline's per-step stopping points configurable per feature.
  Surfaced during this session; unrelated to #136.

## What the test suite will not cover

The merge against a settings file wfctl did not create. The unit tests are dict
literals. A round-trip over three dicts has not exercised a real consumer's
`.claude/settings.json` carrying their own `PreToolUse` hooks, their own
`permissions.deny` list and their own key order — that is a by-hand run on a
scratch repo: install, confirm their rows survive byte-for-byte, re-install,
confirm nothing duplicated, uninstall, confirm the file returns to what it was.
