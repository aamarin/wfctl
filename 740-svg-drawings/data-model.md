# Data model: SVG drawings

## Drawing

The summary wfctl builds from what sits under one heading, `## Boundary` or `### <kind>`. It's a frozen dataclass in `wfctl/arch/_drawing.py`, and every check reads it instead of the fence or the file.

| Field | Type | Meaning |
| --- | --- | --- |
| `format` | `"fence"`, `"svg"`, or `"none"` | What the heading holds. `"none"` means nothing counts as a drawing. |
| `labels` | `tuple[str, ...]` | The labels, in document order. For a fence, what `_labels` returns today. For an SVG, the text of each `<text>`, with its `<tspan>` text joined by spaces. |
| `shows_failure` | `bool` | For a fence, what `_draws_a_failure` returns today. For an SVG, whether any element's class list includes `failing-step`. |
| `failure_fix` | `str` | How to draw the failing step in this drawing's format. The reader sets it, so the failing-step check can print it without reading `format` (PR-004). The table below gives each value. |
| `past_edge` | `tuple[str, ...]` | The text of each label whose estimated extent leaves the drawing's edge (research R-003, R-004). Always empty for a fence. |
| `path` | `Path` or `None` | The resolved SVG path, for an image link. `None` for a fence. |
| `problem` | `Problem` or `None` | Why the drawing can't be used. `None` when it's usable. |

`bool(drawing)` is true when `format` isn't `"none"` and `problem` is `None`. The existing `if not _drawing(record)` checks keep their meaning for a fence, and a drawing with a problem doesn't count as drawn. Each check that reports a missing drawing looks at `problem` first. If there is one, it prints the problem instead of the missing-drawing line. `contracts/cli.md` lists the full output for each case.

| Format | `failure_fix` |
| --- | --- |
| `fence` | `add an alt, opt, break or critical block, or a lost message (-x)`, today's text |
| `svg` | `add class="failing-step" to the element that fails` |
| `none` | `""`, never printed, since the check runs only on a usable drawing |

The message prefixes stay in `_records.py`, and only the fix half moves onto the summary. The check builds `f"a sequence drawing with no step that fails: {drawing.failure_fix}"`, so it has no format code in it, as `740-one-drawing-reader` requires.

## Problem

A frozen dataclass beside `Drawing`, with two string fields, `problem` and `fix`. It has the same shape as `Refusal`. A multi-kind record turns it into a `Refusal` field for field, and a one-kind record joins the two with `: ` into one blocker line, the way every blocker reads today.

`<link>` below is the link target as the record writes it, such as `drawings/x-data-flow.svg`. `_records.py` has no repo root, and the arch root can sit outside the repository. The text the author typed is the one string that's always available, and the author can search the record for it (PR-008).

| Case | `problem` | `fix` |
| --- | --- | --- |
| The file doesn't exist | `drawing links <link>, which doesn't exist` | `create it, or correct the link.` |
| It resolves outside `drawings/` | `drawing links <link>, which is outside drawings/` | `move it into the drawings/ folder beside the records, and update the link.` |
| The link starts with `/` | `drawing links <link>, which isn't relative to the record` | `write it relative to the record, as drawings/<file>.svg.` |
| It carries a DOCTYPE | `drawing <link> declares a DOCTYPE` | `remove it, since a drawing needs none.` |
| It can't be read or parsed | `drawing <link> can't be read: <reason>` | `fix the file so it opens as XML.` |
| A heading has both | `'<heading>' has both an SVG and a fenced block` | `keep one.` |
| A heading has two SVG links | `'<heading>' links two SVG drawings` | `keep one, or give each its own '### <kind>' heading.` |

`<heading>` is `## Boundary` or `### <kind>` as written. `<reason>` is the parser's message for a `ParseError`, and the exception's message for an `OSError` or a decode error (research R-001).

### Validation rules

