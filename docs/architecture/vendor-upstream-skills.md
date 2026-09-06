---
status: accepted
---

# Upstream skills are attributed, and layered rather than forked

## Context

Some skills wfctl ships come from outside the project. Editing one in place is
invisible in a way a normal edit is not: the file reads as the project's own,
the suite passes, and the next upstream pull reverts the change without a
conflict, because the edit was never expressed as a difference from anything.

The behaviour then regresses at an unrelated moment, and nothing in the diff
that caused it mentions the skill.

Invisible provenance also costs something before any pull happens. `MANIFEST.in`
grafts `wfctl/agents` into the wheel, so every release distributes these files;
a file that does not say where it came from ships a derivative work under the
project's own `LICENSE`.

## Decision

*Derived* is the class, and *vendored* is one case of it: a vendored skill is a
derived one nobody has edited. The record keeps its slug, and this repo uses
"vendored" in a second, unrelated sense — the skills tree vendored into the wheel
(#47) — so the class name here is "derived", which collides with neither.

A skill taken from another project carries an attribution line as the last line
of its `SKILL.md`, naming the source repository, upstream's licence, and
upstream's copyright holder:

```
Derived from [obra/superpowers](https://github.com/obra/superpowers) (MIT, © 2025 Jesse Vincent).
```

That line is what identifies an upstream-derived skill. It replaces the earlier
rule, which read the presence of a `license:` frontmatter key: six of the seven
skills below carry no such key, so the rule matched one file, and the table
stayed at one entry while six more arrived unnoticed (#213).

Derived today:

| Skill | Upstream |
| --- | --- |
| `brainstorming` | `obra/superpowers` |
| `finishing-a-development-branch` | `obra/superpowers` |
| `i-have-adhd` | `ayghri/i-have-adhd` |
| `receiving-code-review` | `obra/superpowers` |
| `requesting-code-review` | `obra/superpowers` |
| `using-superpowers` | `obra/superpowers` |
| `verification-before-completion` | `obra/superpowers` |

The upstream licence text itself lives in `wfctl/agents/NOTICES.md`, one entry
per upstream. MIT asks for the permission notice and not only the copyright
line, and a footer is not one; `MANIFEST.in` grafts `wfctl/agents` whole, so a
notice at the top of that tree ships with the files it covers, which a root
`NOTICE` would not.

Line, table and notice are all three required, and `test_skill_attribution.py`
fails on any gap between them — a listed skill with no line, a line no row
lists, a row naming an upstream the line does not, or an attributed upstream
with no entry in `NOTICES.md`.

`knowledge-placement` rules out a fact with two homes, and this is the exception
it names, not a breach of it: the line and the row are not the same fact. The
line says where *this file* came from, and it has to be in the file because that
is what ships. The row says which files the project does not own, which is a
fact about the class and belongs to the record governing it.

Keeping the annotation out of the file used to be the answer to *an upstream
pull would drop it*. The check is the better answer: a pull that drops the line
fails the test rather than passing silently.

Prefer layering to editing. To change how a derived skill behaves, add a skill
that layers over it rather than editing it — `conversation-response-shape` is
the worked example, layering ordering rules on top of `i-have-adhd`'s brevity
rules without touching the file underneath.

Six of the seven above were edited in place before this record existed, and they
stay that way (#213). Attribution is owed on a rewritten derivative work exactly
as on an untouched copy, so the line does not depend on how far a file has
drifted — and a file carrying one is not evidence that editing it was fine.

## Owns truth

Upstream owns the derived file's copyright, whatever the local edits. The
project owns the layer above it, and the attribution line is the file's own
statement of the first fact.

The project cannot own an unedited derived file's contents: it does not
control the next version, and a local edit to a file that gets replaced is a
change with no durable home.

## Considered

- Fork and edit — the pull overwrites it, and the loss is silent because the
  fork was never recorded as one.
- Keep a patch and apply it on install — a patch either applies to a moved line
  silently wrong or fails loudly, and installation gains a merge step.
- Reimplement rather than vendor — loses upstream fixes, and the reimplementation
  drifts from the thing it was copied from.
- A root `NOTICE` file instead of in-file lines — one place to maintain, but
  today's packaging ships no root file into the wheel, so the notice would sit
  in the repository and not in the artifact it is owed on.
- Sort the derived skills by how far they have drifted and attribute only the
  close ones — drift is evidence of derivation, not a threshold for it.

## Consequences

Changing a derived skill's behaviour costs a whole new skill file. That
friction is intended: it makes the change visible in the tree, and it survives
the next pull.

A skill arriving from upstream without its line *and* without its row still
arrives unnoticed — that is #213's own failure and the checks do not close it.
What they close is the drift between the two declarations, which is what let the
table read as authoritative while naming one file out of seven. Finding an
undeclared arrival is a diff against upstream, done by hand.

## Log

- 2026-08-28  accepted    — relocated from `AGENTS.md`
- 2026-09-05  amended     — identification moved from the `license:` frontmatter
  key to an attribution line in the file, six superpowers-derived skills added
  to the table, and `i-have-adhd`'s source named (#213)
