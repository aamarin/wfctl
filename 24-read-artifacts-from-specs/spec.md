# Spec: Read artifacts from specs/&lt;branch&gt;/ and report layout skew

**Status:** Draft
**Date:** 2026-08-06
**Branch:** 24-read-artifacts-from-specs
**Issue:** #24 (sub-issue of aamarin/wf-skills#11)

## Problem

A branch's artifacts live in two directories. Ten of them — spec, plan,
research, tasks, delivery, checklists — sit under `specs/<branch>/`. One, the
design document brainstorming produces, sits at `.agent/spec.md` at the repo
root, because brainstorming runs before speckit has a directory to write into.

wfctl pays for that split in two places:

- `_archive.py` carries `_DESIGN_DOC` as a constant separate from `_SPEC_MAP`,
  and `_plan()` appends it through its own branch before the map iteration —
  a special case that exists only to reach outside the spec dir.
- `_pipeline.py` reads `repo_root / ".agent" / "spec.md"` to decide whether the
  `brainstorm` step is complete.

The upstream feature (`11-agent-artifact-layout`) moves the design document to
`specs/<branch>/design.md`, collapsing the split. This issue is the **consumer**
half: wfctl must read the new location. It must merge and release **before** the
producer half — if the skills start writing `specs/<branch>/design.md` while
wfctl still reads `.agent/spec.md`, every branch's pipeline inference silently
reports `brainstorm` as incomplete, with no error to explain why.

The upstream clarification session settled the transition question: **no
component reads both locations.** A repo carrying the superseded directory is
skew, and skew is reported, not accommodated.

## User Scenarios

1. **Brainstorm recognised at the new path.** A branch whose brainstorming wrote
   `specs/<branch>/design.md` shows `brainstorm ●` in `wfctl status`; step
   inference advances past it.
2. **Archiving a completed story.** A branch that ran the full pipeline archives
   to a contiguous `1-design.md` … `11-analysis-report.md`, with the design
   document occupying slot 1 as an ordinary map entry.
3. **Archiving a partial story.** A branch archived mid-pipeline produces the
   subset of that sequence its artifacts justify. Nothing lands under `extra/`
   that the map should have named.
4. **A repo with the superseded directory.** A developer whose repo still has a
   `.agent/` directory runs `wfctl doctor` and gets a `⚠` naming the superseded
   path and the action that resolves it. The diagnostic fires whether or not
   skills are installed.
5. **A clean repo.** No `.agent/` directory — `doctor` says nothing about it and
   its exit code is unchanged.

## Functional Requirements

- **FR1** The design document is an ordinary `_SPEC_MAP` entry
  (`design.md` → `1-design.md`). `_DESIGN_DOC` and the `_plan()` branch that
  appends it separately are removed, not repointed.
- **FR2** Step inference resolves the brainstorm artifact inside the spec dir
  (`specs/<branch>/design.md`), not at the repo root.
- **FR3** No component *infers* from both the old and new locations. There is no
  fallback, no "try the other path", no transition window. Step inference, the
  archive's numbered sequence, and the skew diagnostic each read exactly one
  place, and it is the new one.
- **FR3a** Preserving a file is not inferring from it. `archive-story` runs from
  workmux's `pre_remove`, so declining to archive an artifact at the old path
  *deletes* it — the opposite of that command's purpose. A design document found
  at `.agent/spec.md` is therefore swept into `extra/legacy-agent-spec.md`.
  Nothing reads the archive, and `extra/` is already the shelf for artifacts the
  map does not name, so the numbered sequence keeps describing only what the
  current pipeline produces. Transition-only: this is deleted once no worktree
  predates the move.
- **FR4** `wfctl doctor` emits a `⚠` when the repo carries a `.agent/`
  directory, naming the superseded path and the resolving action.
- **FR5** The skew diagnostic runs before doctor's installed-skills gate, so a
  repo with nothing installed still gets the warning.
- **FR6** The skew diagnostic does not change doctor's exit code — it reports
  drift the way the `.workmux.yaml` hook check does, not a failure.
- **FR7** `grep -rn '"\.agent"\|\.agent/' wfctl/ tests/` returns only the skew
  diagnostic, the FR3a sweep, and their tests. Nothing else names the old path —
  no reader, no docstring describing the old layout as current. The literal
  "returns nothing" this requirement first carried is unsatisfiable: a warning
  that tells you to remove `.agent/` has to spell `.agent/`, and its tests have
  to assert that string, so that phrasing contradicted FR4.
- **FR8** The `.gitignore` entry for `.agent/` is removed. `specs/` is already
  ignored, so the design document stays local at its new home; a leftover
  `.agent/` becoming visible in `git status` reinforces FR4 rather than hiding
  the skew.

## Success Criteria

- A branch with `specs/<branch>/design.md` and nothing else reports `brainstorm`
  complete; a branch with neither reports it incomplete.
- Archiving a full story yields the numbered sequence 1 through 11 with no gaps
  and no misnumbering past 9.
- Archiving a story with no design document yields the same sequence minus slot
  1 — the absence leaves a gap in the numbers, not a renumbering.
- A repo containing `.agent/` produces exactly one `⚠` from `doctor`, in a repo
  with skills installed and in one without.
- A repo containing no `.agent/` produces no such warning, and doctor's exit
  code is identical with and without the directory present.
- The warning names the *move* — a developer reading it knows to relocate the
  file, not only that a component is stale. It asserts nothing about what wrote
  the directory or when, since a directory cannot establish either.
- Archiving a branch that still has `.agent/spec.md` preserves it under
  `extra/`, with its content intact, both alongside a spec dir and as the only
  artifact present.
- `grep -rn '"\.agent"\|\.agent/' wfctl/ tests/` returns only the diagnostic,
  the sweep, and their tests — no reader of the old path.
- `uv run pytest -q` is green.

## Key Entities

- **Design document** — the brainstorming artifact. Relocates from
  `.agent/spec.md` to `specs/<branch>/design.md`; keeps its archived name
  `1-design.md`.
- **`_SPEC_MAP`** — the ordered source→archived-name list in `_archive.py`. This
  feature grows it by one entry at the front and shrinks the code around it.
- **Layout skew** — a repo whose components disagree about where artifacts
  live, evidenced by a surviving `.agent/` directory. A reported condition, not
  a supported state. The directory is evidence that *something* wrote there, not
  of when: a stale leftover and a component still writing today look identical
  from the outside, so the diagnostic reports the observation, not a cause.

## Assumptions / Out of Scope

- The skew check looks for `.agent/` at the repo root — the only place the old
  layout ever wrote it. No recursive search.
- The producer half (aamarin/wf-skills#11 — the skills that *write* the design
  document, including this repo's installed `speckit-specify`, whose pre-specify
  gate still names `.agent/spec.md`) is **out of scope here** and lands after
  this ships. Installed skills are gitignored; they update via
  `wfctl install-skills`, not this PR.
- Migrating an existing `.agent/spec.md` into the spec dir is out of scope. The
  warning names the action; wfctl does not move a developer's files for them.
- Source tasks T001–T013 and T028 of the upstream
  `specs/11-agent-artifact-layout/tasks.md` define the work; that task file
  lives in the wf-skills repo and is referenced, not vendored.
