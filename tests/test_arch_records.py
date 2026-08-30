"""Tests for `wfctl._arch` — parsing, link validation, supersession, projection."""
from __future__ import annotations

from pathlib import Path

import pytest

from wfctl import _arch


RECORD = """\
---
status: {status}
---

# A decision

## Log

- 2026-03-14  accepted    — because
"""


def _write(root: Path, slug: str, body: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{slug}.md"
    path.write_text(body)
    return path


# --- parsing (T004) ---------------------------------------------------------


@pytest.mark.parametrize("status", ["proposed", "accepted", "superseded", "rejected", "retired"])
def test_each_status_in_the_closed_set_parses(tmp_path: Path, status: str) -> None:
    record = _arch.parse_record(_write(tmp_path, "a-decision", RECORD.format(status=status)))

    assert record.status == status
    assert record.slug == "a-decision"


def test_an_absent_status_is_excluded_not_accepted(tmp_path: Path) -> None:
    """The load-bearing default. A frontmatter scan usually defaults to the
    common case; this one defaults to the conservative case instead, because
    presenting an unreviewed decision as binding is the exact failure the status
    field exists to prevent."""
    path = _write(tmp_path, "no-status", "---\nsupersedes: other\n---\n\n# X\n")

    record = _arch.parse_record(path)

    assert record.status == ""
    assert not record.in_force


def test_an_unrecognised_status_is_excluded(tmp_path: Path) -> None:
    """Anything outside the closed set is excluded (VR-001) — a typo'd `acepted`
    must not read as binding."""
    record = _arch.parse_record(_write(tmp_path, "typo", RECORD.format(status="acepted")))

    assert record.status == ""
    assert not record.in_force


def test_a_missing_frontmatter_delimiter_leaves_the_status_absent(tmp_path: Path) -> None:
    """A body that opens straight into prose has no frontmatter to scan — the
    keys below are content, not settings."""
    path = _write(tmp_path, "prose", "# A decision\n\nstatus: accepted\n")

    assert _arch.parse_record(path).status == ""


def test_frontmatter_ends_at_the_closing_delimiter(tmp_path: Path) -> None:
    """A `status:` line in the body is prose. Scanning the whole file would let
    a quoted example set the record's status."""
    path = _write(
        tmp_path, "quotes-a-status",
        "---\nstatus: proposed\n---\n\n# X\n\nCompare with `status: accepted`.\n",
    )

    assert _arch.parse_record(path).status == "proposed"


def test_supersedes_is_extracted_and_quotes_are_stripped(tmp_path: Path) -> None:
    path = _write(
        tmp_path, "successor",
        '---\nstatus: accepted\nsupersedes: "predecessor"\n---\n\n# X\n',
    )

    record = _arch.parse_record(path)

    assert record.supersedes == "predecessor"
    assert record.in_force


def test_supersedes_is_empty_when_absent(tmp_path: Path) -> None:
    record = _arch.parse_record(_write(tmp_path, "first", RECORD.format(status="accepted")))

    assert record.supersedes == ""


def test_the_slug_is_the_filename_without_extension(tmp_path: Path) -> None:
    """Identity, and what inbound `supersedes` values name — which is why a
    record is never renamed."""
    record = _arch.parse_record(_write(tmp_path, "wfctl-runs-the-check", RECORD.format(status="accepted")))

    assert record.slug == "wfctl-runs-the-check"


def test_an_unreadable_record_parses_as_excluded_rather_than_raising(tmp_path: Path) -> None:
    """One undecodable file must not take down a whole-root read — the record set
    is a directory anyone can drop a file into."""
    path = tmp_path / "binary.md"
    tmp_path.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff\xfe\x00not utf-8")

    record = _arch.parse_record(path)

    assert record.status == ""
    assert not record.in_force


def test_an_unterminated_frontmatter_reads_and_edits_consistently(tmp_path: Path) -> None:
    """A missing final `---` must not mean two different things to two readers.
    The parser scanned to end of file and reported a status; `supersede` used a
    separate scan that treated the block as absent and refused. One record, read
    as accepted and un-editable — so sharing the boundary settled it: if the
    status is readable, it is changeable."""
    path = _write(tmp_path, "unterminated", "---\nstatus: accepted\n\n# X\n\n## Log\n\n- 2026-01-01  accepted  — a\n")

    assert _arch.parse_record(path).status == "accepted"

    _arch.supersede(_arch.parse_record(path), "2026-08-11", "reason")

    assert _arch.parse_record(path).status == "superseded"


# --- link validation (T006) -------------------------------------------------


def _levels(findings: list[_arch.Finding]) -> set[tuple[str, str]]:
    return {(f.level, f.slug) for f in findings}


def test_a_clean_set_produces_no_findings(tmp_path: Path) -> None:
    _write(tmp_path, "old", RECORD.format(status="superseded"))
    _write(tmp_path, "new", "---\nstatus: accepted\nsupersedes: old\n---\n\n# X\n")

    assert _arch.validate(_arch.load_records(tmp_path)) == []


def test_a_dangling_supersedes_is_an_error(tmp_path: Path) -> None:
    """VR-003. The reason a predecessor fell is what the value points at, so a
    value naming nothing leaves the record unreadable — not merely untidy."""
    _write(tmp_path, "new", "---\nstatus: accepted\nsupersedes: never-existed\n---\n\n# X\n")

    findings = _arch.validate(_arch.load_records(tmp_path))

    assert _levels(findings) == {("error", "new")}
    assert "never-existed" in findings[0].message


def test_a_superseded_record_with_no_successor_is_a_warning(tmp_path: Path) -> None:
    """VR-002. A warning, not an error: the usual cause is a successor sitting on
    an unmerged branch, which is true of every record while it is under review."""
    _write(tmp_path, "orphan", RECORD.format(status="superseded"))

    findings = _arch.validate(_arch.load_records(tmp_path))

    assert _levels(findings) == {("warning", "orphan")}


def test_two_records_superseding_the_same_target_is_an_error(tmp_path: Path) -> None:
    """VR-004, the split-supersession edge case: one decision replaced twice,
    independently. No rule picks a winner, so it must reach a human rather than
    resolve itself by directory order."""
    _write(tmp_path, "old", RECORD.format(status="superseded"))
    _write(tmp_path, "branch-a", "---\nstatus: accepted\nsupersedes: old\n---\n\n# A\n")
    _write(tmp_path, "branch-b", "---\nstatus: accepted\nsupersedes: old\n---\n\n# B\n")

    findings = _arch.validate(_arch.load_records(tmp_path))

    assert _levels(findings) == {("error", "old")}
    assert "branch-a" in findings[0].message and "branch-b" in findings[0].message


# --- supersession (T008) ----------------------------------------------------


ACCEPTED = """\
---
status: accepted
supersedes: ancestor
---

# wfctl runs the verification, not the agent

## Context

Completion was accepted from a file the agent wrote.

## Decision

wfctl runs the verification command and records the result.

## Log

- 2026-03-14  accepted    — self-report is cheap, start there
"""


def test_supersession_changes_only_the_status_and_appends_one_log_line(tmp_path: Path) -> None:
    """VR-005. The body is the decision as it was agreed — git holds the edit
    history, the file holds only what git cannot answer. Rewriting it would
    destroy the predecessor the successor points at."""
    path = _write(tmp_path, "wfctl-runs-the-check", ACCEPTED)
    before = path.read_text()

    _arch.supersede(_arch.parse_record(path), "2026-08-11", "unfalsifiable")

    # Compared as raw text, not `splitlines()`: that drops line endings and
    # trailing-newline state, so the assertion passed on files this function was
    # corrupting in exactly those two ways.
    expected = (
        before.replace("status: accepted", "status: superseded", 1)
        + "- 2026-08-11  superseded  — unfalsifiable\n"
    )
    assert path.read_text() == expected


def test_supersession_appends_inside_the_log_section(tmp_path: Path) -> None:
    """`Log` is last by convention, not by rule. Appending at end of file would
    file the transition under whatever heading happens to follow."""
    path = _write(tmp_path, "r", ACCEPTED + "\n## Consequences\n\nThe result binds to a sha.\n")

    _arch.supersede(_arch.parse_record(path), "2026-08-11", "unfalsifiable")

    lines = path.read_text().splitlines()
    log, consequences = lines.index("## Log"), lines.index("## Consequences")
    entry = lines.index("- 2026-08-11  superseded  — unfalsifiable")
    assert log < entry < consequences
    assert lines[-1] == "The result binds to a sha."


def test_supersession_refuses_a_record_with_no_log_section(tmp_path: Path) -> None:
    """A status change with nowhere to record it is the silent edit this
    function exists to prevent — better to refuse than to invent a section."""
    path = _write(tmp_path, "no-log", "---\nstatus: accepted\n---\n\n# X\n")

    with pytest.raises(ValueError, match="Log"):
        _arch.supersede(_arch.parse_record(path), "2026-08-11", "reason")

    assert "status: accepted" in path.read_text(), "a refusal writes nothing"


def test_supersession_refuses_frontmatter_with_no_status_line(tmp_path: Path) -> None:
    """Caught in review: the scan used to stop at the closing delimiter and fall
    through without raising, so the Log line was appended to a record whose
    status never changed — the record then claimed a transition it never made."""
    path = _write(tmp_path, "no-status", "---\nsupersedes: x\n---\n\n# X\n\n## Log\n\n- 2026-01-01  proposed  — a\n")
    before = path.read_text()

    with pytest.raises(ValueError, match="status"):
        _arch.supersede(_arch.parse_record(path), "2026-08-11", "reason")

    assert path.read_text() == before, "a refusal writes nothing"


def test_a_status_line_in_the_body_is_not_the_one_changed(tmp_path: Path) -> None:
    """The scan stops at the closing delimiter. Without that, a record quoting
    frontmatter in its prose gets its example edited and its status left live."""
    path = _write(
        tmp_path, "quotes",
        "---\nstatus: accepted\n---\n\n# X\n\n## Log\n\nstatus: accepted\n",
    )

    _arch.supersede(_arch.parse_record(path), "2026-08-11", "reason")

    lines = path.read_text().splitlines()
    assert lines[1] == "status: superseded"
    assert lines[-2] == "status: accepted", "the body's copy is prose, not a setting"


# --- projection (T010, T011) ------------------------------------------------


def test_only_accepted_is_in_force(tmp_path: Path) -> None:
    """One record per status. `superseded` and `retired` both once governed the
    work; reading either as live is the confusion `status` exists to prevent."""
    for status in ("proposed", "accepted", "superseded", "rejected", "retired"):
        _write(tmp_path, status, RECORD.format(status=status))
    _write(tmp_path, "predecessor", RECORD.format(status="accepted"))
    _write(tmp_path, "successor", "---\nstatus: accepted\nsupersedes: superseded\n---\n\n# X\n")

    projected = {r.slug for r in _arch.in_force(_arch.load_records(tmp_path))}

    assert projected == {"accepted", "predecessor", "successor"}


def test_an_empty_root_projects_an_empty_set(tmp_path: Path) -> None:
    """Not an error: every repo has no records until it writes its first one.
    A root that does not exist yet is the same state."""
    assert _arch.in_force(_arch.load_records(tmp_path)) == []
    assert _arch.load_records(tmp_path / "never-created") == []


def test_an_unparseable_record_is_excluded_and_counted_not_dropped(tmp_path: Path) -> None:
    """Silently vanishing from the contract reads as a decision nobody made —
    the count is what lets the reader tell 'excluded' from 'never written'."""
    _write(tmp_path, "good", RECORD.format(status="accepted"))
    _write(tmp_path, "draft-notes", "# just some notes\n")

    records = _arch.load_records(tmp_path)

    assert [r.slug for r in _arch.in_force(records)] == ["good"]
    assert _arch.excluded_by_status(records) == {"": 1}
    assert [r.slug for r in records if not r.status] == ["draft-notes"], "named, not dropped"


def test_the_excluded_are_counted_by_status(tmp_path: Path) -> None:
    _write(tmp_path, "a", RECORD.format(status="accepted"))
    _write(tmp_path, "b", RECORD.format(status="superseded"))
    _write(tmp_path, "c", RECORD.format(status="superseded"))
    _write(tmp_path, "d", RECORD.format(status="retired"))

    assert _arch.excluded_by_status(_arch.load_records(tmp_path)) == {
        "superseded": 2, "retired": 1,
    }


def test_projection_ordering_is_stable_across_runs(tmp_path: Path) -> None:
    """Ordered by slug, not by directory order, which no filesystem guarantees.
    Unstable output turns every `arch context` into a diff against itself."""
    for slug in ("zulu", "alpha", "mike", "bravo"):
        _write(tmp_path, slug, RECORD.format(status="accepted"))

    slugs = [r.slug for r in _arch.in_force(_arch.load_records(tmp_path))]

    assert slugs == ["alpha", "bravo", "mike", "zulu"]
    assert slugs == [r.slug for r in _arch.in_force(_arch.load_records(tmp_path))]


# --- write-path defects found in review -------------------------------------


def test_a_file_with_no_trailing_newline_keeps_its_entries_apart(tmp_path: Path) -> None:
    """Caught in review: `splitlines(keepends=True)` leaves the last element
    unterminated, so joining welded the new entry onto the previous one — two
    transitions on one line and the predecessor's entry destroyed, in a file
    nothing can reconstruct. Editors and heredocs produce such files routinely."""
    path = _write(tmp_path, "no-eof-newline", ACCEPTED.rstrip("\n"))

    _arch.supersede(_arch.parse_record(path), "2026-08-11", "reason")

    lines = path.read_text().splitlines()
    assert lines[-2] == "- 2026-03-14  accepted    — self-report is cheap, start there"
    assert lines[-1] == "- 2026-08-11  superseded  — reason"


def test_a_repeated_status_key_is_changed_where_the_parser_reads_it(tmp_path: Path) -> None:
    """Caught in review: the parser takes the last of a repeated key and the
    edit changed the first, so the log recorded a transition the record never
    made — silently, and by a route the no-status refusal does not cover."""
    path = _write(
        tmp_path, "twice",
        "---\nstatus: proposed\nstatus: accepted\n---\n\n# X\n\n## Log\n\n- x\n",
    )
    assert _arch.parse_record(path).status == "accepted"

    _arch.supersede(_arch.parse_record(path), "2026-08-11", "reason")

    assert _arch.parse_record(path).status == "superseded"


def test_a_fenced_log_heading_does_not_capture_the_entry(tmp_path: Path) -> None:
    """Caught in review: a record documenting the record format contains a
    fenced `## Log`, and matching it wrote the transition into the body — losing
    the transition and editing an accepted record, which VR-005 forbids."""
    path = _write(
        tmp_path, "documents-the-format",
        "---\nstatus: accepted\n---\n\n# X\n\n## Decision\n\n```markdown\n"
        "## Log\n\n- 2020-01-01  accepted  — example\n```\n\n## Log\n\n- 2026-01-01  accepted  — real\n",
    )

    _arch.supersede(_arch.parse_record(path), "2026-08-11", "reason")

    lines = path.read_text().splitlines()
    entry = lines.index("- 2026-08-11  superseded  — reason")
    assert entry > lines.index("```"), "must land in the real Log, not the fenced example"
    assert lines[entry - 1] == "- 2026-01-01  accepted  — real"


def test_a_crlf_record_keeps_its_line_endings(tmp_path: Path) -> None:
    """Caught in review: `read_text` translates CRLF to LF, so the round-trip
    rewrote every line in the file — a whole-body diff from a function whose
    contract is one field and one appended line."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "crlf.md"
    path.write_bytes(ACCEPTED.replace("\n", "\r\n").encode())

    _arch.supersede(_arch.parse_record(path), "2026-08-11", "reason")

    raw = path.read_bytes()
    assert b"\r\n" in raw
    assert raw.count(b"\n") == raw.count(b"\r\n"), "no line was converted to bare LF"
    assert raw.endswith(b"- 2026-08-11  superseded  \xe2\x80\x94 reason\r\n")


def test_a_spaced_status_key_is_both_readable_and_editable(tmp_path: Path) -> None:
    """Caught in review: `status : accepted` parsed as in force but the edit
    matched on the `"status:"` prefix and missed it, leaving one record readable
    and un-supersedable at the same time."""
    path = _write(
        tmp_path, "spaced", "---\nstatus : accepted\n---\n\n# X\n\n## Log\n\n- x\n"
    )
    assert _arch.parse_record(path).in_force

    _arch.supersede(_arch.parse_record(path), "2026-08-11", "reason")

    assert _arch.parse_record(path).status == "superseded"


def test_a_record_that_supersedes_itself_is_an_error(tmp_path: Path) -> None:
    """Caught in review: a self-reference satisfied VR-003 and made the record
    its own successor, silencing the VR-002 orphan warning — so a one-character
    typo suppressed the finding that exists to catch it."""
    _write(tmp_path, "solo", "---\nstatus: superseded\nsupersedes: solo\n---\n\n# X\n")

    findings = _arch.validate(_arch.load_records(tmp_path))

    # Both, and both true: the self-reference is the error, and the record is
    # still a superseded one with no real successor once the typo is fixed.
    assert _levels(findings) == {("error", "solo"), ("warning", "solo")}
    assert "itself" in findings[0].message


def test_projection_orders_by_slug_not_by_filename(tmp_path: Path) -> None:
    """`data-model.md` says ordering is by slug. Sorting the filenames puts
    `layer-model` first, because `-` sorts before `.` — stable, so the ordering
    test still passed, but not what the contract promises."""
    for slug in ("layerz", "layer-model", "layer"):
        _write(tmp_path, slug, RECORD.format(status="accepted"))

    slugs = [r.slug for r in _arch.in_force(_arch.load_records(tmp_path))]

    assert slugs == ["layer", "layer-model", "layerz"]


def test_load_records_ignores_subdirectories(tmp_path: Path) -> None:
    """`arch none` files its declaration one level down and relies on exactly
    this: a declaration has no `status`, so a recursive glob would surface every
    one of them as a record that cannot be read. The coupling was a comment on
    both sides until this test; `rglob` here is a one-word edit away.
    """
    root = tmp_path / "architecture"
    (root / "declarations").mkdir(parents=True)
    (root / "layer-model.md").write_text("---\nstatus: accepted\n---\n\n# x\n")
    (root / "declarations" / "some-branch.md").write_text("---\nbranch: x\n---\n\n# no\n")

    assert [r.slug for r in _arch.load_records(root)] == ["layer-model"]


def test_a_fenced_decision_heading_is_not_the_decision(tmp_path: Path) -> None:
    """The `_log_bounds` failure one heading over: a record documenting the
    record format carries a fenced `## Decision` example, and projecting it
    would put template text into the contract agents read as binding."""
    root = tmp_path / "architecture"
    root.mkdir(parents=True)
    path = root / "record-format.md"
    path.write_text(
        "---\nstatus: accepted\n---\n\n# How records are written\n\n"
        "```markdown\n## Decision\n\n<what was decided>\n```\n\n"
        "## Decision\n\nRecords are MADR-simple with an added ownership field.\n"
    )

    text = _arch.decision_text(_arch.parse_record(path))

    assert text == "Records are MADR-simple with an added ownership field."
