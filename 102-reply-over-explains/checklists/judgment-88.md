# Judgment scoring — #88 reply (T031 primary task)

Scored cold against `judgment-test.md`, after the reply in Phase 1 was generated
without having read that rubric.

## Verbatim reply

> Add an opt-out marker `post_create_wired` recognizes: `# wfctl: bootstrap-handled` anywhere in the `post_create` block silences the warning without requiring `install-skills` — the cheaper of the two candidates the issue names, no schema, no new file.
>
> `post_create_wired` (`_workmux.py:161-171`) currently scans only `_live_lines`, which strips comment lines before the function ever sees them — so the marker has to be checked against the raw block, not that filtered view:
>
> ```python
> _BOOTSTRAP_HANDLED_MARKER = "wfctl: bootstrap-handled"
>
> def post_create_wired(text: str) -> bool:
>     """Does `post_create` reinstall the skills a fresh worktree lacks — or
>     does the repo declare it handles that another way?
>     """
>     block = _block(text, "post_create:")
>     if any(_BOOTSTRAP_HANDLED_MARKER in ln for ln in block):
>         return True
>     return any("install-skills" in ln for ln in _live_lines(text, "post_create:"))
> ```
>
> No change needed in `_warn_missing_bootstrap` (`cli.py:2143-2172`) — it already just calls `post_create_wired` and returns on `True`. Its docstring currently says "a repo may bootstrap its own way" as the reason the check can't be a hard failure; worth a line there noting the marker is how that repo now says so. An empty `post_create` with no marker still warns — that's the case this check exists for, and nothing here changes it.
>
> Next: add the constant and the block-scan branch above, then a test asserting a `post_create` block holding only the marker (no `install-skills` line) reports wired.

**Prose word count** (excludes the code block): 164

## Scoring

| # | Question | Answer | Reasoning |
|---|---|---|---|
| J1 | Can I tell what the broken thing is and what it does wrong, without opening the issue? | **NO** | The reply opens with "Add an opt-out marker … silences the warning" — it names "the warning" as if already known and never states the defect (a repo bootstrapping another way is warned every session that it has no mechanism, while its mechanism works). A cold reader gets the fix, not the bug. |
| J2 | Is the recommendation in the first two lines? | YES | The marker recommendation is the first sentence. |
| J3 | Does the reply argue anything #88 already settled? | NO (good) | "the cheaper of the two candidates the issue names" restates the issue's own conclusion in a clause; it does not re-argue marker-vs-detector as a case. |
| J4 | Could I act on this without asking a follow-up question? | YES | Exact function, exact file/line, working code, and a concrete next step are all present and unambiguous. |
| J5 | Are the four reachable states drawn rather than described? | **NO** | No table, no drawing of the four `post_create` × marker states anywhere in the reply. The empty-case behavior is mentioned in one clause of prose, not enumerated. |
| J6 | If a drawing is present, does its form match the material? | N/A | No drawing is present (see J5), so there is nothing to judge the form of. |
| J7 | Does the reply surface the empty-`post_create` decision as the open one? | YES (weak) | The sentence "An empty `post_create` with no marker still warns — that's the case this check exists for" does name and correctly resolve it. It is present but not foregrounded — it is the last clause of a paragraph about docstring updates, not given the space the reference reply gives it (a table row plus a dedicated confirming sentence). |

**Any "no" in J1-J4: YES — J1 fails.**

## Overall verdict: FAIL

