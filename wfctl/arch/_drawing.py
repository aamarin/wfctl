"""A record's drawing, read into one summary whatever format it is drawn in.

A drawing can be a mermaid fence or an SVG file (`record-drawing-can-be-svg`).
Each format has one reader here, and each reader builds the same `Drawing`.
The checks in `_records` read only the summary, so a fix to how one format is
read is one edit here, and a check never needs to know which format it got
(`740-one-drawing-reader`).
"""
from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from wfctl._paths import DRAWINGS_DIR


@dataclass(frozen=True)
class Problem:
    """Why a drawing can't be used, with how to fix it.

    The same two fields as `Refusal`, so a multi-kind record turns one into the
    other field for field, and a one-kind record joins them with `: ` into one
    blocker line.
    """

    problem: str
    fix: str


# How to draw the failing step, per format. The reader sets it on the summary
# so the failing-step check can print it without asking which format it read.
FENCE_FAILURE_FIX = "add an alt, opt, break or critical block, or a lost message (-x)"
SVG_FAILURE_FIX = 'add class="failing-step" to the element that fails'


@dataclass(frozen=True)
class Drawing:
    """What sits under one heading, `## Boundary` or `### <kind>`.

    `format` is `"none"` when nothing there counts as a drawing. A drawing with
    a problem is falsy, the same as no drawing, so a caller asking whether a
    heading is drawn gets no for both. A caller that reports a missing drawing
    reads `problem` first, so the author sees what is wrong instead of being
    told to draw something that is already there.
    """

    format: str = "none"
    labels: tuple[str, ...] = ()
    shows_failure: bool = False
    failure_fix: str = ""
    past_edge: tuple[str, ...] = ()
    path: Path | None = None
    # The SVG link as the record writes it. The fingerprint on the Log line
    # names the drawing by this string, which the author can search the
    # record for, rather than by `path`, which is resolved on this machine.
    link: str = ""
    problem: Problem | None = None

    def __bool__(self) -> bool:
        return self.format != "none" and self.problem is None


NO_DRAWING = Drawing()


def read_fence(text: str) -> Drawing:
    """The summary of a fence's interior, or `NO_DRAWING` when it is blank.

    A blank interior is no drawing, as it was before summaries existed, so a
    scratch fence left empty still reads as nothing drawn.
    """
    if not text.strip():
        return NO_DRAWING
    return Drawing(
        format="fence",
        labels=tuple(fence_labels(text)),
        shows_failure=_draws_a_failure(text),
        failure_fix=FENCE_FAILURE_FIX,
    )


def fingerprint(path: Path) -> str:
    """Which version of an SVG the user signed off, as 12 hex digits.

    SHA-256 over the file's bytes with CRLF replaced by LF, because git's
    `core.autocrlf` can rewrite line endings on checkout, and hashing the raw
    bytes would warn about a drawing nobody changed. Twelve digits are enough
    to catch an edit nobody looked at, which is the threat. A forged collision
    isn't, since a hand edit to the Log line shows in the PR diff.
    """
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:12]


def _broken(problem: str, fix: str, path: Path | None = None) -> Drawing:
    return Drawing(format="svg", path=path, problem=Problem(problem, fix))


# The SVG default, used when nothing in the file sets a label's font size.
_DEFAULT_FONT_SIZE = 16.0

# The average advance width of a character, as a share of the font size, for
# the sans-serif stacks GitHub renders with. Slightly generous on purpose, so
# the estimate errs toward a warning the author can check by eye.
_CHAR_WIDTH = 0.6

_CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_CSS_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
_CLASS_SELECTOR = re.compile(r"^\.([A-Za-z0-9_-]+)$")
_FONT_SIZE_DECL = re.compile(r"font-size\s*:\s*([^;]+)")
_TEXT_ANCHOR_DECL = re.compile(r"text-anchor\s*:\s*([^;]+)")
_NUMBER = re.compile(r"^\s*(-?\d+(?:\.\d+)?)(?:px)?\s*$")


