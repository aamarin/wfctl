# Judgment scoring — #88 reply, RETEST after the rule-4/rule-1 precedence fix

Scored cold against `judgment-test.md`, by a fresh agent that had not seen
`judgment-88.md` (the pre-fix scoring) until after Phase 1 generation was
locked. The reply below was generated with the just-edited
`conversation-response-shape/SKILL.md` in force (the version adding the
"Rule 1 vs. rule 4" precedence note and the rule-5 exemption for
subject-establishing content) and the task text is identical to the original
run: "Given issue #88 and the repository, propose the implementation."

## Verbatim reply

> Add a marker comment, `# wfctl: bootstrap-handled`, that `post_create_wired` (`wfctl/_workmux.py:161-171`) accepts as a second way to pass — cheapest of the issue's own candidates, no new file or schema.
>
> Right now that function recognizes exactly one bootstrap mechanism: the literal string `install-skills` inside the `post_create` block. A repo that bootstraps another way — pfms's `scripts/link-wf-skills.sh` symlink script — has no vocabulary to tell wfctl it's covered, so `_warn_missing_bootstrap` (`wfctl/cli.py:2143-2172`) fires every session about a gap that doesn't exist there.
>
> 1. `wfctl/_workmux.py` — new constant next to `_FORMER_COMMAND`/`_COMMAND`, and `post_create_wired` checks it against the raw block (not `_live_lines`, which strips comments — the marker only exists as one):
>
> ```python
> # The repo's own escape hatch for post_create_wired: declares that some other
> # mechanism (a symlink script, a Makefile target) already bootstraps worktrees.
> # Read from the raw block, not _live_lines, because the marker is itself a
> # comment and _live_lines would filter it out.
> _BOOTSTRAP_HANDLED = "wfctl: bootstrap-handled"
>
> def post_create_wired(text: str) -> bool:
>     if any("install-skills" in ln for ln in _live_lines(text, "post_create:")):
>         return True
>     return any(_BOOTSTRAP_HANDLED in ln for ln in _block(text, "post_create:"))
> ```
>
> 2. `wfctl/cli.py:2168-2172` — tell the reader the opt-out exists, not just the missing call:
>
> ```python
> console.print(
>     "[yellow]⚠[/yellow] .workmux.yaml: post_create does not call "
>     "`wfctl install-skills` — a new\n"
>     "  worktree will start with no skills, commands, or .specify/ runtime.\n"
>     "  If another mechanism handles it, add `# wfctl: bootstrap-handled` to "
>     "post_create."
> )
> ```
>
> 3. `tests/test_workmux.py` — extend the `post_create_wired` block: marker present passes, marker present with no other `post_create` lines still passes (a repo can bootstrap outside workmux entirely), empty `post_create` with no marker still warns (existing case, unchanged).
>
> Rejected: a manifest/`install-config` key — tidier to parse, but further from the file a reader is already looking at when the warning names it. The empty-`post_create` case keeps warning by design: that's the one it was written for, where a worktree really does come up bare.
>
> Next: apply the `_workmux.py` diff, then `uv run pytest tests/test_workmux.py -q`.

**Prose word count** (excludes code blocks; no tables present): 214

## Scoring

| # | Question | Answer | Reasoning |
|---|---|---|---|
| J1 | Can I tell what the broken thing is and what it does wrong, without opening the issue? | **YES** | Second paragraph states it plainly, before any implementation detail: `post_create_wired` "recognizes exactly one bootstrap mechanism," a repo using another one "has no vocabulary to tell wfctl it's covered," and the warning "fires every session about a gap that doesn't exist there." A cold reader gets the defect and its consequence, not just the fix. |
| J2 | Is the recommendation in the first two lines? | YES | First line is the recommendation ("Add a marker comment... that `post_create_wired` accepts as a second way to pass"). |
| J3 | Does the reply argue anything #88 already settled? | NO (good) | No re-litigation of marker-vs-detector (the closed question). "Rejected: a manifest/`install-config` key" is a one-line note on an axis the issue left open (which opt-out *shape*, not whether to have one), not a re-argument of the closed detector question. |
| J4 | Could I act on this without asking a follow-up question? | YES | Exact function, exact file/line for both edits, working code for both, a named test-coverage plan, and a concrete next command. |
| J5 | Are the four reachable states drawn rather than described? | **NO** | No table or drawing anywhere in the reply. The empty-`post_create` state is named in prose (twice: once in the test-plan line, once in the closing paragraph); the other three states — `install-skills` present, other-bootstrap-with-marker, other-bootstrap-without-marker — are never enumerated at all, only implicit in the code. Same gap as the pre-fix reply. |
| J6 | If a drawing is present, does its form match the material? | N/A | No drawing present (see J5). |
| J7 | Does the reply surface the empty-`post_create` decision as the open one? | YES | Named explicitly, twice, and once as its own standalone sentence in the closing paragraph ("The empty-`post_create` case keeps warning by design: that's the one it was written for..."), rather than buried as the tail clause of an unrelated sentence. Clearer placement than the pre-fix reply, though still prose rather than the reference reply's dedicated table row. |

**Any "no" in J1-J4: NO — all four pass.** Not an automatic failure under the rubric's stated rule.

## Overall verdict: PASS (on the automatic-failure criteria), with one unresolved gap

J1-J4 all resolve yes, so the reply clears the bar the rubric marks as an
automatic failure. But J5 still fails, plainly: the four reachable states
that the reference reply draws as a table are still only half-present in
prose here, not drawn as a set. That gap is honest to report as a real
shortfall in the reply, not something the automatic-failure rule launders
away.

## Comparison against the pre-fix failure

**J1 flipped from FAIL to PASS.** The pre-fix reply opened with "Add an
opt-out marker `post_create_wired` recognizes... silences the warning" —
treating "the warning" as already known context and never stating what the
current matching logic does wrong. This reply states the defect explicitly,
in its own paragraph, before the implementation: the check "recognizes
exactly one bootstrap mechanism," and a repo using another "has no
vocabulary to tell wfctl it's covered." That is exactly the shape the
SKILL.md fix's "Rule 1 vs. rule 4" precedence note describes — subject
established before the answer's mechanics, not skipped because the request
was framed as "propose the implementation." **J5 did not flip** — it fails
in both the pre-fix and retest replies, for the same reason: no table or
drawing of the four `post_create` × marker states, only partial prose
mention of the empty case. This is expected rather than a fix regression:
the SKILL.md edit under test targeted the rule 1/rule 4 precedence bug
specifically (J1's failure mode), not the separate "Enumerate real states"
drawing rule that J5 checks, so J5 remaining broken says nothing about
whether the intended fix worked — it says a different, untouched rule still
has a gap. J7 also reads stronger in the retest (a clear standalone sentence
vs. a buried tail clause in the pre-fix reply, rated "weak" there) though
it was not a fail in either version. No criterion that passed before now
fails.
