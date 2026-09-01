# Judgment scoring — #88 and #90, RETEST 2 after the "a proposed change is a set" rule

Scored cold against `judgment-test.md`, by a fresh agent that had not read the
rubric, `judgment-88.md`, `judgment-88-retest.md` or `judgment-unscored.md`
until after both Phase 1 replies were written and locked.

The skill under test is the working-tree version of
`wfctl/agents/skills/conversation-response-shape/SKILL.md`, which adds under
*Show: the drawing is the description*:

> **A proposed change is a set.** Naming a fix means naming what the code does
> today and what it does once changed, across every input that reaches it — the
> *rows against columns* row below, and the one most often missed. The
> implementation is not that drawing: a branch the reader has to run in their
> head to recover the states is the holding a drawing exists to prevent.

and cuts **Sections repeat one shape** from *Judgment rules* to stay under the
line ceiling. Both `i-have-adhd` and `conversation-response-shape` were read in
full and in force for every response in this session.

Tasks, verbatim and identical to prior runs: "Given issue #88 and the
repository, propose the implementation" and the same for #90.

---

## Reply 1 — #88

### Verbatim

> The marker comment — option one in the issue. A repo declares `# wfctl: bootstrap-handled` inside its own `post_create:` block, and the check reads it as "this repo has an answer, stop offering mine."
>
> **What the check is today.** One line: it scans the uncommented entries of the `post_create:` block for the string `install-skills`. That answers *does this config name wfctl's command*. What `doctor` prints is a different claim — that a new worktree comes up with no skills at all — and a repo that symlinks its skills in some other way makes the first answer no while the second is false.
>
> The marker lives on a comment line, and `_live_lines` drops comment lines on purpose. So the opt-out reads `_block` directly rather than widening the existing scan.
>
> | `post_create:` block | Today | After |
> |---|---|---|
> | absent, or present with no live entries | warns | warns |
> | an entry containing `install-skills` | silent | silent |
> | some other bootstrap, no marker | warns | warns |
> | any content, plus the marker comment | warns | silent |
>
> Row 1 is the case the check was written for and it keeps warning: an absent block has nowhere to put a marker, so the bare worktree cannot be silenced by accident.
>
> 1. `wfctl/_workmux.py` — new predicate beside `post_create_wired` (line 161), which does not change:
>
> ```python
> # A repo that bootstraps its worktrees another way is not a repo missing a
> # bootstrap. No detector can tell the two apart — any pattern match on script
> # names is guesswork — so the repo declares it, in the block the reader is
> # already looking at.
> _BOOTSTRAP_MARKER = "wfctl: bootstrap-handled"
>
>
> def bootstrap_opted_out(text: str) -> bool:
>     """Has the repo declared that `post_create` bootstraps skills its own way?
>
>     Reads `_block`, not `_live_lines`: the marker *is* a comment, and the live
>     scan exists to drop comments. Keeping it separate from `post_create_wired`
>     keeps each function on one question — that one asks whether the config names
>     our command, this one whether the repo says it doesn't need to.
>     """
>     return any(_BOOTSTRAP_MARKER in ln for ln in _block(text, "post_create:"))
> ```
>
> 2. `wfctl/cli.py:2165` — one clause in `_warn_missing_bootstrap`:
>
> ```python
>     if _workmux.post_create_wired(text) or _workmux.bootstrap_opted_out(text):
>         return
> ```
>
> 3. `tests/test_workmux.py` — after the existing `post_create_wired` block (line 119): marker present with a foreign bootstrap opts out; marker on a line outside the block does not; absent block with no marker still reports unwired.
>
> 4. `docs` — the warning text itself gains the escape hatch, since the reader who sees it is the one who needs to know it exists:
>
> ```
> ⚠ .workmux.yaml: post_create does not call `wfctl install-skills` — a new
>   worktree will start with no skills, commands, or .specify/ runtime.
>   Bootstraps another way? Add `# wfctl: bootstrap-handled` to post_create.
> ```
>
> About 30 minutes, most of it the three tests.
>
> Next: `sed -n '155,175p' wfctl/_workmux.py` to see where the new predicate lands.

**Prose word count** (excludes all code blocks and the table): **255**.
Split: 157 in the four prose paragraphs (opening, defect statement, marker
mechanics, table caption); 98 in the numbered-step lead-ins, the estimate and
the next action. Baseline for comparison: variant A 203, retest 1 214.

### Scoring

| # | Question | Answer | Reasoning |
|---|---|---|---|
| J1 | Can I tell what the broken thing is and what it does wrong, without opening the issue? | **YES** | Second paragraph, before any implementation: the check "answers *does this config name wfctl's command*", `doctor` prints a different claim, and a repo that symlinks its skills "makes the first answer no while the second is false". The false warning is then shown literally in step 4. A cold reader gets the defect. |
| J2 | Is the recommendation in the first two lines? | **YES** | First sentence names the marker; second gives its literal text and what accepting it means. |
| J3 | Does the reply argue anything #88 already settled? | **NO (good)**, with a caveat | No prose paragraph defends marker-vs-detector. But the proposed source comment does echo the closed argument verbatim ("No detector can tell the two apart — any pattern match on script names is guesswork"). It is deliverable content, and the repo's own convention requires a comment explaining *why this shape*, so it is not the failure variant A showed (a bolded "Why a marker and not a smarter detector" paragraph). Borderline, scored pass. |
| J4 | Could I act on this without asking a follow-up question? | **YES** | Exact files and lines for both edits, working code, three named tests, the replacement warning text, and a concrete next command. |
| J5 | Are the four reachable states drawn rather than described? | **YES** | A four-row table with `Today` / `After` columns, placed before the implementation, covering exactly the reference reply's four states: `install-skills` present, other bootstrap without marker, other bootstrap with marker, empty/absent. The implementation follows the drawing rather than standing in for it. |
| J6 | If a drawing is present, does its form match the material? | **YES** | Material is a property varying across rows (block shape) against two columns (behaviour before, behaviour after) — the selection table's *rows against columns* row. A table is the correct pick. |
| J7 | Does the reply surface the empty-`post_create` decision as the open one? | **YES (weak)** | It gets the table's row 1 and the only caption sentence in the reply — the most prominent placement of the three runs. But it is framed as settled ("Row 1 is the case the check was written for") rather than handed back for confirmation the way the reference does ("Row 4 is the one to confirm"). |
| J8 | N/A | — | #88 asks for an implementation, not current state. |

**Any "no" in J1-J4: NO — all four pass.**

### Overall verdict: PASS

First run in this series where J5 passes. J1 through J4 all hold, so the
automatic-failure rule is not triggered, and J5 and J6 both resolve yes on a
drawing that is genuinely load-bearing rather than decorative.

### Two honest defects in the reply, neither a criterion failure

**The four rows are not disjoint.** Row 1 reads "absent, or present with no
live entries" and row 4 reads "any content, plus the marker comment". A
`post_create:` block holding *only* the marker comment satisfies both, and they
disagree: row 1 says warns, row 4 says silent. The proposed code resolves it as
silent (`bootstrap_opted_out` reads `_block`, which includes comment lines), so
the table's row 1 contradicts the reply's own implementation in that one
sub-case. The skill's *Enumerate real states* rule asks for real states; it does
not say they must partition the input, and here they do not.

**The caption's reasoning covers only half of row 1.** "An absent block has
nowhere to put a marker" is true for an absent block and false for a present-
but-empty one — which is precisely the sub-case the issue flagged as the open
decision. So J7 passes on placement while the answer it gives is
under-specified exactly where the issue asked for care.

Both defects are downstream of collapsing "absent" and "present but empty" into
one row. A five-row table, or a marker check gated on the block existing, would
have removed them.

---

## Reply 2 — #90

Scored on J5 and J6 only, per the rubric's scope note for the unscored issues.

### Verbatim

> Scan the worktree's own `specs/<handle>` on every run, independent of where `spec_root` points, and merge whatever is there into the same plan.
>
> **What goes wrong today.** Two questions get one answer. *Where do this repo's specs live* is answered by the durable root, and `_plan` treats that answer as also settling *does this worktree hold artifacts of its own* — so it returns before looking. The containment predicate is right; it is being applied to the only candidate directory instead of to each one.
>
> The candidates are the durable dir and `<worktree>/specs/<handle>`. Only the second can be destroyed by the teardown, and only the second is currently unreachable.
>
> | What the run finds | Today | After |
> |---|---|---|
> | No `spec_root`; specs inside the worktree | archived | archived — same directory, scanned once |
> | Durable dir, nothing local | `✓ durable … nothing copied`, exit 0 | unchanged |
> | Durable dir **and** a local `specs/<handle>` | durable message, exit 0, local files destroyed | `✓ archived N`, local dir named as the source |
> | No durable dir resolved, local `specs/<handle>` present | `ℹ no speckit artifacts`, exit 0, destroyed | `✓ archived N` |
>
> Rows 3 and 4 are the bug — the same silent loss reached two ways. Row 4 is not in the issue and comes free with the fix: `resolve_spec_dir` returns `None` rather than falling back to `<repo>/specs` once a root is configured, so a handle the durable root has never heard of takes that path.
>
> 1. `wfctl/_archive.py` — `_plan` takes the handle and walks a candidate list instead of one directory:
>
> ```python
> def _plan(
>     worktree: Path, spec_dir: Path | None, handle: str
> ) -> tuple[list[tuple[Path, str]], int]:
>     ...
>     # Two directories can hold this story's artifacts, and only containment
>     # decides which is at risk — never which one `resolve_spec_dir` preferred.
>     # A durable root answers *where do the specs live*; it does not answer
>     # *what will this teardown destroy*, and letting it end the scan is how a
>     # worktree-local `specs/` was deleted with the hook reporting success.
>     candidates = [d for d in (spec_dir, worktree / "specs" / handle) if d is not None]
>     seen: set[Path] = set()
>     for cand in candidates:
>         if not cand.is_dir() or not is_inside(worktree, cand):
>             continue
>         if cand.resolve() in seen:      # the no-spec_root case: one dir, two names
>             continue
>         seen.add(cand.resolve())
>         _plan_spec_dir(cand, plan)
> ```
>
> The existing `_SPEC_MAP` loop and the unmapped-file sweep move into `_plan_spec_dir(spec_dir, plan)` unchanged — including `claimed`, which stays per-directory so two candidates cannot collide on `1-design.md`.
>
> 2. Destination names collide if both candidates are ever live at once. They cannot be: a durable candidate fails `is_inside`, so at most one directory is ever scanned. Assert it rather than trusting it — the loop reads as if it supports two.
>
> 3. `wfctl/cli.py:463` — the durable line becomes conditional on nothing local having been found. Reporting "nothing there was at risk, nothing copied" beside `archived 6 artifact(s)` is the same wrong claim in a new place.
>
> 4. Tests in `tests/test_archive.py` — one per row above; row 3 is the regression test and asserts the file exists in the archive, not just the exit code. The issue's repro is byte-identical output with and without an at-risk file, so an output-only assertion would have passed against the bug.
>
> Duplicates: archive unconditionally when both copies exist. A content comparison is a second way to be wrong about which one mattered, and a duplicate in a forensic snapshot costs nothing.
>
> About an hour, most of it splitting `_plan` without disturbing the legacy `.agent/` rescue above it.
>
> Next: `sed -n '228,262p' wfctl/_archive.py` — that is the block that becomes `_plan_spec_dir`.
>
> Separately: the command's docstring justifies the manual route with "`git worktree remove` itself refuses when untracked files are present", and your evidence shows it does not refuse on ignored ones. Want that corrected in the same change or its own?

**Prose word count** (excludes code blocks and the table): 424. Not a scored
criterion for the unscored set; recorded because the rubric records it.

### J5/J6 call

**Form chosen: a table.** Four rows — the input situation the run finds —
against `Today` / `After`.

**Did the material have a row-varying shape?** Yes. The issue itself proposes a
three-state table for the report message. The reply enumerates four states
rather than three, folding the issue's report-message table into the `After`
column instead of drawing a second table beside it.

| | Prior run | This run |
|---|---|---|
| Form | prose; table named as needed, never drawn | table, four rows, placed before the implementation |
| Match | mismatch | **match** |

**J5: pass. J6: pass. The mismatch resolved.** The specific prior failure —
"the reply correctly identifies that a table is warranted and then does not
produce one" — does not recur; there is no sentence in this reply describing a
table that should exist.

Two things worth recording about the drawing itself. Row 4 (no durable dir
resolved, local `specs/<handle>` present) is not in the issue and is reachable
because `resolve_spec_dir` deliberately does not fall back to `<repo>/specs`
once a root is configured (`_paths.py:357-361`) — the drawing found a state the
issue's own three-state table missed, which is the rule's stated purpose
("across every input that reaches it"). And the issue's report-message states
are carried as cells rather than as their own table, so the reply has one
drawing where a naive reading of the issue would have produced two.

---

## Comparison across the three runs

| | Pre-fix (`judgment-88.md`) | Retest 1 (`judgment-88-retest.md`) | Retest 2 (this file) |
|---|---|---|---|
| J1 | **FAIL** | PASS | PASS |
| J2 | PASS | PASS | PASS |
| J3 | PASS | PASS | PASS (caveat: closed argument echoed in a source comment) |
| J4 | PASS | PASS | PASS |
| J5 | **FAIL** | **FAIL** | **PASS** |
| J6 | N/A (no drawing) | N/A (no drawing) | PASS |
| J7 | PASS (weak) | PASS | PASS (weak — framed as settled) |
| Verdict | FAIL | PASS with unresolved gap | PASS |
| Prose words | 164 | 214 | 255 |
| #90 form | — | — | table (was prose) |

**J5 flipped to pass.** Three runs, three replies to the same prompt: the first
two produced no drawing at all; this one produced a four-row `Today`/`After`
table and put it before the implementation. The rule's second sentence — "the
implementation is not that drawing" — is the part that appears to have fired:
both prior replies had the same working code, and both treated the code as
sufficient enumeration. This one states the states first and then writes the
code beneath them.

**#90's form mismatch resolved.** Prior run wrote a sentence saying the message
"needs the three-state table the issue proposes" and then drew nothing. This
run drew four rows and never described a table it did not produce.

**Nothing that passed before now fails.** J1 holds, so the rule-1/rule-4
precedence fix from retest 1 did not regress under the new rule — the defect
statement is still its own paragraph, still before the implementation, still in
plain words. J2, J3, J4 and J7 are unchanged in verdict; J7 is weaker in framing
than retest 1's standalone sentence but stronger in placement (a table row plus
the reply's only caption).

**The cut of "Sections repeat one shape" broke nothing here.** That rule
governed repeated named sections holding the same slots in the same order —
document structure, which is exactly what a reply is forbidden from having
(*Three surfaces that are not prose*: no markdown headers in a reply). Neither
reply contains a set of parallel sections for it to have governed. The one
place its absence is arguably visible is #90's numbered list, where items 1, 3
and 4 are edit sites and item 2 is a design caveat wearing the same number — a
shape inconsistency inside one list. That is a stretch of what the rule covered
and did not affect any criterion.

### Cost recorded, not scored

Prose grew each run: 164 → 214 → 255. The rubric explicitly does not treat word
count as a verdict, and the growth here is not padding — it is the four-line
defect paragraph the rule-4 fix added, plus per-step lead-ins for four edit
sites where retest 1 had three. Worth watching in the next round rather than
acting on: the drawing was supposed to *replace* prose that walks the reader
through states, and in this reply it was added alongside a prose defect
statement rather than in place of anything.