def _local(tag: str) -> str:
    """The tag without its namespace, so a drawing that leaves out `xmlns`
    reads the same as one that declares it."""
    return tag.rpartition("}")[2]


def _number(value: str | None) -> float | None:
    """A plain or `px` length as a number, or None for anything else, such as
    a percentage, which has no fixed size to measure against."""
    if value is None:
        return None
    match = _NUMBER.match(value)
    return float(match.group(1)) if match else None


def _without_media_blocks(css: str) -> str:
    """The stylesheet with every `@media` block removed.

    The drawing style puts the dark-mode colors there, and a font size set
    inside one applies in one theme only, so it isn't the size to measure.
    """
    out: list[str] = []
    i = 0
    while (start := css.find("@media", i)) != -1:
        out.append(css[i:start])
        brace = css.find("{", start)
        if brace == -1:
            return "".join(out)
        depth, j = 0, brace
        while j < len(css):
            depth += {"{": 1, "}": -1}.get(css[j], 0)
            j += 1
            if depth == 0:
                break
        i = j
    out.append(css[i:])
    return "".join(out)


def _class_values(root: ET.Element, declaration: re.Pattern[str]) -> dict[str, str]:
    """The value each class sets for one property in the `<style>` blocks.

    Only a rule whose selector is one class counts, and a selector list counts
    as one rule per class. Any other selector, such as `text.name`, isn't read,
    since matching it would take a CSS engine for one warning.
    """
    css = "\n".join(
        el.text or "" for el in root.iter() if _local(el.tag) == "style"
    )
    css = _without_media_blocks(_CSS_COMMENT.sub("", css))
    values: dict[str, str] = {}
    for selectors, body in _CSS_RULE.findall(css):
        declared = declaration.search(body)
        if declared is None:
            continue
        for selector in selectors.split(","):
            if match := _CLASS_SELECTOR.match(selector.strip()):
                values[match.group(1)] = declared.group(1).strip()
    return values


def _edge(root: ET.Element) -> tuple[float, float] | None:
    """The drawing's left and right edge, in the coordinates its `x` values use.

    `viewBox` first, since it is the coordinate system the labels are written
    in. Otherwise `0` to `width`. No edge means no warning.
    """
    view_box = (root.get("viewBox") or "").replace(",", " ").split()
    if len(view_box) == 4:
        min_x, width = _number(view_box[0]), _number(view_box[2])
        if min_x is not None and width is not None:
            return min_x, min_x + width
    width = _number(root.get("width"))
    return (0.0, width) if width is not None else None


def _past(line: tuple[str, float, float, str], edge: tuple[float, float]) -> bool:
    """Whether one line's estimated extent crosses either edge."""
    text, x, size, anchor = line
    width = len(text) * _CHAR_WIDTH * size
    left = {"middle": x - width / 2, "end": x - width}.get(anchor, x)
    return left < edge[0] or left + width > edge[1]


