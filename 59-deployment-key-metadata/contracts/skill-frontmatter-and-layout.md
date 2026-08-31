# Contract: shipped skill frontmatter and installed layout

wfctl writes into other people's repositories, and five different agent clients
read what it writes. Two contracts are externally visible and are the ones this
change touches. The CLI's own surface — `install-skills`, `uninstall-skills`,
`doctor` — keeps every option and every exit code it has today.

## Contract 1 — what a shipped `SKILL.md` may contain

Every skill wfctl authors conforms to the Agent Skills frontmatter contract. The
allowed top-level keys, enforced by the reference validator:

```
allowed-tools · compatibility · description · license · metadata · name
```

**Before this change** — six skills violate it:

```
---
name: design-levels
description: Runs design as four separate passes …
deployment: skill            ← not in the allowed set
---
```

**After** — nothing wfctl-specific remains:

```
---
name: design-levels
description: Runs design as four separate passes …
---
```

**The one permitted exception.** `i-have-adhd` is vendored, and its upstream
frontmatter carries `disable-model-invocation`. wfctl may not edit it
(`vendor-upstream-skills`), so it is exempt by name from the conformance
assertion and remains the single validator failure in the bundle.

**Enforcement** (FR-010): a test asserting, for every non-exempt skill, that its
top-level frontmatter keys are a subset of the allowed set. Offline — the allowed
set is pinned in the test rather than fetched.

**What this contract does not say.** It constrains keys, not sections. Whether
the *body* follows the agentskills anatomy is #60's question, unresolved and out
of scope here.

## Contract 2 — what lands where on install

Unchanged in shape; one entry is added. Layers are additive, and each owns a
disjoint root.

```
install-skills --agent <a>

  base layer          always
    .agents/skills/<name>          all 28
    .agents/commands/<name>.md     all commands
    .specify/…                     runtime

  agent layer         additive, per --agent
    none      —
    codex     —
    claude    .claude/commands/<name>.md
              .claude/skills/<name>        ← the discoverable set, 7 names
    bob       .bob/skills/<name>  ·  .bob/commands/<name>.md
    copilot   .github/skills/<name>
```

**The only behavioural change**: `.claude/skills/` gains `i-have-adhd`, going
from 6 entries to 7. No other agent's output changes by a byte (FR-006).

### Guarantees this change preserves

| Guarantee | Holds because |
| --- | --- |
| Idempotent — reinstalling produces the same tree | The plan is recomputed from the bundle each run; nothing reads prior state. |
| Uninstall removes exactly what was installed | It iterates the manifest's recorded items; the new native copy is recorded under the `claude` layer like any other. |
| Layer roots stay disjoint | No destination moves; `.claude/skills` was already the Claude layer's own root. |
| Pre-existing files are backed up, and overwrites are announced | Unchanged path. A repo with its own `.claude/skills/i-have-adhd` is now prompted before overwrite, which is the existing mechanism meeting a new case. |
| `.agents/` remains the agent-neutral store every command points into | The mirror is additive, not a relocation — see `research.md` R7. |

### What membership does not grant

A skill in `.claude/skills/` is *discoverable*. Whether the model may invoke it
unprompted is decided by that skill's own frontmatter, not by membership. The
vendored skill declines model-initiated invocation and therefore arrives listed
and loadable on request, never self-invoking.

## Contract 3 — the declaration, for wfctl's own contributors

Internal, but stated because getting it wrong fails silently.

- Adding a skill to the discoverable set is one edit: its name into the
  declaration in `wfctl/cli.py`.
- A name that matches no shipped skill directory fails the test suite (FR-005),
  not the install.
- Removing a name stops the native copy being installed and recorded. It does
  **not** delete an already-installed copy, and no command reports the leftover —
  #110.
