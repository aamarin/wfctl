# Vendor wf-skills into wfctl's package

Design for [wfctl#43](https://github.com/aamarin/wfctl/issues/43). Implements the
decision recorded in wfctl#1.

## Problem Statement

How might we make `wfctl install-skills` produce the same result every time it runs,
given that wfctl and its skills are currently two independently versioned artifacts
with nothing pinning them together?

## Recommended Direction

Ship the skills inside wfctl's wheel as package data and read them through
`importlib.resources`. Delete every call to `aamarin/wf-skills`, then archive that
repo.

The problem being solved is **determinism, not offline capability**. Today
`install-skills` clones `--ref main` — a moving target — so two repos on the same
wfctl version can hold different skills, and running the same command six months
apart gives different results from identical inputs. A skill that references a
command added in wfctl 0.15.0 can land in a repo running 0.14.0 with nothing
detecting it. After vendoring there is one artifact and one version.

Removing the network call is a consequence, not the goal. It does remove a real
failure class — GitHub outages, rate limits, proxies, git prompting for credentials
(already worked around in `ci.yml:71`) — and it takes `install-skills` from ~15s to
instant, but neither would justify the change on its own.

**The cost is losing independent skill releases.** Today a typo fix in a skill is a
push to wf-skills and everyone picks it up on their next `install-skills`. After
this it requires a wfctl release. That trade is right *here* because the same author
owns both, wf-skills is being archived regardless, a release is a tag, and skills
change far less often than the coupling problem bites. If skills iterated faster than
wfctl, or a third party owned them, the answer would be the opposite.

---

## What changes

Five areas. Each is recorded at the level where the decision lives; implementation
detail belongs to the plan, not here.

### 1. Package layout and resource resolution

**Behavior**

```
# now — needs network, ~15s
$ wfctl install-skills
Cloning aamarin/wf-skills@main... ✓
Installed 57 items

# proposed — no network
$ wfctl install-skills
Installed 57 items (wfctl 0.15.0)
```

`--repo` and `--ref` disappear from both `install-skills` and `install-config`.
Offline installs work. That is the entire user-visible surface of this area.

**Design**

Bundled content lives at `wfctl/agents/` and `wfctl/specify/` — flat under the
package, matching `wt-tool`'s `wt_tool/skills/` convention rather than a `_bundled/`
wrapper.

**The leading dots must be stripped.** This is verified, not assumed: a scratch wheel
built with both a dotted and an undotted control file shipped only the undotted one.
setuptools drops `.`-prefixed directories from `build_py` silently — no warning,
exit 0.

`pyproject.toml` gains a section it does not currently have:

```toml
[tool.setuptools.package-data]
wfctl = ["agents/**/*", "specify/**/*"]
```

Without it the wheel ships zero content.

Resolution uses `importlib.resources.files("wfctl")` and **not** `as_file()`.
`as_file` exists to materialize resources that might live inside a zip; wfctl is
installed by `uv tool install` / `pip install`, which always produce a real
directory, so that path is unreachable. `files()` returns a concrete `PosixPath` for
any filesystem install, which `shutil.copytree` accepts directly. Verified on Python
3.11.14, wfctl's floor.

The bundle root is a **module-level constant**, not resolved inline at each call
site — one patch point for tests instead of several.

Every install target is already an `(src, dst)` tuple, so only the source half
changes. `_BASE_TARGETS`, `_AGENT_TARGETS`, `_RUNTIME_TARGETS` and `_CONFIG_SOURCES`
keep their destinations, and installed repo layout is unaffected.

**One source is not in any of those lists.** `install-skills` copies
`.agents/trackers/github.json` inline at `cli.py:1196-1210`, gated on
`--tracker github`. It moves to `wfctl/agents/trackers/github.json` like everything
else — the `agents/**/*` glob already covers it — but two things follow: its
not-found message at `cli.py:1206-1210` interpolates `{repo}@{ref}`, variables that
stop existing and must be reworded; and because it belongs to no target list, it is
the reason the staleness fingerprint hashes the whole tree rather than per layer
(see area 2).

**Deleted:** both clones, the `git rev-parse HEAD`, the `--repo`/`--ref` options, and
the `subprocess`/`tempfile` imports that served them.

### 2. Staleness detection

**Behavior**

```
$ wfctl doctor
⬆ wfctl 0.14.0 → 0.15.0 available
    upgrade: uv tool install --upgrade ...
⬆ base: skills stale — installed by wfctl 0.14.0, running 0.15.0
    update: wfctl install-skills
```

```
$ wfctl doctor          # healthy
✓ wfctl 0.15.0 — latest
✓ base: skills current (wfctl 0.15.0)
```

```
$ wfctl doctor          # offline
⚠ wfctl 0.15.0 — couldn't check latest (offline?)
✓ base: skills current (wfctl 0.15.0)
```

**Architecture**

Authority for "are these skills current?" moves from the git remote to the installed
wheel. Today the answer is defined by a remote branch tip: it can change without you
doing anything, and answering requires network. After vendoring the answer is defined
by the artifact you have installed: it changes only when you upgrade, and answering is
a local comparison.

That splits one question into two independent ones:

| Question | Check | Network |
| --- | --- | --- |
| Is my wfctl behind the latest release? | `_check_wfctl_version` (exists, unchanged) | yes |
| Is this repo behind my wfctl? | new local comparison | no |

**wfctl#43's original text said this "collapses into `_check_wfctl_version`". It does
not.** That function compares the installed tool to the latest release tag and knows
nothing about any repo's `.agents/`. Deleting the per-layer check outright would mean
`uv tool upgrade wfctl` leaves stale skills in every repo with nothing reporting it.
So: **replace, do not delete.** The issue has been corrected.

The two checks are independent. A network failure degrades the release check to a
warning — already its behaviour at `cli.py:1610-1612` — while the skills check still
answers. Offline `doctor` becomes useful, which it is not today.

**Design**

Manifest provenance fields change:

```json
// now
"base": { "repo": …, "ref": "main", "commit": "9ee468a", "installed_at": …, "items": […] }

// proposed
"base": { "wfctl_version": "0.15.0", "content_hash": "9f2a1c…", "installed_at": …, "items": […] }
```

`items` is untouched — `uninstall-skills` and wfctl#38's orphan diff still need it,
and the per-item backup pointers it carries must survive.

Both new fields are needed:

| Option | Problem |
| --- | --- |
| version only | Frozen at install time under `--editable`, so edits to `wfctl/agents/` never register. Also silent through a forgotten version bump. |
| hash only | Correct, but the message degrades to two truncated hashes. |
| **both** | Hash decides, version explains: *"installed by 0.14.0, running 0.15.0."* |

For a released install, version alone would in fact be sufficient. The hash earns its
keep in exactly two cases: **editable dev installs** — which becomes the primary
authoring loop for skills once they live in this repo — and a botched release where
content changed and the version did not.

Both of those cases produce a stale result with *equal* versions on both sides, so
the message needs a second string. `installed by 0.15.0, running 0.15.0` reads as a
bug; something like `bundled skills changed since install` is the honest report when
the hash differs and the version does not.

The fingerprint covers **the whole bundled tree**, not each layer's own sources. Every
layer entry therefore records the same hash.

Per-layer was the first choice — the target lists already partition the tree, so
parameterizing looked free — but it has a silent-miss failure mode. `install-skills`
also copies `.agents/trackers/github.json` inline (`cli.py:1196-1210`), and that path
appears in no target list, so a per-layer hash would leave edits to it invisible. A
whole-tree hash has no coverage holes by construction and nothing to keep in sync as
sources are added later.

The cost is over-reporting: a `.specify/` edit marks every layer stale. That is noise
with a correct remedy — `wfctl install-skills` is the fix either way — and noise beats
a silent miss.

It must cover file paths as well as contents, or a pure rename hashes identical, and
it must iterate in sorted order or the hash is unstable across filesystems and reports
permanent drift.

**Deleted:** `git ls-remote`, the temp-dir clone, and the `git diff --stat` at
`cli.py:1881-1905`. After this, doctor's only network call is the release-tag lookup.

### 3. `install-config`

wfctl#43 does not mention it, but it clones too (`cli.py:1476`).

**Behavior**

```
# now
$ wfctl install-config workmux
Cloning aamarin/wf-skills@main... ✓
Wrote .workmux.yaml

# proposed
$ wfctl install-config workmux
Wrote .workmux.yaml
```

**Why it is in scope**

Leaving it behind means wfctl permanently reads from an archived repo — the second
source of truth the issue exists to eliminate — and wfctl#43's claim to remove the
network dependency would be false.

It also *deletes* duplication rather than abstracting it. The note at `cli.py:1475`
reads "dup'd clone from install_skills_cmd; extract a helper if a 3rd caller
appears." With no clone in either place, the helper never gets written.

**Design**

Unlike `install-skills`, `install-config` writes no manifest entry, so it gets **no
staleness check**. Seed-once means the file becomes the repo's own and wfctl stops
caring the moment it is written.

`_CONFIG_SOURCES` (`cli.py:682`) changes its value only:
`.agents/configs/workmux` → `agents/configs/workmux`. The key and every destination
stay put. Conflict detection, `--force`, and the workmux post-write step are
untouched.

### 4. Testing

**Behavior**

```
# now
CI: test (3.11, 3.13) · lint

# proposed
CI: test (3.11, 3.13) · lint · wheel
```

**Architecture**

The suite currently never touches the artifact. `uv sync` installs editable against
the source tree, where `wfctl/agents/` exists whether or not it is declared as
package data. The entire suite can pass green while the wheel ships nothing — exactly
the failure reproduced during design.

That gap is tolerable today because the artifact is only code, and a missing module
fails loudly on import. After this change the artifact's *contents* are the product,
and a missing content file fails quietly.

Note this is not deferred until a PyPI release: `uv tool install git+https://…`
clones and builds a wheel, so every install already goes through the packaging path.

**Design**

The wheel job does four things: `uv build`; install the wheel into a clean
environment (not editable, not the source tree); run `wfctl install-skills` in a
scratch git repo; assert the skills landed. Step 2 is the point — it is the only
place `package-data` is exercised.

It does **not** run the full suite. Logic is identical whether loaded from source or
wheel; only content presence differs. That is one assertion, not three hundred.

Existing tests build throwaway git repos so they can control what gets installed.
With a fixed bundled source they need another route in:

| Option | Trade |
| --- | --- |
| **Monkeypatch the bundle root** | Tests keep controlling content; one fixture replaces eleven |
| Use the real bundled tree | Simpler, but assertions break whenever a skill is renamed |

Monkeypatch for content-specific tests; the real tree only for the wheel smoke check.
`monkeypatch` is function-scoped and self-undoing, so a shared `conftest.py` fixture
gives shared setup with automatic per-test teardown.

Mechanical fallout: eleven git-repo fixtures (`conftest.py:72,113`,
`test_install_skills.py:39,84,100,203,224,241,306`, `test_install_config.py:28`,
`test_tracker.py:283`) collapse to one temp-directory fixture; four assertions on
`repo`/`ref`/`commit` (`test_install_skills.py:459,505`, `test_spec_root.py:188,196`,
`test_paths.py:267`) move to the new fields; the `GIT_TERMINAL_PROMPT: 0` workaround
and the clone-failure test both delete, since there is no clone left to fail.

### 5. Migration

**Behavior**

```
$ wfctl doctor
✓ wfctl 0.15.0 — latest
⚠ base: installed before content hashing — re-run install-skills

$ wfctl install-skills
Installed 57 items (wfctl 0.15.0)

$ wfctl doctor
✓ wfctl 0.15.0 — latest
✓ base: skills current (wfctl 0.15.0)
```

**Design**

A manifest with no `content_hash` produces one warning and continues — the same shape
as the existing missing-`commit` branch at `cli.py:1874-1879`, so pre-#43 manifests
degrade instead of crashing.

No data loss. The vendored copy comes from the same wf-skills tip the repo already
installed, so the re-install is effectively a manifest rewrite.

Stale `repo`/`ref`/`commit` keys are **dropped** on rewrite, not preserved. They
describe a fetch that no longer happens, and keeping them leaves a manifest claiming
a provenance the tool cannot act on. If origin ever needs tracing, the vendored tree
has its own git history in wfctl.

---

## Key Assumptions to Validate

- [ ] **The `package-data` globs cover everything.** Test: the new wheel CI job — build,
      install clean, `install-skills`, assert item count matches the source tree.
- [ ] **Dot-stripping breaks nothing downstream.** Only source paths change and every
      target is an `(src, dst)` tuple, but
      `test_layer_destinations_are_disjoint` and the backup-attribution tests are the
      check that destinations really did stay put.
- [ ] **The whole-tree hash is stable across machines.** Test: compute twice in CI on
      both matrix Pythons and on macOS/Linux; a differing hash means unsorted
      iteration or path-encoding drift.
- [ ] **The hash covers every installed source.** Test: touch one file in each of
      `agents/skills`, `agents/commands`, `agents/trackers`, `agents/configs`, and
      `specify/templates`; each must change the hash. This is the check that would
      have caught the tracker gap.
- [ ] **The re-install really is a no-op on content.** Test: on a repo installed from
      wf-skills tip `9ee468a`, run the new `install-skills` and diff `.agents/` —
      expect empty.

## MVP Scope

**In:**

1. `wfctl/agents/` and `wfctl/specify/` as package data, with the `pyproject.toml`
   section that makes them ship.
2. Both clones deleted; `--repo`/`--ref` removed from `install-skills` and
   `install-config`.
3. Manifest schema change plus the local whole-tree staleness check in `doctor`,
   replacing the network one.
4. Migration warning for hash-less manifests.
5. The wheel CI job.
6. Test fixtures converted from git repos to a monkeypatched bundle root.

**Out:** everything in "Not Doing" below.

## Not Doing (and Why)

- **A release-time sync step** — a sync step exists to keep two sources of truth
  aligned, and after this there is one.
- **`--repo` / `--ref` as an escape hatch** — wfctl#1 decided against preserving
  external sources. Keeping them would preserve exactly the drift this removes. This
  changes wfctl#35 A2/A3 from "default from the manifest" to "the flags are gone".
- **File-level drift detail in `doctor`** — there is no history to diff against a
  snapshot. Both trees are on disk so a comparison is possible, but the remedy is
  `wfctl install-skills` regardless of what changed, so the detail changes nothing the
  user does. Add when someone asks what changed before running it.
- **Local-edit detection** — the same machinery would catch editing
  `.agents/skills/…` inside this repo and losing it on the next install. Real hazard,
  different check, different message. Deserves its own issue.
- **Running the full suite against the wheel** — slower and redundant; only content
  presence differs between source and wheel.
- **Switching build backend to hatchling** — it would include package directories
  without a `package-data` incantation and would not have dropped the dotted
  directories, but stripping the dots solves the only painful part. Not worth the
  churn.
- **`setuptools-scm` for versioning** — would remove the manual bump and make the tag
  the single source of truth, which is adjacent to the `wfctl_version` field here. Real
  improvement, separate change.
- **Reversing the `.specify/` vendoring** — `.specify/` is spec-kit's generated output
  and vendoring it here makes wfctl a second-order vendor. wf-skills#16 (adopting
  spec-kit's extension system) is the eventual reversal and migrates with the rest.
  Confirmed during design that `.specify/` no longer carries pfms-specific content —
  wf-skills#10 decontaminated it, and wf-skills#16's measurement of that is stale.
- **Batching the gitignore checks** — the note at `cli.py:812-814` defers this because
  ~600ms is nothing "against a ~15s clone". Removing the clone makes it the dominant
  cost, so it becomes worth re-measuring. Not part of this change.

## Sequencing

**Vendor first, then transfer issues, then archive.** Three of wf-skills' open issues
are actively harmed by being fixed in wf-skills first (wf-skills#27 item 2,
wf-skills#22, wf-skills#14). `gh issue transfer` must run before archiving, since
archiving makes the tracker read-only.

All **seven** open wf-skills issues migrate — wf-skills#1, #14, #16, #22, #23, #27,
#28 — not the four wfctl#43 originally listed. None close on migration, though four
need editing on the way over: #16 (stale contamination measurement), #27 (item 2
obsoleted by this change), #14 (stale code quote), and #1 (needs re-scoping).

This lands **before wfctl#41's PR A**, which normalizes a return contract across
doctor's checks — one of which this change rewrites.

## Open Questions

- **What happens to the archived wf-skills repo** — read-only mirror, or left as-is.
  (wfctl#43 item 4, still open.)
- **Which tracker the migrated issues land in** — decided during the move.
- **Does the wheel CI job belong in this issue's scope** or its own? It is the only
  thing that can catch a packaging regression, which argues for here.
