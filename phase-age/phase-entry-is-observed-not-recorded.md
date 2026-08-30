---
status: proposed
---

# Phase entry time is observed from artifacts, never recorded when it happens

## Context

wfctl can say which pipeline phase a feature sits in, but not how long it has
sat there. A feature that stalled in `plan` three weeks ago renders identically
to one that entered `plan` this morning, so the stall is noticed by whoever
happens to remember the branch, weeks late.

Reporting the age needs one value the pipeline does not currently have: when
this feature entered the phase it is in. That value has three possible sources
and they disagree about who owns it — the session that watched the transition,
git, or the artifacts themselves.

The choice is load-bearing in a way it does not look. Every candidate can
produce *a* number; the question is which one is still true after nobody has
touched the feature for a month, because that is the only case the feature
exists to report.

## Decision

Phase entry is derived at read time from the modification times of the spec
artifacts `_infer_steps` already reads, and is never written down when the
transition occurs.

The phase is entered when the previous phase's artifact was last written, so
entry time is the newest mtime among the artifacts of *completed* steps —
excluding any artifact the current step is itself still editing.

The first phase has no predecessor artifact and therefore no mtime to read. For
that case only, entry falls back to where the branch diverged from trunk, which
is the moment the feature began. Both sources are observations of durable
evidence; neither is a transition someone remembered to log.

Where nothing can be observed, the age is reported as unknown. It is never
reported as zero.

## Owns truth

The filesystem owns "when did this feature enter the phase it is in?", answered
by re-reading artifact mtimes on every `status`.

The session cannot: a session observes a transition only when a wfctl command
runs, and the pipeline advances by an agent writing a spec file, which runs no
wfctl command. `events.jsonl` is therefore a log of when someone last *asked*,
not of when something last *happened*, and the two diverge precisely while
nobody is asking. That divergence is measurable today — branch
`86-architecture-knowledge-lifecycle` has a last recorded step of `specify`
against a `tasks.md` written two days later, so a stall report built on the
event log would place that feature four phases behind where it stands.

The failure this produces is not a missing number but a fabricated one. A
recorded history reports a feature as stuck in a phase it left, which is the
exact claim the feature exists to make, inverted. A stall detector whose
evidence is generated only by activity cannot observe the absence of activity.

Git cannot: at the default root, `<repo>/specs` is gitignored on purpose, so the
artifacts whose creation *is* the transition have no commit history at all. A
durable spec root may be its own repository — this project's is — but its
history is committed in batches, one commit spanning design through decompose
and archival commits landing weeks after the work. A commit date says when
someone tidied up, not when a phase was entered. Git dates the branch, and that
is why it answers the first phase and nothing else.

## Considered

- **Record each transition to `events.jsonl` as it happens** — the log is
  appended only by `start`, `next` and `resume`. `/speckit.plan` writing
  `plan.md` fires none of them, so the log has holes exactly where the pipeline
  moved unobserved, and a hole is indistinguishable from a stall.
- **Add a `phase_entered` field to `current.json`** — write-once state that goes
  stale, the shape `session-state-is-re-derived` was written against. It would
  also be wrong on arrival: the field is written by whichever command ran next,
  not by the transition.
- **Read the commit date of the spec artifacts** — absent at the default root,
  which is gitignored, and wrong-grained where a durable root does carry history:
  this project's spec repo commits design through decompose as one commit, so
  the phases inside it share a single date.
- **Use the spec directory's own mtime as a feature-start time** — the spec root
  carries eight directories stamped within the same second, from a bulk move
  that left the files inside untouched. Directory mtimes record the last
  operation on the container, and containers get moved. File mtimes survived
  that same move.
- **Age every step, not just the current one** — needs a full transition
  history, which is the recorded-history option under a different name. Only the
  current phase has an entry time that can be read from what is on disk.

## Consequences

The age is exactly as trustworthy as the mtimes. Restoring a spec dir from a
copy, or touching a file, resets the clock and the phase reads younger than it
is.

That failure runs in the safe direction and is accepted rather than mitigated: a
missed stall leaves today's behaviour in place, while a fabricated stall teaches
the reader to disregard the signal, after which no stall is reported at all.
Under-reporting degrades to the status quo; over-reporting destroys the feature.

Only the named pipeline artifacts may be stat'd. "Newest file in the spec
directory" is not a cheaper spelling of the same thing: Finder has written a
`.DS_Store` into every directory of this project's spec root within one second
of each other, and a scan that counted it reported nine features as active that
had been untouched for eleven to nineteen days. Any file the pipeline does not
name is noise, and noise here reads as progress.

`_pipeline` stays free of `subprocess`. The git fallback is passed in from the
caller as an unevaluated callable, the shape `design_gate` already uses for
`unanswered` and for the same reason — otherwise every test of a phase age has
to build a repository to assert on a string.

The stall threshold is a separate question this record does not answer. It
decides where the number comes from, not what value makes it worth shouting
about.

## Log

- 2026-08-28  proposed    — level-2 gate for reporting how long a feature has sat in its phase
