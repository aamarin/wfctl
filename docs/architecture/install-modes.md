---
status: accepted
---

# Install modes are chosen per path: managed mirror, seed-once, or merge

## Context

wfctl writes three kinds of file into a project, and they have different
lifetimes.

Skills are wfctl's to keep current — a fix should reach every repo. Config files
like `.workmux.yaml` become the repo's own the moment they exist; the next
developer edits them, and wfctl must not undo that.

Treating those two the same picks one failure or the other: overwrite always, and
hand-tuned config is destroyed on every install; overwrite never, and a fixed
skill never reaches a repo that already has the broken one.

`.claude/settings.json` is the third kind, and it fits neither. It holds the
consumer's permissions and their own hooks, so a mirror that rewrites the file
destroys work wfctl never wrote. It also holds a managed hook that must move when
the skill it re-anchors moves, so a seed that never touches the file again
strands that hook at whatever shipped the day it landed.

The unit of ownership is what differs. For a mirror or a seed the whole file
belongs to one party. Here the file belongs to the consumer and one entry per
event wfctl manages belongs to wfctl.

## Decision

Three install modes, chosen per path rather than per run.

| Mode | Command | Unit wfctl owns | Re-run behaviour | Removable |
| --- | --- | --- | --- | --- |
| managed mirror | `install-skills` | the whole file | rewrites from source, tracked by content hash in `.wf-skills-manifest.json` | yes, `uninstall` |
| seed-once | `install-config` | nothing, after the write | writes only if absent, then never touches the file again | no |
| merge | `install-skills --agent claude` | one entry per managed event | replaces its own entries, leaves every other byte | yes, `uninstall` |

A merged entry is recognised by what it runs. Every managed hook's command starts
`wfctl hook `, so the installer finds its own rows by reading the file rather than
by trusting a list of positions that goes stale the moment the consumer edits
around it. The manifest records that an entry exists and where; the file itself
is the authority on whether it still does. Ownership is drawn at the command
entry rather than the matcher group around it, so a consumer is free to put
their own command in the same group as wfctl's — a group is pruned only once
wfctl has emptied it of its own entries.

Merge mode is scoped to the agent layer: the hook schema belongs to Claude Code,
not to wfctl's base layer, so it is claude-only rather than a base-layer path
every agent would have to interpret. It is an explicit branch in `_merge_hooks`,
not an entry in the `_AGENT_SKILL_EXTRAS` table — one file, one event, one agent
does not need a table, and a second merge target is a change to that function
rather than a config edit.

The hook runs a wfctl subcommand rather than carrying pasted text: `wfctl hook
<name>` prints the digest of whichever installed skills carry one. The digest
lives in a sibling `digest.md` next to the skill, not in the skill's
frontmatter — a skill's `description:` is written to tell a model *when to load*
it and ends by naming the slash command that activates it, which is noise once
the skill is already loaded, and a new frontmatter key would fail every shipped
skill against the fixed set `test_skill_frontmatter.py` enforces. A sibling file
also keeps a derived skill eligible: `vendor-upstream-skills` says to layer
over one rather than edit it, and adding a file beside it is not an edit.

## Owns truth

For a managed path, wfctl owns the content, and the manifest hash is what
distinguishes wfctl's output from a hand edit.

For a seeded path, the repo owns the file from the moment it is written. wfctl
cannot own it: it has no record of what the repo intended to change, so any
rewrite is a guess that silently discards local intent.

For a merged path, the consumer owns the file and wfctl owns exactly the entries
whose command carries its prefix. Two consequences follow and both are load
bearing. The path is never gitignored, unlike every mirrored path — it is the
consumer's file and they may want it committed. And it is never listed in the
manifest's `items`, because `uninstall-skills` deletes those outright; a merged
path is recorded as a sibling `merged` entry that uninstall edits instead.

## Considered

- One mode, always overwrite — destroys the hand-tuned config the seed exists to
  start.
- One mode, never overwrite — a corrected skill reaches only fresh installs, so
  every existing repo keeps the bug.
- Three-way merge on every file — needs a stored base version per path, which is
  what the manifest hash deliberately is not. Merge mode avoids that by owning an
  entry rather than a file: there is no base to diff against, only a row to find.
- The hook in `~/.claude/settings.json` — follows the user across projects, but
  the hook reads the skills *this repo* installed, so a global entry fires in
  every checkout on the machine including those that never ran `install-skills`.
  A flag choosing between global and repo-local was also rejected: it makes
  `uninstall`'s blast radius depend on a value nobody remembers passing.
- Preserving the consumer's formatting exactly — needs a format-preserving JSON
  parser, a runtime dependency for one file. Rejected in favour of writing only
  when the merge actually changes something, so the reflow happens once.

## Consequences

A fix to a seeded template reaches only repos seeded afterwards. That is the
accepted cost of the repo owning the file, not an oversight.

The first install that adds a managed entry reflows the consumer's settings file
— the trailing newline and any non-ASCII they wrote survive, key order, array
layout and indent width do not. Indent is written as Claude Code's own two
spaces: sniffing the consumer's width preserved half a shape whose other half
was going anyway, and cost every caller a source-text parameter to do it. The
file's mode is carried over and a symlink is written through rather than
replaced, because `os.replace` installs a fresh inode. Later installs do not
open it.

`doctor` needs a check of its own for merged entries. The bundle content hash
cannot see them: the entry lives in a file wfctl neither owns nor hashes, so a
settings file edited back to the consumer's original leaves every other check
reporting the install as current. What it checks instead is that the entry is
present and that its command matches what this wfctl would install — not
whether the digest text itself is current, which is never in the file, only the
command that fetches it.

## Log

- 2026-08-28  accepted    — relocated from `AGENTS.md`
- 2026-09-01  amended     — third mode, merge (#85); the deferral recorded under
  Considered is resolved by owning an entry rather than a file
- 2026-09-05  amended     — merge owns one entry per event, not one entry (#212
  added a `Stop` hook beside the `UserPromptSubmit` one in the same file). No
  change to the mode: ownership was already drawn at the command entry.
