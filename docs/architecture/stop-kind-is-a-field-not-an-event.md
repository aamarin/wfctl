---
status: proposed
---

# A stop's kind is a field on the `end` event, not a second event

## Context

`events.jsonl` carries exactly one mark for a session stopping: a line whose
`event` key is `"end"`, written only by `wfctl end`. Four readers consult it,
and all four ask the same question — *did a session stop here?*

```
_stall._passes_this_sitting   `event in ("start", "end")` clears the sitting
_stall.opens_a_new_sitting    the same tuple, the same clear
cli.log_cmd._STYLES           `"end": "red"`
start-session step 9          "whether any line carries `"event": "end"`"
```

None of them asks *why* it stopped, because until #352 there was only one
answer. Step 9 reads the single mark as *a human deliberately wrapped up*, so a
run cut off mid-work comes back and stops to ask a question only the absent
human can answer.

#352 adds a reader that asks the second question. Where its answer lives — in
the `event` key, as a second kind of stop, or in the payload of the one that
exists — is a contract between `wfctl end` and every reader of the log, present
and future, and it is expensive to reverse once anything has written a line.

## Direct baseline

A second event kind. `wfctl end --continued` appends
`{"event": "continued", "step": …}` instead of the `end` line; every existing
`end` line and every existing reader of one is untouched. Step 9 scans for the
last line whose event is either `"end"` or `"continued"` and branches on which
it found. This is the handoff's recommendation and it satisfies every functional
requirement in the spec.

## Decision

One event kind. `wfctl end` goes on appending `{"event": "end", …}` for every
stop of either sort, and the payload carries which sort it was:

```
{"ts": …, "event": "end", "step": "plan", "continued": false}   finished
{"ts": …, "event": "end", "step": "plan", "continued": true}    continued
{"ts": …, "event": "end", "step": "plan"}                       predates this
```

The key is written on every new line. Its absence is a line recorded before this
feature existed, and reads as finished.

## Owns truth

The `end` event's **kind** owns `"did a session stop here?"` — unchanged, and
still answered by matching one string. Its **payload** owns `"did that stop
finish?"`.

The kind cannot own the second question. Every reader that answers the first one
matches on the kind, so moving the second answer there turns *a session stopped*
from one name into a set of names, with nothing that can enforce membership. The
four readers above would each have to learn the second name, and the fifth one
written next year fails silently by matching only the first — it does not crash,
it under-counts, and a branch interrupted four times reads as one nobody
touched. `_paths.SCANS_DIR` exists because this repo already pays that tax one
directory over, where three readers of the arch root have to repeat an exclusion
by hand and a fourth has to be told.

A payload key inverts who bears the cost. The reader that asks the new question
is the only reader that has to know the new key exists.

## Considered

- **A second `continued` event kind** — the baseline above, and it is sound:
  it satisfies FR-001 through FR-015, it keeps every existing `end` line
  byte-identical, and it renders as its own coloured row in `wfctl log`. It
  loses on fit, not on fault. The handoff argued against the field on the
  grounds that it "makes every existing reader interpret a payload it has never
  had to look at" — that turns out not to describe the readers. None of the four
  reads the payload, because none of them asks the new question; the key is
  inert to every one of them. The cost the baseline does carry is the one above,
  and it is unbounded in the number of future readers rather than paid once.
- **Deleting the `end` line when a run is cut off** — rejected in #352 itself
  and restated here because it is the cheapest option and needs no wfctl change
  at all: a hook could do it today. It reaches into wfctl's state behind its
  back, races concurrent writes, and erases the evidence User Story 3 exists to
  keep — a branch interrupted four times becomes indistinguishable from one
  nobody ever worked on.
- **A separate `stops.jsonl`** — a second log for a fact the first one already
  records. Every reader answering *did a session stop here* would have to merge
  two files, and the ordering between them is not recoverable when both are
  appended in the same second.
- **A `status` key on the `end` event** — the spelling
  `test_end_reports_observations` explicitly forbids: `{"event": "end",
  "status": "complete"}` was the unobservable completion claim #70 removed.
  `continued` is a different fact — it is declared by the caller, not concluded
  by `end` — but the word `status` invites the old reading back, and the test
  that asserts `"status" not in last` is the record of why.

## Consequences

- FR-011 falls out of the shape rather than needing to be arranged: a call site
  that passes nothing writes `continued: false`, and nothing about its meaning
  changes.
- SC-005 holds with no migration. Lines already on disk carry no key, absent
  reads as finished, and every existing reader matches the kind exactly as
  before.
- Step 9's rule has to change from *any line carries `end`* to *the most recent
  `end` line's kind*, which is FR-007. The old phrasing cannot express it: on a
  branch with a finished stop followed by a continued one, "any" finds the wrong
  answer.
- `wfctl log` gains no row and no colour. The kind shows up in the detail string
  as `continued=True`, beside `step=`.

## Log

- 2026-09-11  proposed    — #352's architecture gate. The spec deferred the
  choice between a second event kind and a payload key to this level, on the
  grounds that it changes what existing readers must interpret and is expensive
  to reverse once written.
