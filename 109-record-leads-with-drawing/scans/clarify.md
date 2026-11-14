# Clarify scans for #109

## Session 2026-09-16

- Verdict: satisfied
- Scanned: spec.md
- Asked: 4 · Answered: 4 · Outstanding: 0 · Deferred: 1
- Detail: /Users/andremarin/Development/wfctl-specs/109-record-leads-with-drawing/spec.md § Clarifications

### Coverage

| Category | Status |
| --- | --- |
| Functional Scope & Behavior | Resolved |
| Domain & Data Model | Resolved |
| Interaction & UX Flow | Clear |
| Non-Functional Quality Attributes | Deferred |
| Integration & External Dependencies | Resolved |
| Edge Cases & Failure Handling | Clear |
| Constraints & Tradeoffs | Clear |
| Terminology & Consistency | Resolved |
| Completion Signals | Clear |
| Misc / Placeholders | Clear |

### Findings

- **Terminology & Consistency** — the spec required "the drawing as a required
  section" without naming the section, and three words for the thing were in
  circulation: `design-levels` says sketch, #109 says drawing, the proposed
  frontmatter key says diagram.
  Q: What is the drawing's section called? → A: `## Boundary`, unchanged.
  Basis: `pipeline-state-is-one-payload` and `session-state-is-re-derived` both
  carry `## Boundary` with a mermaid block, added by `1e7fa41`, and both are
  `accepted` — so their bodies are frozen by the rule in
  `architecture-decisions/SKILL.md`.
  Decided against **rename to `## Drawing`**: matches #109's own wording, and it
  would leave two frozen records carrying drawings under a heading the check no
  longer looks at. The rename is unavailable rather than merely worse.
  Decided against **rename to `## Diagram`**: same defect, plus it collides with
  the `diagram:` frontmatter key, so a reader would meet the same word naming a
  kind in one place and a section in another.

- **Domain & Data Model** — the spec said a record must carry a drawing and
  never said what one is. The corpus makes this material: records hold 31 fenced
  blocks with no language tag, and only 2 tagged `mermaid`, so an untagged fence
  is as often a command or a sample of output as it is a picture.
  Q: What counts as a drawing? → A: any non-empty fenced block under
  `## Boundary`; its content is never classified.
  Basis: measured over `docs/architecture/*.md` by walking the fences. Scoping to
  the section removes the classification problem rather than solving it, which is
  available only because the previous finding fixed the section name.
  Decided against **a block containing box-drawing characters or tagged
  mermaid**: it is the rule that matches what the corpus actually looks like
  today, and it fails on a legitimate drawing made of plain ASCII — and on a code
  sample that happens to contain a pipe.
  Decided against **mermaid specifically**: it is what a record read on a hosting
  site renders best, and it would reject the ASCII drawings that 20 records
  already carry, which is a migration this feature explicitly does not do.

- **Functional Scope & Behavior** — `design.md` recorded as open where the label
  report surfaces, and `spec.md` carried an assumption in its place.
  Q: Where does the label-disagreement report surface? → A: with the existing
  record findings, which `doctor` prints.
  Basis: `cli._check_arch_records` already collects `_arch.validate`'s findings,
  prints `⚠` for a warning, holds the exit code only for an error, and prints the
  records directory underneath. Every property the label report needs is there.
  Decided against **printing it at accept beside the refusals**: it puts the
  warning where a person is definitely reading, which is a real advantage, and it
  loses because accept is a refusal surface — a warning there either reads as a
  refusal that did not happen, or trains a reader to skim the refusals.
  Decided against **both**: no new property, and two emitters of one finding is
  the copy that stops agreeing with itself.

- **Integration & External Dependencies** — the spec's scope was written from
  this repository's corpus, and the skills ship to other repositories whose
  records this would also bind.
  Q: Does this bind records in repositories that install wfctl? → A: yes, by the
  same rule — it turns on a record's status, not on which repository holds it.
  Basis: `the-drawing-is-required-at-acceptance` scopes the requirement to the
  `proposed` → `accepted` edge, and that edge exists identically in every repo.
  No second policy is needed, and the frozen-body rule protects a consuming
  repo's accepted records for the same reason it protects these five.
  Decided against **checking only wfctl's own records**: it is the conservative
  option and it would need a way to tell wfctl's arch root from anyone else's,
  which is a distinction the tool does not make anywhere else.
  Decided against **an opt-in manifest key**: it gives a project control over its
  own gate, which is defensible, and it loses on what it would cost — a
  repository that never sets the key gets the defect this feature exists to fix,
  silently, forever.

### Deferred

- **Non-Functional Quality Attributes** — performance, scale, availability and
  security are unaddressed in the spec, and no question was asked about them. The
  work reads text files in one directory that holds 38 of them, at one moment a
  person runs a command by hand. There is no threshold worth writing down, and
  inventing one to fill the category is the thing the method warns against.
