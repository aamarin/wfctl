# Phase 1 Data Model: version check — default branch and fork

Three values and one decision table. Nothing is persisted; every value is derived
per invocation of `wfctl doctor`.

## E1: InstalledBuild

What the running wfctl was built from. Parsed from the installed distribution's
`direct_url.json` (PEP 610).

| Field | Source | Absent when |
| --- | --- | --- |
| `url` | `direct_url.json` → `url` | no `direct_url.json` (index or sdist install) |
| `commit` | `vcs_info.commit_id` | not a source-control install |
| `requested_revision` | `vcs_info.requested_revision` | installed from a bare branch URL |

**Representation**: `_Build(url, commit, pinned)` — a NamedTuple — or `None`
when the build records no origin at all.

`pinned` is a field rather than a fourth `None` case. Collapsing it looked
tidier and was wrong: it discarded the url along with the eligibility, and the
url is what every remedy has to name (E3, FR-012). A pinned fork build that lost
its url was told to upgrade from upstream — caught in code review, after the
tests passed.

**Rules**:

- R-1: No `direct_url.json` → `None`. (Index or archive install.)
- R-2: No `vcs_info` key → `None`. (Editable or local-directory install; see
  research R5 — decided by key presence, never by URL scheme.)
- R-3: `requested_revision` present → `pinned=True`, url and commit retained.
  Suppresses the branch comparison only (research R3).
- R-4: Malformed JSON → `None`. Doctor is a health check; it must not raise on a
  metadata file written by a third party.

## E2: RemoteState

What the origin says right now. One `ls-remote --symref -- <url> HEAD
'refs/tags/v*'` per repository consulted.

Two details of that command line are load-bearing, both found by running the
real binary rather than a stub:

- **No `--refs`.** It filters out everything outside `refs/`, which includes
  `HEAD` — so `--refs` and `--symref HEAD` cancel, the branch half silently
  reads as unreachable, and doctor warns forever. The cost of omitting it is
  that annotated tags also emit a `^{}` row, which is harmless here.
- **`--` before the url.** The url comes from a metadata file this process does
  not own, and git reads leading-dash arguments as options wherever they sit. A
  recorded url of `--upload-pack=<command>` runs that command on every doctor,
  which means every session start. Both are pinned by argv-level tests.

| Field | Parsed from | Notes |
| --- | --- | --- |
| `branch` | `ref: refs/heads/<name>	HEAD` | resolved, never assumed (FR-003) |
| `tip` | the `HEAD` SHA row | the commit `InstalledBuild.commit` is compared to |
| `tags` | `refs/tags/vX.Y.Z` rows | only from the upstream constant (FR-009) |

**Rules**:

- R-5: Upstream install (`InstalledBuild.url` equals the upstream constant) →
  one query answers both halves.
- R-6: Fork install → two queries: tags from upstream, `branch`/`tip` from the
  recorded URL.
- R-7: Non-zero exit or empty output → that half is unavailable, recorded as a
  failure rather than an empty result. The distinction matters: "no tags" and
  "couldn't reach the tag source" must not render alike (FR-009a).

## E3: FreshnessReport

The two independent verdicts and the single exit code they produce.

| Release verdict | Branch verdict | Output | Exit |
| --- | --- | --- | --- |
| newer tag exists | *(suppressed)* | `⬆ wfctl X → Y available` + upgrade command | 1 |
| current | commit == tip | `✓ wfctl X — latest` | 0 |
| current | commit != tip | `✓ … — latest release` + drift block | 1 |
| current | skipped (`None` or pinned) | `✓ wfctl X — latest` | 0 |
| current | query failed | one `⚠` line naming the branch check | 0 |
| query failed | commit == tip, or skipped | one `⚠` line naming what could not run | 0 |
| query failed | commit != tip | one `⚠` line + drift block | **1** |

**Rules**:

- R-8: A newer tag suppresses the branch line (FR-007) — the upgrade command
  already prescribed resolves both, and two remedies is one too many to act on.
- R-9: Drift exits 1 (FR-006) — including when the tag query failed. That last
  table row is where FR-006 and FR-009a's original wording collided: a failed
  query must not bury a verdict that succeeded, so the warning is folded into the
  one `⚠` line and the drift still drives the exit code. Only reachable on a fork
  install, where the two queries can fail independently.
- R-10: Exactly one `⚠` line per report, whose text names every comparison that
  could not run (FR-009a). A comparison that failed is never silently omitted;
  its absence would otherwise read as a pass.
- R-11: The `✓` string is `— latest` alone and `— latest release` when the drift
  block follows, so the unqualified case stays byte-identical to today's output.

## State transitions

None. Every value is computed fresh per invocation and discarded; no cache, no
state file, no manifest entry. This is deliberate — a cached freshness verdict is
a freshness verdict that can itself go stale.
