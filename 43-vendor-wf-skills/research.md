# Research: Vendor wf-skills

**Feature**: [spec.md](./spec.md) · **Design**: [design.md](./design.md)

The brainstorm settled the direction and the major trade-offs; `design.md` is the
record and is not repeated here. This file covers only what planning had to
resolve on top of it — three questions that were load-bearing and unverified, and
two that changed shape once the code was read closely.

---

## 1. Does a wheel preserve the executable bit on `.specify/scripts/*.sh`?

**Decision**: Yes. No `chmod` step is needed at install time.

**Why this was a blocker.** Every speckit skill invokes its scripts by bare path
— `.specify/scripts/bash/check-prerequisites.sh --json` — not through `bash <file>`.
The five scripts are mode `755` on disk today because they arrive from a `git
clone`, which restores the bit git tracks. Vendoring routes them through a wheel
instead, and if that path dropped the bit, every speckit command would break with
`Permission denied` — after a green test suite, since the suite copies from a
source tree that still has the bit.

**Evidence.** Built a throwaway setuptools package with a `chmod +x`'d `.sh` and a
plain `.json` under `package-data`, then read the archive back and installed it:

```
modepkg/scripts/data.json: mode=0o100644 exec=NO
modepkg/scripts/run.sh:    mode=0o100755 exec=yes
installed mode=0o755 exec=yes
```

The mode round-trips through `build_py`, the zip's `external_attr`, and the
installer. `shutil.copy2` — already what `install-skills` uses — preserves it on
the final copy into the repo.

**What still has to be true**, and is not automatic: the vendored `.sh` files must
be *committed* with git's exec bit set. A `cp` that lands them `644` produces a
wheel that faithfully preserves `644`. This is why the wheel job asserts the bit
rather than assuming this finding covers it.

**Alternatives considered**: `os.chmod(0o755)` on `.sh` after copy (unnecessary
work, and it would mask a genuinely broken bundle); hashing file modes into the
fingerprint so `doctor` reports a lost bit (couples the fingerprint to umask and
buys one assertion's worth of coverage for real complexity — rejected in favour of
the assertion).

## 2. Does `importlib.resources.files()` return a real path on the floor version?

**Decision**: Yes — `files("wfctl")` without `as_file()`.

**Evidence.** Against the wheel installed above, on wfctl's floor interpreter:

```
3.11.14 PosixPath True True
```

A concrete `PosixPath`, which `shutil.copytree` and `Path.iterdir` accept
directly. `as_file()` exists to materialise resources that may live inside a zip;
`uv tool install` and `pip install` both produce a real directory, so that path is
unreachable here and the context manager would be ceremony.

**Alternatives considered**: `Path(__file__).parent` (works identically, but is
what linters flag and what breaks under any non-filesystem loader);
`as_file(files(...))` (correct but unreachable, and adds a `with` block around the
whole install).

## 3. Where do the bundle root and the fingerprint live?

**Decision**: a new module, `wfctl/_bundle.py`, holding two things — the bundle
root constant and the whole-tree hash.

**Rationale.** This is the same argument `_manifest.py` already documents in its
own docstring: both `cli` commands need it, and putting it in `cli` means the
fingerprint cannot be exercised without importing typer, rich, and every command.
`cli.py` is ~1900 lines; the hash is the one piece of this change with real logic
worth testing in isolation. Two call sites and a testability argument is enough —
this is not an abstraction invented for a single caller.

**Alternatives considered**: inline in `cli.py` (cheapest diff, but the hash test
then drags the whole CLI in); a `_resources.py` split from a `_hash.py` (two
modules for ~30 lines).

## 4. How do tests point at a different bundle?

**Decision**: `monkeypatch.setattr` on the module-level constant. Test-only, no
shipped surface.

