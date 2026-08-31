# Phase 0 Research: deployment key metadata

No `NEEDS CLARIFICATION` markers entered this phase. The design session
(`design.md`) and `/speckit.clarify` resolved every unknown, and each factual
claim below was checked against the code or a real command run rather than
inferred. This file records what was decided, why, and what settled it.

## R1 — Where the discoverable-skill switch lives

**Decision**: One `frozenset` constant in `wfctl/cli.py`. No skill file carries a
wfctl-specific frontmatter key.

**Rationale**: `layer-model` already states that `install-skills` owns what lands
in each layer. A per-file switch made that half-false, because a skill file owned
part of the answer. Moving it into the installer makes the code match an accepted
record. It also removes the vendored/owned distinction from the mechanism
entirely, which is what makes #108 fall out for free.

**Alternatives considered**:

- *`metadata.wfctl-deployment` in frontmatter* — the issue's own proposal, and
  spec-legal. Rejected: the project has no YAML parser, so `_skill_deployment()`
  would need indentation-tracking to find a nested key. The spec-compliant shape
  costs more parsing code than the violating one. It also leaves layer authority
  split between two owners.
- *Both — frontmatter for owned skills, a list for vendored ones* — preserves
  locality, but needs a union rule, two mechanisms to document and test, and
  keeps the parser alive for six files.
- *A data file in the bundle (`agents/skills.json`)* — data rather than code, but
  adds a file, a reader and a missing-file branch to handle. Earns its keep only
  if the list grows past bare names.
- *A column on the table in `vendor-upstream-skills.md`* — the record is the
  precedent for where such a fact belongs, but code cannot read markdown, so the
  truth would be duplicated between record and constant.

**Verified**: `_skill_deployment()` has exactly one call site (grep);
`pyproject.toml:16` lists only `typer` and `rich`; no `import yaml` anywhere in
`wfctl/`.

## R2 — No compatibility shim for the removed key

**Decision**: Read nothing from a previously installed skill tree. No dual-read
release, no `doctor` check for the flat key.

**Rationale**: The issue's Compatibility section weighs those two options against
each other, but neither defends against a reachable state. The install loop reads
skills from the package it ships in:

```python
cli.py:1463   src = _bundle.BUNDLE_ROOT / src_rel
cli.py:1487   extra = extra_fn(repo_root, item) if extra_fn else None
```

`item` always comes from `src`. An installed `.agents/skills/` is only ever a
destination — overwritten on the next install, never a source the switch is read
from. The declaration and the code that reads it ship in the same wheel and
cannot disagree.

**Alternatives considered**: *Read both keys for one release* and *read only the
new form, with `doctor` flagging the old* — both discarded once the read path was
traced. They would report or tolerate a state that cannot arise.

**Verified**: read `cli.py:1455-1500`; the only other `BUNDLE_ROOT` read
(`cli.py:1788`) is `install-config`, unrelated.

## R3 — How conformance is enforced

**Decision**: An offline test asserting no non-vendored skill carries a
frontmatter key outside the Agent Skills allowed set. The upstream reference
validator confirms the counts once during implementation but is not a test
dependency.

**Rationale**: Clarify Q1. A manual check leaves the regression invisible — the
next skill to invent a key ships clean until someone runs an external validator
by hand. Shelling out to the real validator would put a network fetch inside
`uv run pytest` and force #60's vendored-exemption policy to be settled here.

**Alternatives considered**: *Manual only* (no guard against recurrence);
*automated with the real validator* (network in the suite, CI flakes when the git
host is down, and it pre-empts #60).

**Verified**: ran the reference validator over all 28 shipped skills. Before: 21
valid, 7 failed — 6 for `deployment`, 1 for the vendored skill's
`disable-model-invocation`. The allowed set it enforces is `allowed-tools`,
`compatibility`, `description`, `license`, `metadata`, `name`.

## R4 — The vendored skill joins the set, with a narrowed claim

**Decision**: Include `i-have-adhd`. State plainly that it becomes loadable on
request, not self-invoking.

**Rationale**: Clarify Q2. Its vendored frontmatter carries
`disable-model-invocation: true`, so membership makes it listed but never invoked
unprompted. wfctl cannot remove that key — `vendor-upstream-skills` forbids
editing a file upstream replaces. #108's stated payload is unprompted
self-correction, so this change delivers the reachable half only.

**Alternatives considered**: *Drop it from the set* — smallest change, but FR-004
and User Story 2 lose their only instance and #108 is untouched. *Add a
wfctl-owned skill layering over it* — the vendor record's prescribed pattern, and
a whole new skill to author; that is #108's work.

**Verified**: read `wfctl/agents/skills/i-have-adhd/SKILL.md:4`.

## R5 — How the existing mirror tests are refounded

**Decision**: The four mirror tests monkeypatch the constant rather than writing
frontmatter into a fixture.

**Rationale**: They build a *synthetic* skill named `native-skill` inside a temp
bundle and mark it in frontmatter. A `frozenset` of real names cannot see it, so
editing the fixture string does not help — the mechanism the tests were written
against is gone. The pattern is already in the file: the autouse `bundle` fixture
does exactly this to a different constant.

**Alternatives considered**: *Point the tests at a real mirrored skill name* —
couples the tests to the production list, so renaming a skill breaks them for the
wrong reason. *Thread the set through as a parameter* — plumbing for one caller.

**Verified**: read `tests/test_install_skills.py:196-250` and
`tests/conftest.py:86-108`.

## R6 — Which documents change

**Decision**: Amend `docs/architecture/layer-model.md`. Add no record; leave
`vendor-upstream-skills.md` alone.

**Rationale**: `knowledge-placement` and `layer-model` between them already
answer where this fact belongs, and #108 said as much — *"applying an answer the
project already gave, not inventing one."* Two sentences in `layer-model` become
false and must be corrected in the same change, or an accepted record describes a
mechanism that no longer exists. `vendor-upstream-skills` needs nothing because
the mechanism stops treating vendored skills specially at all.

**Verified**: read both records; filed the `wfctl arch none` declaration during
design.

## R7 — The mirror stays additive

**Decision**: `.claude/skills/` remains a second copy on top of the agent-neutral
`.agents/skills/`, not a relocation.

**Rationale**: Considered moving skills to `.claude/skills/` for `--agent claude`
instead of copying — mechanically viable, since every command file already
carries a `../skills/` fallback written for exactly that layout. Rejected because
everything in `.claude/skills/` is offered to the model for auto-invocation, so
all 28 skills would become auto-invocable and the `speckit-*` internals would
start firing unprompted. `layer-model` chose against that deliberately. It would
also make `.claude/` non-additive and the base layer conditional.

**Verified**: read `_AGENT_TARGETS` (`cli.py:945-958`) — `claude` installs
commands only; read `wfctl/agents/commands/start-session.md` for the fallback
path.

## Open items carried out of research

None blocking. Two follow-ups are filed rather than resolved here:

- **#110** — `doctor`'s orphan scan never covers `.claude/skills/`, so removing a
  name from the set later leaves a stale copy nothing reports. Not a regression;
  deliberately a second diff.
- **#60** — adopting the upstream reference validator, and the general
  vendored-exemption policy it needs. The offline assertion in R3 does not
  pre-empt that decision.
