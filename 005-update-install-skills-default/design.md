# install-skills: stop assuming

Closes #5. Blocks #6.

## Problem Statement

How might we make `wfctl install-skills` install what a repo actually needs, instead of assuming every repo runs Claude and tracks issues on GitHub?

Today a bare `install-skills` writes `.claude/commands/` shims whether or not Claude is in use, and (as of the current branch tip) writes a GitHub tracker config without asking. Consuming repos end up with the same skills in two places and a tracker they may not use — the PFMS cleanup that prompted #5.

## Recommended Direction

**Split installation into a base layer and optional agent layers, and ask before writing anything repo-specific.**

The base layer is canonical and agent-agnostic: `.agents/skills` + `.agents/commands`, plus the `.specify` runtime. Every install writes it. An agent layer is additive and owns a unique root — `.claude/`, `.bob/`, `.github/` — so no two manifest entries ever write the same path.

That structure is what makes the `cli.py:395` backup cross-attribution disappear rather than get patched: the bug exists because `claude` and `none` both claim `.agents/skills`. Once the base owns it and agent layers own only their own roots, there is nothing to cross-attribute. It matches how `github/spec-kit` handles the same problem (`multi_install_safe` requires "a static, unique agent root and command directory").

The second half is consent: bare install prompts once for the GitHub tracker when a human is present, never writes one in CI or a workmux hook, and points at both routes back when declined. After a base-only install it names the agents that need native paths. Same theme as the default flip — the tool stops deciding for you and tells you how to decide.

## Target Layout

```python
# Always installed — canonical, agent-agnostic.
_BASE_TARGETS = [
    (".agents/skills",   ".agents/skills"),
    (".agents/commands", ".agents/commands"),
]

# Only with --agent X. Each owns a unique root; no two overlap.
_AGENT_TARGETS = {
    "none":    [],
    "codex":   [],  # notice-only; see below
    "claude":  [(".agents/commands", ".claude/commands")],
    "bob":     [(".agents/skills", ".bob/skills"), (".agents/commands", ".bob/commands")],
    "copilot": [(".agents/skills", ".github/skills")],
}
```

`claude` keeps its `_AGENT_SKILL_EXTRAS` hook mirroring `deployment: skill` items to `.claude/skills`. `_RUNTIME_TARGETS` (`.specify/*`) stays repo-level and unchanged.

### Manifest and uninstall semantics

- The base layer records under the manifest key `base`, a sibling of the per-agent entries and of `tracker`. Everything that iterates agents (`doctor`, `uninstall-skills`, the agent list) skips `base` the way it already skips `tracker`.
- `--agent none` and `--agent codex` write no agent entry at all — only `base`. So `uninstall-skills --agent codex` reports nothing to remove rather than failing on a missing entry.
- `uninstall-skills --agent claude` now removes **only** `.claude/*`; `.agents/*` survives because `base` still owns it. That is a behavior change: today it takes the skills with it. `uninstall-skills --agent base` removes the base layer.
- `uninstall-skills` keeps its current `--agent claude` default. Changing it is out of scope; the flag is explicit in every documented invocation.

Item counts, measured on this repo:

| Layer | Contents | Items |
|---|---|---|
| base | 25 skills, 23 commands, 8 runtime, 1 tracker | 57 (56 if the tracker is declined) |
| `+ claude` | 23 command shims, 3 native skill mirrors | +26 |
| `+ bob` | 25 skills, 23 commands | +48 |
| `+ copilot` | 25 skills | +25 |

## Key Assumptions to Validate

- [x] **Copilot CLI discovers `.github/skills/<name>/SKILL.md`.** Inferred from spec-kit's `CopilotSkillsIntegration`, not from GitHub's docs. **Validated 2026-08-01 against Copilot CLI 1.0.63**: a scratch repo installed with `--agent copilot` had 23 of 25 skills listed by name, and asked to use one the CLI reported `● skill(using-wfctl)`, confirming it loaded "via the skill registry, not a raw file path". That distinction was the point — reading a markdown file that happens to sit in `.github/skills` would not have validated anything. The `.agent.md` fallback is not needed. One skill (`agent-brief`) was absent from the registry despite ordinary frontmatter; Copilot still found and read it by globbing. Cause unknown, not blocking.
- [x] **wf-skills SKILL.md frontmatter is compatible with Copilot skills.** **Validated in the same session, and the risk did not materialise**: `disable-model-invocation` is *honoured*, not ignored. `i-have-adhd` carries it and was the one skill deliberately absent from Copilot's list, so a skill meant to be user-triggered will not fire on its own there.
- [ ] **`.agents/commands` in the base layer earns its place.** Nothing reads it: agent layers copy from the fresh wf-skills clone, not from the repo copy, so it is documentation rather than machinery. Kept because it is the canonical human-readable form and because aamarin/wfctl#6 may collapse commands into skills entirely. **Test:** none needed now; wfctl#6 settles it, and this feature is deliberately not blocked on it.

