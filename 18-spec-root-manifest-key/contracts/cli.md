# Contracts: spec-root-manifest-key

wfctl is a published CLI whose output is consumed by other programs, so its
contracts are command surfaces and the shape of what they print.

## `wfctl spec-root [PATH] [--unset]` — new

Record, show, or remove the repository's spec root.

| Invocation | Behavior | Exit |
|---|---|---|
| `wfctl spec-root` | prints the effective root and its source | 0 |
| `wfctl spec-root <path>` | records `<path>`, prints the file written | 0 |
| `wfctl spec-root --unset` | removes the key, prints the file written | 0 |
| `wfctl spec-root <path> --unset` | rejected — contradictory | 2 |
| outside a git repo | `wfctl: not a git repository` (existing `get_repo_root` behavior) | 1 |

**Write target**: the main checkout's manifest whenever one is identifiable (git
common dir named exactly `.git`), otherwise the current repo root's. The written
path is always printed — a write to a location other than the current directory
must never be silent.

**Show output** names both the root and where it came from, since four sources
are possible:

```
spec root: /Users/x/Development/pfms-specs
source:    /Users/x/Development/pfms/.wf-skills-manifest.json
```

```
spec root: /Users/x/Development/pfms/specs
source:    default (no spec_root recorded)
```

```
spec root: /tmp/elsewhere
source:    WFCTL_SPEC_DIR
```

**Guarantees**: the path is stored exactly as typed (no `~` expansion, no
resolution, no existence check, no directory creation); no other manifest key is
modified.

## `wfctl feature-paths` — changed behavior, unchanged interface

The field names, their order, the `NAME='value'` single-quoted form, and the
`eval`-safety of stdout are **unchanged**. `.specify/scripts/bash/common.sh:45`
consumes this and must keep working untouched.

What changes: `FEATURE_DIR` and its dependents resolve under the configured spec
root when one is recorded. Previously `FEATURE_DIR` fell back to
`<repo>/specs/<branch>` unconditionally when no spec directory existed.

```bash
# no spec_root recorded — unchanged from today
FEATURE_DIR='/repo/specs/18-feature'

# spec_root recorded as ~/Development/pfms-specs
FEATURE_DIR='/Users/x/Development/pfms-specs/18-feature'
```

**Invariant**: nothing is added to stdout. Diagnostics belong on stderr or in
`doctor`; a stray line here is `eval`'d by the caller's shell.

## `wfctl doctor` — one added check

Adds a report when a spec root is recorded *and* `<repo>/specs/` still holds
directories:

```
⚠ spec_root is set, but <repo>/specs/ still holds 3 spec directories —
  they will not be found. Move them to <root> or remove them.
```

**Guarantees**: reports only. Never moves, deletes, or resolves to those
directories, and never changes doctor's exit code — consistent with
`_check_workmux_hook`, which treats drift as reportable rather than failing.

**Placement**: called before the `if not layers:` early return (`cli.py:1362`),
since a repo can record a spec root without having installed skills.

## `spec_root(repo_root: Path) -> Path` — new internal contract

The single decision point both call sites consume; `resolve_spec_dir` and
`feature_paths_cmd` must never resolve a root independently again.

| Guarantee | Detail |
|---|---|
| Total | always returns a `Path`; never `None` |
| Precedence | `WFCTL_SPEC_DIR` → current repo manifest → main checkout manifest → `repo_root / "specs"` |
| No side effects | reads only; creates nothing |
| Raises | only on an unparseable manifest (D6) — never on a missing file, missing key, or missing directory |

## Unchanged contracts

- `resolve_spec_dir` — signature, return type, and match order (exact branch,
  issue-key glob, ancestor branches) are preserved; only the root it searches
  under changes.
- `.specify/scripts/bash/*` — no change; they already delegate to
  `wfctl feature-paths`.
- `wfctl install-skills`, `wfctl uninstall` — no interface change; they must
  preserve an unrecognized `spec_root` key, which a test pins.
