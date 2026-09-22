---
status: proposed
---

# The template-placeholder check reads its own projection, and `quoted_out` blanks HTML comments for everyone else

## Context

`quoted_out` is the projection every structural read in `_evidence` matches
against: markdown with the parts that only *illustrate* syntax blanked out, so a
document quoting a heading does not read as carrying one. Until #419 it blanked
two shapes, fenced blocks and inline spans.

A third shape was missing. Commenting a section out is how an author parks it
without losing the text, and a heading parked inside `<!-- -->` was read as a
heading the document carried. That is a wrong verdict in two places at once: a
record whose only `## Diagram` sat in a comment was reported as a level-3 record
misfiled at the root, and a `spec.md` whose sections were all commented out read
as written.

The pressure is that blanking comments is wrong for exactly one reader.
`TEMPLATE_PLACEHOLDER` — the string that tells an untouched template copy from a
written artifact — ships *inside* an HTML comment in both templates, and is
matched against `quoted_out` output. Widening the projection makes every
untouched template read as written work, which is the failure
`TEMPLATE_PLACEHOLDER` exists to prevent, met from the other side.

Constrained by `pipeline-state-is-one-payload` (accepted): whatever answers this
is read once and carried on `Evidence`, not recomputed per view.
`419-placement-reads-the-tiers-by-name` settled that the placement check reaches
`missing_sections` and `quoted_out` rather than growing a matcher of its own,
and that record's argument is what rules out fixing this locally.

## Verified

- `_evidence.py:310` — `TEMPLATE_PLACEHOLDER = "ACTION REQUIRED"`. The
  comment block above it stated the dependency outright before this change —
  the constant lives in an HTML comment, `quoted_out` left those alone, "and
  that is deliberate" — which is what made widening the projection a decision
  rather than an oversight. This change rewrites that comment.
- `plan-template.md:14-18` — the string sits inside a comment whose opening
  and closing markers are each on their own line. `spec-template.md:70-73` is
  the same shape. The multi-line form is the one that matters: a heading matches
  at the start of a line, so a marker and a heading on one line never counted.
- `_evidence.py:1106` and `:1175` — `specify` and `plan` each read the
  placeholder before anything structural, and both matched
  `TEMPLATE_PLACEHOLDER in ev.spec_text` / `ev.plan_text` before this decision.
- `_evidence.py:990` — `build_evidence` is the one place `quoted_out` is
  applied to `spec.md` and `plan.md`, so a second projection has one call site
  per artifact and not one per predicate.
- `_md.py:15` — "This yields per-line state and projects nothing. Each caller
  wants a different shape from the same walk." The walker states that the
  projection is the caller's, which is where a comment cut has to live.
- `tests/test_pipeline_sections.py:664` and `:685` — two tests written before
  #419 assert that a verbatim plan template does not read `done` and a verbatim
  spec template routes to `specify` rather than `clarify`. Both fail against a
  single comment-blanking projection, and both pass again under this decision.

## Assumed

- That no artifact wants a *third* answer from this projection. Two settings
  cover every caller in the tree today; a third question would make the boolean
  parameter the wrong shape and ask for named projections instead.
- Falsified by: a caller needing fences kept, or comments kept while spans are
  cut. Either arrives as a second boolean, which is the tell.

## Direct baseline

Leave `quoted_out` as it was and cut comments inside the placement check alone:
`_check_record_placement`'s `readable()` blanks `<!-- -->` in the text it has
just read, before handing it to `missing_sections`. Ten lines, one function, no
new field on `Evidence` and no parameter on a shared helper.

## Decision

The projection moves into `_blanked(text, *, comments: bool)`, and the two
readers take one setting each. `quoted_out` is `comments=True` and stays the
name every structural read calls — the placement check, `specify`'s section and
marker reads, `plan`'s sections, the task tally. `_still_the_template(text)` is
`comments=False`, and is the only caller that keeps them.

The blanking runs fences first, then inline spans, then the comment cut. Each
pass removes text that the next one would otherwise read as syntax, so a
document that only *illustrates* `<!--` never opens one — which is the contract
`quoted_out` already stated for fences, carried to the shape this decision adds.
Two consequences follow and both are deliberate: a `-->` quoted inline no longer
closes a comment that is genuinely open, and an unpaired backtick before `<!--`
still opens one.

`Evidence` carries `spec_is_template` and `plan_is_template`, computed in
`build_evidence` from the raw file text. The predicates read the boolean rather
than matching the constant, so the projection a verdict rests on is chosen once,
beside the read, rather than implied by which field a predicate reached for.

The verdict is carried as a boolean and not as the second projection's text. The
text would answer other questions too, and every other question in this module
wants comments cut.

## Diagram