## MVP Scope

**In:**

1. `_BASE_TARGETS` split out; `_AGENT_TARGETS` holds only agent-specific destinations; `--agent` defaults to `none`.
2. Manifest gains a `base` entry alongside per-agent entries. `wfctl doctor` and `uninstall-skills` skip it the way they already skip `tracker`.
3. **Foreign-file detection unions all manifest entries.** Required for migration: a repo installed today records `.agents/skills/*` under `claude`; after this change those paths belong to `base`, and without the union the first upgrade backs up all 25 skills and prompts to overwrite them. One-line change to how `prior_items` is built.
4. `--agent copilot` → `.agents/skills` → `.github/skills`. Plain directory copy, no frontmatter transform.
5. `--agent codex` prints a notice (prompts live in `~/.codex/prompts`, repo entry point is `AGENTS.md`) and installs the base layer. Exit 0, not an error. Implemented as a notice map so future read-only agents cost one string.
6. Post-install hint after a base-only install, naming `--agent claude|bob|copilot`.
7. Per-layer install summary:
   ```
   ✓ Installed from https://github.com/aamarin/wf-skills@main
     base     25 skills · 23 commands · 8 runtime · 1 tracker
     claude   23 commands · 3 skills
   ```
   Replaces `✓ Installed 83 item(s)`, which reads as 83 skills when there are 25.
8. **Tracker consent** (already implemented on this branch): first interactive install offers the GitHub backend; non-interactive and `--yes` write nothing; declining prints both routes back. `--tracker github|none|<name>` unchanged.
9. README rewrite of the install section; minor version bump (breaking default).

**Tests** — on top of the existing 32:

- Bare install writes `.agents/skills` + `.agents/commands`, no `.claude/`; manifest lists only `.agents/*` and `.specify/*` paths.
- `--agent claude` reproduces today: `.agents/*` + `.claude/commands` + `.claude/skills` for `deployment: skill` items.
- `--agent copilot` writes `.github/skills/<name>/SKILL.md` byte-identical to the source.
- `--agent codex` exits 0, installs base only, output mentions `AGENTS.md`.
- `--agent none` still resolves.
- Base install then `--agent claude` creates zero backup entries for `.agents/skills`.
- `uninstall-skills --agent claude` removes `.claude/*` and leaves `.agents/skills` intact.
- **Migration:** a manifest in the old shape (`.agents/skills/*` under `claude`) upgrades silently — no backups, no overwrite prompt.
- **Invariant:** every destination across `_BASE_TARGETS` and all `_AGENT_TARGETS` entries is unique. Guards the property that makes cross-attribution unreachable; without it a future agent breaks it silently.

## Not Doing (and Why)

- **Symlinking agent layers to `.agents/`** — no agent tooling does this; spec-kit renders real files per agent and reserves symlinks for its dev mode. Symlinks would also break on Windows and give `wfctl doctor` a second failure mode.
- **Modernizing `claude` and `bob` to skills-only layouts** — spec-kit treats `.bob/commands` as deprecated and ships Claude as skills-only, but #5 criterion 2 requires `--agent claude` to reproduce today's behavior. Moving them breaks every `/speckit.*` slash command in existing repos. Deferred to #6, which researches whether `commands/` is actually dead across vendors.
- **The `.github/agents/*.agent.md` transform** — the layout spec-kit is phasing out ("deprecated and will stop being the default"). Choosing the skills layout removes the frontmatter transform that #5 estimated as the bulk of the work. Revisit only if the Copilot assumption above fails.
- **Migrating existing repos off the old default** — release note, per #5. The union check makes the upgrade silent; nobody has to run anything.
- **Per-path refcounts in the manifest** — disjoint layers make the bookkeeping unnecessary. New state to keep correct, for a problem that no longer exists.

## Open Questions

- None. Both assumptions above were validated during implementation (T028); no open questions remain.
