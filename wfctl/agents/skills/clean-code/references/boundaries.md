# Boundaries

Use this reference at the edge of what you control: a third-party library, an
operating system, a service, a generated client, or a component that does not
exist yet.

Each of those is a **change boundary** — something that will move for reasons
nobody on this side decides.

## Protecting the code behind the edge

1. Define the narrow capability the application actually needs, rather than the
   capability the dependency happens to offer.
2. Place vendor-specific conversion and failure handling at the edge.
3. Prevent external types from spreading where they would couple stable code to
   volatile detail.
4. Write focused learning or contract tests demonstrating the behaviour the
   application depends on.
5. Record the assumptions that cannot be enforced in a type or a test.

Step 4 is the one most often skipped, and it is the one that makes an upgrade
survivable: a contract test says what you were relying on, which is exactly
what a release note cannot tell you.

## When a wrapper earns its place

A wrapper is justified where it narrows a broad API, translates concepts,
centralises risk, or creates a test seam.

It is not justified where it mirrors a stable dependency's API and adds only
indirection. A wrapper with one method per underlying method has taken on the
dependency's shape, which means it will change whenever the dependency does —
the opposite of what it was built for.

## A component that does not exist yet

Define the interface from the consuming side and build against a test
substitute. Replace the substitute at the boundary rather than letting guesses
about the provider shape the domain.

The interface you write before the provider exists is a statement of what you
need. Writing it from a guess at what the provider will offer inverts that, and
the guess then propagates inward.

## Failure at the edge

Translating a vendor failure into a domain one is where the two halves meet:
what the caller can distinguish is [errors.md](errors.md), and the edge is
where that translation happens exactly once. A vendor error type reaching the
domain is the same leak as a vendor data type reaching it.

## Review prompts

- Are external concepts translated at a narrow boundary, or do they appear
  inward of it?
- Does the wrapper narrow, translate or centralise anything — or does it mirror?
- Is there a contract test for the behaviour actually depended on?
- Where the provider does not exist yet, was the interface written from the
  consumer's need or from a guess at the provider?
- Which assumptions about this dependency are recorded nowhere?
