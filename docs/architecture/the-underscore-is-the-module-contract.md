---
status: proposed
---

# A leading underscore is the module's contract, and `cli` is bound by it

## Context

Four private names cross a module boundary into `cli`:

```
   cli → _paths._SPEC_DIR_OVERRIDE     ─┐  env var names, printed by
   cli → _paths._STATE_DIR_OVERRIDE    ─┘  `wfctl spec-root` and refused
                                           by `wfctl state-dir --branch`

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

The underscore is the contract, and it governs **members, not modules**.

```
   module name      _pipeline  _arch  _paths  _io …
                    internal to the package, not to a module.
                    `cli` importing `_pipeline` is not a crossing.

   member name      _infer_steps  _current_step_name
                    _SPEC_DIR_OVERRIDE  _STATE_DIR_OVERRIDE
                    internal to the module that defines it.
                    No other module may import one.
```

Thirteen of fourteen modules carry the prefix, so a rule phrased over "a name
prefixed with `_`" forbids the package's own structure. The distinction above is
the rule; the earlier phrasing was the same rule stated in a way that could not
tell its two subjects apart.

**The rule is expressed as an executable check, not as the marker alone.** A
check over the AST fails the build on any import of a `_`-prefixed member from
another module in the package. `tests/` is exempt by name.

Where `cli` needs a name today, the name becomes public rather than the crossing
being tolerated:

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

Renaming and writing the check are phase 2 and belong to the branch that does
them.

## Owns truth

Each module owns *"which of my members may another module import?"*, and it
answers with the underscore.

`cli` cannot compute it. Whether a name is safe to depend on is a statement
about what its module promises not to change, and only that module can make it.
A caller that reaches past the marker has decided the question on the callee's
behalf, from the outside, using the fact that Python let it — and the callee
then cannot rename its own internals without breaking a caller it never agreed
to have.

The package owns *"which of my modules may something outside import?"*, and that
question is not this record's. It is answered today by there being no consumer:
nothing outside the wheel imports `wfctl.*`.

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
  `cli`, so a private name it depends on has exactly one consumer. It loses on
  enforceability rather than on a flaw: an exemption for the one module that
  touches everything exempts the coupling that matters, and it would have to be
  repealed the moment `cli` is split — which is phase 2's most likely first move.
- **The marker alone, with the four names promoted.** The original decision here,
  and the one the #149 amendment held open. Equally sound on the boundary and it
  loses on the ranked driver only: nothing new can check it, so the fifth
  crossing arrives the way the first four did. Not rejected for a flaw in its
  reasoning.
- **`__all__` on each module, plus the check.** Declares each module's surface as
  data a tool and a reader can both consume, which the marker cannot: `_` is
  distributed across every name, `__all__` is one list. It answers a legibility
  driver that this iteration ranked below enforcement, and it is the option to
  revisit if a reader is ever observed unable to identify a module's surface. Not
  chosen because the check alone satisfies the ranked driver, and fourteen lists
  to keep in sync is vocabulary this decision does not need. Zero modules declare
  `__all__` today.
- **Enforce it with a test rather than deciding it.** Rejected as an *answer* and
  adopted as the *expression*: a check can hold a rule but cannot choose one, so
  the rule is this record and the check is how it binds. Stated separately
  because the two were previously conflated.

## Consequences

The check fails on `tests/`, which imports twenty-six distinct private names,
including six private modules. The exemption is by directory and is the price of
the decision rather than a flaw in it — a test that could not reach past the
marker would be testing the public surface only, which is a different rule
nobody proposed.

`tests/test_architecture_view.py` pins the *count* of crossings at four, so it
fails when a fifth is added and equally when one of the four is resolved. That
is the inventory, not the rule. The check this record names is the rule, and the
count assertion becomes redundant once the check exists.

#115 unblocks: the question its fix turns on is answered here, and the fix
should point its test at whatever `_infer_steps` is renamed to rather than
cementing the private name.

#168 is not blocked by this record, but it should not be read as satisfying it.
Moving `next_cmd` onto `build_report` removes two crossings and answers nothing;
`infer_pipeline` is still the dead public name afterwards.

## Log

- 2026-09-04  proposed    — #149 phase 1, pass 2: the four private crossings
- 2026-09-05  revised     — expression decided: an executable check over members, not the marker alone (#149 amendment)