def _read_tree(root: ET.Element) -> tuple[tuple[str, ...], bool, tuple[str, ...]]:
    """The labels, the failing step, and the labels past the edge.

    Labels are measured at their written `x`, with any `transform` ignored:
    the drawing style teaches absolute coordinates, and composing transforms
    is a matrix library for one warning.
    """
    parents = {child: parent for parent in root.iter() for child in parent}
    class_sizes = {
        name: size
        for name, value in _class_values(root, _FONT_SIZE_DECL).items()
        if (size := _number(value)) is not None
    }
    class_anchors = _class_values(root, _TEXT_ANCHOR_DECL)
    edge = _edge(root)

    def classes(el: ET.Element) -> list[str]:
        return (el.get("class") or "").split()

    def lineage(el: ET.Element) -> list[ET.Element]:
        """`el`, then each ancestor up to the root, nearest first."""
        chain = [el]
        while (parent := parents.get(chain[-1])) is not None:
            chain.append(parent)
        return chain

    def class_size(el: ET.Element) -> float | None:
        return next((class_sizes[n] for n in classes(el) if n in class_sizes), None)

    def font_size(text: ET.Element) -> float:
        # The label's own attribute, then its class, then the nearest
        # ancestor's attribute, then an ancestor's class: close enough to how
        # a browser resolves it for the drawings the style teaches.
        own = _number(text.get("font-size"))
        if own is None:
            own = class_size(text)
        if own is not None:
            return own
        ancestors = lineage(text)[1:]
        for size in (_number(a.get("font-size")) for a in ancestors):
            if size is not None:
                return size
        for size in (class_size(a) for a in ancestors):
            if size is not None:
                return size
        return _DEFAULT_FONT_SIZE

    def anchor(text: ET.Element) -> str:
        # Each element's attribute, then its class, nearest first: the same
        # sources the font size reads, so a class that centers a label isn't
        # measured as if the label started at its `x`.
        for el in lineage(text):
            if value := el.get("text-anchor"):
                return value.strip()
            if found := next((class_anchors[n] for n in classes(el) if n in class_anchors), None):
                return found
        return "start"

    def lines(text: ET.Element) -> list[tuple[str, float, float, str]]:
        """Each rendered line of a label: its text, `x`, font size, and anchor.

        A `<tspan>` with its own `x` starts a new line, which is how a label
        is wrapped. Measuring the joined text as one line flagged a wrapped
        label that fits, and the author had no way to clear it. Text outside
        such a tspan stays on the line the `<text>` element starts.
        """
        starts = [c for c in text if _number(c.get("x")) is not None]
        first = [text.text or ""]
        for child in text:
            if child not in starts:
                first += ["".join(child.itertext()), child.tail or ""]
        candidates = [(text, " ".join(p.strip() for p in first if p.strip()))]
        candidates += [(c, "".join(c.itertext()).strip()) for c in starts]
        return [
            (line, x, font_size(el), anchor(el))
            for el, line in candidates
            if line and (x := _number(el.get("x"))) is not None
        ]

    labels: list[str] = []
    past_edge: list[str] = []
    for el in root.iter():
        if _local(el.tag) != "text":
            continue
        label = " ".join(part.strip() for part in el.itertext() if part.strip())
        if not label:
            continue
        labels.append(label)
        if edge is not None and any(_past(line, edge) for line in lines(el)):
            past_edge.append(label)

    shows_failure = any("failing-step" in classes(el) for el in root.iter())
    return tuple(labels), shows_failure, tuple(past_edge)


