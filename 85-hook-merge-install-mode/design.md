# A merge install mode, so wfctl can manage a hook in a file the consumer owns

**Issue**: #85
**Status**: design settled, not yet specified
**Written**: 2026-08-31

## Problem Statement

**How might we keep an agreed rule in force for a whole session, when the file
carrying it is read once and then decays?**

A skill loaded at `/start-session` is fully in context at turn 0 and effectively
gone by turn 40. Nothing re-reads it, and re-invoking it by hand requires the
reader to notice they have drifted — which is precisely what drifting prevents.

```
turn 0    ████████  skill loaded — fully in context
turn 10   ███
turn 40   ·         only the title survives

          ✗ nothing re-reads it
          ✗ reload depends on noticing the drift
```

The fix is delivery, not content: send a short digest **every turn** rather than
the whole skill once. That needs a `UserPromptSubmit` hook, and hooks live in the
agent's settings file — which belongs to the consumer.

wfctl has two ways to write into a project and neither reaches that file:

| Path | Who owns it | wfctl's behaviour |
| --- | --- | --- |
| skills, commands, `.specify/` | wfctl | whole-file mirror, rewritten each install |
| `.workmux.yaml`, PR template | the repo, after the write | seeded once, never touched again |
| `.claude/settings.json` | the consumer | **neither fits** |

Overwriting destroys the consumer's permissions and their own hooks. Seeding once
strands the hook at whatever shipped the day it landed, when the whole point is
that it moves as the skill moves.

**The unit of ownership is what differs.** For a mirror or a seed, one party owns
the whole file. Here the file belongs to the consumer and a single entry inside it
belongs to wfctl.

## Recommended Direction

A third install mode, **merge**: wfctl owns one hook entry per event and leaves
every other byte of the file alone.

```
consumer's .claude/settings.json
┌──────────────────────────────────────┐
│ their permissions                    │  never touched
│ their own hooks                      │  never touched
│ wfctl hook user-prompt               │  wfctl's — replaced each install,
└──────────────────────────────────────┘  removed on uninstall
```

The entry is found by **what it runs**. Every managed hook's command begins
`wfctl hook `, so the installer locates its own rows by reading the file rather
than by remembering a position that goes stale the moment the consumer edits
around it.

The hook runs a wfctl subcommand rather than carrying pasted text, so the injected
rules cannot fork from the skill they came from.

## Behavior

### `install-skills --agent claude`

Six reachable states, each judged by whether its output is true in that state.

```
no settings.json at all
  ✓ Installed from wfctl 0.15.0
      claude  7 skills · 24 commands · 1 hook
  → file created containing only wfctl's entry

settings.json exists, no UserPromptSubmit hooks
  ✓ Installed from wfctl 0.15.0
      claude  7 skills · 24 commands · 1 hook
  → array created, entry appended

settings.json holds the consumer's own UserPromptSubmit hooks
  ✓ Installed from wfctl 0.15.0
      claude  7 skills · 24 commands · 1 hook
  → entry appended; every foreign entry byte-identical

wfctl's entry present and already current
  ✓ Installed from wfctl 0.15.0
      claude  7 skills · 24 commands · 1 hook
  → file not opened for writing; no reflow

wfctl's entry present but its command has changed
  ✓ Installed from wfctl 0.15.0
      claude  7 skills · 24 commands · 1 hook
  → that entry replaced in place, never duplicated

settings.json exists but is not valid JSON
  ✗ .claude/settings.json is not valid JSON — not modified
  → install of every other target still completes
```

The last state is the one that matters most and is easiest to get wrong. A parse
failure must not be silent and must not take the rest of the install down with it:
the consumer's malformed file is theirs to fix, and the skills still need to land.

### `uninstall-skills --agent claude`

```
wfctl's entry is the only one in its group
  → entry removed, now-empty group pruned

the consumer has their own command in the same group
  → wfctl's entry removed, group kept, their command untouched

no wfctl entry present
  → file not opened for writing
```

