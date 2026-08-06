# Research: spec-root-manifest-key

No `NEEDS CLARIFICATION` markers survived `/speckit.specify` or
`/speckit.clarify`, so Phase 0 records the decisions already taken — each with
the evidence that settled it — rather than opening new questions.

## D1 — Config lives in `.wf-skills-manifest.json`, not an env var

**Decision**: A `spec_root` key in the existing per-repo manifest.

**Rationale**: `WFCTL_SPEC_DIR` is process-global. The only way to make an env
var persistent is to export it from a shell profile, which then redirects *every*
repository wfctl touches to one spec root. A file at `<repo>/.wf-skills-manifest.json`
cannot leak across repos by construction. The file is already read by the CLI
(`_load_manifest`, `cli.py:644`) and already carries a non-layer scalar key
(`tracker`), so this adds a key to an established shape rather than a config
surface.

**Alternatives considered**:
- *Extend `WFCTL_SPEC_DIR` to the create path* — rejected above; it is retained
  as a per-invocation override.
- *A new committed config file* (`.wfctl.json`, or a key in `.workmux.yaml`) —
  would propagate to worktrees via git for free, which is genuinely attractive.
  Rejected because it adds a config surface to read, document, and keep
  consistent with the manifest, when D2 solves propagation with no new file.

**Source**: issue #18 "Fix direction", quoting `MarinVentures/pfms#499`.

## D2 — The manifest lookup falls back to the main checkout

**Decision**: When the current repo root's manifest declares no `spec_root`, read
the main checkout's manifest — but only when the git common dir is named exactly
`.git`.

**Rationale**: Verified, not assumed — `.wf-skills-manifest.json` is gitignored
(`.gitignore:15`) and untracked (`git ls-files` reports it unknown), and
`.workmux.yaml:72` runs `wfctl install-skills` in every fresh worktree, which
writes a brand-new manifest containing only `base`/`claude`/`tracker`. A
worktree-local `spec_root` therefore cannot exist at the moment the pipeline
first runs there. Without a shared read location the setting is unreachable
exactly when it matters, and specs fall back into the worktree and die with it —
the failure this feature exists to remove.

The `.git`-name guard is the safety property. In this layout
`git rev-parse --git-common-dir` returns `/Users/andremarin/Development/wfctl/.git`,
whose parent is the main checkout. In a bare or separate-gitdir layout it returns
`<something>.git`, whose parent is a container directory that may hold an
unrelated project's manifest; reading that would silently apply another repo's
spec root. When the name does not match, there is no fallback.

**Alternatives considered**:
- *Per-worktree config with an `install-skills --spec-root` flag* — trades a
  manual symlink step for a manual config step in every worktree; the same
  "someone forgets" failure mode, differently spelled.
- *Walk parent directories for a manifest* — unbounded, and could pick up a
  manifest from any ancestor directory. The git common dir is the only
  authoritative link from a worktree back to its project.

**Precedent**: `project_name()` (`_paths.py:194`) already resolves the main
checkout from a worktree via `--git-common-dir`, for the same reason — a
worktree's own directory is named after its branch and is not the project.

## D3 — Precedence: env override wins over the recorded setting

**Decision**: `WFCTL_SPEC_DIR` → manifest `spec_root` → `repo_root / "specs"`.

**Rationale**: An explicit per-invocation flag beating persistent config is the
conventional order, and issue #18's acceptance criteria require the env var to
keep working. It stays an escape hatch (`WFCTL_SPEC_DIR=/tmp/x wfctl
feature-paths`), never the recommended way to configure a repo.

## D4 — `spec_root` must be a non-layer manifest key

**Decision**: `_NON_LAYER_KEYS = frozenset({"tracker", "spec_root"})`.

**Rationale**: `_layer_keys` (`cli.py:530`) returns every manifest key not in that
set, and `cli.py:728` does `manifest[key].get("items", [])`. With `spec_root` a
bare string, the next `install-skills` raises `AttributeError: 'str' object has
no attribute 'get'`. `doctor` (`cli.py:1361`) iterates the same helper. This is a
correctness requirement, not tidiness.

With the key registered, durability follows from the existing code:
`install_skills_cmd` loads the current manifest (`cli.py:717`), rewrites only
layer entries (`cli.py:894`), and saves (`cli.py:927`), so unrecognized keys pass
through — `tracker` is the standing precedent. `uninstall` deletes only its own
agent key (`cli.py:1023`). A test pins this rather than trusting the reading.

## D5 — No fallback to `<repo>/specs` once a root is recorded

**Decision**: The recorded root is the only root. `doctor` reports the case where
a root is recorded and `<repo>/specs/` still holds spec directories.

**Rationale** (`/speckit.clarify` Q1): a read-fallback would let one feature's
artifacts split across two locations — `spec.md` found in the old root while
`plan.md` is written to the new one. A single root keeps resolution predictable;
the diagnostic keeps the transition from being silent, which is the failure class
this whole issue is about. Migration of existing specs stays out of scope
(`MarinVentures/pfms#499` owns it).

**Placement note**: `doctor_cmd` returns early when no layers are installed
(`cli.py:1362`), so the check must be called *before* that gate — beside
`_check_workmux_hook` (`cli.py:1358`), which sits there for the same reason.

## D6 — An unparseable manifest fails loudly

**Decision**: No error swallowing. A malformed manifest raises, in both the
current repo and the main checkout.

**Rationale** (`/speckit.clarify` Q2): this feature exists because a path
silently resolved to the wrong place. Defaulting on a corrupt config recreates
that — specs land in the worktree with no signal. Failing names the file and is
fixed in seconds. It also matches today's behavior: `_load_manifest` calls
`json.loads` unguarded, so reusing it delivers this requirement with no code.

**Alternative considered**: tolerate a malformed *main checkout* manifest with a
stderr warning, so a corrupt file in another directory cannot block this
worktree. Rejected as inconsistent — and a warning printed during an `eval`'d
command is easy to miss, which is how a silently misplaced spec happens.

## D7 — The root is never created or validated

**Decision**: `spec_root()` and `wfctl spec-root` neither create the directory nor
check that it exists.

**Rationale**: A not-yet-existing directory is the precise case that broke the
create path — `resolve_spec_dir` returns `None` for it, and the hardcoded
fallback took over. Re-introducing an existence check would rebuild the bug.
`setup-plan.sh` already creates the feature directory when it writes there.