def read_svg(link: str, record_dir: Path) -> Drawing:
    """The summary of the SVG file `link` names, resolved from `record_dir`.

    `link` is the target as the record writes it. Every problem quotes it,
    because the arch root can sit outside the repository, and the text the
    author typed is the one string they can search the record for.

    The containment check runs after resolving, so a symlink in `drawings/`
    pointing elsewhere counts as outside. Outside is refused rather than read:
    an SVG elsewhere under the arch root would count as a changed record.

    The file is decoded as UTF-8 before the DOCTYPE check, and the parser
    reads that same text. A check on the raw bytes would miss a UTF-16 file,
    and an encoding named in the XML declaration can't make the parser see
    characters the check didn't. Refusing a DOCTYPE removes the entity
    expansion question on every machine, whatever expat it links, since a
    hand-drawn SVG needs none.
    """
    if link.startswith("/"):
        return _broken(
            f"drawing links {link}, which isn't relative to the record",
            "write it relative to the record, as drawings/<file>.svg.",
        )
    drawings = record_dir / DRAWINGS_DIR
    # Resolving both sides would follow a symlinked folder to its target, so
    # anything it points at would pass as inside.
    if drawings.is_symlink():
        return _broken(
            f"drawing links {link}, but drawings/ is a symlink",
            "make drawings/ a folder beside the records, not a link to one.",
        )
    try:
        path = (record_dir / link).resolve()
        inside = path.is_relative_to(drawings.resolve())
    # A NUL byte raises `ValueError`, and on 3.11 a symlink loop raises
    # `RuntimeError` (3.13 resolves it and the file reads as missing).
    # `OSError` covers the rest. Any of them escaping would crash every
    # reader of the whole record set over one record's link.
    except (OSError, RuntimeError, ValueError) as exc:
        reason = exc.strerror if isinstance(exc, OSError) and exc.strerror else exc
        return _broken(f"drawing links {link}, which can't be resolved: {reason}", "correct the link.")
    if not inside:
        return _broken(
            f"drawing links {link}, which is outside drawings/",
            "move it into the drawings/ folder beside the records, and update the link.",
            path,
        )
    unreadable = "fix the file so it opens as XML."
    try:
        # `utf-8-sig` so a byte-order mark, which some editors write, doesn't
        # reach the parser as text before the root element.
        text = path.read_bytes().decode("utf-8-sig")
    # Read first and ask why afterwards: on 3.11 a separate `exists()` raises
    # `PermissionError` under a locked folder instead of returning.
    except FileNotFoundError:
        return _broken(
            f"drawing links {link}, which doesn't exist",
            "create it, or correct the link.",
            path,
        )
    except OSError as exc:
        return _broken(f"drawing {link} can't be read: {exc.strerror or exc}", unreadable, path)
    except ValueError as exc:
        return _broken(f"drawing {link} can't be read: {exc}", unreadable, path)
    if "<!doctype" in text.lower():
        return _broken(
            f"drawing {link} declares a DOCTYPE", "remove it, since a drawing needs none.", path
        )
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return _broken(f"drawing {link} can't be read: {exc}", unreadable, path)
    if _local(root.tag) != "svg":
        return _broken(
            f"drawing {link} isn't an SVG: its root element is not <svg>", unreadable, path
        )
    labels, shows_failure, past_edge = _read_tree(root)
    return Drawing(
        format="svg",
        labels=labels,
        shows_failure=shows_failure,
        failure_fix=SVG_FAILURE_FIX,
        past_edge=past_edge,
        path=path,
        link=link,
    )


# A node label: quoted, bracketed, braced, or piped — the shapes mermaid
# accepts for display text. `[*]` is excluded at the call site rather than
# here, because the pattern that matches it is the same pattern that matches
# every other bracketed label; the exclusion is content, not syntax.
#
# The bracketed pattern prefers a quoted interior, because `[^\]]*` alone stops
# at the first `]` — and a quoted label is allowed to contain one, so
# `["Use [cache]"]` would otherwise be read as the fragment `"Use [cache`.
_QUOTED_LABEL = re.compile(r'"([^"]*)"')
_BRACKETED_LABEL = re.compile(r"\[(\"[^\"]*\"|[^\]]*)\]")
_BRACED_LABEL = re.compile(r"\{([^}]*)\}")

# An edge label — `-->|text|`, `--x|text|`, `-.->|text|`. The arrow is required,
# and required to be adjacent: a bare `|text|` is how ASCII box art draws a cell
# wall, and matching that would hand the check two labels for every row of a
# table it is supposed to read nothing from (R-004's stated limit).
_EDGE_LABEL = re.compile(r"([-.=]{2,}[>xo]?)\|([^|]*)\|")

# A rounded or circular node — `A(text)`, `A((text))`. The node id must be
# adjacent for the same reason the arrow is above: a bare `(text)` is an aside
# in ordinary prose, and a transition label is allowed to contain one, so
# matching it loose would split `A --> B: refuses (silently)` into two labels.
# Circles are read first; `[^)]*` cannot cross the inner `)` of a double paren.
_CIRCLE_LABEL = re.compile(r"\w+\(\(([^)]*)\)\)")
_ROUNDED_LABEL = re.compile(r"\w+\(([^)]*)\)")

# A transition or message arrow whose label follows a `:` — a state diagram's
# `-->`, and every arrow a `sequenceDiagram` draws a message with: `->`, `->>`,
# `-x` and `-)`, solid or dotted. Reading only `-->` left a sequence's solid
# messages unread, so the drawing could name a step the prose never mentions
# and the check said nothing.
_MESSAGE_ARROW = re.compile(r"-{1,2}(?:>>|>|x|\))")