### `wfctl doctor`

```
✓ claude: skills current (wfctl 0.15.0)
✓ claude: hook current

⬆ claude: hook entry behind — update: wfctl install-skills --agent claude

⬆ claude: hook entry missing — update: wfctl install-skills --agent claude
```

`doctor` cannot check the *injected text* for staleness, because that text is
never in the file — only the command that fetches it. What it checks is that the
entry exists and that its command matches what this wfctl would install.

### `wfctl hook user-prompt`

Prints the installed digests to stdout. Exit 0 and no output when nothing is
installed that carries one — a hook that fires on every prompt must be silent
rather than noisy when it has nothing to say.

## Boundaries and Ownership

```
consumer                          │  wfctl
──────────────────────────────────┼───────────────────────────────────
.claude/settings.json             │
  permissions, their own hooks    │    never read for meaning,
                                  │    never rewritten
                                  │
  one entry per managed event  ◄──┼──  written at install
    command: `wfctl hook …`       │    replaced at re-install
                                  │    removed at uninstall
                                  │
every turn                        │
  agent fires UserPromptSubmit ───┼─►  `wfctl hook user-prompt`
                                  │    reads installed digest files
                                  │    prints them
                                  │
  ✗ never stores the rules        │    the skill owns the text;
     in settings.json             │    settings.json holds a command
```

**The consumer owns the file.** wfctl owns exactly the entries whose command
carries its prefix, and nothing else in it. Two consequences follow, both
load-bearing:

- The path is **never gitignored**, unlike every mirrored path. It is the
  consumer's file and they may want it committed.
- It is **never listed in the manifest's `items`**, because `uninstall-skills`
  deletes those outright. A merged path is recorded as a sibling entry that
  uninstall *edits* rather than removes.

**The skill owns the injected text.** `settings.json` holds a command, never
prose. Pasted rules fork from their source on the first edit to either, and
nothing would reconcile them.

**The developer's environment owns which agent runs.** The entry names no agent:
it lives inside `.claude/settings.json`, so its location already scopes it, and a
fact stated twice can disagree with itself. This follows the reasoning in
`no-hardcoded-agent`, whose literal subject is `.workmux.yaml`.

## Naming

`wfctl hook user-prompt` — namespace, then event.

`hook ` is the ownership marker, not decoration. It is what makes an entry
self-identifying, so install, uninstall and doctor can all find it. A name like
`wfctl digest` would say what the command prints but never say *this row is
managed*, and a consumer's own `wfctl digest` line would be silently overwritten.

`user-prompt` names the event, matching how every hook system names hooks —
Claude Code's `UserPromptSubmit`, git's `pre-commit`, `direnv hook bash`. It also
scales in the right direction: a second managed hook later is a different event,
not a different skill.

This is why the answer to "one entry or one per skill" is **one entry per event**.
The entry reads the installed tree at run time, so skills can arrive and leave
without touching the consumer's file.

## Checked vs Assumed

