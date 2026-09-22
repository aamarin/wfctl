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
record under the arch root, asks which level's required section the file carries,
and reports the file when the directory holding it disagrees. Three answers are
findings:

| The file | What it is | Marker |
|---|---|---|
| Under `design/`, carries `Owns truth` | a level-2 decision that has stopped binding | `✗` |
| At the root, carries `Diagram` and not `Owns truth` | a level-3 record filed up, which `arch context` loads and prints as though it bound something | `✗` |
| Carries neither section, either directory | it weighed nothing and belongs under `implementation/` | `⚠` |

`Owns truth` is asked first and `Diagram` only in its absence, so a file carrying
both is level-2 rather than a fourth case. That follows from what the section
means: `Owns truth` is what makes a record bind, and a diagram drawn beside one
is decoration on a decision that still owns something. Reading the two sections
as an exclusive pair would have forced an answer for a shape that is not actually
ambiguous.

The second row is the first one's mirror, and it is the direction #419 does not
mention. Filing a level-2 record down hides it; filing a level-3 record up
publishes it, and a session then loads a contract carrying a decision nobody
meant to bind. Both are wrong the moment they land, so both reach the exit code.

`arch check` and the `status` design gate keep the questions they already ask.
Neither is extended, and neither is retired.

## Owns truth

`doctor` owns *"is every record filed at the level its directory claims?"*.

`arch check` cannot: it is handed one path by a caller who already has that
record in mind, so it can only ever confirm a suspicion someone already had. The
failure here is that nobody suspects anything — a misfiled record produces no
symptom, which is why it survived the whole corpus and the whole of the time
records have existed here. A check that reaches only named paths reproduces the
silence it was built to break.

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
- **Both sections as a finding of its own** — a file carrying `Owns truth` and
  `Diagram` together is ambiguous about its level, so a third marker could ask
  its author which they meant. Rejected: the ambiguity is in the pair, not in
  the file. One of the two sections decides whether a record binds and the other
  does not, so asking them in order answers the question that a fourth finding
  would only have forwarded to a human.
- **`doctor`'s remit as originally written** — "state wfctl installed or seeded"
  would have excluded this outright, and #419 argues from that reading. #113
  already widened it: `_check_arch_records` reads a directory wfctl never wrote,
  because "integrity over content wfctl only *reads* is still a question with one
  right answer" (`cli.py`). This decision takes that rule at its word rather than
  extending it again.

## Consequences

A finding that reaches the exit code turns `/start-session` and the definition of
done red, so the cases are not equal and cannot share a marker: a record whose
directory makes it lie about whether it binds is wrong today and takes `✗`, while
a note in the wrong drawer takes `⚠` and only nags. That split is this decision's,
not the implementation's.

`doctor` runs unprompted at every session start, which its own docstring names as
a hazard — "a magnet for anything you want noticed, and each arrival costs the
exit code some of its meaning". This is the second check admitted under the
widened remit, and #443 exists to decide the admission list before there is a
third.

Nothing on disk trips any of the three rows. Run 2026-09-21: all 58 records
carry exactly one of the two sections and sit in the directory that section
names — 39 with `Owns truth` at the root, 19 with `Diagram` under `design/`,
none with both and none with neither. A check that fires on a correctly-placed
record gets ignored and then removed, so that run is the evidence this decision
rests on rather than a fixture built to agree with it.

The count is dated because it drifts with every record added, including the two
this change writes. What the run establishes is the verdict — no false positive
on a corpus nobody built to agree with it — and the test that re-establishes it
declines to assert a number for the same reason.

## Log

- 2026-09-21  proposed  — #419 asked which command owns the verdict that a record
  is misfiled; `arch check`, `status` and `doctor` each answer a different
  question about the same tree, and only one of them reaches a record nobody
  named.
- 2026-09-21  amended  — the rule now asks `Owns truth` before `Diagram` rather
  than treating them as an exclusive pair, which settles the both-sections case
  the first draft left open, and a level-3 record filed up at the root is a
  finding in its own right. Run over all 57 records on disk: no false positives.
