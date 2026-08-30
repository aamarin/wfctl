# Phase 0 Research: reply over-explains

Three unknowns carried from `spec.md`. All resolved; no `NEEDS CLARIFICATION`
remains.

---

## 1. How the reply-quality criteria get measured

**Decision**: judge against a written rubric — `judgment-test.md`, seven yes/no
questions on #88 — scored by hand. Do not build a harness. Do not report word
count as a verdict.

**The original measurement does not measure what this feature is for.** Both
recorded axes count presence, not correctness: prose word count cannot separate
#556's forty-word failure from a success, and "did a table appear" counted #61's
unwarranted table as a hit. design.md's two headline claims — *every variant
carrying a register rule killed it*, *the table habit is entirely rule-caused* —
are presence claims, and neither can validate the design on its own. The rubric
is written before any run so it cannot be fitted to the output.

The spec's SC-001 (prose word count), SC-009 (form matches material) and SC-011
(zero "what X are we talking about" follow-ups) are the only criteria that need
anything beyond reading the diff. SC-011 is the awkward one — it reads the
*reader's next message*, not the reply.

**Rationale**: SC-011 cannot be automated without a reader. An agent scoring its
own reply for "would a human have to ask what this is about" is the same
judgment that produced the failure. A human read of five replies is minutes of
work and is the only measurement that is actually valid.

The baseline is recoverable even though the original replies are gone. What
survives is what is needed:

| Recorded on #102 / design.md | Lost with the scratchpad |
| --- | --- |
| Prose word counts per variant (A 203, B 103, C 120, D 91, E 152) | The reply texts themselves |
| Which of five tasks produced a table, per variant | Intermediate variant files |
| The C-vs-F table/literal-output tallies (3/5 vs 0/5) | |
| The two live exchanges, #99 and #556, quoted in design.md | |

The five fixed tasks are open issues — #88, #90, #76, #85, #61 — and are
re-runnable as-is. That is enough to re-derive a baseline for the tasks that
matter without re-running variant A.

**Alternatives considered**:
- *A scored harness.* Rejected: SC-011 needs a human, so a harness would cover
  the two axes that were already the weak ones and skip the one that caught the
  #556 failure.
- *Re-run all six variants.* Rejected: the variants are the design's evidence
  and the design is settled. The only open experimental question is SC-009,
  which needs two arms (with and without the selection table), not six.
- *Skip measurement, ship on the design's evidence.* Rejected for SC-009
  specifically — it is the one claim in the spec that has never been run, and
  `spec.md` already flags it as inferred from two cases.

