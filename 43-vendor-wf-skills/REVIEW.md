# Review: `delivery.md` + issues #45/#46 (43-vendor-wf-skills)

**Date**: 2026-08-16
**Target**: not a code diff — the branch is at `241b245`, identical to `master`,
clean tree, zero commits. Implementation has not started. The reviewable work
product is `delivery.md` and the two issue bodies created from it, which are
implementation instructions with file:line references.
**Out of scope**: `spec.md`, `plan.md`, `tasks.md` — covered by
[analysis-report.md](./checklists/analysis-report.md), which ran before
`delivery.md` existed.

---

## Findings

### BLOCKER — the wheel job cannot pass in PR 1

`delivery.md` (PR Decomposition), issue #45 acceptance criterion 6, `tasks.md`
T040.

T040 specifies a job that "runs `wfctl install-skills` in a scratch git repo, and
diffs the installed tree against `wfctl/agents`/`wfctl/specify`". I moved it into
PR 1 on the argument that the bundle should never be unverified. **That argument
does not survive contact with T040's actual assertion.**

PR 1 does not touch `cli.py`. In PR 1, `install-skills` still clones
`aamarin/wf-skills@main` and installs from the clone. The job would therefore
diff *upstream `main`* against the *vendored copy*, which:

- requires network in CI, in a job whose whole premise is the offline bundle;
- passes only while upstream `main` happens to match the tree T001 copied, and
  fails the moment upstream moves — a green job that means nothing, then a red
  job that means nothing.

T041 inherits the defect: "executable after install" means after
`install-skills`, same dependency.

**Fix — split T040 by what each half can actually assert.**

| Half | Assertion | PR |
| --- | --- | --- |
| Packaging | build the wheel, install it into a clean env, assert `wfctl/agents/**` and `wfctl/specify/**` are present in `site-packages` and the `.sh` files are mode `755` there | PR 1 |
| End-to-end | run `wfctl install-skills` in a scratch repo, diff the installed tree against the bundled tree, assert the exec bit survived the copy | PR 2 |

The PR 1 half still fails on a broken `package-data` glob or a lost exec bit —
the two failure modes that justified pulling the job forward — with no
behavioural dependency and no network. The PR 2 half is the FR-018 / SC-002
end-to-end claim and belongs with the code that makes it true.

### WARNING — "~80 files" is unverified, and was used to correct a different number

`delivery.md` (File-touch matrix note), `tasks.md` Incremental Delivery.

I counted **64** files in this repo's installed `.agents/` + `.specify/`, then
inferred "~80" for a fresh clone. The inference is loose: the installed tree
already carries per-skill `assets/` and `references/`, so a fresh clone adds only
`trackers/github.json` and `configs/workmux/*` — roughly **66**, not 80.

Replacing "thousands" with another unverified figure is the same error at a
smaller scale. State what is verified: **64 files installed today, plus trackers
and configs — under 100.** The exact count lands when T001 runs; it is not worth
a clone to pin now.

The reviewability argument the number supports is unaffected either way.

### WARNING — no task owns the deferred half of the wheel job

Follows from the BLOCKER. Once T040 splits, PR 2 must extend the job, and
nothing in `delivery.md`'s PR 2 wave table or issue #46 says so. PR 2 Wave 11
currently lists only T042/T043 against `ci.yml`.

**Fix**: add the end-to-end extension to PR 2 Wave 11 alongside T042/T043, and to
issue #46's entry points and acceptance criteria. Without it, the FR-018
end-to-end assertion is dropped by both PRs — each assuming the other has it.

### NIT — `Closes #46, Closes #43` looks like a rule violation

`delivery.md` (PR Decomposition).

SKILL.md's red flags list "a PR closes multiple issues → restructure", while
`references/issue-grouping-patterns.md` Pattern 4 explicitly sanctions the parent
close on the final PR. The plan follows the reference, but a future reader
checking against the red-flag list will read it as a defect and "fix" it.

