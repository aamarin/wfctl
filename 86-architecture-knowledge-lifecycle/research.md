# Phase 0 Research: Architecture Knowledge Lifecycle

Seven unknowns resolved. Each was checked against the code rather than recalled;
where a claim rests on something not verified, it says so.

## 1. Reading a record's status without a new dependency

**Decision**: A frontmatter line scan, mirroring `_skill_deployment`
(`wfctl/cli.py:786-799`).

**Rationale**: wfctl's runtime dependencies are `typer` and `rich`, and this is
already settled house style. `_workmux.py:12-15` states it directly — *"No YAML
parser: wfctl's runtime dependencies are typer and rich, and every existing
config edit is a line scan. `ruamel.yaml` would remove the smell but adds a
runtime dependency for a 62-line file."*

`_skill_deployment` is the same problem already solved: open the file, require
`---` on line one, scan until the closing `---`, match a key prefix, strip
quotes, and return a default when the key is absent. Fourteen lines, covered by
the suite.

One deliberate difference. `_skill_deployment` defaults to `"command"` — the
common case. A record with an absent or unrecognised status must default to
**excluded from the in-force set**, never to `accepted`. Presenting an unreviewed
decision as binding is the failure the status field exists to prevent, so the
default is the conservative value rather than the common one.

**Alternatives considered**: PyYAML or `ruamel.yaml` — rejected, adds a runtime
dependency for one field. JSON sidecar per record — rejected, splits one decision
across two files and breaks the "record stands alone" property.

## 2. Record format

**Decision**: MADR simple, plus one field: ownership of truth.

**Rationale**: Verified against Fowler's ADR page and two existing ADR skills
(`skillrecordings/adr-skill`, the `agents-architecture-decision-records` skill).
The record shape is solved prior art and not worth reinventing. What no ADR
format on the market carries is a statement of which side owns a piece of truth
and why the other side cannot compute it — which is the one thing `design-levels`
level 2 exists to extract, and the thing 0 of 11 existing designs captured.

**Alternatives considered**: Full MADR 4.0 — rejected, its RACI frontmatter
(decision-makers, consulted, informed) is team ceremony a small repository leaves
blank. Forking `skillrecordings/adr-skill` — rejected, inherits their choices and
needs a licence review for a format we can state in a page.

## 3. Identity scheme

**Decision**: Descriptive slug, no sequence number.
`docs/architecture/wfctl-runs-the-check.md`.

**Rationale**: Settled during `/speckit.clarify`. Monotonic numbering collides
whenever two worktrees create a record in overlapping windows, which is this
repository's normal case — six worktrees were checked out while this spec was
written. Renumbering to resolve a collision breaks inbound `supersedes` links,
reintroducing the dangling-reference problem that the single-unit model was
chosen to avoid.

The numbering half of ADR convention exists to give "a clear log of decisions and
how long they governed." Explicit status values and supersession links state that
more precisely than sequence does.

**Alternatives considered**: number-at-merge — rejected, leaves the record with no
stable id during review, which is exactly when it is being linked. Branch-prefixed
numbering — rejected, longer ids and cross-issue ordering follows issue numbers
rather than decision dates.

## 4. Architecture root resolution

**Decision**: Mirror `spec_root` (`wfctl/_paths.py:233-264`) exactly —
`WFCTL_ARCH_DIR` → this repo's manifest → main checkout's manifest →
`repo_root/docs/architecture`.

**Rationale**: The resolution order, its reasoning, and its tests already exist
for specs; a second, differently-shaped resolver would be two things to keep in
step. The env var stays a per-invocation escape hatch because it is
process-global — exporting it from a shell profile would redirect every repo
wfctl touches.

**Open, deliberately**: the main-checkout fallback exists for specs because the
manifest is gitignored and regenerated in every fresh worktree, so a
worktree-local setting cannot exist when the pipeline first runs there. An
in-tree, version-controlled default resolves identically in every worktree, so
the fallback may be dead weight here. Included for symmetry; flagged in
`design.md` and worth deleting if the tests for it read as vacuous.

**Alternatives considered**: a fixed in-tree path with no configuration —
rejected, the user asked for it to be configurable in the way the state dir is.

## 5. How the in-force set reaches the agent

**Decision**: Add a step to the `start-session` skill, which already runs
`wfctl start` and `wfctl doctor`.

**Rationale**: This is the finding that changed the plan. The obvious path — a
`SessionStart` hook — is **not a path wfctl controls in this repository**. The
hook that loads output-style skills lives in the user's own
`~/.claude/settings.json`, not in the repo and not seeded by wfctl. Managing
hooks inside a settings file the consumer owns is open issue #85, so routing
FR-009 through a hook would make this feature depend on unshipped work.

`start-session` is wfctl-owned, ships in the skills bundle, is harness-agnostic,
and already exists to load session context. Adding `wfctl arch context` to it is
zero new plumbing and satisfies FR-009's wording — *the same path as existing
session guidance*.

**Alternatives considered**: a `SessionStart` hook — deferred to #85, and
per-harness rather than universal. Injecting into `AGENTS.md` — rejected in
`design.md` as it ends the hand-authoring that gives that file its value.

**Known limitation**: `start-session` runs when invoked, not automatically. An
agent that never runs it does not receive the in-force set. This is the same
reach the rest of wfctl's session guidance has, so the feature is no worse off
than what exists — but it is not the same as unconditional delivery, and #85
would close that gap.

## 6. Record format versioning

**Decision**: Not versioned. Deferred from `/speckit.clarify` as low impact.

**Rationale**: A record is read by scanning for known keys and ignoring the rest.
Adding a field later leaves older records readable, because absent keys already
have defined defaults (`status` absent means excluded). The format only needs a
version if a key's *meaning* changes, which is a change we would be choosing to
make and can carry its own migration then.

**Alternatives considered**: a `format:` key on every record from day one —
rejected as speculative; it costs a field on every record to solve a problem that
has not occurred.

## 7. Retiring the orphaned promotion command

**Decision**: Remove `wfctl promote`, `_session.promote`, the
`WFCTL_CANDIDATES_FILE` environment variable, its README row, and its tests.

**Rationale**: Verified orphaned. `wfctl promote` reads
`<state-dir>/memory-candidates.md`; a repository-wide search finds that filename
only in `cli.py:580`, `README.md:479`, and `tests/test_agent_session.py` — no
producer anywhere. It writes `<state-dir>/promoted/<date>.md`, which nothing
reads. Left in place it is a second, contradictory promotion mechanism competing
with the one this feature introduces.

**Alternatives considered**: give it a producer and reuse it — rejected, its sink
is machine-local and per-branch, which fails the epic's continuity principle
outright.