**Scope**: #88 is scored, because it is the only task with a recorded baseline
(variant A, 203 prose words, recovered from #102's comments). #90, #76, #85 and
#61 are read unscored for the form questions J5/J6. Treating one task's number as
a five-task benchmark would overstate what is known.

**Consequence for tasks**: one task is "run the rubric on #88", and it is
sequenced *after* the edit. It validates; it does not gate.

---

## 2. Where each rule goes, and the resulting section order

**Decision**: the two new rules join the numbered precedence list; the two new
form instructions join the drawing section. No new top-level section.

The skill already has a three-rule precedence list ("Answer first", "Frame in
plain language", "Scale depth"). The subject rule belongs in that list because
it governs content and order, and because its whole point is that a reply can
satisfy the other rules and still fail — which is only legible if it sits beside
them (FR-011a).

```
 §Precedence            1. Answer first
                        2. Frame in plain language
                        3. Scale depth to the question
                        4. Establish the subject        ← NEW (FR-011)
                        5. Nothing that needs no
                           decision gets a paragraph    ← NEW (FR-001)

 §1 … §3                unchanged bodies, except:
   §3 "Scale depth"       − "Terseness is the default, not a ceiling"  (conflict 3)

 §4 Establish the       ← NEW body: the 3-row precedence table, the
    subject               observable check (FR-011b)

 §5 Register            ← NEW body: the tell, the boundary against rule 1

 §Show                  ~ "the artifact does not replace…" → caption  (conflict 2)
                        ~ "reach for it when… getting long" → the
                          hold-a-set/location/count/branch test        (conflict 1, FR-005)
                        + form-selection table                         (FR-005a)
                        + reply composition, two genres                (FR-004, FR-004a)
                        ~ wfctl-end example abstracted                 (FR-006, closes #80)

 §Judgment rules        unchanged
 §Untangling            unchanged — design.md preserves it deliberately
 §Three surfaces        unchanged
 §Failure modes         + two entries for the new rules
 §Pre-send check        + two questions
```

**Rationale**: appending as rules 4 and 5 rather than inserting them earlier
preserves every existing cross-reference. Counted in the file, not assumed —
seven numeric references, no test covering any of them:

| Refers to | Lines |
| --- | --- |
| This skill's own rules | 100 (twice, "rule 3"), 176 ("rule 1") |
| `i-have-adhd`'s rules | 39, 47, 60, 71, 112 |

Renumbering would silently break the first row, and prose is not something the
suite checks.

Worth flagging for the edit: the file already writes both kinds as "rule N", and
disambiguates only by whether `i-have-adhd` is named in the sentence. Two more
own-skill rules makes that collision more likely, so the new text should say
"this skill's rule 4" or reference by name ("the subject rule") rather than
adding bare numerals.

Ordering *within* the list is deliberate: subject before register. Establishing
the subject is a precondition for judging whether material needs a decision — you
cannot tell whether a side-note is volunteered until you know what it is about.

**Alternatives considered**:
- *A new top-level section for each rule.* Rejected: the precedence list exists
  precisely to state which rule wins, and a rule outside it has no stated
  precedence.
- *Fold the subject rule into rule 2 (plain language).* Rejected — this is the
  confusion the #556 evidence exists to prevent. Reply 2 used plain language and
  still failed. Two obligations, two rules.
- *Renumber so the new rules sit next to the ones they resemble.* Rejected: see
  the cross-reference breakage above.

---

## 3. What #556's two skills need from this feature

**Decision**: nothing beyond FR-007's pointer rule, which is already specified.
No task in this feature touches either skill.

**Rationale**: `speckit-delivery-plan` and `finishing-a-development-branch` will
each gain a one-line obligation — *a body leads with a figure* — at the point
where the body is written. Under FR-007 they point at
`conversation-response-shape` for which figure and when, and restate nothing. So
this feature's only obligation to them is to *be* the single owner, which
FR-005a and FR-007 already establish.

Checked, not assumed: both skills live under `wfctl/agents/skills/`, and neither
carries `license:` in its frontmatter. `vendor-upstream-skills` records
`i-have-adhd` as the only vendored skill, so neither of #556's targets raises the
vendoring constraint.

**Alternatives considered**:
- *Land the two one-liners here.* Rejected: they belong to #556, and folding them
  in would make this PR span two issues. `CLAUDE.md`'s "one PR = one issue" is
  the rule; `/speckit.decompose` is where a genuine split gets raised.
- *Wait for #556 before shipping this.* Rejected — the dependency runs the other
  way. #556's pointers need this feature's selection table to exist; this feature
  needs nothing from #556.

---

---

## 4. How much of the skill #80 actually touches

**Not planned as an unknown — surfaced while testing the C-6 check.** Recorded
because it changes the size of FR-006.

design.md describes #80 as "its `wfctl end` example is a defect". Run against the
file, the check finds wfctl vocabulary in **two** fenced example blocks, not one:

| Block | Section | What it is |
| --- | --- | --- |
| line 207 | *Show: the drawing is the description* | the `wfctl end` / `Session closed` literal-output example — the one #80 names |
| line 292 | *Untangling compressed explanations* | the worked example, built entirely on `wfctl status`, `wfctl verify` and `implement-complete.md` |

The second is the larger job. It is not a passing mention — the whole example
is a wfctl scenario, and abstracting it means rewriting the example rather than
swapping an identifier. It is also the example design.md deliberately preserves
for its decision-trace value, so the rewrite has to keep that shape.

**Consequence for tasks**: FR-006 is two edits of unequal size, and the second is
the largest single piece of prose work in this feature. Sequence it on its own.

The check that found this is `awk '/^```/{f=!f} f && /wfctl/'` — four hits across
the two blocks today, zero when FR-006 is done. Red now, green at the end; it is
the FR-012 test for C-6.

## Carried forward, not resolved

Two items the spec flags that research cannot close, recorded so planning does
not mistake them for settled:

- **Whether the new rules survive session decay.** Unmeasurable in this feature —
  every piece of evidence was gathered in a fresh context. #85 owns it. This
  feature adds ~50 lines to the file whose rules already decay, which the plan
  budgets but does not fix.
- **Whether stating the subject rule makes it fire.** It is checkable after the
  fact from the reader's follow-up, which no other rule here is. Nothing has
  tested whether it fires unprompted; SC-011 is the check, and it runs after the
  edit.
