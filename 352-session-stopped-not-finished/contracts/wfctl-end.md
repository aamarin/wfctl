# Contract: `wfctl end [--continued]`

The CLI surface. Everything not stated here is unchanged from today, and
"unchanged" is load-bearing — FR-002 requires the two kinds of stop to differ in
exactly one observable, the event line's `continued` key.

## Signature

```
wfctl end [--continued]
```

`--continued` is a boolean flag, default off. Omitting it records a finished
stop with today's meaning and today's console output (FR-011).

There is no `--finished`. Its absence is the default, and a flag whose only
effect is the default invites a caller to believe the other one needs pairing.

## Exit codes

| Code | When | Output |
|---|---|---|
| 1 | no session has been started on this branch | today's `_NO_SESSION` refusal, byte-identical, with or without the flag (Story 2 scenario 3) |
| 0 | otherwise | below |

## Side effects, in order

1. `session-summary.md` written **only if absent**, from the same template, at
   the same path. An existing file is left untouched whatever the flag says
   (FR-002, Story 2 scenario 2).
2. One line appended to `events.jsonl`:

   ```json
   {"ts": "…", "event": "end", "step": "…", "continued": false}
   {"ts": "…", "event": "end", "step": "…", "continued": true}
   ```

   Nothing else in the log is read, rewritten or removed (FR-008).

## Console output

Unchanged for a finished stop. For a continued stop, one line differs and one
line may be added.

```
✓ Session closed — plan, boundary unanswered, tree clean.
  Summary: /…/session-summary.md
```

```
✓ Session stopped, not finished — plan, boundary unanswered, tree clean.
  Summary: /…/session-summary.md
```

The first clause is the only difference, and it says what was recorded rather
than what is true of the work. `end` cannot observe that the work is unfinished
(#70); it can observe that it was told the work continues, and "stopped, not
finished" is the issue's own title for that.

The kept-file line is unchanged and appears under both, when it applies:

```
  ⚠ kept — this session wrote nothing; last modified 2026-09-11T16:12:03Z.
```

### The FR-013 warning

Printed **only** with `--continued`, and only when the handoff on disk is a file
`end` itself wrote — one carrying the `**Step**:` reading — whose
`## Next Session TODO` section is absent, empty, or holds just the
`- [ ] (fill in)` placeholder:

```
  ⚠ the handoff's next-action section is still the template's — fill it in, or
    the next session will ask.
```

**A handoff `end` did not write is not judged.** `worktree-handoff` tells authors
in as many words not to add a `Next Session TODO` — the sentence step 9 quotes
goes in that document's own shape — so reading "no section" as "no first action"
warns on every fresh worktree, which is #352's own scenario and the file most
likely to be complete. `end-session` already names the three `**Step**` /
`**Boundary**` / `**Tree**` readings as what separates the two, so the
discriminator is documented rather than invented here.

Says what was observed and what follows from it. It is not a refusal: the stop
is recorded either way (FR-013), because the operator may be leaving precisely
because they cannot finish the sentence. It is also the *last* thing `end` does,
after the stop is appended — so the read is guarded, and an unreadable handoff
costs the warning rather than the stop.

## What this contract does not change

- `wfctl status` and `wfctl status --json` — no new field, no changed field, no
  changed row. FR-015, and the clarification behind it.
- `wfctl log` — no new event kind, so no new row and no new colour. The flag
  shows up inside the existing `end` row's detail string as `continued=True`.
- `_stall._passes_this_sitting` and `_stall.opens_a_new_sitting` — both match on
  `event in ("start", "end")` and a continued stop is an `end`, so a sitting
  still closes at a stop of either kind with no edit to either function.
