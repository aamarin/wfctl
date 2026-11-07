# Data model: Reviewers check that each layer accepts the same input

This feature adds no stored state. The only structured thing it adds is the trail in a reviewer's report, which `contracts/review-report.md` describes.

- **Input**: a value from outside the program that the change adds or changes, such as a form field, a request body, a CLI flag, a config or data file, or an environment variable. It has a name and a list of layers.
- **Layer**: one place that checks, converts, or stores an input. It has a file and line, and a limit (type, nullability, unit, bounds, precision, storage range) or "unknown" with the reason.
- **Rule**: a check or fix the change adds, read from the diff and from the commit messages when the review covers commits. It has a file and line, and a list of siblings.
- **Sibling**: another place that writes the same value or sink as a rule. It has a file and line, and is either covered or not.
