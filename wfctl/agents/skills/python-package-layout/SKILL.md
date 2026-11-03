---
name: python-package-layout
description: 'Lay out how a Python package presents itself once its boundary is settled — the package as the public surface, underscore modules, `__all__`, lazy re-exports, and when to split a module. Use during design-levels level 4, when creating a Python package or changing what one exports. Not for drawing the boundary, and not for picking a mechanism inside a module.'
---

# Python package layout

## Overview

This skill decides how a Python package presents itself to the code that
imports it. That covers which names callers may use, where those names are
listed, how they load, and when one internal module becomes two.

It runs at level 4 of `.agents/skills/design-levels`, beside
`.agents/skills/python-pattern-selection`. The two skills split level 4 by
scope:

1. `python-pattern-selection` picks the mechanism inside a module, such as a
   function before a Strategy class.
2. This skill picks the shape of the package around those modules, such as an
   `__init__.py` that re-exports lazily.

Both take the boundary as given. Level 2 decides that a package exists and
which other packages may import it. In wfctl that decision is the accepted
record `contexts-are-packages`, which `wfctl arch context` prints.

## When to use

Use it while writing Python, when you:

1. create a package, or turn a module into one;
2. add, remove, or rename a name another package imports;
3. edit an `__init__.py` or an `__all__`;
4. are about to split a module, or merge two.

**Not for** drawing or moving the boundary. Deciding that a package exists, or
which packages may depend on which, is level 2, and
`.agents/skills/design-levels` routes it. If you aren't sure the boundary is
settled, it isn't, and this is the wrong skill.

## Authority

- Project instructions and accepted architecture records outrank this skill.
  Read the in-force set with `wfctl arch context`. Where a record fixes a
  layout, such as `contexts-are-packages` in wfctl, follow the record.
- This skill produces no verdict, no gate, and no waiver. `design-levels` owns
  the gates.
- Each rule below is a default. Departing from one is fine, and the departure
  is what gets written down, in the commit message for a one-off, or under
  `<arch-root>/implementation/` when the next reader will ask why.
  `python-pattern-selection` describes that shelf, and `wfctl arch-root` prints
  where it is.

## The layout

The package is the public surface, and everything inside it is private unless
`__init__.py` says otherwise. For example:

```
wfctl/evidence/
  __init__.py      the public surface: re-exports and __all__, nothing else
  _status.py       internal
  _paths.py        internal
```

A caller writes `from wfctl.evidence import derive`. It never writes `from
wfctl.evidence._status import derive`, so the package can move `derive` to
another file without breaking anyone.

### 1. Callers import from the package, never from a module inside it

A caller that imports a module by its path depends on the file that holds the
name. Once that happens, the package can't split or rename the file without
breaking the caller. Importing from the package keeps the file layout an
internal detail.

### 2. Every module inside the package starts with an underscore

The underscore marks a module as internal, and Python tooling reads it that
way. PEP 8 says internal interfaces, modules and packages included, should
still start with an underscore even when `__all__` is set, and documentation
generators such as Sphinx's autodoc skip those names by default.

A plain-named module looks public, whatever the package intends. Every new
plain-named file widens what callers may import, and nobody decides to widen
it. The underscore makes the default private, so a name becomes public only
when `__init__.py` lists it.

The underscore also prevents a quieter bug. When Python imports a submodule, it
sets the submodule as an attribute of its package. If the package re-exports a
function called `derive` and also has a module called `derive.py`, the first
import of that module replaces the function on the package with the module. A
module named `_derive.py` can't collide that way.

### 3. `__init__.py` holds the re-exports and `__all__`, and no logic

Code in `__init__.py` runs on every import of the package, including imports of
a single name. Logic there runs for callers that never use it, and it's the
first place a reader looks for the package's surface, not its behavior. Keep
functions and classes in underscore modules, and keep `__init__.py` to the
names it re-exports.

### 4. `__all__` lists every public name, in one place

`__all__` is the one list of what the package offers. It controls these three
things:

1. `from package import *` imports exactly the names it lists.
2. Type checkers treat a name imported into `__init__.py` as re-exported when
   `__all__` lists it. Under mypy's `--no-implicit-reexport`, which `--strict`
   turns on, an imported name that isn't listed is private, and a caller
   importing it gets an error.
3. Documentation tools and `dir()` show what it lists.

Keep each name in `__all__` exactly once, and keep it in sync with the
re-exports. A test that imports every name in `__all__` from the package is
what keeps the two in sync, for the reason rule 5's last paragraph gives.

### 5. Re-exports are lazy by default

An eager re-export imports the module that defines the name as soon as the
package is imported. A package that re-exports from ten modules eagerly loads
all ten for a caller that wanted one name.

That cost matters whenever something imports the package often and needs
little of it. In wfctl, the worktree guard imports wfctl before every shell
command an agent runs. One eager import in a context's `__init__.py` makes
every one of those commands load the whole context. That's why
`contexts-are-packages` requires every re-export to stay lazy.

Python 3.7 and later support a module-level `__getattr__` (PEP 562). Python
calls it only when a name isn't already defined in the module, so it can
import the defining module on first use:

```python
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._status import derive
    from ._paths import feature_paths

__all__ = ["derive", "feature_paths"]

_LAZY = {
    "derive": "._status",
    "feature_paths": "._paths",
}


def __getattr__(name: str) -> object:
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module, __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return list(__all__)
```

