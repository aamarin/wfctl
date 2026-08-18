# CLI Contract: Vendor wf-skills

**Feature**: [spec.md](../spec.md)

wfctl's external interface is its command surface. This records what a caller can
rely on before and after the change. Anything not listed here is unchanged.

---

## `wfctl install-skills`

### Signature

| Option | Before | After |
| --- | --- | --- |
| `--repo URL` | default `https://github.com/aamarin/wf-skills` | **removed** |
| `--ref NAME` | default `main` | **removed** |
| `--agent NAME` | `none`\|`codex`\|`claude`\|`bob`\|`copilot` | unchanged |
| `--yes` / `-y` | skip overwrite confirmation | unchanged |
| `--tracker NAME` | `github`\|`none`\|custom | unchanged |

**Removal is an error, not a no-op** (FR-004). Typer's default for an unknown
option already exits 2 with `No such option: --repo`. That satisfies the
requirement without custom code — a caller with `--repo` in a script gets a
non-zero exit and the offending flag named, which is what "explanatory" asks for.

### Output

```
# before — network, ~15s
Cloning… ✓
✓ Installed from https://github.com/aamarin/wf-skills@main
  base: 25 skills, 23 commands, 2 runtime

# after — no network
✓ Installed from wfctl 0.15.0
  base: 25 skills, 23 commands, 2 runtime
```

Only the provenance line changes. Per-layer, per-kind counts, the overwrite
prompt, the backup notice, the gitignore summary and the agent-hint block are
untouched.

The `--tracker github` not-found warning (`cli.py:1206-1210`) interpolates
`{repo}@{ref}` today. Those names stop existing, so the string is reworded to name
the wfctl version instead.

### Guarantees

| ID | Guarantee |
| --- | --- |
| IS-1 | Makes no network call, under any option combination |
| IS-2 | Installed destination paths are identical to the previous release |
| IS-3 | Writes `wfctl_version` and `content_hash` on every layer it records |
| IS-4 | Drops `repo`/`ref`/`commit` from any entry it rewrites |
| IS-5 | Preserves `items` and every `backup` pointer across the rewrite |
| IS-6 | Still requires a git repo, still exits 1 with `✗ Not in a git repo.` |

## `wfctl install-config <name>`

### Signature

| Option | Before | After |
| --- | --- | --- |
| `--repo URL` | default wf-skills | **removed** |
| `--ref NAME` | default `main` | **removed** |
| `--force` | overwrite existing | unchanged |
| `--agent NAME` | workmux `agent:` value | unchanged |

### Output

```
# before
✓ Seeded workmux config (1 file(s)) from https://github.com/aamarin/wf-skills@main

# after
✓ Seeded workmux config (1 file(s)) from wfctl 0.15.0
```

The `✗ Config 'x' not found in {repo}@{ref}` error at `cli.py:1486` loses its
interpolated variables and is reworded. It becomes near-unreachable — a missing
config now means a broken wheel, not a bad `--ref` — but stays as the guard it is.

### Guarantees

| ID | Guarantee |
| --- | --- |
| IC-1 | Makes no network call |
| IC-2 | Remains seed-once: no manifest entry, no backup, no uninstall, no staleness check |
| IC-3 | Conflict detection, `--force`, the `wt/` gitignore step and the workmux `agent:`/`window_prefix` substitution are unchanged |

## `wfctl doctor`

### Output contract

Line 1 — the release check — is unchanged, including its offline degradation:

```
✓ wfctl 0.15.0 — latest
⬆ wfctl 0.14.0 → 0.15.0 available
      upgrade: uv tool install --upgrade https://github.com/aamarin/wfctl.git
⚠ wfctl 0.15.0 — couldn't check latest (offline?)
```

The per-layer block is replaced. Before, per layer: an `ls-remote`, a clone, and a
`git diff --stat`. After, per layer: a dictionary comparison.

| State | Line | Exit contribution |
| --- | --- | --- |
| current | `✓ base: skills current (wfctl 0.15.0)` | 0 |
| stale, versions differ | `⬆ base: skills stale — installed by wfctl 0.14.0, running 0.15.0` | 1 |
| stale, versions equal | `⬆ base: bundled skills changed since install` | 1 |
| no fingerprint on record | `⚠ base: installed before content hashing — re-run install-skills` | 0 |

Both stale lines are followed by `    update: wfctl install-skills` — the same
indented remedy the current code emits at `cli.py:1905` (FR-013).

### Guarantees

| ID | Guarantee |
| --- | --- |
| D-1 | The skills verdict never contacts the network and is accurate offline (FR-011, FR-014) |
| D-2 | A failed release check degrades to `⚠` and returns 0, leaving the skills verdict authoritative |
| D-3 | The `✗ {layer}: couldn't reach…` state disappears — with no remote there is nothing to fail to reach |
| D-4 | A record with no fingerprint warns once and does not raise (FR-015) |
| D-5 | `Nothing installed — run \`wfctl install-skills\` first.` on an empty manifest, unchanged |
| D-6 | The four pre-manifest checks — workmux hook, stale archive hook, spec-root migration, legacy `.agent/` — are untouched and still run before the manifest gate |

## `wfctl uninstall-skills`

Unchanged. Listed because it is the reason `items` and `backup` survive the
manifest rewrite: it restores from those pointers and knows nothing about
provenance fields.

## Internal seams (not user-facing, but contracts the tests hold)

| Seam | Contract |
| --- | --- |
| `wfctl._bundle.BUNDLE_ROOT` | Module-level `Path`. Read through a module-global lookup at call time so `monkeypatch.setattr` reaches it. Never bound as a default argument. |
| `wfctl._bundle.content_hash(root)` | Pure function of a directory tree. Same tree → same value, on any platform and any supported Python. |

Neither is exported, documented, or settable by a user. There is deliberately no
`WFCTL_BUNDLE_ROOT` environment variable — see [research.md](../research.md) §4.