**Fix**: one clause naming the exception. Already partly present ("the parent
close is on the final PR only") — make it cite Pattern 4.

### NIT — T011's autouse fixture is inert in PR 1

The fixture monkeypatches `wfctl._bundle.BUNDLE_ROOT` so "no test silently reads
the real bundle". In PR 1 nothing reads it — `cli.py` is untouched and
`test_bundle.py` builds its own trees. It is harmless there and load-bearing in
PR 2.

Not a defect; the module and its seam belong together in PR 1. Worth one line in
issue #45 so a reviewer does not go looking for the fixture's effect and find
none.

---

## Over-engineering pass

`delivery.md:L…` (Agent Fanning Instructions): `delete:` three near-identical
agent prompts (~45 lines) for T013/T014/T015, immediately preceded by
"Recommended: a single agent per PR" and followed by an explanation of why every
*other* wave should not be fanned. Three copies of one template, for the one wave
I advise against fanning. → one prompt template plus "identical for T014
(`test_install_config.py:18`) and T015 (`test_tracker.py:260`)".

`net: −30 lines possible`

---

## Verified clean

- `cli.py` anchors cited in issue #46 — `:630`, `:641`, `:672`, `:682`, `:963`,
  `:1436`, `:1840` — all correct against the current file.
- Test-builder anchors in the fanning prompts — `test_install_skills.py:22`,
  `test_install_config.py:18`, `test_tracker.py:260` — all correct, as is the
  `subprocess` import at `test_install_skills.py:4`.
- Wave completeness: 50 tasks, 15 in PR 1 and 35 in PR 2, each in exactly one
  wave, none duplicated, none dropped. Re-counted rather than trusted.
- `.gitignore` does not endanger the vendored tree. `.agents/` is a
  non-anchored pattern and matches at any depth, but only the *dotted* name — so
  `wfctl/agents/` is unaffected. The dot-strip that `research.md` justifies on
  setuptools grounds turns out to be load-bearing for git too. Worth a sentence
  in `plan.md`'s Structure Decision.
- T048 → T049 ordering is right: the quickstart install must precede the version
  bump for T049 to have a prior-version repo to compare against.
- PR 1 leaves `pytest` green — the autouse fixture patches a constant nothing
  reads yet.

---

`net: −30 lines possible`
**Verdict: Request changes** (1 blocker, 2 warnings)

---

## Remediation applied (2026-08-16)

| Finding | Resolution |
| --- | --- |
| **BLOCKER** | T040/T041 rescoped to assert against `site-packages` only; new **T051** carries the end-to-end half (`install-skills` + tree diff + exec bit after copy) into PR 2. Appended rather than inserted, so no existing task ID renumbers and every cross-reference still resolves. Task count 50 → 51; PR 2 goes 35 → 36 tasks. |
| **WARNING** (file count) | Both `delivery.md` and `tasks.md` now state the verified 64 plus trackers and configs, "under 100", with the exact count deferred to T001. |
| **WARNING** (orphaned assertion) | T051 added to `tasks.md` Phase 6, `delivery.md` PR 2 Wave 11, and issue #46's entry points, acceptance criterion 10 and verification table. |
| **NIT** (double `Closes`) | `delivery.md` now cites Pattern 4 as the sanctioned exception. |
| **NIT** (inert fixture) | Noted in issue #45 so a reviewer does not read the no-op as a defect. |
| **Over-engineering** | Three duplicated Wave 0 agent prompts collapsed to one template plus a substitution table. |

Also folded in from the verified-clean list: the `.gitignore` observation is
worth adding to `plan.md`'s Structure Decision — the dot-strip is load-bearing
for git as well as for setuptools. Not yet applied.

**Verdict after remediation: Approve.**

---

# Review: PR 1 — `master...43-vendor-wf-skills` (#45)

**Date**: 2026-08-16
**Target**: `db86ed2..ebd0aab`, four commits, 72 files / +7675.
**Scope**: the 66 vendored files are upstream content carried verbatim at
wf-skills `9ee468a` — reviewed for modes and dot-paths, not for their contents.
The authored diff is `pyproject.toml`, `wfctl/_bundle.py`, `tests/test_bundle.py`,
`tests/conftest.py`, `.github/workflows/ci.yml` and
`.github/scripts/check_wheel_contents.py`.

No BLOCKERs. Nothing below is a live bug on this branch today; all four warnings
are gaps between what a guarantee claims and what it actually covers.

## Findings

### WARNING — `check_wheel_contents.py:58`: `.sh` is a proxy for a fact git already holds

The exec-bit assertion fires only on `relative.endswith(".sh")`. The mode is not
read from git at all — it is inferred from the filename. Today the two coincide
exactly (`git ls-files -s` shows 5 files at `100755`, all `.sh`), but that is an
upstream coincidence, not a derived fact. An executable `.py` helper, or a script
with no extension, ships 644 and the job stays green — the precise failure this
job exists to catch.

The file's own docstring argues the comparison is against `git ls-files` "not a
hardcoded list", because a hand-maintained list "would answer a different, staler
question". The mode half breaks that principle on the same line it is stated.

**Fix**: `git ls-files -s`, key the assertion on mode `100755` rather than on the
suffix.

### WARNING — `check_wheel_contents.py:45`: `stdout.split()` splits paths on whitespace

`.split()` breaks a tracked path containing a space into two entries, both of
which then report as `MISSING`. It fails loudly rather than silently — the safe
direction — but the output names files that do not exist and hides the one that
does. `git ls-files` also quote-escapes such paths by default, so the two halves
arrive with stray quotes.

**Fix**: `.splitlines()`. Folds into the W1 fix — `git ls-files -s` puts a tab
before the path, so splitting on `\t` gives the mode and the exact path in one
pass.

### WARNING — `_bundle.py:56`: an absent bundle hashes to the digest of nothing

Verified: `content_hash(Path("/nonexistent/xyz"))` returns
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` —
`sha256(b"")`. A bundle that failed to package produces a well-formed, stable
fingerprint meaning "there is nothing here."

Latent in this PR — nothing calls it yet. It goes live in #46, where `doctor`
would read a broken install as ordinary drift and print "stale, run
`install-skills`", a remedy that would then install nothing.
`check_wheel_contents.py:49` treats the identical empty case as a hard failure
with the reasoning "a vacuous pass is the failure mode this check exists to
prevent". The two modules answer the same question opposite ways.

**Fix**: raise when *none* of `TREES` resolves to a directory. That keeps
`test_content_hash_is_defined_for_a_tree_that_is_missing_one_half` passing and
keeps the suite's `agents/`-only fixture working, since both have at least one.

### WARNING — `_bundle.py:43`: the collision-seam claim has no test

The length-prefix rationale is the module's one non-obvious invariant. It is
real — with plain concatenation, `agents/ab` + `c` and `agents/a` + `bc` collide;
length-prefixed they do not (verified both ways). But no test exercises it.

`_FIXED_TREE_DIGEST` catches a change to the scheme only incidentally, and the
documented response to a digest change is to re-record the literal — which would
retire the property silently while every test stayed green.

**Fix**: one test, the two trees above, `assert content_hash(a) != content_hash(b)`.

### NIT — `pyproject.toml:39`: the comment claims more coverage than the globs have

"Matched by pattern rather than named outright so the next dotfile upstream adds
does not fail the same way" holds for dot-*files*. It does not hold for a file
inside a dot-*directory*: with `agents/**/*` plus `agents/**/.*`,
`agents/.hiddendir/f.md` matches neither (verified). `**` does not descend into
hidden directories, so an upstream skill gaining a `.github/` or `.claude/`
subdirectory reproduces the original bug exactly.

Chasing glob completeness here is a rabbit hole (`agents/**/.*/**/*` covers one
more level and still misses dot-files inside dot-dirs), and the wheel job turns
this into a red build rather than a silent drop. So the defect is the comment,
not the pattern: as written it will convince the next maintainer the case is
handled.

**Fix**: state the boundary — dot-files yes, dot-directories no, wheel job
catches the rest.

### NIT — `check_wheel_contents.py:40`: `check=True` outside a checkout

Run from an unpacked sdist, the git call raises a `CalledProcessError` traceback
instead of the file's own clean failure message. Cosmetic; CI always has `.git`.

## Verified clean

- **Digest determinism** (FR-010) — bytes and POSIX paths only, sorted walk. The
  hardcoded literal is the right call and runs on 3.11 and 3.13 in the `test`
  matrix; darwin/linux divergence is caught by the local run.
- **Modes** — 61 × `100644`, 5 × `100755`, no symlinks (no `120000`).
- **Hash scoping** — excluding `cli.py` and `__pycache__` is correct, and
  `test_trees_are_the_two_vendored_directories` pins the pairing with
  `package-data`.
- **`bundle` fixture scope** — must be function-scoped because `monkeypatch` is;
  `tmp_path_factory` over `tmp_path` is right, since tests use `tmp_path` as the
  repo under test.
- **File mode is absent from the fingerprint** — checked against FR-008/FR-009,
  which scope it to contents and paths. Out of scope by spec, not an oversight.
- **Wheel job isolation** — `python .github/scripts/…` puts `.github/scripts` on
  `sys.path[0]`, not the repo root, so `import wfctl` resolves to site-packages;
  the explicit source-tree guard is correct belt-and-braces.
- **Six-way parametrization** in `test_content_hash_covers_every_sourceable_directory`
  reads redundant but is mandated by FR-008's "including content that belongs to
  no layer target list". Keep.

net: `Lean already.` — the four fixes add ~8 lines; nothing here is deletable.

**Verdict: Approve — merge after W1 and W2**, which are a single edit to
`check_wheel_contents.py` and sit inside the one check that justifies this PR.
W3 and W4 are fine to carry into #46, where W3 first has a caller.

## Remediation applied (2026-08-16) — `0042851`

| Finding | Resolution |
| --- | --- |
| **W1** (`.sh` proxy) | `git ls-files -s`; the assertion keys on mode `100755`. Proven to close the gap: with `wfctl/agents/trackers/github.json` set executable in the index and left 644 on disk, the old check passed and the new one reports `NOT EXECUTABLE`. |
| **W2** (`stdout.split()`) | `-z` plus the tab git puts before the path. Also stops C-quoting mangling non-ASCII names, which `splitlines()` alone would not have. |
| **W5** (overclaiming comment) | `pyproject.toml` now states the boundary — dot-files covered, dot-directories not, no finite glob set closes it, wheel job catches it. |
| **W6** (`check=True`) | Not applied. One traceback in a context CI never enters; a `try` around it costs more than it returns. |

Both original negatives re-confirmed through the rewritten parse: `chmod -x` on
`common.sh` → `NOT EXECUTABLE`; `package-data` narrowed → `MISSING
.workmux.yaml`. `380 passed`, mypy and ruff clean.

**W3** (absent bundle hashes to `sha256(b"")`) and **W4** (untested collision
seam) deferred to #46 by decision, not oversight — W3 has no caller until
`doctor` reads it there, and both edits land in `_bundle.py`, which #46 already
opens.

**Verdict after remediation: Approve.**

---

# Review: PR 1 second pass — five-axis + quality gates

**Date**: 2026-08-16
**Target**: `master...43-vendor-wf-skills` at `0042851`, five commits.
**Framing**: `code-review-and-quality`'s axes as a second pass. Findings the first
review already raised are not repeated; this covers what that pass did not reach —
change sizing, provenance, dependency discipline, dead code, and the security
posture of shipping executable third-party scripts.

**Status: both required findings applied in PR 1**, not deferred to a follow-up
issue as this review originally proposed. `08c70a9` imports `BUNDLE_ROOT`;
`71ebc96` adds `BUNDLE_SOURCE`. Both land in files PR 1 already creates, and the
PR was not yet open, so there was no review-churn cost to weigh against shipping
a known gap. The `Consider` and `FYI` items below stand as recorded.

## Findings

### Required — `check_wheel_contents.py:39` re-derives `BUNDLE_ROOT` instead of importing it

Line 37 imports `TREES` from `wfctl._bundle`. Line 39 then writes
`Path(str(files("wfctl")))` — character-for-character `_bundle.py:32` — rather
than importing `BUNDLE_ROOT` from the module already open on the line above.

The consequence is not style. **`BUNDLE_ROOT` has no automated verification
anywhere in this PR.** `conftest.py:77` monkeypatches it in all 380 tests, so no
test ever sees its real value; and the CI job that appears to exercise it is
validating its own copy. Change `BUNDLE_ROOT` to a wrong expression and the suite
stays green *and* the wheel job stays green — the one constant the entire feature
hangs on is checked by nothing.

Importing it closes that: the job then resolves the real shipped constant against
a clean install, which is the assertion the job was written to make.

**Fix**: `from wfctl._bundle import BUNDLE_ROOT, TREES`, drop the local
re-derivation and the now-unused `files` import. Net −2 lines.

### Required — provenance survives only in a commit message

`aamarin/wf-skills @ 9ee468a` appears in `db86ed2`'s body and nowhere in the
tracked tree — no marker file, no `pyproject.toml` field, no README line.
Searched; the only matches are unrelated prose about the `install-skills` command.

Ordinarily a nit. Two things sharpen it:

1. **The upstream repo is being archived** as part of #43. The commit message
   becomes the sole surviving pointer to a source that will be read-only and,
   eventually, unfamiliar.
2. **Vendoring is a dependency-acquisition act.** 7,325 lines of third-party
   content entered this repo. "Where did this come from, at what revision" is the
   first question of any re-sync, license audit or CVE response, and it is
   currently answerable only by `git log` archaeology over a tree that will have
   moved by then.

**Fix**: one tracked line recording repo and commit — `wfctl/agents/ORIGIN`, or a
`[tool.wfctl] bundle-source` key. Cheap now, unrecoverable later.

### Consider — the wheel carries 119 KB nothing reads until #46 lands

Measured: the bundled trees are 121,823 of the wheel's 178,526 compressed bytes —
**68% of the artifact**. Between this PR merging and #46 merging, every install
ships that payload while `install-skills` still clones the same content over the
network. Two sources of truth for one set of files, one of them unread.

That is the deliberate price of the split, and the split is right — a 7.6k-line
diff plus a behaviour change in one review is worse. Worth an explicit note on #46
that a stall there leaves users carrying dead weight, so the window is something
someone is watching rather than something nobody wrote down.

### FYI — the security posture improves, and this is the axis the feature is really about

Scanned all five vendored `.sh` files for what matters when shipping executable
third-party code: no `curl`/`wget`, no pipe-to-shell, no `base64 -d`, no
`http://`. Three use `eval $(get_feature_paths)` to import shell vars from a
helper — upstream speckit's own idiom, carried over unchanged.

Not a finding against this PR: those exact bytes already reach users through
`install-skills`'s clone today. The relevant point is the direction of travel.
Today `--ref main` resolves at install time, so what lands on a user's disk is
whatever upstream's default branch held at that moment, reviewed by nobody. After
this PR it is pinned bytes in a package that had to pass review to get here.
**Vendoring narrows the trust surface it is often assumed to widen** — worth
saying out loud in the PR, because the instinct on "we vendored 7k lines of shell"
runs the other way.

### Nit — change sizing

7,675 added lines is ~7× the "split it" threshold. The authored portion is **+350**
(`pyproject.toml`, `_bundle.py`, both test files, the CI job and its script); the
other 7,325 are verbatim upstream — precisely the sanctioned exception, bulk
content where a reviewer verifies intent and provenance rather than every line.
Noted because that exception is only load-bearing if provenance is checkable,
which is the second finding above.

## Axes with nothing to report

- **Correctness** — covered in the first pass; W3 and W4 stand as recorded.
- **Dead code** — nothing orphaned. `cli.py` is untouched, so no clone path is
  superseded yet; that cleanup belongs to #46 and is tracked there.
- **Dependencies** — the `pyproject.toml` diff adds `[tool.setuptools.package-data]`
  and nothing else. No new runtime or dev dependency. `_bundle.py` is `hashlib`,
  `importlib.resources`, `pathlib` — stdlib throughout.
- **Performance** — `content_hash` reads whole files, largest 25 KB, 66 of them,
  once per call. No hot path, no query pattern, nothing unbounded.
- **Change descriptions** — all five subjects imperative and standalone; no "Fix
  bug", no "Phase 1", no "Moving code from A to B". Bodies carry the reasoning,
  including the `update=1` / `SOURCES.txt` caching trap.
- **Verification story** — documented per-criterion in the PR body, with both
  hand-run negatives and their exact output.

## Verdict

**Request changes** — one required fix (`BUNDLE_ROOT` import) and one required
addition (provenance). Both small; neither is a defect in what the code does, and
both are gaps between what a guarantee appears to cover and what it covers. The
change definitely improves code health and should merge once they are in.

**Resolved.** Both applied — `08c70a9` and `71ebc96`. Re-verified from clean:
`380 passed`, mypy and ruff clean, and the wheel check through the rewritten
import — positive path `OK: 66` resolving the site-packages root, the source-tree
guard still exiting FAIL, and the `chmod -x` negative still reporting
`NOT EXECUTABLE`. **Verdict after remediation: Approve.**

---

# Third pass — `/simplify` (cleanup, not correctness)

**Framing**: four parallel agents over the 359 non-vendored lines — reuse,
simplification, efficiency, altitude. The vendored trees were excluded from scope
as a verbatim upstream mirror. This pass looked for reuse, simplification,
efficiency and altitude problems only; correctness was the previous two passes.

**Status: two findings applied in `c4adea9`, three skipped, two passes clean.**

## Applied

### Altitude (HIGH) — the glob pair was a workaround where a mechanism exists

`[tool.setuptools.package-data]` is expanded with Python's `glob`, which cannot
see dot-prefixed names — hence the `.*` twins. The comment above them already
conceded the pair was knowingly incomplete: `**` does not descend into a
dot-prefixed *directory*, and "no finite set of globs closes that off". That
sentence was true and the conclusion drawn from it was wrong. The remedy is not a
better glob, it is not globbing: `MANIFEST.in`'s `graft` is processed by
`FileList.graft` → `findall` → `os.walk`, with no `glob` module and no
hidden-name filtering anywhere in the path.

Verified independently before applying, from clean builds (`rm -rf build dist
wfctl.egg-info` first) against a tree carrying `wfctl/agents/skills/.hiddendir/note.md`:

| packaging rule | files | dot-dir | exec bits |
| --- | --- | --- | --- |
| `package-data` globs | 66 | absent | 5 × `100755` |
| `MANIFEST.in` graft | 67 | present | 5 × `100755` |

`include_package_data` defaults to true under pyproject metadata, so the
`package-data` section is deleted rather than emptied — a build with `graft` and
no `package-data` at all ships 66 files, `.workmux.yaml` included, 5 executables.

The cost of the old altitude was not just the four patterns. It was that the
wheel job backstopped a gap with **no available remedy**: it would go red, and
the person hitting it at re-sync time could not write a glob that fixed it. The
job now backstops mode loss and the two build-cache traps, which are things a
human can act on.

### Altitude (MEDIUM) — the pairing test was a change-detector

`test_trees_are_the_two_vendored_directories` asserted `TREES == ("agents",
"specify")` and its docstring claimed to guard the pairing with pyproject. It
could not. Add a third tree to the packaging rule and forget `TREES`: the literal
still matches, the test passes, the files ship, nothing hashes them, and drift in
them is invisible to `doctor` forever. Only the safe direction failed, and it
failed as a change-detector — the author edits the literal and the *docstring* is
what reminds them.

Now reads the `graft` lines out of `MANIFEST.in` and compares sets. Confirmed to
fail in the previously-silent direction by appending `graft wfctl/thirdtree`:
`AssertionError: Extra items in the left set: 'thirdtree'`.

## Skipped

### Efficiency — autouse `bundle` fixture does I/O for all 380 tests

Real observation, wrong remedy. The proposed fix — make it opt-in until a
consumer exists — reverses the documented reason it is autouse: opt-in means a
test that forgets reads the real `wfctl/agents/` and passes for the wrong reason,
and autouse is only a guarantee if it predates the first test that could forget.

Measured rather than argued: **0.223s for 380 fixture builds, against a 41s
suite — 0.46%.** Not a trade worth making.

### Altitude (HIGH/MEDIUM) — re-dot the vendored trees to match upstream

Proposed `git mv wfctl/agents wfctl/.agents` so `cli.py`'s existing dotted
`(src, dest)` constants work against `BUNDLE_ROOT` directly and PR 2 needs no
path-translation shim. Genuinely interesting, and the agent verified a `.agents/`
wheel builds correctly under `graft`.

Skipped on two grounds. It relocates 66 explicitly out-of-scope vendored files.
And it engages only one of the two independent reasons `db86ed2` gave for
de-dotting — the setuptools half, which `graft` does dissolve. The other stands:
`.gitignore:12-14` lists `.agents/`/`.specify/` unanchored, so those patterns
match at any depth and a vendored `wfctl/.agents/` would not be tracked at all
without negation patterns. **Worth raising on #46** before PR 2 hardcodes the
de-dotted form; not a change to make inside this diff.

### Altitude (LOW) — extract the local repro into `.github/scripts/check_wheel.sh`

CI does not need the `rm -rf` step (fresh checkout), so the script either carries
a step CI skips or diverges from CI anyway — which defeats the "same path
locally and in CI" argument for having it. Docstring stays.

### Altitude (LOW) — `BUNDLE_ROOT`-as-default-argument enforced by prose only

The agent recommended no mechanism itself, on the grounds that `B008` is
unusable noise in a typer codebase. Agreed.

## Clean

**Reuse** — checked `_manifest.py`, `_paths.py`, `_io.py`, `cli.py` and the
existing test helpers. No `git ls-files` usage and no other `hashlib` call exists
in the tree; the `_make_wf_skills_repo()` helpers in `test_install_skills.py` and
`test_tracker.py` build a dotted *git repo* standing in for the clone source, a
different abstraction from the undotted non-git bundle fixture. Nothing to reuse.

**Simplification** — no findings. `tracked` as a dict is read twice for two
different purposes; the two output lists are two genuinely different failure
categories; the parametrized directory test is the right tool over six copies.

## Verdict

**Approve.** `380 passed`, mypy and ruff clean, wheel check `OK: 66` through the
new mechanism, and both negatives re-confirmed against it — `chmod -x` reporting
`NOT EXECUTABLE`, and the graft narrowed to `wfctl/agents/skills` reporting
`25 missing` including `.workmux.yaml`.
