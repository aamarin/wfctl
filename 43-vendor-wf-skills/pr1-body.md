Vendors the wf-skills tree into `wfctl/` as package data, adds the module that
reads and fingerprints it, and adds the CI job that proves the built wheel
carries both the files and their executable bit.

**Behaviour is unchanged.** `install-skills` still clones. This is the package
half only — the vendored diff lands where a reviewer can assess it from
`MANIFEST.in` and one CI job, and `cli.py` is untouched.

Closes #45

## What's here

| Commit | |
| --- | --- |
| `db86ed2` | 66 files vendored from wf-skills `9ee468a`, all five `.sh` at `100755` |
| `4389f67` | `[tool.setuptools.package-data]` |
| `69a75dd` | `_bundle.py` — `BUNDLE_ROOT` + `content_hash`, 11 tests, autouse fixture |
| `ebd0aab` | the `wheel` CI job |
| `0042851` | first-review fixes — see below |
| `08c70a9` | the wheel job checks the shipped `BUNDLE_ROOT`, not a copy |
| `71ebc96` | `BUNDLE_SOURCE` — the upstream revision this tree was copied from |
| `c4adea9` | `MANIFEST.in` graft replaces the globs — see below |
| `87013c5` | `eval "$(get_feature_paths)"` — one real Copilot finding, two rejected |
| `8d063c2` | `${word^^}` → `tr`; the script aborted under macOS's bash 3.2 |

**66 files, not the ~80 the issue estimates** — counted from the built wheel.

## Two things worth a reviewer's attention

**Packaging the trees is not a globbing problem.** `[tool.setuptools.package-data]`
is expanded with Python's `glob`, which cannot see dot-prefixed names. That costs
two files' worth of trouble in opposite ways: `agents/**/*` alone ships 65 of 66
and silently drops `agents/configs/workmux/.workmux.yaml`, the only file
`install-config workmux` copies — and adding `agents/**/.*` recovers dot-prefixed
*files* while `**` still refuses to descend into a dot-prefixed *directory*. The
final state uses `graft` in `MANIFEST.in`, which walks with `os.walk` and filters
nothing, so the whole class is covered rather than two instances of it. See the
last section for the measurements. The 380-test suite passes under every one of
these variants; only the wheel job can tell them apart.

**The wheel job is the only check that can see any of this.** `test` and `lint`
both run against the source tree, where the trees are present and executable
regardless of what the wheel ships. It compares against `git ls-files` rather
than a hardcoded manifest — including which files should be executable — and
treats an empty result as a failure, since a vacuous pass is the outcome it
exists to prevent.

## Verification

All seven acceptance criteria on #45 hold. The two that needed doing by hand:

```
$ chmod -x wfctl/specify/scripts/bash/common.sh   # then rm -rf build dist wfctl.egg-info; uv build --wheel
  NOT EXECUTABLE: wfctl/specify/scripts/bash/common.sh

$ # graft narrowed to `wfctl/agents/skills`  (SC-008)
  FAIL: 25 missing, 0 not executable out of 66 tracked bundle files
  MISSING: wfctl/agents/configs/workmux/.workmux.yaml   (among them)
```

Neither reproduces without clearing `build/`, `dist/` and `wfctl.egg-info/`
first. `build_py` copies with `update=1`, so a `chmod` — which leaves mtime
alone — never reaches the wheel; and `SOURCES.txt` re-includes files the
packaging rule stopped covering. Left in place, either turns a deliberately
broken build green. CI checks out fresh and has neither, which is why the job
needs no such step; the script's docstring records it for anyone reproducing
locally.

`380 passed`, `mypy` and `ruff` clean.

## Review fixes in `0042851`

`/code-review` on the first four commits found no blockers and four warnings.
Three are applied here; the full findings are in `REVIEW.md` in the feature dir.

**The exec-bit assertion inferred the mode from the filename.** It fired only on
paths ending `.sh`. Correct by coincidence — all five executables in the tree are
shell scripts — but it guessed at something `git ls-files -s` already records,
one line below a docstring arguing against exactly that. Now keyed on mode
`100755`. Verified to close a real gap, not just read better: with
`wfctl/agents/trackers/github.json` set executable in the index and left 644 on
disk, the old check passed and the new one reports `NOT EXECUTABLE`.

**`stdout.split()` tore paths on whitespace.** A bundled path containing a space
became two entries that both reported as `MISSING` — loud, but naming files that
do not exist while hiding the one that does. Replaced by `-z` plus the tab git
puts before the path, which also stops C-quoting from mangling non-ASCII names.

Both original negatives were re-confirmed through the rewritten parse.

Two warnings are deferred to #46 by decision: `content_hash` on an absent bundle
returns `sha256(b"")` — a well-formed digest meaning "nothing here" — and the
length-prefix collision property has no test of its own. Neither has a caller
until `doctor` reads the fingerprint, and both edits land in `_bundle.py`, which
#46 already opens.

