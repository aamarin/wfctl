# Contract: what the commands print

The interface this feature changes is console output read by a human and by an
agent. Each contract below is the literal text, because a sentence describing a
string is longer than the string and less certain.

## `wfctl status`

```
#74  74-session-truth-ownership
────────────────────────────────────
brainstorm   ●
specify      ●
clarify      –
plan         ▶  ← current
tasks        ○
analyze      ○
decompose    ○
implement    ○
next: /speckit.plan
```

**Changed**: the trailing `next:` line. It is the one field `current.md` carried
that no other command produced (FR-004).

**Guarantees**:
- Exactly one step carries `← current`, or none when the story is complete.
- `next:` names a command when a step is current, and the completion sentence
  when none is.
- Symbols appear here and nowhere above the renderer.

## `wfctl status --json`

```json
{
  "issue": "74",
  "branch": "74-session-truth-ownership",
  "session_started": true,
  "current": "plan",
  "next_command": "/speckit.plan",
  "steps": [
    {"name": "brainstorm", "state": "done", "annotation": null, "is_current": false},
    {"name": "specify", "state": "done", "annotation": null, "is_current": false},
    {"name": "clarify", "state": "skipped", "annotation": null, "is_current": false},
    {"name": "plan", "state": "in_progress", "annotation": null, "is_current": true},
    {"name": "tasks", "state": "pending", "annotation": null, "is_current": false},
    {"name": "analyze", "state": "pending", "annotation": null, "is_current": false},
    {"name": "decompose", "state": "pending", "annotation": null, "is_current": false},
    {"name": "implement", "state": "pending", "annotation": null, "is_current": false}
  ]
}
```

**New**: this is the surface an agent reads once `current.json` is gone. Without
it the only source of per-step state is the block above, whose four glyphs are
lossy by construction — `–` and `●` are drawn differently and both mean "does
not block".

**Guarantees**:
- Rendered from the same `PipelineReport` the console renders from. A fact
  reachable in one output is reachable in the other; the flag selects a format,
  never a second inference.
- `state` is one of `done`, `in_progress`, `pending`, `skipped`. No glyph appears
  at any depth.
- `current` is `null` exactly when `next_command` is `null`.
- Every step in the pipeline is present, in pipeline order.

## `wfctl status` — nothing exists yet

```
#74  74-session-truth-ownership
────────────────────────────────────
(no spec dir found)
brainstorm   ○  ← current
specify      ○
…
next: /speckit.brainstorm
```

**Guarantee**: identical whether the feature directory is absent or present and
empty (FR-005). The first step is `pending`, never `skipped`.

## `wfctl status` — every step behind

```
#74  74-session-truth-ownership
────────────────────────────────────
brainstorm   ●
…
implement    ●  8/8 done
next: Story complete — open PR or run `/end-session`.
```

**Changed**: the completion sentence. Today this state renders as an absence —
no cursor, no line — and the sentence exists only in `resume`.

## `wfctl end`

```
✓ Session closed — implement 3/8 done, boundary answered, tree dirty.
  Summary: /Users/…/state/wfctl/<branch>/session-summary.md
```

A finished pipeline reads `every step done`, not `complete`. The pipeline's own
name for that position is accurate about the artifacts, but on a handoff line it
reads as a verdict on the session — which is the word FR-006 removes.

`boundary` is one of `answered`, `unanswered`, `unknown`. Three readings because
git cannot always tell, and reporting a missing answer as `answered` is the same
class of claim as `complete`.

**Guarantees**:
- Every clause names something observed at that moment: pipeline position, the
  boundary check, `git status --porcelain`.
- No clause asserts a completion (FR-006). The word does not appear.

## `session-summary.md`, as written by `end`

```markdown
# Session Summary: 2026-08-30 — 74-session-truth-ownership

**End**: 2026-08-30T18:04:11Z
**Step**: implement 3/8 done
**Boundary**: answered
**Tree**: dirty

## What We Accomplished

- (fill in)

## Next Session TODO

- [ ] (fill in)
```

**Changed**: `**Status**: complete` is gone. The three observed lines replace it.

**Guarantee**: honest standing alone (FR-008). Unfilled prose reads as unfilled,
and nothing above it claims the session finished.

## `wfctl resume`, `wfctl end` — no session started

```
✗ No session found for this branch. Run `wfctl start` first.
```

**Changed**: the condition. Today it is "`current.json` does not exist"; it
becomes "no `start` event in this branch's event log".

## Migration

Any command that touches a state directory removes `current.md` and
`current.json` if present, silently (FR-012). Nothing is printed: the files are
tool-written, never hand-edited, and a notice about a file the reader never knew
existed is noise.
