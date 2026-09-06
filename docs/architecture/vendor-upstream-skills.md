---
status: accepted
---

# Upstream-derived files are attributed, and layered rather than forked

## Context

Some skills wfctl ships come from outside the project. Editing one in place is
invisible in a way a normal edit is not: the file reads as the project's own,
the suite passes, and the next upstream pull reverts the change without a
conflict, because the edit was never expressed as a difference from anything.

The behaviour then regresses at an unrelated moment, and nothing in the diff
that caused it mentions the skill.

Invisible provenance also costs something before any pull happens. `MANIFEST.in`
grafts `wfctl/agents` and `wfctl/specify` into the wheel, so every release
distributes these files; a file that does not say where it came from ships a
derivative work under the project's own `LICENSE`.

## Decision

*Derived* is the class, and *vendored* is one case of it: a vendored skill is a
derived one nobody has edited. The record keeps its slug, and this repo uses
"vendored" in a second, unrelated sense — the skills tree vendored into the wheel
(#47) — so the class name here is "derived", which collides with neither.

A file taken from another project carries an attribution line naming the source
repository, upstream's licence, and upstream's copyright holder:

```
Derived from [obra/superpowers](https://github.com/obra/superpowers) (MIT, © 2025 Jesse Vincent).
```

In a `SKILL.md` it is the last line. In a shell script it is a `#` comment on
the line after the shebang, where a reader of a script looks — same sentence,
same three facts.

That line is what identifies an upstream-derived file. It replaces the earlier
rule, which read the presence of a `license:` frontmatter key: six of the seven
skills listed when the rule was written carry no such key, so it matched one
file, and the table stayed at one entry while six more arrived unnoticed
(#213).

Derived today:

| Skill | Upstream |
| --- | --- |
| `brainstorming` | `obra/superpowers` |
| `finishing-a-development-branch` | `obra/superpowers` |
| `i-have-adhd` | `ayghri/i-have-adhd` |
| `idea-refine` | `addyosmani/agent-skills` |
| `receiving-code-review` | `obra/superpowers` |
| `requesting-code-review` | `obra/superpowers` |
| `speckit-analyze` | `github/spec-kit` |
| `speckit-checklist` | `github/spec-kit` |
| `speckit-clarify` | `github/spec-kit` |
| `speckit-constitution` | `github/spec-kit` |
| `speckit-implement` | `github/spec-kit` |
| `speckit-plan` | `github/spec-kit` |
| `speckit-specify` | `github/spec-kit` |
| `speckit-tasks` | `github/spec-kit` |
| `using-superpowers` | `obra/superpowers` |
| `verification-before-completion` | `obra/superpowers` |

`speckit-delivery-plan` and `speckit-orchestrate` are absent because they are
wfctl's own: both score 0% against every spec-kit command template. The prefix
is a naming convention, not a provenance claim, and the eight above were
identified by content — `speckit-specify` carries no `source:` key and would
have been missed by any rule reading frontmatter (#216).

`wfctl/specify/` is derived from the same upstream and is a second table
because it holds no skills. The scripts carry the attribution line as a comment
on the line after the shebang; the templates carry nothing, because
`create-new-feature.sh` runs `cp` on `spec-template.md` to make a project's
`spec.md`, so a line in a template would assert GitHub's copyright over every
spec, plan and task list the runtime generates. Their notice is
`wfctl/specify/templates/NOTICES.md`, which names each of them.

| File under `wfctl/` | Upstream |
| --- | --- |
| `specify/scripts/bash/check-prerequisites.sh` | `github/spec-kit` |
| `specify/scripts/bash/common.sh` | `github/spec-kit` |
| `specify/scripts/bash/create-new-feature.sh` | `github/spec-kit` |
| `specify/scripts/bash/setup-plan.sh` | `github/spec-kit` |
| `specify/scripts/bash/update-agent-context.sh` | `github/spec-kit` |
| `specify/templates/agent-file-template.md` | `github/spec-kit` |
| `specify/templates/checklist-template.md` | `github/spec-kit` |
| `specify/templates/constitution-template.md` | `github/spec-kit` |
| `specify/templates/plan-template.md` | `github/spec-kit` |
| `specify/templates/spec-template.md` | `github/spec-kit` |
| `specify/templates/tasks-template.md` | `github/spec-kit` |

`specify/templates/github-issue-template.md` is the one file in that tree the
project owns: it describes `/speckit.decompose`, which spec-kit has no
counterpart for.

A skill added later is declared when it is added, by whoever adds it: a file
taken from elsewhere gets its line and its row in the same change that brings it
in, and its upstream gets an entry in `NOTICES.md` if it has none. There is no
later pass that sweeps for missed ones — #213 is what that pass costs when it is
deferred, and #216 and #218 are what it missed. The check below holds the three
together from then on; what it cannot do is notice a file that arrived declaring
nothing.

The upstream licence text itself lives in a `NOTICES.md` per grafted tree, one
entry per upstream: `wfctl/agents/NOTICES.md` and
`wfctl/specify/templates/NOTICES.md`. MIT asks for the permission notice and not
only the copyright line, and a footer is not one; `MANIFEST.in` grafts
`wfctl/agents` and `wfctl/specify` whole, so a notice inside a tree ships with
the files it covers, which a root `NOTICE` would not.

The specify tree's copy sits one level down, in `templates/`, because that is
where the files it covers can be reached from. `install-skills` mirrors
`specify/scripts` and `specify/templates` into a project and nothing above them,
so a notice at the top of `wfctl/specify/` would ship in the wheel and never
arrive in a repository wfctl installed the derived templates into. The scripts
need no such reach: their line travels inside them.

Line, table and notice are all three required, and `test_skill_attribution.py`
fails on any gap between them — a listed file with no line, a line no row
lists, a row naming an upstream the line does not, or an attributed upstream
with no entry in `NOTICES.md`. The templates are the one case where the notice
stands in for the line, so the same pair runs between the template rows and
`wfctl/specify/templates/NOTICES.md` instead: a row that file does not name, or
a file it names with no row, fails the same way.

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

Most of the files above were edited in place before this record existed, and
they stay that way (#213, #216). Attribution is owed on a rewritten derivative
work exactly as on an untouched copy, so the line does not depend on how far a
file has drifted — `specify/scripts/bash/common.sh` is 20% upstream and
`specify/templates/constitution-template.md` is all of it, and both are listed.
A file carrying a line is not evidence that editing it was fine.

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
- An attribution line in the templates, as the skills carry one — the templates
  are copied verbatim to become a project's `spec.md`, `plan.md` and
  `tasks.md`, so the line would arrive as a copyright claim on writing GitHub
  had no hand in.
- `wfctl/specify/NOTICES.md`, at the top of the tree, mirroring
  `wfctl/agents/NOTICES.md` — symmetrical, and out of reach: the install
  targets are `specify/scripts` and `specify/templates`, so it would ship in
  the wheel and never reach a project.

## Consequences

Changing a derived skill's behaviour costs a whole new skill file. That
friction is intended: it makes the change visible in the tree, and it survives
the next pull.

A derived file arriving from upstream without its line *and* without its row
still arrives unnoticed — that is #213's own failure and the checks do not
close it. What they close is the drift between the two declarations, which is what let the
table read as authoritative while naming one file out of seven. Finding an
undeclared arrival is a diff against upstream, done by hand.

## Log

- 2026-08-28  accepted    — relocated from `AGENTS.md`
- 2026-09-05  amended     — identification moved from the `license:` frontmatter
  key to an attribution line in the file, six superpowers-derived skills added
  to the table, and `i-have-adhd`'s source named (#213)
- 2026-09-06  amended     — the eight `speckit-*` skills and eleven files under
  `wfctl/specify/` added, with `wfctl/specify/templates/NOTICES.md` as the
  second tree's notice and the templates covered by it rather than by a line
  (#216)