## Second review pass — `08c70a9`, `71ebc96`

**The wheel job was validating its own copy of `BUNDLE_ROOT`.** It re-derived
`Path(str(files("wfctl")))` one line below importing `TREES` from `_bundle`.
Both expressions agree, so nothing was broken — but the net effect was that the
constant every caller resolves the bundle through was verified by *nothing*:
`conftest.py`'s autouse fixture monkeypatches it out of all 380 tests, and the
one job running against a real install was checking a duplicate. Now imported,
so this is where it is exercised as shipped — the positive path prints the
site-packages directory it resolved.

**Provenance was only in a commit message.** `aamarin/wf-skills @ 9ee468a` is
recorded in `db86ed2`, and this same feature archives that repository. Anyone
re-syncing the tree needs the base revision to diff against, and a pointer into
an archived repo is a poor place to keep it. `BUNDLE_SOURCE` in `_bundle.py`
pins the full sha next to `TREES`. Nothing reads it until `doctor` does in #46.

## Cleanup pass — `c4adea9`

A four-angle review (reuse, simplification, efficiency, altitude) over the 359
non-vendored lines. Reuse and simplification came back clean. Two altitude
findings applied:

**The glob pair was a workaround where a mechanism exists.** `graft` in
`MANIFEST.in` walks with `os.walk` and filters nothing, so it covers dot-prefixed
directories as well as files. Measured from clean builds against a tree carrying
a `wfctl/agents/skills/.hiddendir/note.md`:

| packaging rule | files | dot-dir | exec bits |
| --- | --- | --- | --- |
| `package-data` globs | 66 | absent | 5 × `100755` |
| `MANIFEST.in` graft | 67 | present | 5 × `100755` |

`include_package_data` already defaults to true under pyproject metadata, so
`[tool.setuptools.package-data]` is deleted rather than emptied. The wheel job
keeps its value — mode loss, the `update=1` trap, the `SOURCES.txt` trap — but
is now a backstop rather than the only thing standing between us and a case no
glob could express.

**The pairing test could only fail in the safe direction.** It asserted
`TREES == ("agents", "specify")`. Ship a third tree and forget `TREES` and it
still passed, while the files went unhashed and drift in them stayed invisible
to `doctor` forever — the exact failure the test was named for. It now reads the
graft lines out of `MANIFEST.in` and compares the sets. Confirmed bidirectional
by adding a third graft and watching it report the extra item.

Three findings were skipped with reasons recorded in `REVIEW.md`. The one worth
flagging here: the efficiency pass wanted the autouse `bundle` fixture made
opt-in until a consumer exists, which reverses the reason it is autouse. Measured
instead of argued — **0.223s across 380 fixture builds, 0.46% of a 41s run.**

## Copilot review — `87013c5`

Four findings, all against vendored scripts. **One real, applied:**
`eval $(get_feature_paths)` word-splits the helper's output and rejoins the
fragments with single spaces. Single-space paths survive by luck — the separator
that split them is the one put back — but a spec root under `/tmp/a  b` comes
back as `/tmp/a b`, and every derived path then points nowhere. Measured:
unquoted `/tmp/a b`, quoted `/tmp/a  b`. Fixed at all **three** call sites; the
third, `update-agent-context.sh:56`, was found by grepping the pattern rather
than by fixing what was reported.

**Two rejected as false positives**, both verified rather than argued:
`\b` is a word boundary in BSD grep as well as GNU (`AI` matches in "use AI
tooling", not in "SAID nothing"), and `[[ ... ]]` performs no word splitting or
globbing on unquoted expansions, so quoting `$(ls -A "$1")` there is inert. The
fourth was a duplicate of the first.

Editing vendored files diverges the tree from `BUNDLE_SOURCE`. That is now the
expected steady state — wf-skills is archived by this same feature, so there is
no upstream to send fixes to — and the comment on the constant says it is a diff
base, not a byte-identical claim.

**A real defect the review walked past, fixed in `8d063c2`.** `${word^^}` on the
same line as the rejected `\b` finding is bash 4+, and with `set -e` on that is
not a skipped branch — `bad substitution` aborts the script, so
`/speckit.specify` fails outright on a stock Mac. Replaced with the `tr` form
`clean_branch_name` already uses. Verified under /bin/bash 3.2.57: parses, "use
AI tooling" keeps `ai`, "use xy tooling" still drops `xy`.

## Note on the inert fixture

`conftest.py`'s autouse `bundle` fixture does nothing in this PR — nothing reads
`BUNDLE_ROOT` until `cli.py` changes in #46. It ships here because the module and
its test seam belong in one diff, and because autouse is only a guarantee if it
predates the first test that could forget it.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
