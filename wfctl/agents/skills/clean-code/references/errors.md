# Errors and absence

Use this reference when deciding how a unit fails, what a caller can do about
it, and how an absent value is expressed.

## Failure is part of the API

Design failure behaviour deliberately, alongside the success path.

- Keep the successful path readable.
- Preserve the operation, the input and the boundary context when translating a
  failure. A failure that loses where it came from costs the next debugging
  session more than the code it saved.
- Expose the distinctions a caller can act on, and only those. Do not leak a
  vendor's entire error taxonomy through a stable boundary.
- Guarantee resource cleanup with the language's structured mechanism.
- Reject an invalid mandatory input near the boundary, rather than letting it
  fail ambiguously later.

Do not select exceptions, result values, error codes or panics by slogan. Use
the target ecosystem's idiom and make the caller's obligations unmistakable.

## Absence is a value, and it is explicit

Make expected absence explicit through a type, a result, an optional value, a
documented sentinel or a documented nullable contract. Which mechanism is the
language's business; that the caller cannot miss it is not.

Avoid a special value that can be confused with a valid domain value. A
sentinel indistinguishable from real data is a defect waiting for the one input
that collides with it.

Avoid swallowing a failure to preserve a visually simple control flow. Control
flow that reads well because it discards information is not simple, it is
quiet.

## Where the translation goes

One boundary translating failures consistently beats every caller repeating
the same mechanics. That boundary is where a vendor concept becomes a domain
concept — see [boundaries.md](boundaries.md) for what else belongs there.

Inside a function, keeping cleanup and translation from obscuring the normal
path is [functions.md](functions.md)'s concern. This reference is about what
the caller can distinguish; that one is about how the code reads.

## Review prompts

- Can callers distinguish and handle the failures that matter to them?
- Does a translated failure still carry the operation, the input and the
  boundary it came from?
- Is expected absence expressed in the type system or in a documented
  contract, rather than assumed?
- Is any failure swallowed, and if so, what evidence says nobody needed it?
- Is cleanup guaranteed on every path, including the one nobody tested?
