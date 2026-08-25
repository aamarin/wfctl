# Review: 27b83ae (`origin/main...73-judgment-rules-section`)

Doc-only diff, 51 insertions / 2 deletions, one file:
`wfctl/agents/skills/conversation-response-shape/SKILL.md`.

## Context checked

- Spec FR-001…FR-009 and SC-001…SC-003 (`spec.md`), issue #73 body.
- `AGENTS.md` layer model — edit lands in `wfctl/agents/` (source), not
  `.agents/` (install output). Correct layer.
- `.agents/` copy byte-identical to source. `.claude/skills/` correctly has no
  copy (no `deployment: skill` in frontmatter — the file's own comment explains
  why).
- No dangling references to the old title `Show, to simplify the description`
  anywhere in the repo.
- 515 tests pass, ruff clean, mypy clean.

## Requirements trace

| FR | Status |
|---|---|
| FR-001 sibling section, framed as re-derivation | met (see WARNING 1 on the framing sentence) |
| FR-002 enumerate real states | met in text; illustration covers half (WARNING 3) |
| FR-003 sections repeat one shape | met |
| FR-004 "the drawing leads" filed under judgment | met |
| FR-005 rule 3 architecture row amended | met, matches issue wording verbatim |
| FR-006 retitle | met |
| FR-007 domain-agnostic examples | met — grep of the new section finds no tool-specific strings |
| FR-008 lives in `conversation-response-shape` | met |
| FR-009 base bundle | met |
| SC-002 zero wfctl strings in new section | met |
| SC-003 architecture row no longer table-first | met |
| SC-001 reader can sort checkable vs judgment from the file alone | **at risk** — WARNING 1 |

## Findings

WARNING  SKILL.md:L210 — "The rules above are checkable" is false about most of
what is above it. Rules 1–3 (answer first, frame in plain language, scale depth)
are the file's *most* judgment-heavy rules; "scale depth to the question" cannot
be decided by inspecting output. The three clauses that follow ("the line is
rendered, the table exists, the columns split") map only to the #72 section
immediately above, so the intent is inferable — but a reader taking the sentence
literally learns the wrong sorting rule, which is exactly what SC-001 measures.
→ Name the section instead of saying "above":
`The three rules under *Show: the drawing is the description* are checkable —`

WARNING  SKILL.md:L231-238 — the exhibit for "the drawing leads" is mis-notated.
`├`/`└` are tree glyphs and conventionally read as *children of* `request`
(parallel alternatives). What is depicted is a sequential middleware chain where
each stage either rejects or falls through — a relationship the tree does not
express. The gloss then claims it "reads left to right in one glance," but the
tree's sequence reads top to bottom. In the one exhibit whose entire thesis is
that the drawing carries structure the prose does not have to, notation
contradicting the structure is the failure the rule exists to prevent — and this
is the shape agents will copy into every downstream repo.
→ Draw the chain along the axis the gloss claims:
```
request ─► auth check ─► rate limit ─► handler ─► response
                │             │
                ▼             ▼
          401 if no      429 if quota
             token           spent
```

WARNING  SKILL.md:L214-224 — "Enumerate real states" makes two claims; the
illustration demonstrates one. The table and its gloss show only the second
("two states that leave identical output are one state reached two ways"). The
first — "a property that varies across every row is a column, not a row" — is
coined shorthand with no worked example, which rule 2 of this same file forbids:
*"Coined shorthand … is not framing — it is more jargon, and needs an example
before it means anything."* A reader cannot act on it as written.
→ Either add a two-line before/after showing rows collapsing into a column, or
cut the first claim and let the rule be about collapsing identical states only.

NIT  SKILL.md:L254-255 — "Same two slots, same order — the reader learns the
shape once and reuses it for every section after" restates L241-242 ("holds the
same slots in the same order — after the first, the reader knows where to look
in the rest") almost word for word. The other two glosses earn their line by
pointing at which cell is doing the demonstrating; this one does not.
→ delete: the code block is self-evident.

## Metric

net: −3 lines possible (the L254-255 gloss).

**Verdict: Approve** — no blockers; the change clearly improves the skill. Three
WARNINGs are each a one- or two-line edit and worth landing before merge, since
this file installs into every downstream repo and its examples are the pattern
agents copy.