- A fence whose interior is empty or only whitespace is `format="none"`, as `_drawing` treats it today.
- wfctl ignores an image whose target is a URL, a `data:` URI, or a file that doesn't end in `.svg`. A heading holding only that is `format="none"`.
- A heading holding both a non-empty fence and an SVG link is `format="svg"` with a problem (clarify Q1).
- A heading holding two SVG links is `format="svg"` with a problem. Two fences keep today's rule, where the first one wins, because changing it would change results that FR-011 keeps the same (research R-007).
- A leading-slash link, or one that resolves outside `drawings/`, has a problem, and wfctl doesn't read its file.
- A missing file, a DOCTYPE, or a read or parse failure sets `problem` and leaves `labels` and `past_edge` empty.

## Building it

`_drawing.py` has three functions, and `_records.py` calls them:

1. `read_fence(text: str) -> Drawing` builds the summary from a fence's interior.
2. `fence_labels(text: str) -> list[str]` is today's `_labels`, moved with its regexes and docstrings unchanged. `read_fence` calls it. `tests/test_arch_labels.py` imports it instead of `_records._labels`, and every assertion stays the same (PR-010).
3. `read_svg(link: str, record_dir: Path) -> Drawing` checks the link, resolves it, checks the folder, parses the file, and reads the labels, the failing step, and the edge.

`read_svg` takes the record's folder, `record.path.parent`. `load_records` reads one level under the arch root, so that folder is the arch root, and `drawings_dir` is `record_dir / DRAWINGS_DIR`. wfctl resolves the link with `(record_dir / link).resolve()`, and the file is inside when the result `is_relative_to(drawings_dir.resolve())`. Resolving first follows symlinks, so a symlink in `drawings/` that points elsewhere counts as outside (PR-008).

`_records.py` keeps the heading logic. `_drawing(record)` and `_drawings(record)` keep their names and their rules about which fence or link belongs to which heading. They return `Drawing` instead of `str`, and choose `read_fence` or `read_svg` from what the heading holds.

## State

The summary has no state and no cache. Each call to `_drawing` or `_drawings` rebuilds it from the record and the file on disk, so one `validate` call parses a record's SVG a few times. An SVG is a few KB, and `session-state-is-re-derived` prefers reading the file again to a cache that could go stale (PR-012).

## Drawing fingerprint

A fingerprint records which version of an SVG the user looked at when they accepted the record. It's text on a Log line, not a type.

| Part | Value |
| --- | --- |
| Where | The end of an `accepted` or `redrawn` Log line, after the citation |
| Form | ` · drawing <link> sha256:<12 hex>`, once per SVG, in heading order |
| `<link>` | The link target as the record writes it, the same string the problem lines use |
| Hash | The first 12 hex digits of SHA-256 over the file's bytes, with CRLF replaced by LF |

For example, a record with one SVG accepted on 2026-11-20 gets:

```
- 2026-11-20  accepted    — the #740 plan walkthrough · drawing drawings/x-data-flow.svg sha256:3f9a0c1b2d4e
```

A later `redrawn` line has the same form with `redrawn` as the status word. `_drawing.py` gets one more function, `fingerprint(path: Path) -> str`, and `Drawing` keeps its fields. `_records.py` reads the Log lines, since the Log is the record's structure, not the drawing's format.

### Reading it back

For each SVG link a record has today, doctor finds the last `accepted` or `redrawn` line in `## Log` that names the same link, and compares its fingerprint with the file's current one.

| What doctor finds | Result |
| --- | --- |
| The fingerprints match | Nothing |
| They differ | A warning naming the SVG |
| No Log line names the link | Nothing. This covers a record accepted before this change, and an SVG link added to an accepted record, which the frozen-body convention and the design gate already cover, since the link is in the record's body |
| The drawing has a problem | The problem line, from FR-021, and no fingerprint comparison |

## Paths

| Name | Value | Where |
| --- | --- | --- |
| `DRAWINGS_DIR` | `"drawings"` | `wfctl/_paths.py`, added to `non_record_subtrees` with a comment pointing to #761 |