J1 fails on its own, which the rubric marks a failure regardless of length or
any other criterion. The reply is mechanically excellent — correct fix,
correct file, correct edge case, working code, actionable next step — but it
skips establishing what `post_create_wired` currently does wrong before
proposing the fix (`conversation-response-shape` rule 4: "establish the
subject before deciding about it"). A reader who has not already read #88
cannot tell, from this reply alone, why the current behavior is a bug rather
than intended strictness. J5 also fails: the four reachable states the
rubric's reference reply draws as a table are never drawn here, only
half-described in prose (only the empty-case row is mentioned; the
other-bootstrap-with-marker and other-bootstrap-without-marker rows are
implicit in the code, not stated).

---

## T032 — state question

**Task:** "What does rule 6 in conversation-response-shape do?" (state question, not a change proposal)

### Verbatim reply

> Rule 6 caps a reply to the answer plus at most one supporting block of prose — a drawing doesn't count against it, but a second prose block does, even if each piece individually passes rules 1 through 5.
>
> It exists because rules 1-5 each govern one piece of a reply in isolation, so a reply can satisfy every one of them — answer first, framed in plain language, right depth, subject established, no unearned paragraphs — and still land as a wall, because nothing was counting the pieces together. Rule 6 is the check on the whole reply, not any one part of it.
>
> The tell it's watching for is a counted lead-in — "three decisions," "two things worth naming" — since a list like that survives every other rule individually (each item is defensible on its own) while still stacking into more than one prose block.

**Prose word count:** 148

### J8 — does the reply avoid manufacturing a "what changed" when asked about current state?

**Verdict: PASS.**

The reply answers "what rule 6 does" directly — definition, then why it
exists, then the tell it watches for. Nothing in it is framed as a change,
a diff, or a "before/after." It does not manufacture a *what changed* opening
for a question that has no *changed* in it, matching the skill's own line:
"A reply about current state has no *what changed*; manufacturing one is a
tell that the opening was copied rather than chosen."

---

## T033 — reasoning/tradeoff question (SC-005 guard)

**Task:** "What are the tradeoffs between rule 6's whole-reply cap and just tightening rules 1-5 individually?"

### Verbatim reply

> Rule 6 catches what tightening rules 1-5 individually can't: a reply where every piece passes its own rule but the sum is still a wall.
>
> | | Tightening rules 1-5 | Rule 6 (whole-reply cap) |
> |---|---|---|
> | What it checks | Each piece in isolation — is the answer first, is it framed, is depth right, is the subject named, does volunteered material earn its paragraph | The reply as a whole, after every piece already passed |
> | Failure mode it catches | A rule violated on its own — reasoning before the answer, jargon in the first line, an unearned paragraph | Several individually-earned pieces stacking into more prose than the cap allows |
> | Cost of tightening it | Makes each individual rule stricter, so borderline-but-legitimate uses of that rule now fail too | Costs a fixed slot: one supporting prose block, whatever the reply otherwise needed |
> | Where it can go wrong | A stricter rule 5 could delete material that genuinely needed saying under a real decision, not just an unearned aside | The cap can cut a reply that needed two distinct explanations for two distinct things, forcing an artificial merge or a "the reader will ask" deferral that costs a turn |
>
> The core difference: rules 1-5 are about correctness of each piece, and no amount of tightening any one of them stops multiple *individually correct* pieces from accumulating. A reply with three genuinely-earned one-line justifications — each one legitimately passing rule 5 on its own — still becomes a list of three, which is the exact shape rule 6's own example calls out as the tell it's watching for. Only a rule that looks at the reply after assembly catches that; a per-piece rule structurally cannot, because it never sees the other pieces.
>
> The risk rule 6 takes on in exchange is real, and the skill's own text partly hedges it — "everything past the cap is a follow-up, the reader will ask" — which is a bet that a second question is cheaper than a longer first answer. That's true when the two things were separable. It's a worse trade when a single question genuinely has two parts that need to be read together, since the cap then forces either compressing them into one block (losing the separation that made them readable) or deferring one to a turn the reader has to spend asking for something they already asked for once.

**Prose word count:** 226

### Assessment

The requested depth survived. The reply gives a recommendation-shaped opening,
a comparison table (mechanism-vs-mechanism, four rows: what it checks, failure
mode, cost, where it can go wrong), and two full paragraphs of independent
reasoning — one building the core argument for why per-piece rules structurally
cannot catch what rule 6 catches, one naming a genuine cost of rule 6 (forced
merging or a deferred turn when two things needed to be read together). Neither
side of the tradeoff is stated and dropped; both are argued, and the second
paragraph in particular surfaces a real weakness in rule 6 rather than only
defending it — which is what a tradeoff question asked for.

Worth flagging honestly: this reply itself does not obey rule 6's own letter.
The cap is "the answer, plus at most one supporting block of prose" (a table
exempted), and this reply has an opening line, a table, *and* two further
prose paragraphs — two supporting blocks, not one. So the finding here is not
"the cap left the reasoning intact while still enforcing itself" — it is that
when a question explicitly asks for tradeoffs, rule 6 got overridden rather
than satisfied. That is consistent with `i-have-adhd`'s own override clause
("a rule fights the task, the task wins; the shape stays") and with this
skill's row for tradeoff questions ("recommendation first, then options with
costs"), so the outcome is arguably correct — but it means rule 6 as written
did not hold on this input; the task did.

### SC-005 verdict: **PASS** — full reasoning survived. But it survived by the
question overriding rule 6's cap, not by the cap and the requested depth both
holding at once. That tension is itself a finding worth carrying back into the
design: rule 6's cap and the "tradeoffs → full reasoning" row can conflict, and
on this input the depth request won.