**Rationale.** The obvious alternative — a `WFCTL_BUNDLE_ROOT` environment
variable — would fit this repo's existing habit (`WFCTL_REPO_ROOT`,
`WFCTL_STATE_DIR`, `WFCTL_SPEC_DIR`) but is the wrong shape here: it is a shipped,
user-reachable override for where skills come from, which reintroduces the second
source of truth the feature exists to remove. A monkeypatched constant is
invisible outside the suite.

The constant must be read at call time through a module-global lookup, not bound
as a default argument, or `setattr` will not reach it.

**Alternatives considered**: env var (above); `importlib.resources` patching (patches
a stdlib seam rather than our own, and breaks whenever the resolution call moves).

## 5. Corrections to the design's read of the test suite

Two claims carried from the brainstorm did not survive reading the files.

**"Eleven git-repo fixtures collapse to one."** The eleven were miscounted: the
`agent_dir` / `storyctl_dir` / `repo_root` fixtures in `conftest.py` build the
*destination* repo, which this feature does not touch — `install-skills` still
requires a git repo to install into. What actually changes is three **source**
builders, referenced on ~80 lines:

| Builder | Referencing lines (incl. its `def`) |
| --- | --- |
| `tests/test_install_skills.py:22` `_make_wf_skills_repo` | 63 |
| `tests/test_install_config.py:18` `_make_wf_skills_repo_with_config` | 15 |
| `tests/test_tracker.py:260` `_make_wf_skills_repo_with_tracker` | 4 |

Each becomes a plain-directory builder: same tree, no `git init`, no `add`, no
`commit`. The call sites keep their shape but drop `--repo`/`--ref` from the
invocation.

**"The clone-failure test deletes."** There is no test named for a clone failure.
The one `GIT_TERMINAL_PROMPT` protects is
`test_install_skills.py:251 test_install_skills_bad_repo_exits_one`, which passes a
real nonexistent GitHub URL. It deletes along with the flag it exercises, and the
`env:` block at `ci.yml:70-71` goes with it — but so does the suite's last
unstubbed network call, which is worth stating as a gain rather than a deletion.

## 6. What happens to a caller passing `--repo` / `--ref`?

**Decision**: delete the options outright and let typer's own unknown-option
handling satisfy FR-004. No code.

**Evidence.** Confirmed on the current build — an unrecognised option exits 2,
prints `Usage:`, `Try 'wfctl install-skills --help' for help.`, and an error panel
naming the offending flag. That is the "explanatory error" FR-004 asks for.

The flags are effectively undocumented: `README.md` never shows either in a usage
example, mentioning `--ref` once in prose (line 260) that this change rewrites
anyway. A script passing them fails loudly and immediately, and `--help` shows
what replaced them.

**Alternatives considered**: keeping them `hidden=True` with a tailored "wfctl
ships skills as of 0.15.0" message (~8 lines per command, and dead options carried
in the signature indefinitely — worth it only if a script in the wild is known to
pass them); accepting and ignoring them with a warning (**rejected outright** — it
installs content the caller did not ask for, which is the exact failure this
feature exists to remove).

## 7. Self-hosting: wfctl installs its own skills

**Decision**: accepted as-is, with one documentation change and no code for it.

`.agents/` and `.specify/` are gitignored in this repo (`.gitignore:12-14`) —
they are `install-skills` *output*, not source. After vendoring, the committed
source is `wfctl/agents/` and `wfctl/specify/`, and this repo's own `.agents/`
becomes a copy of its own package data.

The consequence is a real editing loop, not a hazard: change
`wfctl/agents/skills/<x>/SKILL.md`, run `wfctl install-skills`, and the working
copy updates. Under an editable install the version never moves, which is exactly
the case the content fingerprint exists to cover. `AGENTS.md` does not exist in
this repo, so there is nothing here to correct — the wf-skills#27 item 2 wording
fix lands in the migrated repo after the transfer.

**Not doing**: renaming `.wf-skills-manifest.json` or `.wf-skills-backup/`. The
names are stale after this change, but every installed repo's backup pointers are
recorded relative to that directory, and renaming trades a cosmetic gain for a
restore path that silently misses. Separate change, if ever.
