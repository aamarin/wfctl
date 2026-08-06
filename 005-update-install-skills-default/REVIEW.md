# Review: `origin/master...HEAD` (6 commits, wfctl#5)

Reviewed the branch diff as it stands before the PR: `wfctl/cli.py` (+254),
`tests/` (+408), `README.md` (+88), version 0.11.0 → 0.12.0. 204 tests passing.

Every finding below was reproduced against the code, not inferred from reading it.

---

BLOCKER  wfctl/cli.py:L901 — `_resolve_config_agent` dropped the `!= "none"` guard, so a repo installed under the pre-split `--agent none` seeds a literal `agent: none` into the committed `.workmux.yaml` → filter agents with no installable layer, restoring the old guard

WARNING  wfctl/cli.py:L822 — the backup-recovery hint prints `--agent {agent}`, but base-layer backups are recorded under `base`; after a bare install it tells the user to run `--agent none`, which no-ops → name the layer(s) that actually recorded backups

WARNING  wfctl/cli.py:L845 — `uninstall-skills` still defaults to `claude` and its `--help` lists `_AGENT_TARGETS`, which omits `base`; the one value that removes the default install is undiscoverable from the CLI (README documents it) → add `base` to the listed names

WARNING  wfctl/cli.py:L643 — declining the tracker is never recorded, so every later interactive install re-asks; `--tracker none` pops the key rather than storing the opt-out, so there is no way to stop being asked. FR-012 says "asked once" → persist the decline and treat any present `tracker` key as a made choice

WARNING  wfctl/cli.py:L636 — a pre-split `none` manifest entry survives the upgrade (the `none` layer installs nothing, so it is never overwritten) and duplicates `base`'s ownership of `.agents/*`; `uninstall-skills --agent none` then deletes paths `base` still claims → drop or migrate a legacy `none` entry on install

NIT      wfctl/cli.py:L636 — literal `key != "tracker"` duplicates `_NON_LAYER_KEYS` (L455); the `isinstance(entry, dict)` guard exists only to cover the drift → use `_NON_LAYER_KEYS` and delete the isinstance

net: −4 lines possible
Verdict: **Request changes** (1 blocker)

---

## Evidence

### BLOCKER — `agent: none` seeded into a committed config

`95afa1d` rewrote the fallback:

```python
# before
agents = [a for a in _load_manifest(repo_root) if a != "tracker"]
if len(agents) == 1 and agents[0] != "none":   # ← guard
    return agents[0]
return "claude"

# after
agents = _agent_keys(_load_manifest(repo_root))
return agents[0] if len(agents) == 1 else None
```

`_agent_keys` filters `tracker` and `base` only. `none` passes through.

Reproduced end to end — a repo whose manifest has the pre-split `none` shape,
then `wfctl install-config workmux`:

```
SEEDED >>> ['agent: none']
```

`.workmux.yaml` is version-controlled, so this lands in every checkout, and
workmux would launch a pane running a command literally named `none`.

The affected population is precisely this feature's audience: anyone who opted
out of `.claude/` shims under the old default by passing `--agent none`. The
stale key is never cleaned up (see WARNING 5), so re-running `install-skills`
after upgrading does not clear it.

The commit's own rationale — "don't invent an agent for an agent-agnostic repo"
— is right; the implementation just widened the filter past the case the old
guard was covering.

### WARNING — recovery instruction that does nothing

Bare install over a user-authored `.agents/commands/test-cmd.md`:

```
HINT >>> ℹ Backed up 1 pre-existing file(s) to .wf-skills-backup/ —
          restored by `wfctl uninstall-skills --agent none`

FOLLOWING IT >>> Nothing installed for agent 'none' — nothing to uninstall.
FILE AFTER   >>> '# test-cmd\n'     (still wfctl's copy)
```

Not data loss — the original is intact in `.wf-skills-backup/` — but the printed
recovery path fails silently. `test_user_authored_file_is_still_backed_up`
passes because it calls `--agent base`, the command the tool does *not* print.

---

## What the review did not find

- **Correctness of the layer split itself.** `_BASE_TARGETS` / `_AGENT_TARGETS`
  disjointness holds, and `test_layer_destinations_are_disjoint` enforces it
  structurally rather than by comment — a new agent claiming a taken root fails
  the suite. This is the right shape.
- **The `prior_items` union.** Load-bearing and correctly scoped: it relaxes
  ownership only for paths wfctl recorded, and
  `test_user_authored_file_is_still_backed_up` is a real guard on that
  boundary, not a restatement.
- **Security.** No untrusted input crosses a boundary. `src.iterdir()` yields
  direct children only, so item names cannot traverse.
- **Performance.** Not applicable to this diff.
- **Over-engineering.** Little to cut. `_layer_keys` / `_agent_keys` have one
  caller each but name a real distinction; `_interactive()` is a justified test
  seam.

## Known and already filed

- `.gitignore` line churn (redundant entries under an existing glob) — wfctl#11.
- `doctor`'s "Nothing installed" wording predates base-only installs — carried
  in the session TODO.
