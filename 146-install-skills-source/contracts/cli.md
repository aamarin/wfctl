# CLI contract: install-skills source

The user-facing surface this feature adds or changes. Exact wording is
illustrative where marked; the states and exit codes are the contract.

## `wfctl install-skills --from <path>`

| | |
|---|---|
| Type | Optional string, a filesystem path |
| Default | Unset — the running tool's own bundle, exactly as today |
| Scope | The single invocation it is given on (FR-014) |
| Help | `Install from this bundle root instead of the running wfctl. Accepts a checkout root or the package directory inside it.` |

### Resolution

```
<path>/agents exists          → use <path>
<path>/wfctl/agents exists    → use <path>/wfctl
neither                       → error, exit 1, repo untouched
```

Resolved to an absolute path before anything is copied.

### Failure

```
✗ No bundled trees under ../not-a-checkout — expected one of agents, specify
  (also looked in ../not-a-checkout/wfctl)
```

Exit 1. Never falls back to the default (FR-010).

### Success

```
✓ Installed from ../116-pr
  base  33 skills · 27 commands · 8 runtime
```

The default install's line is unchanged: `✓ Installed from wfctl 0.16.0`.

This one line prints the path **as typed** (FR-002); it is read beside the
command that produced it. Every line below prints the **resolved** path, because
the record has to mean the same thing from any directory (FR-004) — so a run
from elsewhere shows `/home/u/wt/116-pr/wfctl` where these examples show
`../116-pr`.

### Replacing a named-source install

When the record names a source and this run names none (FR-015):

```
⚠ Will replace an install from /home/u/wt/116-pr/wfctl with wfctl 0.16.0 — no source named
✓ Installed from wfctl 0.16.0
```

Printed before the copy. **Not suppressed by `--yes`** — the unattended
session-start refresh is the case it exists for.

## `wfctl doctor`

Four reachable states per layer. The first is today's behavior, unchanged.

| Recorded source | Comparison | Output | Exit |
|---|---|---|---|
| absent | running tool's bundle | `✓ base: skills current (wfctl 0.16.0)` — or today's stale/changed lines | 0 / 1 |
| present, matches | that source's digest | `✓ base: skills current (from /home/u/wt/116-pr/wfctl)` | 0 |
| present, differs | that source's digest | `⬆ base: source changed since install — /home/u/wt/116-pr/wfctl` + remedy | 1 |
| present, unreachable | — | `⚠ base: installed from /home/u/wt/116-pr/wfctl — source is gone, can't check` | unchanged |

### The remedy line

```
⬆ base: source changed since install — /home/u/wt/116-pr/wfctl
    update: wfctl install-skills --from /home/u/wt/116-pr/wfctl
```

The printed command **must** carry `--from` with the recorded source (FR-008).
Running it must leave the project installed from the same source it was installed
from (SC-003). Single-quoted when the path holds a space, since the line is read
back by a shell.

For a default-source layer the remedy stays `update: wfctl install-skills`.

**`doctor` prints the repair for the drift, and no policy on top of it.** No
`--prune`, no `--yes` — those belong to whoever is running the repair, and
`/start-session` adds them because it refreshes unattended. An earlier draft of
this file showed them on the source-bearing line only, which would have made one
command print two shapes of the same verb.

### Exit code

- `source changed since install` is a finding — exit 1, same as today's drift.
- An unreachable source is a warning — it does not itself make the run fail
  (FR-009), matching how `⚠` is already documented to map to either code. The
  rendered string stays `source is gone, can't check`; "unreachable" is the term
  the prose uses for the state.

## `/start-session` step 2

Prose change only. The step lists two literal repair commands as examples; it
must state that the command `doctor` printed governs over them, because that
printed command is what carries `--from` (FR-013).

## Unchanged

- `wfctl uninstall-skills` — operates on recorded paths, indifferent to source.
- `wfctl install-config` — seeds committed files, not a managed mirror.
- `--prune` — already evaluates against what was just installed, so it follows
  the named source with no change (FR-012, verified).