Each part of that file has a job:

1. The `TYPE_CHECKING` block never runs. Type checkers and IDEs read it, so a
   caller's `from wfctl.evidence import derive` gets the real signature instead
   of `object`. Importing `typing` costs about 4 ms, so a package on a path that
   doesn't load `typing` already can write `TYPE_CHECKING = False` instead of
   importing it. mypy treats a variable with that name as true either way.
2. `_LAZY` maps each public name to the module that defines it. A table keeps
   the mapping explicit, which is how pydantic does it. A rule that computes the
   module from the name, such as Textual's, works when every name follows the
   rule, and breaks for the first one that doesn't.
3. `globals()[name] = value` caches the result, so Python finds the name on
   later lookups and doesn't call `__getattr__` again.
4. The `AttributeError` message matches the one Python raises for a missing
   name, so `from package import missing` still raises `ImportError`.
5. `__dir__` makes `dir()` and tab completion show the public names, which
   aren't in the module's namespace until first use.

A type checker can't catch a misspelled name against this file. With a
module-level `__getattr__` that returns `object`, mypy types `from
wfctl.evidence import dervie` as `object` and reports no error. The typo fails
only at runtime. A test that imports every name in `__all__`, and checks that
`__all__`, `_LAZY`, and the `TYPE_CHECKING` block list the same names, is what
finds it before a caller does.

Python 3.15 adds explicit lazy imports (PEP 810), written `lazy from ._status
import derive`. When a project's oldest supported Python has them, they replace
the `__getattr__` table. wfctl supports Python 3.11, so it uses `__getattr__`.

### 6. An eager re-export needs a stated reason

An eager re-export is the right choice in a few cases:

1. The package is small, and every caller uses most of it.
2. Importing the module has to have an effect, such as registering a plugin
   or a codec, before any name is used.
3. The name is a constant or a type alias defined in `__init__.py` itself, so
   there's no module to defer.

Whichever case applies, write it down beside the import as a comment, since
the next reader will otherwise make the import lazy again.

### 7. Split a module when it has two reasons to change, not when it's long

Because callers import from the package, splitting an internal module changes
no caller. `__init__.py` and `_LAZY` update, and nothing else does. That makes a
split cheap, and it should happen for one of these reasons:

1. The module holds two groups of names that change for different reasons and
   that callers don't use together. `.agents/skills/clean-code` covers the
   "one reason to change" test.
2. A cheap path needs one part of the module and the rest is expensive to
   import. Splitting lets the lazy re-export load only the cheap part.
3. Two modules import each other. Moving the shared part to a third module
   removes the cycle.

Size alone isn't a reason, and neither is one class per file. A long module
whose names change together reads better as one file than as five that always
change in the same commit.

A module becomes a package of its own when it needs internal modules that the
rest of the parent package shouldn't import. Until then, it stays a module.

## Projects this draws on

The rules above are stated in full, so they apply without opening any of these
projects. Each one shows a rule in a well-known codebase:

1. **pydantic** (`pydantic/__init__.py`) re-exports more than 130 names lazily.
   It maps each name to its module in a `_dynamic_imports` table, imports the
   types under `TYPE_CHECKING` for type checkers, caches the result in
   `globals()`, and makes `__dir__` return `__all__`. Its internal code lives in
   a `_internal` subpackage, which is rule 2 applied to a whole subpackage.
2. **Textual** (`textual/widgets/__init__.py`) re-exports every widget lazily
   from underscore modules such as `_button.py` and `_data_table.py`, and says
   it does so to cut start-up time. It computes the module name from the class
   name, which rule 5 notes works only while every name follows the
   convention.
3. **SQLAlchemy** (`sqlalchemy/__init__.py`) re-exports eagerly, writing each
   one as `from .engine import Engine as Engine`. That form marks the name as
   re-exported for type checkers without relying on `__all__`. SQLAlchemy is
   the counterexample for rule 5. Importing `sqlalchemy` loads the engine, pool,
   schema, types, and SQL expression modules, which is a fair trade for
   a library whose callers use most of it and a poor one for a package a hook
   imports on every command.

## Common mistakes

| Mistake | What goes wrong |
|---|---|
| A caller imports `package._module` to reach a name the package doesn't export. | The package can no longer move that name. Export it from `__init__.py` instead. |
| A new module gets a plain name because "it might be useful elsewhere". | Callers start importing it by path, and the file can't move. Give it an underscore, and export the names that are useful. |
| `__init__.py` imports every module "for convenience". | Every import of the package pays for all of them. Make the re-exports lazy. |
| A test patches `package.name` to change what code inside the package calls. | Code inside the package imports the name from its own module, so it never reads the package's copy, and the patch has no effect on it. Patch the name in the module where the code under test looks it up. |
| `from package import *` in a module that the cheap path loads. | A star import reads `__all__` and triggers `__getattr__` for every name, which loads the whole package eagerly. |

## Verification

Before the change is done:

- [ ] No caller outside the package imports a module inside it.
- [ ] Every module inside the package starts with an underscore.
- [ ] `__init__.py` holds re-exports and `__all__`, and no logic.
- [ ] `__all__`, the lazy table, and the `TYPE_CHECKING` block list the same
      names, and a test imports every name in `__all__`.
- [ ] Every eager re-export has a comment naming which case in rule 6 it is.
- [ ] Every module split had one of rule 7's reasons, and the commit message
      names it.
