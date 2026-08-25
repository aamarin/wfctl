# Phase 0 Research: Machine-checked done

No `NEEDS CLARIFICATION` markers reached this phase — the spec's five
clarifications resolved them. What follows are the decisions that required
reading the existing code rather than choosing from preference, each with what
was rejected.

## 1. Child process output: stream, not capture

**Decision**: `wfctl verify` runs each command with output inherited by the
terminal. It does not capture.

**Rationale**: `_tracker.dispatch` (`_tracker.py:219`) uses
`subprocess.run(argv, capture_output=True, text=True, cwd=repo_root)`. That is
right for `gh issue view` — sub-second, output reformatted before display. A test
suite runs for minutes, and a buffered one prints nothing until it finishes, which
is indistinguishable from a hang. The verdict comes from the exit code either way,
so capturing buys nothing the record needs.

**Alternatives considered**: capture and replay on failure — still silent while
running, and doubles peak memory on a verbose suite. Capture with a live spinner —
a spinner that cannot show which test is running is worse than the test names.

## 2. `wfctl.json` needs no ignore-list change

**Decision**: FR-011 requires no code change. It becomes a regression test only.

**Rationale**: `install-skills` builds `gitignore_targets` (`cli.py:1191-1231`)
by appending the relative path of every file it is about to install, then calls
`_ensure_gitignored` over `(_MANIFEST_PATH, _BACKUP_DIR/, *gitignore_targets)`
(`cli.py:1355-1357`). `wfctl.json` is hand-authored and never installed, so it
cannot enter that list. The requirement is satisfied by construction.

**Why a test anyway**: the list is built by appending inside two loops, and a
future change that installs a starter config would silently ignore it. The test
pins the property, not the current implementation.

**Alternatives considered**: an explicit exclusion list — defends against nothing
today and would read as though `wfctl.json` were at risk.

## 3. Code identity: `rev-parse HEAD` plus `status --porcelain`

**Decision**: identity is the pair (commit sha, whether the working tree is
clean). Both captured before and after the run.

**Rationale**: `status` already runs `git rev-parse --show-toplevel` and `git
branch --show-current` (`_paths.py:36-65`) on every invocation, so two more git
queries are the same order of cost, and SC-002's constant-query bound holds
regardless of how many commands the definition of done holds. `--porcelain`
includes untracked files by default, which the spec's Assumptions require.

**Alternatives considered**: hashing the working tree — exact, and it walks every
file on a check that must stay cheap. `git stash create` as a tree identity —
writes objects into the repository as a side effect of reporting status.

## 4. The record's home is the existing state dir

**Decision**: `$(wfctl state-dir)/verify.json`, written with the existing
`write_json_atomic`.

**Rationale**: `resolve_agent_dir(repo_root, branch)` already produces a
per-branch directory holding `current.json` and `events.jsonl`. Atomic replace
(`_io.py:11-25`) means a concurrent `wfctl status` never reads a half-written
record, which matters because verification runs for minutes while status runs
constantly.

**Alternatives considered**: the spec directory — this repo's `spec_root` resolves
outside the working tree, so "committed and reviewable" would not hold. A
gitignored file in the repository — a fourth place wfctl keeps state, with no
property the state dir lacks.

## 5. No record format version field

**Decision**: the record carries no schema version.

**Rationale**: `current.json` has none, and `load_agentconfig` (`_io.py:53-61`)
returns `{}` on a malformed or absent file. A record that fails to parse, or lacks
a key a later version expects, is treated as "never verified" — which is both the
safe direction and true. A version field would let a future reader trust a record
it cannot fully interpret.

**Alternatives considered**: a `version` integer — invites migration code for a
file that is cheap to regenerate by re-running the command.

## 6. Streaming plus a non-zero exit is enough; no output is stored

**Decision**: the record stores which command failed, not its output.

**Rationale**: the output was already on screen when it ran (decision 1), and
storing a failing suite's output in a state file makes an unbounded file out of a
fixed-size one. FR-007 needs the command's identity to render the reason, not its
stderr.

**Alternatives considered**: storing the last N lines — an arbitrary cutoff that
is either too short to diagnose or long enough to bloat.

## Open, resolved by decision rather than research

- **`wfctl.json` versus `.wfctl.json`** — visible, per the spec's Assumptions. A
  repository's definition of done is not incidental configuration, and a dotfile
  reads as machine-managed when this one is hand-authored.
- **Comparing the recorded commands to the definition of done** — exact list equality, order
  included. Reordering does not change what is checked, but comparing exactly is
  one expression and never wrong; a permissive comparison would have to justify
  each permission it grants.
