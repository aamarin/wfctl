# Contract: `start-session` steps 4 and 9

The routing rule. It lives in `wfctl/agents/skills/start-session/SKILL.md` —
committed package data, shipped in the wheel, installed into every consuming
repo by `install-skills` (FR-012, `layer-model`).

## Step 4 — what is read

Today:

> `events.jsonl` — … Step 9 needs one fact out of it: whether any line carries
> `"event": "end"`.

Becomes two facts. The first decides most branches on its own.

**`issue`, out of the `wfctl status --json` this step already runs.** A key
(`352`, `PROJ-123`) means the branch exists for one tracked thing and names it;
the literal `unknown` means it does not — a trunk branch. Read the literal, not
the branch name: `key_pattern` is what decides, so `main-rewrite` is trunk and
an agent eyeballing names gets that wrong in the direction that starts work
unbidden.

**The most recent stop and its kind**, read with one stated command rather than
an improvised one. This decides a trunk branch's row and nothing else.

```bash
grep '"event": "end".*}$' "$(wfctl state-dir)/events.jsonl" | tail -1
```

| What comes back | The fact |
|---|---|
| nothing | no session has stopped on this branch |
| a line containing `"continued": true` | the last session stopped without finishing |
| any other line | the last session was wrapped up |

The third row covers a line carrying `"continued": false` and a line carrying no
such key at all — a stop recorded before this feature existed. They route alike
and neither needs telling apart.

`tail -1` is the whole of FR-007. The old phrasing — *any* line carries `end` —
cannot express it: on a branch wrapped up once and interrupted since, "any"
finds the older stop and asks a question the newer one already answered.

## Step 9 — the table

Still three rows, and both of the first two conditions are rewritten. The column
they turn on changes: it was *did a session stop here*, then *what kind of stop*,
and it is now *what is this branch for*, with the kind reading only the trunk
half of rows one and two. Row three does not move.

| Step 4 found | This step |
|---|---|
| an issue branch, or a stop marked continued — with a summary naming a first action | **Do not ask.** Quote the line that names the action, say in one line what you are doing, and leave the skill. |
| a trunk branch with no stop at all, or whose last stop was not continued — with a summary naming a first action | Ask: "What are we working on today?", offering the summary's top **Next Session TODO** item as the default. |
| no summary, one whose next action is still `(fill in)`, or one naming no next action | Ask: "What are we working on today?" |

## The invariants the rows encode

- **The quote is still the gate.** Row three outranks rows one and two whatever
  the branch is and whatever the stop says. Neither licenses acting on an
  inferred first action (FR-006, SC-003).
- **An issue branch never asks** (FR-004). The branch is named for the work and
  `wfctl status` prints the key on its first line, so the question has one answer
  and it is already on screen. A stop that wrapped up deliberately there left the
  same issue open — the next session is not at liberty to work on something else,
  so the stop's kind decides nothing.
- **A trunk branch with no stop at all asks too**, and the row says so rather
  than leaving it to be inferred. Step 4's read has a `nothing` outcome and step
  9 has to consume it; the first draft of this table did not, and the pre-#352
  rule resolved that same state the other way — so an agent filling the gap from
  precedent would begin work against `main`'s accumulated handoff.
- **A trunk branch whose last stop was a wrap-up still asks** (FR-005, SC-002).
  `wfctl end` fills a `Next Session TODO` on every `/end-session`, so `main`
  accumulates one from every session that ever ended there and its top item is as
  likely to be last month's. This is the half a manual exercise skips when it
  only tests the new path.
- **A trunk branch whose last stop was continued does not** (FR-016). It is the
  one place the stop's kind changes a row, and it is #352's own case met where
  nothing else answers it.
- **`tail -1` is FR-007**, and FR-007 now reaches only rows one and two's trunk
  halves. An issue branch never consults the stop record at all.
- **Provenance is still never inferred from the handoff file.** #239 stands: a
  kept handoff and a freshly written one are the same bytes. The rows ask the
  log, not the file.

## What pins it

`tests/test_start_session_asks_conditionally.py`, which asserts against
individual table rows rather than against step 9's text. Its docstring records
why: an earlier version checked for substrings anywhere in the step, and a
review panel showed all three assertions passing on a copy with the two cells
swapped.
