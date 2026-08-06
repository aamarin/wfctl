# Phase 0 Research: update-install-skills-default

Three unknowns entered planning. Two were resolved from source; the third was
resolved by decision with a defined fallback and has since been **validated
against a live Copilot session** — see §1.

## 1. Where should `--agent copilot` write?

**Decision**: `.agents/skills` → `.github/skills/<name>/SKILL.md`, a plain
directory copy.

**Rationale**: `github/spec-kit`'s Copilot integration declares two modes. Its
skills mode targets exactly that path:

```python
# src/specify_cli/integrations/copilot/__init__.py
config = {"folder": ".github/", "commands_subdir": "skills", ...}
registrar_config = {"dir": ".github/skills", "extension": "/SKILL.md"}
```

Its markdown mode (`.github/agents/*.agent.md` plus companion
`.github/prompts/*.prompt.md` plus `.vscode/settings.json`) carries an explicit
deprecation in the same file: *"Copilot legacy markdown mode is deprecated and
will stop being the default in a future Spec Kit release."*

The decisive practical consequence: `.agents/skills/<name>/SKILL.md` is already
the shape the skills layout expects, so the copy needs no frontmatter transform
and no filename rewrite. Issue #5 estimated that transform as the bulk of the
work; choosing this target removes the work rather than implementing it.

**Alternatives considered**:

- `.github/agents/<name>.agent.md` — what issue #5 specifies, citing GitHub's
  own documentation for Copilot CLI custom agents. Rejected as the direction
  being phased out, and it requires the transform: rename to `*.agent.md`,
  rewrite Claude-shaped frontmatter (`disable-model-invocation`,
  `allowed-tools`) into `name`/`description`/tools.
- `.github/prompts/<name>.prompt.md` — the closest semantic match to a slash
  command, since the shims are slash-command wrappers. Rejected: VS Code only,
  nothing for Copilot CLI, and spec-kit treats it as a companion to the
  deprecated mode rather than a target of its own.
- Both surfaces — rejected under the no-new-abstraction gate; roughly doubles
  transform code, manifest entries, and tests for an assistant that is being
  consolidated onto one layout.

**Validated 2026-08-01** (T028) against GitHub Copilot CLI 1.0.63, in a scratch
repo installed with `wfctl install-skills --agent copilot`:

- **Discovery confirmed.** `copilot -p "List the skills available to you"`
  returned 23 of the 25 installed skills by name.
- **Registry-loaded, not file-read.** Asked to use one, the CLI reported
  `● skill(using-wfctl)` and stated it loaded "via the skill registry, not a raw
  file path", then quoted the skill's first instruction correctly. This is the
  distinction that mattered: reading a markdown file that happens to sit in
  `.github/skills` would not have validated anything.

The `.agent.md` fallback is therefore **not needed** and this decision stands.

Two observations from the same session, neither blocking:

- **`disable-model-invocation` is honoured.** `i-have-adhd` carries that key and
  was the one skill deliberately absent from the list. The open question in §2
  below — whether a Claude-specific frontmatter key would cause Copilot to
  auto-invoke a user-triggered skill — is answered: it does not.
- **`agent-brief` was not registered**, though it has ordinary frontmatter and no
  opt-out. Copilot still found it by globbing the filesystem and read it
  correctly, so the content is reachable; it is simply not in the registry.
  Cause unknown — possibly a per-session registry cap. Worth a look if more
  skills go missing, not worth blocking on for one.

## 2. How should the backup cross-attribution be fixed?

**Decision**: make it unreachable by construction — the base layer owns
`.agents/*`, each agent layer owns only its own root — and additionally union
all manifest entries when deciding whether a file is foreign.

**Rationale**: the bug at `cli.py:395` exists because `claude` and `none` both
list `.agents/skills` as a destination, so installing the second attributes the
first's files to itself. Disjoint destinations remove the condition entirely.
`spec-kit` reaches the same conclusion from the opposite direction: its
`multi_install_safe` flag requires "a static, unique agent root and command
directory," enforced by registry tests.

The union is a separate concern that survives the structural fix: ownership of
`.agents/skills` *moves between entries* in this version, so a manifest written
by the old code lists those paths under `claude` while the new code expects them
under `base`. Without the union, the structural fix creates a worse first-run
experience than the bug it replaces.

**Alternatives considered**:

- Union only, keeping overlapping layers — rejected: leaves the shared-destination
  design that caused the bug, so uninstall bookkeeping stays ambiguous.
- One agent per repo, erroring on a second — rejected: kills the
  Claude-and-Copilot-in-one-repo case the Copilot target exists to enable.
- Per-path refcounts in the manifest — rejected under the complexity gate: new
  persistent state to keep correct, for a problem disjoint layers already solve.

## 3. What does the bare install write?

**Decision**: `.agents/skills` **and** `.agents/commands`.

**Rationale**: `.agents/` is the canonical, agent-agnostic form; agent layers are
derived views of it. Shipping only the skills would leave the command
definitions reachable exclusively through an assistant-specific directory, which
is the duplication issue #5 opens with, inverted.

**Known weakness, accepted**: nothing reads `.agents/commands` at runtime. Agent
layers copy from the freshly cloned wf-skills tree, not from the repo's copy, so
it is documentation rather than machinery. Kept because it is the canonical
human-readable form and because aamarin/wfctl#6 may collapse command
wrappers into the skills they wrap, which would settle the question properly.

**Alternatives considered**:

- Skills only (issue #5's literal text) — rejected per the above.
- Neither, with agent layers as the only destination — rejected: leaves a repo
  with no agent-agnostic copy at all, so a repo used by two assistants has two
  copies and no canonical one.

## Resolved: no NEEDS CLARIFICATION markers remain, no open validations

The Technical Context carries no unknowns. The one empirical question — whether
Copilot CLI discovers `.github/skills` — was closed by T028 on 2026-08-01; see
§1. Nothing in this feature now rests on an unverified assumption.
