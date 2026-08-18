# Data Model: Vendor wf-skills

**Feature**: [spec.md](./spec.md)

Two artifacts change shape: the bundled tree that ships inside the wheel, and the
per-repo installation record. Nothing else in the manifest moves.

---

## 1. Bundled content

Read-only package data. The single source of truth for what a repo receives.

```
wfctl/
├── agents/
│   ├── skills/            → .agents/skills/          (25 skill dirs today)
│   ├── commands/          → .agents/commands/
│   ├── trackers/
│   │   └── github.json    → .agents/trackers/github.json   (only with --tracker github)
│   └── configs/
│       └── workmux/       → repo root                (install-config only)
└── specify/
    ├── scripts/bash/      → .specify/scripts/bash/   (mode 755, required)
    └── templates/         → .specify/templates/
```

**Leading dots stripped.** `setuptools`' `build_py` drops `.`-prefixed
directories silently — verified by building a wheel with both spellings and
finding only the undotted one shipped. Exit 0, no warning.

**Declared in `pyproject.toml`**, which currently has no such section:

```toml
[tool.setuptools.package-data]
wfctl = ["agents/**/*", "specify/**/*"]
```

Without it the wheel ships zero content and every test still passes, because the
suite runs against the source tree. That gap is what the wheel CI job closes.

### Invariants

| # | Invariant | Enforced by |
| --- | --- | --- |
| B1 | Every path an install command can source exists in the built wheel | wheel CI job (FR-005, SC-008) |
| B2 | `specify/scripts/bash/*.sh` are mode 755 in the wheel | wheel CI job assertion |
| B3 | Destination paths are byte-identical to today's | `test_layer_destinations_are_disjoint`, backup-attribution tests (FR-006) |
| B4 | The tree is read-only at runtime | nothing writes under the bundle root; copies flow one way |

## 2. Content fingerprint

A single value over the whole bundled tree. One computation, one value, recorded
identically on every layer entry.

**Inputs**: for every file under the bundle root, in sorted order — the file's
path relative to the root, then its bytes.

| Property | Why | Requirement |
| --- | --- | --- |
| Covers paths, not just contents | A pure rename hashes identical otherwise | FR-009 |
| Sorted iteration | `iterdir` order is filesystem-dependent; unsorted means permanent phantom drift | FR-010 |
| Whole tree, not per layer | `.agents/trackers/github.json` is copied inline (`cli.py:1196-1210`) and belongs to no target list, so a per-layer hash would leave it invisible | FR-008 |
| Path separators normalised | The hash must match across platforms | FR-010 |

**Accepted cost**: over-reporting. An edit under `specify/templates/` marks every
layer stale. The remedy is `wfctl install-skills` either way, so the noise carries
a correct instruction — which beats a silent miss.

**Not covered**: file modes (see [research.md](./research.md) §1), and the
installed files in the repo. Detecting hand-edits to *installed* content is a
different check with a different message, and is out of scope.

## 3. Installation record

`.wf-skills-manifest.json` at the repo root. Filename unchanged.

```jsonc
{
  "base": {
    "wfctl_version": "0.15.0",        // NEW  — replaces repo/ref/commit
    "content_hash": "9f2a1c…",        // NEW
    "installed_at": "2026-08-16T…",   // unchanged
    "items": [                        // unchanged — uninstall depends on it
      { "path": ".agents/skills/brainstorming", "backup": null },
      { "path": ".agents/commands/x.md", "backup": ".wf-skills-backup/.agents/commands/x.md" }
    ]
  },
  "claude": { "…same shape…" },
  "tracker": "github",                // unchanged scalar, not a layer
  "spec_root": "…",                   // unchanged scalar
  "spec_root_asked": true             // unchanged scalar
}
```

### Field transitions

| Field | Before | After |
| --- | --- | --- |
| `repo` | wf-skills URL | **dropped on rewrite** |
| `ref` | `"main"` | **dropped on rewrite** |
| `commit` | resolved clone HEAD | **dropped on rewrite** |
| `wfctl_version` | — | `importlib.metadata.version("wfctl")` at install time |
| `content_hash` | — | whole-tree fingerprint at install time |
| `installed_at`, `items` | unchanged | unchanged |

Dropped rather than preserved: they describe a fetch that no longer happens, and a
manifest asserting a provenance the tool cannot act on is worse than one that is
silent about it. The vendored tree carries its own history in wfctl's git.

### Layer state machine

`doctor` reads one layer entry and lands in exactly one state:

| State | Condition | Report | Exit |
| --- | --- | --- | --- |
| **Current** | `content_hash` equals the running bundle's | `✓ {layer}: skills current (wfctl {v})` | 0 |
| **Stale, versions differ** | hash differs, `wfctl_version` ≠ running | `⬆ {layer}: skills stale — installed by wfctl {a}, running {b}` + remedy | 1 |
| **Stale, versions equal** | hash differs, versions match | `⬆ {layer}: bundled skills changed since install` + remedy | 1 |
| **Unmeasurable** | no `content_hash` key | `⚠ {layer}: installed before content hashing — re-run install-skills` | unchanged |

The equal-version state is not an edge case to tolerate — it is the *primary* case
under an editable install, which is how skills get authored once they live in this
repo. `installed by 0.15.0, running 0.15.0` would read as a bug, so it needs its
own string (FR-012).

**Unmeasurable** is the migration path, and mirrors the existing missing-`commit`
branch at `cli.py:1874-1879` exactly: warn, `continue`, leave the exit code alone.

### Invariants

| # | Invariant | Enforced by |
| --- | --- | --- |
| M1 | `items` and every `backup` pointer survive the rewrite | uninstall-restore test over a pre-change manifest (FR-016) |
| M2 | Every layer entry in one manifest carries the same `content_hash` | consequence of whole-tree hashing |
| M3 | Scalars (`tracker`, `spec_root`, `spec_root_asked`) are never treated as layers | existing `_NON_LAYER_KEYS` (`cli.py:693`), unchanged |
| M4 | A layer that installs nothing writes no entry | existing behaviour, unchanged |
| M5 | `install-config` writes no entry and is never staleness-checked | FR-017 |

## 4. Layer

Unchanged by this feature. Listed because three of its invariants are the ones
most likely to break silently while the source paths are being rewritten.

`_BASE_TARGETS` (`cli.py:630`), `_AGENT_TARGETS` (`cli.py:641`), `_RUNTIME_TARGETS`
(`cli.py:672`) and `_CONFIG_SOURCES` (`cli.py:682`) each hold `(src, dst)` pairs —
**only the `src` half changes**, from `.agents/skills` to `agents/skills` and so
on. Destinations, disjointness, backup attribution and the `_kind_of` label
derivation (`cli.py:764`) all follow the source directory's *basename*, which the
dot-strip does not touch.
