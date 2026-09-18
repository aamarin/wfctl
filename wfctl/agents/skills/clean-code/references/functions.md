# Functions

Use this reference when a function is hard to read, hard to call correctly, or
hard to test — even where the larger design is sound.

## One coherent responsibility

A function expresses one coherent operation at one level of abstraction. That
does not mean one statement or one branch. It means a caller can name what the
function accomplishes without joining unrelated responsibilities with "and
then".

Signals that a function holds several responsibilities:

- sections that need headings;
- branches selected by a mode flag;
- business decisions mixed with parsing, persistence, rendering or transport;
- error translation interleaved with the normal path;
- changes requested by unrelated stakeholders for unrelated reasons.

Extract a helper only where the new name explains a real sub-concept, isolates
a boundary, or removes distracting detail. Do not fragment a simple operation
into indirection with no explanatory value.

## Keep one level of abstraction

Let the function read from intent to detail. High-level policy calls named
lower-level operations rather than alternating unpredictably between domain
decisions and low-level mechanics.

Put related helpers near the behaviour they support, following the
repository's conventions. Optimise for a reader following the flow, not for an
arbitrary ordering rule.

## Arguments and effects

Prefer the smallest argument set that accurately expresses the operation.

- Group values only where they form a durable concept, never merely to reduce a
  count.
- Treat a boolean or selector argument as evidence that one function may be
  several operations.
- Prefer return values or an explicit mutation API over output parameters.
- Make a dependency explicit where it affects behaviour or testability.
- Avoid hidden writes, cache population, network access, clock reads or global
  state changes behind a name that implies a pure query.

Separate commands from queries where the distinction improves reasoning. A
command may return an identifier, a version or an affected count without
becoming a query; what matters is that its mutation is explicit.

## Error handling inside the function

Keep cleanup and error translation from obscuring the normal operation. Use a
helper, a scope construct or a boundary adapter where it makes the main flow
clearer without losing diagnostic context.

Do not repeat failure-handling mechanics across every caller where one boundary
can translate them consistently. The error model itself — what a caller can
distinguish and act on — is [errors.md](errors.md).

## Review prompts

- Can a reader predict the function's effects from its name and signature?
- Does each block operate at a coherent abstraction level?
- Are the relationships between arguments explicit?
- Is there a hidden state change or ordering requirement?
- Would a rename or an extraction remove the need for a comment?
