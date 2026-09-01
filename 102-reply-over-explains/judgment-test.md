# Judgment test: what a good reply to #88 looks like

Written **before** running anything, so it cannot be fitted to whatever comes
out. Nothing here counts words.

## Why this file exists

The original experiment measured two things — prose word count on #88, and
whether a table appeared across five issues. Both count *presence*, not
correctness:

```
what was counted            what it fails to see
────────────────            ────────────────────
prose words                 #556 scored 40 words and still failed
table appeared              #61's table was unwarranted and still counted
```

So neither number can separate a good reply from a bad one, and both of
design.md's headline claims rest on them. This file supplies the missing half:
a definition of the target, against which a reply can be judged.

## The task

Given issue #88 and the repository, propose the implementation.

That is the whole prompt. No instruction to be brief, no mention of
`conversation-response-shape` — the skill is either in force or it is not, and
telling the agent to be short would test compliance rather than the rule.

## What #88 has already decided

This is the discriminator. The issue argues its own direction and closes it:

> "No general detector exists for 'some other mechanism handles this' — any
> pattern match on script names is guesswork… The honest shape is an opt-out the
> repo declares, since only the repo knows."

A marker comment is named as the cheapest candidate. **Marker versus smarter
detector is settled in the issue text.** Variant A's failure was a bolded
paragraph titled *"Why a marker and not a smarter detector"* — re-arguing the
closed question.

## What #88 leaves open

One thing, stated in the issue:

> "Worth deciding whether the check then still fires for a repo with an *empty*
> `post_create` — it should, since that is the case it was written for."

That is the only decision the reader has. A good reply spends its space there.

## The reference reply

Not a template to match word for word — a demonstration that the target is
reachable.

> `post_create_wired` returns true only if a `post_create:` line contains the
> literal string `install-skills`. A repo that bootstraps another way is told
> every session it has no mechanism, while its mechanism works.
>
> Accept a `# wfctl: bootstrap-handled` marker in the block. Four reachable
> states:
>
> | `post_create` | today | with the marker |
> |---|---|---|
> | contains `install-skills` | quiet | quiet |
> | other bootstrap, no marker | **warns — wrong** | warns |
> | other bootstrap + marker | **warns — wrong** | quiet |
> | empty | warns — right | warns |
>
> Row 4 is the one to confirm: the empty case keeps warning, which is the case
> the check was written for.
>
> `_workmux.py:161-171`, plus a test per row.

Note what it does *not* do: no paragraph on why a marker beats a detector, no
recap of the pfms evidence, no summary of what the issue said.

## Criteria

Each answered yes or no by a human reading the reply cold, without opening #88
first. Any **no** in the first four is a failure regardless of length.

| # | Question | Tests |
| --- | --- | --- |
| J1 | Can I tell what the broken thing is and what it does wrong, without opening the issue? | FR-011 — subject |
| J2 | Is the recommendation in the first two lines? | FR-002 — answer first |
| J3 | Does the reply argue anything #88 already settled? A **yes** here is a failure. | FR-001 — register |
| J4 | Could I act on this without asking a follow-up question? | SC-011, adapted |
| J5 | Are the four reachable states drawn rather than described? | FR-005, FR-005a |
| J6 | If a drawing is present, does its form match the material? | SC-009 |
| J7 | Does the reply surface the empty-`post_create` decision as the open one? | the discriminator |
| J8 | If the prompt asked about **current state** rather than a change, does the reply avoid manufacturing a "what changed"? | FR-004 — genre, SC-010 |

J5 is the specific claim of the form-selection change: this material is
"a property varying across rows", the skill's own *Enumerate real states* rule
already names that shape, and variant C produced the table while F did not.

J8 does not apply to #88, which asks for an implementation. It applies to the
state-question read added to the unscored set — the genre split FR-004 introduces
is otherwise never exercised, because every benchmark task is a change proposal.

J7 is the sharpest single question. Re-arguing the closed decision and missing
the open one is the exact failure #102 was filed for.

## How SC-011 is measured here

Not as written. SC-011 asks whether the reader's next message requests the
subject — a benchmark reply has no next message.

```
observed in the wild (#556)   →  did the reader ask "what hook are we
                                 talking about again"?
observable here (J1, J4)      →  reading this cold, can I name what it is
                                 about, and act, without asking?
```

Same defect, different instrument. Honest as long as it is not reported as the
first.

## Scope of this test

**#88 only.** It is the sole task with a recorded baseline — variant A at 203
prose words, from #102's own comments. The other four issues (#90, #76, #85,
#61) have no per-task baseline and are read unscored, for J5 and J6 only.

Word count is still recorded, and still never reported alone (SC-012). Under
this rubric it is a description of a reply, not a verdict on one.