# A sequence participant given a display name — `participant R as renderer`.
# The alias is what the rendered drawing shows; the id before `as` is not.
_PARTICIPANT_ALIAS = re.compile(r"^(?:participant|actor)\s+\S+\s+as\s+(.+)$")

# A `sequenceDiagram` block that draws a path other than the happy one, or a
# message that is lost (`-x`, `--x`). A `sequence` record exists to show what is
# left when a step fails partway, so a drawing with none of these has drawn the
# half of the flow the kind was not added for.
_FAILURE_BLOCK = re.compile(r"^(?:alt|opt|break|critical)\b")
_LOST_MESSAGE = re.compile(r"\w\s*-{1,2}x")


def _draws_a_failure(drawing: str) -> bool:
    """True when a sequence drawing shows a path other than the happy one."""
    for line in drawing.splitlines():
        stripped = line.strip()
        if stripped.startswith("%%"):
            continue
        if _FAILURE_BLOCK.match(stripped) or _LOST_MESSAGE.search(stripped):
            return True
    return False


def fence_labels(drawing: str) -> list[str]:
    """Every node label in `drawing`: piped, bracketed, braced, quoted, a bare
    `subgraph` title, a participant's `as` alias, or the text after `:` on a
    transition or message line.

    `<br/>` and `<br>` become whitespace before any of the shapes are read, so
    a wrapped label reads as the one phrase its author wrote rather than as
    line-broken fragments. `[*]` — mermaid's start/end marker — yields no
    label; it is a syntax element, not a name for anything.

    Each shape removes what it reads before the next one runs, so one label is
    never reported twice. `A["a label"]` is mermaid's own common shape — a
    quoted string inside brackets — and reading the quote separately as well
    would report one label as two.

    Order is what keeps a mixed transition label whole. `A --> B: known "x"` is
    one label, and a bare-quote scan running first would take `"x"` out of it
    and leave `known` behind as a second — so the colon scan runs before it and
    claims the whole tail.

    Three shapes are syntax rather than names and yield nothing: a `%%` comment
    line, which mermaid ignores whatever it contains; `:::`, which attaches a
    CSS class; and a `subgraph` title that is bracketed or quoted, already read
    as a label by the shape it is written in.
    """
    text = drawing.replace("<br/>", " ").replace("<br>", " ")
    found: list[str] = []

    def _unquote(content: str) -> str:
        if content[:1] == '"' and content[-1:] == '"' and len(content) >= 2:
            return content[1:-1]
        return content

    def _take(m: re.Match[str]) -> str:
        content = _unquote(m.group(1).strip())
        if content and content != "*":
            found.append(content)
        return ""

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("%%"):
            continue
        if stripped.startswith("subgraph "):
            title = stripped[len("subgraph ") :].strip()
            if title and "[" not in title and '"' not in title:
                found.append(title)
                continue
        alias = _PARTICIPANT_ALIAS.match(stripped)
        if alias:
            found.append(_unquote(alias.group(1).strip()))
            continue

        def _take_edge(m: re.Match[str]) -> str:
            content = _unquote(m.group(2).strip())
            if content and content != "*":
                found.append(content)
            return m.group(1)

        remainder = _EDGE_LABEL.sub(_take_edge, line)
        remainder = _BRACED_LABEL.sub(_take, _BRACKETED_LABEL.sub(_take, remainder))
        remainder = _ROUNDED_LABEL.sub(_take, _CIRCLE_LABEL.sub(_take, remainder))
        arrow_match = _MESSAGE_ARROW.search(remainder)
        if arrow_match:
            arrow = arrow_match.start()
            colon = remainder.find(":", arrow)
            if colon != -1 and remainder[colon : colon + 3] != ":::":
                after = _unquote(remainder[colon + 1 :].strip())
                if after:
                    found.append(after)
                remainder = remainder[:colon]
        _QUOTED_LABEL.sub(_take, remainder)
    return [label.strip() for label in found if label.strip()]