| Checked against the code | Assumed, still to verify |
| --- | --- |
| `_CONFIG_SOURCES` is seed-once and holds `.workmux.yaml` (`cli.py:989`) | that `settings.json` reflow is acceptable to consumers who commit the file |
| `_MIRRORED_SKILLS` replaced the `deployment:` frontmatter key (#112, `cli.py:1052`) | that no consumer already runs a command beginning `wfctl hook ` |
| `_AGENT_SKILL_EXTRAS` is the per-agent dispatch seam (`cli.py:1079`) | that one digest-bearing skill stays the common case |
| `test_skill_frontmatter.py` fails on any non-spec top-level key | |
| `install-modes` currently opens "Two install modes" — the sentence this makes false | |
| `no-hardcoded-agent` governs committed config, not settings files | |
| `digest.md` exists on `111-response-shape-digest`, unmerged (`98b63d5`) | |
| both #85 candidate branches conflict against current `main` in `cli.py` | |

The two candidate branches (`worktree-agent-a5dc310d043b4fb76`,
`worktree-agent-a8970fc2061a77080`) hold unreviewed implementations whose
`_settings.py` and architecture records survive, but whose `cli.py` wiring was
written against `_skill_frontmatter()`, which #112 deleted.

## MVP Scope

**In:**

- Merge mode for one path, `.claude/settings.json`, one event, `UserPromptSubmit`.
- `wfctl hook user-prompt`, printing the digests of installed skills that carry one.
- Manifest bookkeeping that records a merged entry as something uninstall edits.
- `doctor` reporting a missing or behind entry.
- The `install-modes` record amended from two modes to three.

**Out:**

- Any second event or second agent.
- Global `~/.claude/settings.json`, and any flag choosing between the two.
- Format-preserving JSON writing.

## Not Doing (and Why)

- **Global `~/.claude/settings.json`, or a flag for it** — `install-skills` is
  repo-scoped everywhere else, and uninstall in one repo removing a hook every
  other repo depends on is not a tradeoff worth exposing. A consumer who
  gitignores the file still gets a working hook; it just isn't shared with their
  team.
- **A `merge-config <name>` command** — it would split the hook from the skill it
  delivers, making them separately installable and separately forgettable. One
  file needs merging today; a general surface invites the question of which files
  are mergeable when the answer is one.
- **Marker keys or a delimited `wfctl` block** — a consumer editing inside the
  block gets it silently overwritten, and one who deletes a marker gets a
  duplicate entry on the next install. Self-identifying commands have neither
  failure. JSON has no comments, which is why Ansible's `blockinfile` pattern
  does not transfer.
- **Preserving the consumer's JSON formatting** — needs a format-preserving
  writer for one file. Instead the merge reports whether anything changed, and an
  unchanged file is never opened, so the reflow happens once.
- **Three-way merge against a stored base** — needs a recorded copy of the file
  per install, which is exactly what `install-modes` says the manifest hash
  deliberately is not. Owning an entry rather than a file means there is no base
  to diff, only a row to find.
- **Putting the digest in frontmatter** — #112 moved this class of declaration out
  of skill files on purpose, and `test_skill_frontmatter.py` now fails on a
  non-spec key. A sibling `digest.md` carries prose without putting it in
  `cli.py`, and works for a vendored skill because it is a new file rather than an
  edit to one wfctl does not own.

## Open Questions

- **Does #111 land first?** Its `digest.md` is the only thing `wfctl hook
  user-prompt` has to print. Building against an unmerged branch is workable but
  means the hook ships with nothing to say until #111 merges.
- **Is `settings.json` reflow acceptable to a consumer who commits the file?**
  Indentation becomes wfctl's on the one install that changes something. Assumed
  acceptable; nobody has been asked.

## Decisions Ledger

| # | Level | Decision |
| --- | --- | --- |
| 1 | architecture | third install mode: wfctl owns an entry, the consumer owns the file |
| 2 | architecture | repo-local `.claude/settings.json` only, no flag |
| 3 | architecture | agent layer, via the existing per-agent dispatch |
| 4 | architecture | ownership marker is the command prefix `wfctl hook ` |
| 5 | design | subcommand is `wfctl hook user-prompt` — namespace, then event |
| 6 | design | the entry names no agent; its location already scopes it |
| 7 | design | one entry per event, printing whatever digests are installed |
| 8 | design | digest is a sibling `digest.md` (#111), not frontmatter, not a dict |
| 9 | design | a malformed settings file fails loudly and does not fail the rest of the install |

## References

- Issue #85 — the filing, and the three questions this settles
- Issue #111 — the digest and its per-turn cadence; names #85 as its missing half
- PR #112 (`c3b0c35`) — moved the mirror switch into the installer; invalidates
  both candidates' `cli.py` wiring
- `docs/architecture/install-modes.md` — the record this amends
- `docs/architecture/no-hardcoded-agent.md` — the reasoning behind decision 6
- `docs/architecture/layer-model.md` — why `.agents/` paths are generated
