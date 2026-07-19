# Spec: Configurable issue-key resolution

**Status:** Draft
**Date:** 2026-07-19
**Branch:** issue-tracker-dispatcher

## Problem

wfctl derives an *issue key* from the current branch name — used to label the
session (`#{issue}`) and to locate the branch's spec folder under `specs/`. That
derivation happens in two places that **disagree**:

- `_resolve_context` (`cli.py`) matched `^([A-Za-z]+-\d+|\d+)[-_]` — it required
  a trailing separator, so a bare `342` branch (no slug) fell through to
  `unknown`.
- `resolve_spec_dir` (`_paths.py`) used `branch.split("-")[0]` + `.isdigit()` +
  `glob("{key}-*")` — **numeric-only** and **hyphen-only**, so a letter-prefixed
  key (`PROJ-123-*`) or an underscore separator could never find its spec dir.

wfctl operationalizes spec-driven development, where the branch is `{key}-{slug}`
and the spec folder mirrors it. On GitHub the key is a plain issue number; on a
private Jira/Linear/Shortcut tracker it is not. Both resolvers must agree on
**one key shape**, defaulting to the GitHub case and configurable per tracker for
everything else.

## User Scenarios

1. **GitHub user, zero config.** Branch `342-state-workflow`. Key resolves to
   `342`; `specs/342-state-workflow/` is found. No tracker config required.
2. **Bare-number branch, no slug.** Branch `342`. Key resolves to `342` (the
   optional-slug fix). Previously resolved to `unknown`.
3. **Underscore separator.** Branch `342_state_workflow`. Key resolves to `342`.
4. **Jira user, custom key.** Tracker config sets `key_pattern` for the project's
   key shape (e.g. `[A-Z]+-\d+`). Branch `PROJ-123-auth-lifecycle`. Key resolves
   to `PROJ-123`; `specs/PROJ-123-auth-lifecycle/` is found.
5. **Non-key branch.** Branch `feature-123-x` with the default pattern. Key
   resolves to `unknown` (correct — a `feature-*` branch has no issue key). No
   mis-read into `feature-123`.

## Functional Requirements

- **FR1** A single shared extractor derives the key; both call sites use it, so
  they cannot drift.
- **FR2** Default pattern is `\d+` (plain leading number).
- **FR3** The slug is optional: the key may stand alone or be followed by a
  `-`/`_` separator and slug. Anchor: `^({pattern})(?:[-_]|$)`.
- **FR4** A tracker backend may override the shape via a `key_pattern` string in
  `.agents/trackers/<name>.json` (sibling of `verbs`).
- **FR5** An absent, empty, or un-compilable `key_pattern` degrades to the
  default — never raises.
- **FR6** `resolve_spec_dir` matches either separator: `glob("{key}[-_]*")`.

## Success Criteria

- Default `\d+`: `342`, `342-x`, `342_x` all resolve to `342`.
- Default `\d+`: `feature-123-x` and `PROJ-123-x` resolve to `unknown`.
- With `key_pattern = [A-Z]+-\d+`: `PROJ-123-x` resolves to `PROJ-123`.
- With that config and branch `PROJ-123-demo`, `resolve_spec_dir` returns
  `specs/PROJ-123-demo/`; the underscore variant is found too.
- An invalid `key_pattern` yields the default behavior, not a crash.

## Key Entities

- **`key_pattern`** — optional per-tracker regex naming the key's shape. The only
  configurable field this feature adds.
- **Shared extractor** (`extract_issue_key(branch, pattern) -> str`) — anchored,
  optional-slug, error-safe. Reused by `_resolve_context` and `resolve_spec_dir`.

## Assumptions / Out of Scope

- Key-first ordering (`{key}-{slug}`) is universal convention and stays
  hardcoded — no `{slug}-{key}` toggle, no separator config, no name template.
- This spec's own folder is descriptive (`configurable-issue-key/`) because the
  wfctl branch has no numeric key — the exact case this feature exists to teach
  wfctl to handle.
- The broader speckit-workflow rework — dropping issue *creation* in
  `speckit.specify`, a branch-shape pre-req guard, removing the `%03d` numeric
  requirement in `create-new-feature.sh`, and the `.agents/commands` install
  packaging gap — is a **separate follow-up spec**, not this one.
