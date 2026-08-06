# Phase 0: Research

**Feature**: install-config substitution (#17)
**Date**: 2026-08-02

All `NEEDS CLARIFICATION` items were resolved before this phase — three during
brainstorming (D1–D3) and three during `/speckit.clarify`. This document records
what was measured rather than assumed, because several findings contradicted the
issue's original framing.

---

## R1 — `pre_remove: []` is an opt-out, not an empty default

**Decision**: Replacing it forfeits nothing that today's seeded repos still have.

**Rationale**: workmux's own generated reference documents the default as
*"Auto-detects Node.js projects and fast-deletes node_modules"* and names
`pre_remove: []` as the documented way to **disable** it. The shipped template is
therefore not "unconfigured" — it actively turns the hook off.

The practical consequence matters for Node consumers: a repo seeded from this
template already lost the fast-delete default, so wiring an archive call in its
place is not a regression. It inherits an existing cost rather than introducing
one.

**Alternatives considered**: Preserving the fast-delete behavior alongside the
archive call. Rejected — the template already gave it up, so this would restore
something no seeded repo currently has, and it would need Node detection logic
wfctl has no business owning.

---

## R2 — The project-name helper already exists and is untested

**Decision**: Promote `_paths._project_name` to public `project_name`. Do not
write a new helper.

**Rationale**: `_paths.py:194` already derives the project name via
`git rev-parse --git-common-dir` → `.parent.name`, with a docstring describing the
exact worktree trap issue #17 raises. Measured from this worktree:

```
--show-toplevel   -> .../wfctl/wt/17-install-config-substitution
  basename        -> 17-install-config-substitution      WRONG
--git-common-dir  -> .../wfctl/.git
  parent basename -> wfctl                               RIGHT
_project_name()   -> wfctl
```

`grep -rn _project_name tests/` returns nothing — it has one caller
(`_paths.py:228`) and zero test coverage. So the work is promotion plus a
regression test, not new logic.

**Alternatives considered**: A second helper local to `_workmux.py`. Rejected —
two derivations of the same value drift, and the existing one is already correct.

---

## R3 — tmux rewrites exactly two characters in session names

**Decision**: Sanitize `[.:]` to `_` before writing the prefix. No wider set.

**Rationale**: Measured against a live tmux server rather than reasoned about.
Sessions were created, listed, and killed:

| Requested | Created as | Targetable by requested name |
| --------- | ---------- | ---------------------------- |
| `wfprobe.dot` | `wfprobe_dot` | **no** — `can't find pane: dot` |
| `wfprobe:col` | `wfprobe_col` | **no** |
| `wfprobe a b` | `wfprobe a b` | yes |
| `wfprobe$dol` | `wfprobe$dol` | yes |
| `wfprobe-dash` | `wfprobe-dash` | yes |
| `wfprobe_us`  | `wfprobe_us`  | yes |

The failure is silent at creation and only surfaces later as a *missing pane*
rather than a bad name — a genuinely misleading error for a preventable cause.

Neither known consumer (`wfctl`, `pfms`) is affected, so this is insurance.

**Alternatives considered**: Sanitizing all non-alphanumerics. Rejected as
speculative — four of six probed characters pass through untouched, and widening
the set would mangle legitimate names.

---

## R4 — The placeholder check must watch the symptom, not the mechanism

**Decision**: After writing, warn if the literal `<project>` survives anywhere in
the file. Do not warn on a missing key.

**Rationale**: The template lives in a separate repository and versions
independently. Three drift shapes were considered:

| Drift | Key found? | Placeholder ships? |
| ----- | ---------- | ------------------ |
| Key removed | no | no — falls back to the tool's default prefix |
| Key renamed | no | **yes** |
| Key reformatted (`window_prefix :`) | no | **yes** |

A missing-key check fires on all three but says nothing about which are harmful.
A surviving-placeholder check fires on exactly the two that ship a broken config.
tmux accepts `<` and `>` verbatim (R3), so an unsubstituted prefix produces a real
session literally named `<project>__<branch>`, committed for everyone on the repo.

**Constraint discovered**: `<agent>` on template line 22 is workmux's *own*
runtime placeholder, resolved by workmux rather than by seeding. A generic
`<...>` scan would false-positive on it, so the check targets `<project>`
specifically.

---

## R5 — No YAML parser is available, and none should be added

**Decision**: Line scanning, matching the existing `agent:` patch at `cli.py:1138`.

**Rationale**: Runtime dependencies are `typer` and `rich`. Nothing parses YAML,
and every existing config edit is a line scan.

**Alternatives considered**: `ruamel.yaml` for comment-preserving round-trips.
Rejected — a new runtime dependency for a 62-line config, and comment-preserving
round-trips carry their own maintenance burden. The line-scan smell is real and is
mitigated by concentrating all four scan sites in one tested module rather than by
adding a parser.

---

## R6 — Part 1 is already specified upstream

**Decision**: Depend on wf-skills#8 rather than re-specify the template edit.

**Rationale**: wf-skills#8 (*"workmux template: wire pre_remove to `wfctl
archive-story`"*) contains the identical YAML block this feature assumed — same
comment text, same `command -v` guard, same explicit `"$WM_WORKTREE_PATH"
"$WM_HANDLE"` arguments. Its stated blocker was wfctl#10, which has shipped
(`e64d047`, `0e250e6`, `87626a5`), so it is ready to land independently.

Two issues describing one edit to one file is duplication. The spec now carries a
Dependencies section and marks User Story 1 as delivered upstream.

---

## R7 — Retrofit demand is real but small

**Decision**: Prompt-only retrofit, no flag, no dedicated command.

**Rationale**: State directories show the gap concretely:

```
~/.local/state/wfctl/wfctl/005-update-install-skills-default/archive   1 archive
~/.local/state/wfctl/pfms/                     22 branches, 0 archives
```

`wfctl` wires the hook by hand and archives. `pfms` has `pre_remove: []` and 22
branches have come and gone without a trace.

But the backlog is one file. A `--fix` flag relocates the reachability problem
rather than solving it — something still has to decide to run. The mitigation is
FR-013a: the non-interactive report names how to reach the prompt.

**Alternatives considered**: `wfctl doctor --fix` (deferred until the warning is
demonstrably ignored); a dedicated command (more surface for a one-file backlog).

---

## R8 — The retrofit's blast radius, measured

**Decision**: Patch only `pre_remove: []`; refuse every other shape.

**Rationale**: Generated against a copy of the real `pfms` config:

```diff
-pre_remove: []
+pre_remove:
+  - command -v wfctl >/dev/null && wfctl archive-story "$WM_WORKTREE_PATH" "$WM_HANDLE" || true
```

326 → 327 lines. Every other byte identical, including `window_prefix: 'pfms__'`,
the per-issue port arithmetic in `post_create`, the `deploy` window, and the
commented `pre_remove:` example immediately below the patched line.

A repo whose `pre_remove` holds real entries has hooks whose ordering and intent
we would be guessing at, and appending a top-level key to an unparsed EOF is how a
config file gets mangled. Refusing with manual instructions is cheaper than being
clever.

---

## Deferred, deliberately

- **Wiring `post_create` in the template.** The template ships it fully commented,
  so a seeded repo never runs `install-skills` on worktree creation the way
  `wfctl/.workmux.yaml:72` does. Unrelated to #17; file separately.
- **wf-skills' foreign project content.** 24 references to `pfms`/`zmodel`/
  `zenstack`/`pnpm` across 8 files, including the spec and plan templates used by
  this very pipeline. Tracked partially as wf-skills#3, which is scoped to one
  file and undercounts by seven.
- **Skill-text drift.** wf-skills#6, #7, and the hardcoded `dev` trunk in
  `speckit-specify` are the same class of defect: skill text naming something that
  does not exist. Worth one sweep.
