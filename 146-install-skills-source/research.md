# Research: install-skills source

Phase 0 for #146. Six unknowns from the spec and the design's open questions,
each resolved against the code at `4c3b546`.

## R1 — Where the source is recorded

**Decision**: In each layer entry of `.wf-skills-manifest.json`, beside
`content_hash`.

**Rationale**: `install_skills_cmd` already writes layer entries in one loop
(`manifest[layer] = {wfctl_version, content_hash, installed_at, items}`). Adding
a key there is one line inside an existing write. A manifest-root key would need
its own write plus a rule for the case the spec's edge cases already raise — a
later install for a different agent layer naming a different source. Per-layer
answers that by construction: each part is reported against the source that
produced it.

**Alternatives considered**: A root-level key (smaller on disk, but cannot
represent per-layer sources and needs a reconciliation rule); `wfctl.json`
(rejected in the architecture record — it is tracked, so recording a per-checkout
fact there dirties the branch on every install).

## R2 — How "the default" is represented

**Decision**: By the key being absent. No sentinel string.

**Rationale**: Absence is unambiguous here, and that is not true of the key
beside it. A manifest written before this feature has no `content_hash` and
`doctor` cannot tell whether the tree is current — hence its "installed before
content hashing" warning. A manifest written before this feature also has no
`source`, and there `absent` carries a complete answer: the default was the only
source that existed. So no migration state, no warning, and no backfill.

There is precedent for reading absence as a decision rather than a gap: the
`tracker` key is documented as behaving "exactly like an absent key" when null,
because its readers test truth rather than presence.

**Alternatives considered**: `"source": "default"` (a value to keep in sync with
a magic string, and it makes every pre-existing manifest read as unmeasurable);
recording the wheel's own path (rejected during clarification — an upgrade
rewrites that path's contents, so a routine version bump would report as the
source having changed).

## R3 — The resolution seam in `_bundle`

**Decision**: A new public function, `_bundle.resolve_root(path) -> Path`. It
applies the nested-checkout probe, verifies the bundled trees are present, and
raises `FileNotFoundError` naming what it looked for and where.

**Rationale**: `BUNDLE_ROOT` stays exactly what it is — the running package's
directory, and the default. The new seam is a separate name so nothing about the
default path changes. Public rather than `_`-prefixed because `cli` is the
caller, and the proposed `the-underscore-is-the-module-contract` record makes a
cross-module `_` name a violation; choosing the public name now costs nothing and
avoids a rename if that record is accepted.

`content_hash` already raises `FileNotFoundError` with a message naming the
expected trees, so `resolve_root` reuses that failure shape rather than inventing
one.

**Alternatives considered**: A parameter on `content_hash` (conflates "where is
the bundle" with "what does it hash to", and `content_hash` already takes a
resolved root); doing the probe inline in `cli` (puts bundle-layout knowledge in
the installer, which is what `_bundle` exists to hold).

## R4 — How `doctor` branches without ballooning

**Decision**: Read `entry.get("source")` per layer. `None` takes today's code path
unchanged. A value resolves and hashes that root, memoized by resolved path
across layers.

**Rationale**: The existing loop already handles per-layer entries and computes
one bundle hash before it. Per-layer sources mean up to one hash per distinct
source, so the single pre-computed value becomes a small dict keyed on resolved
path. That is the whole structural change; the four reported states are three
branches inside the loop plus the untouched default path.

**Alternatives considered**: Hashing every recorded source up front (does work for
layers that may not need it, and has to handle an unreachable source before it
knows whether any layer cares); a separate `doctor` subcommand for named-source
installs (two code paths reporting the same condition, and the whole point is one
report).

## R5 — Backward compatibility

**Decision**: Nothing to migrate. Covered by R2 — an absent key is a correct and
complete answer for every manifest that predates this feature.

**Rationale**: Before `--from`, the running wheel was the only possible source.
Every historical manifest therefore describes a default install, which is exactly
what an absent key will mean.

## R6 — Path handling

**Decision**: Resolve at install time and store an absolute path. Validate before
anything is copied.

**Rationale**: FR-004 requires the recorded value to resolve identically from any
directory, and `doctor` runs from wherever the session happens to be. Resolution
must therefore happen where the user's cwd is still the right frame of reference,
which is the install. Validation goes before the copy for the reason
`content_hash` is already computed before the copy: a run that fails must leave
the repo untouched rather than half-installed with no manifest.

The nested probe: if `<path>/agents` is absent and `<path>/wfctl/agents` present,
use the latter. This makes `--from ../116-pr` work when pointed at a checkout
root rather than the package directory inside it. A path with neither raises.

**Alternatives considered**: Storing the path as given (breaks FR-004 for any
relative value); accepting only the exact package directory (rejected as
ergonomics — the checkout root is what people have in hand, and the failure
message would be the only teacher).

## Verified, needing no work

- **FR-012 (pruning evaluates against the named source)** holds with no code.
  `--prune` diffs the previous record against `installed_paths`, which is built
  from the plan, which is built by iterating the source. Pointing the source
  elsewhere carries through automatically. Verified at `cli.py:2111-2119`.
