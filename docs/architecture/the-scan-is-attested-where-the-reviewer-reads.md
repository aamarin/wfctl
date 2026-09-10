---
status: proposed
---

# A scan is attested where the reviewer reads, and detailed where the pipeline reads

## Context

`clarify` and `analyze` are the two steps whose whole job is to find problems.
Both write what they find into `FEATURE_DIR`: clarify into `spec.md`'s
`## Clarifications` section, analyze into `checklists/analysis-report.md`. That
directory resolves outside the working tree in this repo and is gitignored under
the default `<repo>/specs`, so neither reaches the change under review.

Nothing today owns the question a reviewer actually asks. "Was this change
scanned for problems?" is answerable only by opening a store the reviewer has no
path to, and the answer there is the *existence of a file*, which an agent that
skipped the scan produces as readily as one that ran it. A thorough run and a
skipped one are the same change.

The design levels met this and answered it: `121-level3-records-in-pr` gave a
level-3 record a visibility check, on the grounds that a structural argument made
only in `design.md` "is made to nobody". The two review steps were left where
they were.

The failure this has to survive is instruction-level, not artifact-level. Told to
auto-choose, an agent stops generating clarification questions at all — so an
empty artifact is the expected output of both the thorough case and the skipped
one, and a fix that only improves the artifact when the step ran properly has
missed the case.

## Direct baseline

Leave both artifacts where they are, and require the agent to paste clarify's
coverage summary and analyze's findings table into the PR body — the rule
`opening-a-change` already applies one stage later to the review panel's
disposition table, for this exact indistinguishability.

It costs no file, no directory and no new concept, and it puts the evidence in
front of the person who is about to approve the change.

What it does not produce is anything a check can see. A PR body is written once
at the end by a different skill, is editable after review, is absent from the
repository for anyone reading the change later, and is not an artifact the work
produces — so `a-rule-is-expressed-as-a-check` leaves the rule as prose in a
skill, with nothing able to observe a violation. That is the same shape as the
defect, one layer up.

## Decision

The repository holds the attestation; the spec store keeps the detail.

`clarify` and `analyze` each write one file per change, at
`<arch-root>/scans/<issue>-<step>.md`, committed on the branch. It carries the
verdict as one of `satisfied` / `unsatisfied` / `inconclusive`, the coverage the
scan achieved, what it found, and a path to the full artifact in `FEATURE_DIR`.

The `FEATURE_DIR` artifacts are unchanged, and so are the predicates that read
them. Nothing about which steps are automatic changes.

## Owns truth

The repository owns *"was this change scanned, and what did the scan cover?"*.

The spec store cannot own it. `spec_root` resolves outside the working tree and
`<repo>/specs` is gitignored, so nothing it holds is part of the change under
review — the reviewer asking the question has no path to the answer, and an
agent's report that the scan ran is unfalsifiable for the reason
`wfctl-runs-the-verification` gives about its own step.

The spec store keeps *"what exactly did the scan say?"* — the integrated
clarifications and the full findings table. The repository does not take a second
copy of those; `knowledge-placement` rules out a fact with two homes, and these
are two facts, the way an attribution line and its table row are two facts in
`vendor-upstream-skills`. One says a scan happened and how far it reached. The
other is the scan's output, read while the feature is being built and closed when
it ships.

## Considered

- **The PR body**, per *Direct baseline* — the strongest alternative, and it
  loses on being unobservable rather than on being wrong.
- **A record per step per issue under `<arch-root>/design/`** — the destination
  the issue's own sketch names first. That directory belongs to
  `software-design-decisions`, whose records carry a `Direct baseline`, two
  graphs and a `Considered`; a scan that found nothing fills none of them, and
  `design-levels` reads a record with an empty `Considered` as a gate skipped
  more quietly rather than a gate passed. It would also make `<issue>-` ambiguous
  in a directory that is one record per issue today.
- **Appending to the level-3 record the branch already carries** — conditional on
  an unrelated decision. A change that weighed no credible alternative earns no
  level-3 record, and one that declared `arch none` has none at all, so the
  destination goes missing exactly on the branches carrying the least other
  evidence.
- **A new tree beside `docs/architecture/`** — sound, and loses on reach.
  `arch_root` is overridable, so a subdirectory of it moves with a repo that
  relocates its records, while a second top-level tree stays where it was written
  and the skills would have to name both.
- **One file per change with a section per step** — fewer files, and one absence
  to notice instead of two. It needs a merge rule, that analyze replaces its own
  section rather than appending, which nothing can check; an agent following
  prose is the reader that gets merge rules wrong.
- **Having the `clarify` and `analyze` predicates read the new file** — that is
  #100's call about what a gate proves, not this record's. This decision makes
  the evidence reachable. Whether it is sufficient to gate on is decided where
  the evidence contract is decided, and taking it here would answer #100 by side
  effect.

## Consequences

`wfctl arch check` gains a second class of caller and needs no change: it
resolves an arbitrary path and never asks whether that path is under the arch
root (`cli.py:1233`). The scan file's visibility is checked by the command that
already answers "will a reviewer opening this branch read this?".

A fourth subdirectory under the arch root, and nothing in it enters the
projection of decisions in force — `load_records` globs `<root>/*.md` one level
deep (`_arch.py:146`), which is the same reason `design/`, `declarations/` and
`views/` stay out of `wfctl arch context`.

A scan file cannot spuriously satisfy the design gate. `design_block` returns
`None` once `spec.md` exists (`_predicates.py:520`), and both steps run after
`specify`, so a file written under the arch root by either can never be the
record that answers the boundary question. That holds by step order rather than
by exclusion: a change to the order has to re-check it, and would find
`touched_on_this_branch(repo_root, arch, exclude=arch / "design")` counting the
scan directory.

A run that never scanned still writes a file, and this decision does not stop it.
What changes is that its emptiness is in the diff. Refusing the step on it is a
gate, and gates are #100's.

## Log

- 2026-09-09  proposed    — #307. Two steps that exist to find problems, reporting
  where the reviewer has no path to the report.
