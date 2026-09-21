---
status: proposed
---

# `doctor` owns whether a record is filed at its own level

## Context

A record's level is carried by the directory it sits in, and nothing checks that
the file agrees. `load_records` globs one level, so a level-2 record written to
`<arch-root>/design/` is not reported wrong by `wfctl arch context` — it is
absent. The session loads a contract that silently lacks it, the file is on disk
looking settled, and no run anywhere disagrees. `software-design-decisions`
states the failure in its own words and ships it as prose a reader has to
remember (#419).

`a-rule-is-expressed-as-a-check` (accepted) decides what to do about that: the
violation is a file in the pull request, so the rule is owed a check. What that
record does not decide is which command runs it, and the three candidates answer
different questions about the same tree.

## Direct baseline

Extend `wfctl arch check <record>`, which already takes a record path, already
resolves the repo root, and is already invoked by
`software-design-decisions`' own verification list and by four
`speckit.*` wrappers through `allowed-tools`. The placement rule is then a
comparison between the headings the file carries and the directory it was
handed in — no new command, no new call site, and it fires at the moment the
record is written, which is the cheapest moment to move a file.

## Decision

`doctor` gains a placement check beside `_check_arch_records`. It reads every
record under the arch root and reports one whose sections do not match the
directory holding it: a file under `design/` carrying `Owns truth` is a level-2
decision that has stopped binding, and one carrying neither `Owns truth` nor
`Diagram` weighed nothing and belongs under `implementation/`.

`arch check` and the `status` design gate keep the questions they already ask.
Neither is extended, and neither is retired.

## Owns truth

`doctor` owns *"is every record filed at the level its directory claims?"*.

`arch check` cannot: it is handed one path by a caller who already has that
record in mind, so it can only ever confirm a suspicion someone already had. The
failure here is that nobody suspects anything — a misfiled record produces no
symptom, which is why it survived 56 records and two years. A check that reaches
only named paths reproduces the silence it was built to break.

`status` cannot either, and for a reason of its own rather than the same one: its
design gate is scoped to one branch, excludes `design/` by name, and answers only
whether a boundary question was *put* — never whether the answer was right
(`_predicates.py`, FR-010a). Records already on disk are outside its scope by
construction, and correctness is outside its purpose by decision.

## Considered

- **`wfctl arch check <record>`, the baseline** — sound, cheapest, and it fires
  earlier than the decision does. It loses on fit rather than fault: it answers
  about the path it is given, and the records this check exists to find are the
  ones nobody thought to name.
- **`status`'s design gate** — catches the mistake while the author still has the
  file open, which is the one property `doctor` cannot offer. Rejected because
  adopting it would contradict the gate's stated purpose, and a gate that both
  counts records and judges them can no longer say which of the two it failed on.
- **A new `wfctl check` group beside `config`** — #419's own recommendation.
  It describes a command that does not exist; `wfctl.json` validation is reached
  through `wfctl change check`, not a `check` group. Building the group to hold
  one finding also skips the question of what else belongs in it, which is #443.
- **`doctor`'s remit as originally written** — "state wfctl installed or seeded"
  would have excluded this outright, and #419 argues from that reading. #113
  already widened it: `_check_arch_records` reads a directory wfctl never wrote,
  because "integrity over content wfctl only *reads* is still a question with one
  right answer" (`cli.py`). This decision takes that rule at its word rather than
  extending it again.

## Consequences

A finding that reaches the exit code turns `/start-session` and the definition of
done red, so the two cases are not equal and cannot share a marker: a rule that
has stopped binding is wrong today and takes `✗`, while a note in the wrong
drawer takes `⚠` and only nags. That split is this decision's, not the
implementation's.

`doctor` runs unprompted at every session start, which its own docstring names as
a hazard — "a magnet for anything you want noticed, and each arrival costs the
exit code some of its meaning". This is the second check admitted under the
widened remit, and #443 exists to decide the admission list before there is a
third.

Left open: a record carrying both `Owns truth` and `Diagram` satisfies neither
branch of the rule, and whether that is a finding is undecided.

## Log

- 2026-09-21  proposed  — #419 asked which command owns the verdict that a record
  is misfiled; `arch check`, `status` and `doctor` each answer a different
  question about the same tree, and only one of them reaches a record nobody
  named.
