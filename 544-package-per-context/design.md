# Check imports against the Context Map

Contexts: architecture-records

## Problem

The domain page draws seven bounded contexts and a Context Map of which one
depends on which, and nothing in the code follows it. wfctl is one flat package
of 42 modules, and any module can import any other. The status code already
imports the session module to read the event log, which reverses relationship
R6 on the map, and no check found it.

## Decision

`docs/architecture/contexts-are-packages.md` is accepted. Each context becomes a
package with one public module, and an import between contexts is allowed only
along an arrow the Context Map draws, and only into the other context's public
module. This branch ships the check and its baseline. No module moves here. The
moves are follow-ups under #671, one context per PR.

The domain page now names each context's package in its Bounded Contexts table:

| Context | Package |
| --- | --- |
| Evidence and derivation | `evidence` |
| Architecture records | `arch` |
| Design method | `design` |
| Install and drift | `install` |
| Session continuity | `session` |
| Attention | `attention` |
| Worktree guard | `guard` |

Architecture records is `arch` rather than `records`, because Evidence keeps
review runs, verdicts, and completion records too. A bare "record" means a
lasting decision at level 2 or level 3, and the vocabulary table on the domain
page now says so.

## What the developer sees

The check prints one block per failing import, with the boundary drawn. An
arrow means "imports", and ✗ marks the import the check refuses:

```
✗ wfctl/evidence/_status.py:41 imports wfctl.session

  ┌ Evidence and derivation ┐           ┌ Session continuity ─┐
  │                         │◀──────────│                     │  allowed, the map draws it
  │ _status.py ─────────────┼─────✗────▶│ wfctl.session       │  refused, no arrow this way
  └─────────────────────────┘           └─────────────────────┘

  Move what you need into Evidence and derivation. If the dependency is
  meant, ask the user to add the arrow in docs/architecture/domain/wfctl.md.


✗ wfctl/session/_handoff.py:12 imports wfctl.evidence._paths

  ┌ Session continuity ─┐           ┌ Evidence and derivation ┐
  │                     │──────────▶│ public                  │  allowed
  │ _handoff.py ────────┼─────✗────▶│ _paths                  │  refused, internal
  └─────────────────────┘           └─────────────────────────┘

  Import it from wfctl.evidence.public. If that module lacks what you
  need, export it there.


✗ wfctl/_pipeline.py -> wfctl._session is on the baseline, and no import
  matches it any more. Delete the line so it can't come back unnoticed.
```

The module names above are placeholders, since each context picks its public
module's name when its code moves. A fourth failure covers naming. A public
module outside `arch` that defines a bare `Record`, `record`, `load_record`, or
`records` fails, and the message names the qualified form to use instead, such
as `load_verdict`.

## How the check works

1. The check is `.github/scripts/check_imports.py`, beside the release note
   check. `wfctl verify` runs it from `wfctl.json`, CI runs it, and a test in
   the suite runs it, so all three use the same script.
2. It reads the Context Map's mermaid block and the Bounded Contexts table from
   `docs/architecture/domain/wfctl.md`. Nodes labelled "(outside)" are outside
   parties and are skipped. Each arrow between two contexts allows the
   downstream context to import the upstream one.
3. It builds the import graph the way `tests/test_architecture_view.py` already
   does, including function-local imports and private names reached through an
   attribute.
4. A module's context is the package its path is in. A module that hasn't
   moved yet has no package, so the baseline gives its context on a
   `_session.py session` line, taken from the module placement agreed on
   2026-11-01. Without those lines the check would pass every import until the
   first move, including the reversal of R6. `_paths.py` serves three contexts
   until it splits, so its placement line puts it in the shared core for now.
5. The baseline also lists the imports that break the rules today, one
   `src -> dst` line each.
6. It fails on any import that breaks a rule and isn't on the baseline, and on
   any baseline line that matches no import or no module. A move deletes the
   placement lines for the modules it moves, so both lists only shrink.
7. A module that isn't in a package and has no placement line fails too, so a
   new flat module can't skip the check.

The check covers direct imports only, because the map is meant to compose
through each context's public module.

## Out of scope

- Moving any module. Each move is its own PR under #671, and it deletes the
  baseline lines it resolves.
- Letting a record name the check that guards it, which is #688.
- A formatter and pre-commit hooks, which are #690. The import check joins those
  hooks once both land.
- The member half of `the-underscore-is-the-module-contract.md`, which governs
  private names inside one context and stays proposed.

## Risks

The `test_the_package_is_still_flat` test fails on the first move, as it was
written to, so the first move PR has to teach the current-state view about
subpackages. The worktree for #432 is still active and changes some of the same
modules, so the move plan names which open branches each move conflicts with.

## Software design decisions

No level-3 record. The script's location, how it reads the map, and the
baseline format are choices inside one script, and no second module has to
follow them.
