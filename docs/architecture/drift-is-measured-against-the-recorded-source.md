---
status: proposed
---

# Drift is measured against the source an install recorded, not the running wheel

## Context

`install-skills` copies from `_bundle.BUNDLE_ROOT`, the installed package's own
directory. In a worktree the `wfctl` on PATH is the uv-tool release, so a branch
that edits a skill installs the released copy of it instead — #75, and the reason
a skill cannot be developed on a branch today.

Pointing the installer somewhere else is one parameter. What makes it more than a
flag is `doctor`: it recomputes its reference from the running wheel on every
run, so an install from anywhere else reads as drift permanently, and the remedy
it prints reinstalls the release and destroys the thing being tested.

The reference point, not the source path, is the question. An installer that
records nothing leaves `doctor` no basis to compare against except the wheel it
happens to be running from.

## Decision

The manifest records which bundle root an install copied from, beside the
`content_hash` it recorded for that root. `doctor` re-reads that root and
compares against it.

The running wheel is the default, and it is recorded by the key being **absent**
rather than by its path. Before this decision the wheel was the only source there
was, so absence carries a complete answer for every manifest that predates it —
no migration, no sentinel. Recording the wheel's own path would be worse than
redundant: an upgrade rewrites that path's contents, so a routine version bump
would report as the source having changed.

## Owns truth

The repo's manifest owns "which bundle produced this install, and what did it
hash to?". It is written by `install-skills` at copy time, from the argument the
caller supplied.

`doctor` cannot compute it. Two installs from different sources can be
byte-identical — a branch whose skills happen to match the release produces
exactly the release's tree — so nothing in the installed files distinguishes
them. Provenance is knowable only to the process that did the copying, and only
at the moment it copied.

The running wheel cannot supply it either. It is a property of the machine
`doctor` is invoked on, not of the repo `doctor` is inspecting, and the same repo
inspected by two differently-versioned wfctl installs would get two answers to a
question that has one.

## Considered

- **Record nothing; suppress the drift finding when a `--from` flag was used.**
  The flag is not present on the `doctor` run that reports the drift, so there is
  nothing to suppress on. Suppression would have to be recorded, which is the
  recording this decision makes.
- **Record the source but never re-read it.** `doctor` then says where an install
  came from and cannot say whether that source has moved since — silent through
  the edit-install-test loop that is the whole reason to install from a branch.
- **Per-layer content hashes.** Addresses a different false-drift problem and not
  this one; `_bundle.content_hash` documents why the digest is whole-tree, and
  `agents/trackers/github.json` belongs to no layer.
- **Infer the source from the worktree's checkout.** Rejected as a default in
  #146: a worktree silently running unreleased skills makes every bug report
  ambiguous about which version produced it.

## Consequences

`doctor` gains a state it did not have — a recorded source that is no longer on
disk. It is a warning, not a finding: the repo is not wrong, the answer is just
unreachable.

It also makes #38 answerable. "Orphaned relative to which source" has had no
recorded answer, and the abandoned-entry scan has been comparing disk against a
record whose origin was implicit.

The recorded source is per-checkout, so it lives in `.wf-skills-manifest.json`
(gitignored) rather than `wfctl.json` (tracked). Recording it in the tracked file
would dirty a branch every time someone installed from a path.

## Log

- 2026-09-04  proposed    — level-2 gate for #146; `--from` plus provenance
- 2026-09-05  implemented — Decision amended: the default is recorded by the key
  being absent, not by the wheel's path. The original wording read as though the
  wheel were recorded like any other source, which the implementation rejected —
  an upgrade would then report as the source having changed.
