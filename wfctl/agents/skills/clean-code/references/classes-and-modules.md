# Classes and modules

Use this reference when deciding what a unit owns, where a decision belongs, or
how a system's pieces are assembled.

## Objects, data, and responsibility

Choose a representation from the kind of change the system has to support.

- A **behaviour-oriented** abstraction protects its representation and exposes
  meaningful operations.
- A **data-oriented** structure makes its shape explicit so independent
  operations can transform or inspect it.
- A hybrid that exposes its internals while also claiming to protect behaviour
  usually inherits the disadvantages of both.

Do not force every domain into objects. Records, algebraic data types, tables,
functions, pipelines, actors and modules may express the same separation more
honestly.

## Limit what a unit knows

A unit knows its direct collaborators, not the internals of theirs. Repeated
reach-through — `a.b.c.d` — can indicate that structure is leaking across a
boundary.

Ask whether the caller should instead:

- request a meaningful operation from its collaborator;
- receive a purpose-built value;
- own the traversal, because the data is intentionally transparent; or
- use an adapter that hides an external representation.

Fluent APIs and deliberate data pipelines are not automatically violations. The
issue is dependence on distant structure, not punctuation.

## Place behaviour deliberately

Put a decision where the knowledge it needs already lives, unless doing so
would violate a stronger ownership or dependency boundary. Watch for a unit
that spends most of its effort inspecting another unit's state: that behaviour
probably belongs nearer that state.

Keep domain rules out of transport, persistence, rendering and framework glue
unless the accepted architecture assigns them there.

## One reason to change

Keep a class or module focused on one reason to change and a cohesive set of
responsibilities. Measure focus by the model it owns, not by line count.

Low cohesion shows up as:

- small subsets of functions using disjoint subsets of state;
- unrelated workflows sharing a type for convenience;
- a name gone vague because no single concept covers the contents;
- changes that repeatedly touch one portion and leave the rest irrelevant.

Splitting helps where the new boundaries have meaningful names and a clear
dependency direction. Do not create a swarm of tiny pass-through types that
hide the flow.

## Organise for change

Keep stable policy from depending directly on volatile detail. Depending on an
interface or a function boundary is useful where it:

- isolates a real source of change;
- supports multiple implementations that are needed, or foreseeable from
  evidence;
- makes important behaviour independently testable; or
- preserves an accepted dependency direction.

Do not introduce an interface because every concrete type might someday
change. Prefer the simplest boundary that serves a present design pressure.

## System assembly

Separate construction and configuration from ordinary use. A composition root,
a startup layer, a factory, a dependency-injection mechanism or an explicit
assembly function makes lifecycle and dependency choices visible.

Keep business behaviour from locating its own infrastructure through a hidden
global registry where explicit assembly is practical.

Treat logging, authorisation, transactions, caching, retries, metrics and
similar cross-cutting behaviour as named policies with a clear placement.
Scattering them through domain logic makes both concerns harder to verify.

Let the architecture grow through tested increments, but do not use emergence
as a reason to ignore a known system constraint. Delay an irreversible detail
decision where evidence is missing; make a structural decision explicitly where
ownership, deployment, data or a public contract requires it.

Adopt a framework, a standard or a pattern where it provides demonstrable value
in this system. Conformance alone is not value.

## A simple-design check

Once correctness and the required behaviour are proven, improve the design in
this order:

1. Remove real duplication, preserving distinct concepts that only look
   similar.
2. Make intent and domain rules obvious through names, structure and focused
   tests.
3. Remove elements carrying no behaviour, contract, explanation or boundary
   value.
4. Re-run the tests and reassess whether the result is simpler to change.

Do not pursue a minimal element count at the expense of clarity. A named value,
helper or type can reduce conceptual complexity even while adding a
declaration.

## Review prompts

- Is the representation intentionally behaviour-oriented or data-oriented?
- Does any caller depend on a collaborator's distant internal structure?
- Are domain decisions located with the knowledge and the authority they need?
- Does each module own a coherent change responsibility?
- Is construction separated from use?
- Does each abstraction protect a demonstrated source of change?
