# Research: design passes on every change

Each entry gives the decision, why, and what else was weighed. The spec left no
`NEEDS CLARIFICATION` marker, so these are the questions reading the code
raised.

## R1. The finding messages name no section-specific instruction

- **Decision**: `check-body` uses one message shape for every listed section,
  with the heading quoted. The instruction for what a good answer looks like
  lives in the template's HTML comment under that heading.

  ```
  ⚠ "Needs a spec?" is missing. This repository asks every pull request to answer it.
  ⚠ "Needs a spec?" is empty. The template's comment under that heading says what to write.
  ⚠ "Needs a spec?" holds N/A. The template's comment under that heading says what to write.
  ```

- **Rationale**: The spec's first draft had "Answer yes or no, and say why in
  one sentence" in the N/A message. That sentence is about one section, and
  `628-spec-answer-in-pr-body.md` decides that wfctl hardcodes no section
  names. A message that knows what the section asks is the same thing one step
  removed. The agent reads the template in `opening-a-change` Step 2, so the
  comment under a listed section is where that instruction belongs. Not every
  section in this repo's template has a comment, so the one for "Needs a
  spec?" is written out in `contracts/cli.md`. A repo that lists a section is
  responsible for its comment, and `check config` doesn't check for one.
- **Alternatives considered**: Let each `change_sections` entry be an object
  with a `hint` string. We didn't choose it because it adds a schema for a
  sentence the template already holds, and the two copies would drift.
- **Effect on the spec**: User Story 2's acceptance scenarios 1 and 2 now quote
  these strings.

## R2. The marker is `⚠`, not `✗`

- **Decision**: Findings print with `check-body`'s existing `⚠` marker, and
  the command still exits 1 when it finds anything.
- **Rationale**: `check_body_cmd` (`wfctl/cli.py:6439`) prints every finding as
  `⚠` and exits 1. Its docstring says it gates nothing and exits 1 so the
  finding is hard to walk past. A second marker for one kind of finding would
  suggest a second severity that doesn't exist.
- **Alternatives considered**: `✗`, as `design.md` drew it. We didn't choose it
  for the reason above.

## R3. A clean body still prints the existing `✓` line

- **Decision**: When nothing is found, `check-body` prints
  `✓ <path>: the drawings look right`, exactly as today.
- **Rationale**: SC-003 requires byte-identical output in a repo that lists no
  sections. `design.md` showed a clean run printing nothing, which was wrong
  about today's output. Rewording the line only for repos that list sections
  would make the output depend on config for no reader's benefit.

## R4. How a section is found in a body

- **Decision**: A section is an ATX heading (`#` to `######`) whose text,
  trimmed and compared case-insensitively, equals the listed name. Its body
  runs to the next ATX heading of the same or a higher level. Headings inside
  fenced code blocks don't count, using `wfctl/_md.py`'s `walk`.
- **Rationale**: `_md.walk` is the fence-aware reader `_shape.py`, `_arch.py`,
  and `_evidence.py` already share. A heading quoted inside a fence is the
  failure its module docstring names. Matching on text rather than level lets
  a repo put the section at `##` or `###`.
- **Alternatives considered**: Setext headings (`Title` over `===`). We didn't
  choose them because no template in this repo or the shipped seed uses them,
  and a renamed or missing heading already fails safe as "missing".

## R5. What counts as empty, as N/A, and as no reason

- **Decision**: Strip every `<!-- … -->` comment, including multi-line ones,
  then whitespace. Nothing left is empty. What's left matching
  `n/?a\.?`, case-insensitive, is N/A. What's left matching `(yes|no)[.!]?`,
  case-insensitive, is a bare answer with no reason.
- **Rationale**: The template carries a comment under the heading, and a body
  that only kept it answers nothing. `N/A`, `n/a`, `NA`, and `N/A.` are the
  forms an agent writes when following the template's "N/A over deletion" rule.
  A bare yes or no leaves no record of why the decision was made, and the
  reason is what a reviewer compares with the diff to catch a contradiction.
  The rule applies to every listed section, not only "Needs a spec?", since a
  repo lists a section for a reader and a one-word answer gives the reader
  nothing. The check confirms that a reason is there, not that it's a good
  one: "No, small change." passes, and the reviewer judges it.