```
             baseline                             decision

stable  ┌──────────────────┐              ┌──────────────────────┐
        │ _md.walk         │              │ _md.walk             │
        └────────┬─────────┘              └──────────┬───────────┘
                 │ per-line fence state              │ per-line fence state
        ┌────────▼─────────┐              ┌──────────▼───────────┐
        │ quoted_out       │              │ _blanked(comments=)  │
        │  fences + spans  │              └───┬──────────────┬───┘
        └──┬────────────┬──┘                  │ True         │ False
           │ calls      │ calls        ┌──────▼─────┐  ┌─────▼──────────────┐
           │            │              │ quoted_out │  │ _still_the_template│
   ┌───────▼──────┐ ┌───▼──────────┐   └──┬─────────┘  └─────┬──────────────┘
   │ placement    │ │ build_       │      │ calls            │ calls
   │  check       │ │  evidence    │   ┌──▼───────────┐ ┌────▼─────────────┐
   │  cuts its    │ │  spec_text   │   │ placement    │ │ build_evidence   │
   │  own         │ │  plan_text   │   │  check       │ │  spec_text       │
   │  comments    │ │              │   └──┬───────────┘ │  spec_is_template│
   └───────┬──────┘ └───┬──────────┘      │             └────┬─────────────┘
           │ reads      │ reads           │ reads            │ reads
══ inference re-derives from artifacts (session-state-is-re-derived) ══
           ▼            ▼                 ▼                  ▼
volatile ┌─────────┐ ┌──────────┐   ┌─────────┐       ┌──────────┐
         │ arch    │ │ spec.md  │   │ arch    │       │ spec.md  │
         │ records │ │ plan.md  │   │ records │       │ plan.md  │
         └─────────┘ └──────────┘   └─────────┘       └──────────┘
```

The graphs differ by where the comment question is answered. In the baseline it
is answered once, inside the one check that noticed it, and `quoted_out` goes on
returning a projection that is wrong for every other caller — so `spec.md` with
its sections commented out still reads as written, and the next reader who finds
that writes a second local cut. In the decision it is answered where the
projection is built, and the one reader that wants the opposite answer says so
by name at the point it asks.

## Considered

- **The baseline, a local cut in the placement check** — smallest, and it fixes
  the finding that was reported. It loses on reach rather than on fault: the
  same misread is live in `specify`, `plan` and the task tally, which read the
  same projection over documents just as likely to carry a parked section. It
  also re-creates a private matcher for a shape `quoted_out` already owns, which
  `419-placement-reads-the-tiers-by-name` rejected by name for `_md`'s reason.
- **Blank comments in `quoted_out` and leave the placeholder check alone** —
  zero new surface, and it is what the working tree held when this decision was
  put. Rejected because it is wrong rather than costly: `ACTION REQUIRED` lives
  in a comment, so every untouched template reads as written work, and
  `specify` routes a file nobody has written to `/speckit.clarify`, which cannot
  write one.
- **Move `TEMPLATE_PLACEHOLDER` out of the templates' comments** — the
  projection stays single, and the marker becomes visible prose. Rejected
  because the templates are spec-kit-derived: an in-place edit is reverted by
  the next upstream pull with no conflict to notice, and the check would fail
  open from then on.
- **Carry the second projection's text on `Evidence` instead of the verdict** —
  symmetric with `spec_text`, and no new derived field. Rejected because a text
  field is reachable by the next question someone asks of `Evidence`, and every
  other question wants comments cut. The boolean makes that misuse impossible;
  `has_markers` is the same shape for the same reason.
- **Named projections rather than a boolean parameter** — `quoted_out` and
  `quoted_out_keeping_comments` as two functions over a shared walk. Equally
  sound, and rejected only on count: two settings do not need a vocabulary, and
  the parameter is where a third would become visible as pressure.

## Consequences

`Evidence` grows two fields, and every hand-built fixture changes with it. The
positional construction in `tests/test_evidence.py` is deliberate for exactly
this — it breaks rather than defaulting, which is how a field added to the
dataclass is forced through the builder.

A caller of `quoted_out` now gets comments blanked whether it thought about them
or not. That is the right default and it is a silent change of behaviour for any
future reader who wanted them: the parameter is on `_blanked` and not on
`quoted_out`, so reaching the other setting means going through
`_still_the_template` or adding a second named reader — visible either way.

The two projections can drift apart in one direction without any test noticing:
a shape added to `_blanked` under `comments=True` only. Nothing structural
prevents it, so the verification below pins the disagreement itself rather than
only the behaviour either setting produces.

`_arch._headings` is a second projection of the same files and it blanks fences
alone, so after this change the placement check and `_log_bounds` / `supersede`
disagree about a heading parked in a comment. The reachable case is narrow — a
`## Log` inside a comment would take an appended transition — and it is left
open here rather than widened in passing, because `_arch`'s readers write to a
record and this one only reads.

## Verification

- The two pre-existing template tests pass unchanged. They are the proof the
  split worked, because they are what a single projection breaks.
- A test that a `spec.md` whose sections are all inside `<!-- -->` reads
  `in_progress`, and one that a comment closed on the same line leaves the rest
  of the file intact — the guard on a scanner that would swallow to EOF.
- A test asserting the two settings disagree about a verbatim template:
  `_still_the_template` true, and the marker absent from `quoted_out`. This is
  the drift named in Consequences, and it is the only assertion that fails on
  the day someone widens `quoted_out` without asking what the other reader
  wanted.
- One test per ordering pass: a marker quoted in an inline span does not open a
  comment, and one carried inside a fenced block does not either. Both were
  written against a mutation, because a fixture quoting a marker *pair* balances
  it and passes against the defect.
- A test that a record whose only `## Diagram` sits in a comment draws the `⚠`
  row and exit 0 rather than an error row.
- `uv run wfctl doctor` over this repository prints no placement finding, and
  `wfctl status` over a written spec still reads its sections.

## Log

- 2026-09-22  proposed  — a panel reviewer found the comment misread, and the
  first fix for it broke the template check on its way past. Andre chose this
  over a local cut in the placement check and over shipping the misread unfixed.
  A second panel then found that the cut ran before inline spans were blanked,
  so a quoted `<!--` opened a real comment — the same class of defect this
  record exists to close, arriving by a new route. The ordering above is that
  finding's answer.
