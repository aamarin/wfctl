---
status: proposed
---

# A leading underscore is the module's contract, and `cli` is bound by it

## Context

Four private names cross a module boundary into `cli`:

```
   cli → _paths._SPEC_DIR_OVERRIDE     ─┐  env var names, printed by
   cli → _paths._STATE_DIR_OVERRIDE    ─┘  `wfctl spec-root` and refused
                                           by `wfctl handoff --branch`

   cli → _pipeline._current_step_name  ─┐  the inference itself, called
   cli → _pipeline._infer_steps        ─┘  by `wfctl next`
```

`_pipeline` states the rule it means to follow, at line 53:

> Public because `cli` imports them — the data above stays private.

Two names on that same module break it. And the inversion runs deeper than the
crossings: `infer_pipeline` (line 354) is public and has **zero** production
callers and one test assertion; `_infer_steps` (line 131) is private and is what
`cli` and every other test actually call. The public entry point is dead and the
private one is the real surface.

`#115` proposes pointing that one test at `_infer_steps` directly. That closes
the dead-code finding and makes the inversion permanent, which is why the
boundary question belongs here rather than there.

#118 sharpened this while this record was being written. `build_report` now
carries `auto`, `resume` renders a report instead of inferring, and `next_cmd`
is the last view in `cli` that calls the inference by hand — filed as #168.
Two consequences pull in opposite directions. `_pipeline`'s real public entry
point is now visibly `build_report`, not `infer_pipeline`, which is the surface
this record is about. And #168 would delete two of the four crossings as a side
effect of a plumbing change, with nobody having answered the question — leaving
`infer_pipeline` dead, `_infer_steps` private, and the inversion intact with its
last visible symptom gone.

Nothing enforces any of this. A module-private name is a convention Python does
not check, so today the underscore is a comment that four call sites contradict.

## Decision

The underscore is the contract: a name prefixed with `_` is internal to its
module, and no other module may import it. Where `cli` needs a name today, the
name becomes public rather than the crossing being tolerated.

Applied to the four crossings:

```
   _SPEC_DIR_OVERRIDE   → public.  The env var name is a user-facing
   _STATE_DIR_OVERRIDE            contract already; `cli` prints it in a
                                  diagnostic, so it is documented whether
                                  or not the constant is.

   _infer_steps         → public.  It is `_pipeline`'s real entry point.
   _current_step_name   → public.

   infer_pipeline       → the dead shape. It survives or is removed on
                                  #115's evidence, not this record's.
```

Renaming is phase 2 and belongs to the branch that does it.

## Owns truth

Each module owns *"which of my names may another module import?"*, and it
answers with the underscore.

`cli` cannot compute it. Whether a name is safe to depend on is a statement
about what its module promises not to change, and only that module can make it.
A caller that reaches past the marker has decided the question on the callee's
behalf, from the outside, using the fact that Python let it — and the callee
then cannot rename its own internals without breaking a caller it never agreed
to have.

## Considered

- **Leave the four crossings and treat the underscore as advisory.** The code
  works and the names are stable in practice. Rejected: it makes the marker mean
  nothing, and `_pipeline.py:53` already spends a comment stating a rule the
  module then breaks. A marker that four call sites ignore is worse than no
  marker, because the next reader cannot tell which of the remaining private
  names are real.
- **Declare `cli` exempt — it is the only importer, so nothing else can be
  broken by the coupling.** This is the honest version of the status quo and it
  is not obviously wrong: `cli` imports all thirteen modules and nothing imports
  `cli`, so a private name it depends on has exactly one consumer. It loses to
  driver 1, not to a flaw: an exemption for the one module that touches
  everything exempts the coupling that matters, and it would have to be repealed
  the moment `cli` is split — which is phase 2's most likely first move.
- **Enforce it with a test rather than deciding it.** A check over the AST could
  fail on any private cross-module import. Rejected as an answer, kept as a
  consequence: a test can hold a rule but cannot choose one, and it would fail
  today on four crossings with nothing saying which side is wrong.
- **`__all__` on each module instead of the underscore.** A second marker beside
  the one already in use, on fourteen modules, to express what the first one
  already expresses. Rejected: vocabulary added before a decision needs it.

## Consequences

`tests/test_architecture_view.py` fails on a fifth crossing, and on any of these
four being resolved without the current-state view being updated. It enforces
the count, not the rule — the rule is this record.

#115 unblocks: the question its fix turns on is answered here, and the fix
should point its test at whatever `_infer_steps` is renamed to rather than
cementing the private name.

#168 is not blocked by this record, but it should not be read as satisfying it.
Moving `next_cmd` onto `build_report` removes two crossings and answers nothing;
`infer_pipeline` is still the dead public name afterwards.

## Log

- 2026-09-04  proposed    — #149 phase 1, pass 2: the four private crossings