- **Alternatives considered**: Require a minimum length, such as five words.
  We didn't choose it because a length can't tell a reason from padding
  either, and it would fail a short real answer.
- **Alternatives considered**: Also treat "TBD", "-", or "None" as no answer.
  We didn't choose them because "None" can be a real answer in some section,
  and the check is meant to catch the template's own escape hatch, not judge
  wording. The reviewer judges the answer.

## R6. How `check config` finds the PR template

- **Decision**: `_sections.templates(repo_root)` mirrors `opening-a-change`
  Step 2: files up to three levels deep, outside `.git`, whose path matches
  `pull_request_template` or `merge_request_template` case-insensitively. Every
  template found has to carry every listed section, and each gap is its own
  finding naming the template and the section. Listing sections with no
  template found is one finding.
- **Rationale**: This was the clarify scan's one deferred row. A
  `PULL_REQUEST_TEMPLATE/` directory holds one template per kind of change, and
  a template missing a listed section produces a PR that can't pass. Reporting
  each gap by template tells the author which file to edit.
- **Alternatives considered**: Check only the first template found. We didn't
  choose it because the template the agent picks in Step 2 is the change's
  choice, so any of them can be the one in use.
- **Duplication**: The search now exists in Python and in the skill's `find`
  line. `628-spec-answer-in-pr-body.md` names that duplication as a reason not
  to read sections from the template in `check-body`. Here it's confined to
  `check config`, which the author runs after editing `wfctl.json`, and a
  drifted search shows up as a finding there, not as a PR that silently passes.

## R7. A malformed `change_sections` isn't silent in `check-body`

- **Decision**: `_sections.load_required` returns `(names, problems)` like
  `_change.load_required`. `check config` prints the problems. `check-body`
  adds them as findings too.
- **Rationale**: A value that isn't a list of strings would otherwise turn the
  check off with no output, which is the "check that quietly stops checking"
  `_change.py` warns about. `check-body` is the command the author is running
  at that moment.
- **Alternatives considered**: Report it only in `check config`, the way
  `_change.load_required` leaves a malformed `wfctl.json` to `doctor`. We
  didn't choose it because nothing makes the author run `check config` before
  opening a PR.

## R8. `design-passes` ships as a skill with no command wrapper, and is mirrored

- **Decision**: `wfctl/agents/skills/design-passes/SKILL.md`, with no file in
  `wfctl/agents/commands/`, and an entry in `_MIRRORED_SKILLS` in
  `wfctl/cli.py`.
- **Rationale**: The route line, the "not for" lines, and `AGENTS.md` point to
  the skill by path, the way `opening-a-change` points to
  `fanning-out-code-review`. An agent that follows one of those pointers and
  calls the skill by name is refused unless the skill is in `_MIRRORED_SKILLS`.
  The entry fixes that. The test in `tests/test_install_skills.py` pins only
  the skills that also have a wrapper, so it doesn't change. We first left the
  entry out, and the skill didn't appear under `.claude/skills` until we added
  it.
- **Alternatives considered**: A `/design-passes` command. We didn't choose it
  because a description- or command-triggered entry is exactly what #290 found
  isn't reached unattended.

## R9. The shipped PR template seed stays as it is

- **Decision**: `wfctl/agents/configs/github/.github/pull_request_template.md`
  gets no "Needs a spec?" section. Only this repo's template does.
- **Rationale**: Other repos opt in with one line in `wfctl.json`. A seeded
  section with no `change_sections` entry would be one more section for every
  new repo's PRs to fill, with nothing behind it.
- **Alternatives considered**: Seed it so a new repo only has to add the
  `wfctl.json` line. We didn't choose it because it decides for every repo
  that the spec question belongs in its PRs.
