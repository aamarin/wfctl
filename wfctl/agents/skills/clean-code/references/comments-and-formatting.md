# Comments and formatting

Use this reference when deciding whether a comment earns its place, or how a
file should be laid out.

## What a comment has to earn

A comment preserves information the code cannot express well by itself.

A useful comment may explain:

- the reason for a surprising decision;
- a legal, protocol, compatibility or safety constraint;
- a warning whose consequence is not locally visible;
- an intentionally incomplete area, with an actionable owner or tracking
  reference;
- a public contract a caller cannot infer from types and names;
- why an apparently simpler implementation would be incorrect.

Remove or revise a comment that:

- paraphrases the next statement;
- describes behaviour that has changed;
- compensates for a misleading name or a tangled structure that can be fixed
  directly;
- retains deleted code, or a change history version control already holds;
- states a distant fact likely to drift independently;
- adds a ceremonial heading, separator or boilerplate with no meaning.

Evaluate the code and its comment as one unit. A correct but non-obvious
invariant may need both a clearer implementation and a concise explanation of
why it exists.

**The test is who the comment is for.** A comment that informs the next reader
of the file belongs in the file. A comment that narrates the change to a
reviewer belongs in the commit message, and putting it in the file leaves a
sentence that stops making sense as soon as the diff is no longer beside it.

## Formatting and locality

Formatting communicates conceptual grouping and dependency. Use the
repository's formatter and conventions first.

Within those conventions:

- keep tightly related statements together;
- separate distinct concepts with visible structure;
- place a declaration close enough to its use that the reader need not search;
- order concepts so the main behaviour can be understood before the
  implementation detail;
- use indentation to make control structure unmistakable;
- avoid horizontal alignment, which makes whitespace edits fragile;
- keep files navigable rather than optimising for an arbitrary maximum length.

Team consistency outweighs an individual's preferred brace, quote or wrapping
style. Where formatting can be automated, automate it rather than debating it
in review.

## Review prompts

- Does every remaining comment explain an intent or a constraint, and does it
  still match reality?
- Is any comment compensating for something a rename would fix?
- Are related concepts local, and unrelated concepts visibly separated?
- Would the repository's formatter produce this layout?
