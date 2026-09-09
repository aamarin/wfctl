"""The whole inference payload, pinned against a snapshot taken before #314.

The rest of the suite asserts on step states and on console substrings. That
leaves a gap #314 walks straight into: a restructure that moved every predicate
into a new shape while preserving each existing assertion would pass completely,
and nothing would notice that `decompose` had started reaching a different
verdict or that a blocked step had lost its remedy.

So this pins the payload itself — every step's `state`, `annotation`, `reason`
and `remedy`, across every combination that reaches a different arm. The
snapshot beside this file was generated from the code as it stood before the
predicates were given one signature; a diff against it is the evidence that the
restructure changed no behaviour, and it goes on being that evidence for #308,
#309, #240 and #299, each of which deliberately *does* change a verdict and must
say so by updating this file.

`state` and never the glyph: `cli` renders `done` and `skipped` with two symbols
that cannot be told apart once printed, so a snapshot of the console would be
blind to exactly the distinction inference exists to carry.

To regenerate after a deliberate behaviour change:

    uv run python -c "import json,tempfile,pathlib; \
        import tests.test_pipeline_payload_snapshot as s; \
        d=pathlib.Path(tempfile.mkdtemp()); \
        pathlib.Path('tests/pipeline_payload_snapshot.json').write_text( \
            json.dumps(s.build_payload(d), indent=2, sort_keys=True) + chr(10))"

and say in the commit message which verdict moved and why.
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import subprocess
from collections.abc import Iterator
from pathlib import Path

from tests.conftest import git_repo
from wfctl._pipeline import _infer_steps

SNAPSHOT = Path(__file__).parent / "pipeline_payload_snapshot.json"

MARKED_SPEC = "# Spec\n\n[NEEDS CLARIFICATION: which one?]\n"
CLARIFIED_SPEC = "# Spec\n\n## Clarifications\n\n### Session 2026-01-01\n\n- none\n"
OPEN_TASKS = "- [x] T001 done\n- [ ] T002 open\n"
CLOSED_TASKS = "- [x] T001 done\n- [x] T002 done\n"
# #308: a file that exists and holds no task, and one whose only box is a worked
# example inside a fence. Both cleared `tasks` and `implement` before #308 while
# proving nothing, so a snapshot that cannot tell them from a real task list
# cannot see that change at all.
NO_TASKS = "# Tasks\n\nProse, and not one box.\n"
FENCED_TASKS = "# Tasks\n\n```\n- [ ] T001 what a task looks like\n```\n"
SENTINEL = {"checklists/implement-complete.md": "x"}

KEYED_DELIVERY = """# Delivery

## Issue Grouping Map

| Issue | Tasks |
|-------|-------|
| #12 | T001 |
"""
UNKEYED_DELIVERY = """# Delivery

## Issue Grouping Map

| Issue | Tasks |
|-------|-------|
| _(TBD)_ (Issue A) | T001 |
| _(TBD)_ (Issue B) | T002 |
"""
NO_MAP_DELIVERY = "# Delivery\n\nNo grouping table here.\n"

_ANALYZED = {
    "spec.md": CLARIFIED_SPEC,
    "plan.md": "x",
    "tasks.md": OPEN_TASKS,
    "checklists/analysis-report.md": "x",
}

# Each row reaches an arm no other row reaches. A row that duplicates another's
# path is noise in the diff, not extra coverage.
MATRIX: list[tuple[str, dict[str, str]]] = [
    ("empty", {}),
    ("design-only", {"design.md": "x"}),
    ("spec-only", {"spec.md": "# Spec\n"}),
    ("spec-marked", {"spec.md": MARKED_SPEC}),
    ("spec-clarified", {"spec.md": CLARIFIED_SPEC}),
    ("spec-plan-unclarified", {"spec.md": "# Spec\n", "plan.md": "x"}),
    ("tasks-open", {"spec.md": CLARIFIED_SPEC, "plan.md": "x", "tasks.md": OPEN_TASKS}),
    ("tasks-closed", {"spec.md": CLARIFIED_SPEC, "plan.md": "x", "tasks.md": CLOSED_TASKS}),
    ("analyzed", _ANALYZED),
    ("decompose-keyed", {**_ANALYZED, "delivery.md": KEYED_DELIVERY}),
    ("decompose-unkeyed-tasks-open", {**_ANALYZED, "delivery.md": UNKEYED_DELIVERY}),
    (
        "decompose-unkeyed-tasks-closed",
        {**_ANALYZED, "tasks.md": CLOSED_TASKS, "delivery.md": UNKEYED_DELIVERY},
    ),
    ("decompose-no-map", {**_ANALYZED, "delivery.md": NO_MAP_DELIVERY}),
    ("decompose-skipped", {**_ANALYZED, "tasks.md": CLOSED_TASKS}),
    ("tasks-no-checkbox", {"spec.md": CLARIFIED_SPEC, "plan.md": "x", "tasks.md": NO_TASKS}),
    (
        "tasks-only-a-fenced-example",
        {"spec.md": CLARIFIED_SPEC, "plan.md": "x", "tasks.md": FENCED_TASKS},
    ),
    (
        "tasks-no-checkbox-but-implemented",
        {"spec.md": CLARIFIED_SPEC, "plan.md": "x", "tasks.md": NO_TASKS, **SENTINEL},
    ),
    (
        "tasks-open-but-implemented",
        {"spec.md": CLARIFIED_SPEC, "plan.md": "x", "tasks.md": OPEN_TASKS, **SENTINEL},
    ),
    # The design gate's other early return: past the boundary, so a `design.md`
    # with no record still reads `done` once `spec.md` exists.
    ("design-past-boundary", {"design.md": "x", "spec.md": CLARIFIED_SPEC}),
]

# `implement`'s blocking arms, which need a definition of done and a verification
# record rather than a feature-dir shape. Each is the *first* reason
# `verification_block` returns for that record, in its own order — so a row that
# holds two conditions at once is testing the earlier one.
#
# `None` for the record means none was written.
DONE = [["true"]]
_SHA = "0" * 40
VERIFY_ROWS: list[tuple[str, str | None, dict | None]] = [
    ("malformed-config", "{ not json", None),
    ("no-definition-of-done", None, None),
    ("unverified", json.dumps({"verify": DONE}), None),
    ("inconclusive", json.dumps({"verify": DONE}),
     {"command": DONE, "exit": 0, "failed": [], "sha": _SHA, "dirty": False,
      "inconclusive": True, "at": "2026-01-01T00:00:00Z"}),
    ("failed", json.dumps({"verify": DONE}),
     {"command": DONE, "exit": 1, "failed": [["true"]], "sha": _SHA, "dirty": False,
      "inconclusive": False, "at": "2026-01-01T00:00:00Z"}),
    ("stale-definition", json.dumps({"verify": [["false"]]}),
     {"command": DONE, "exit": 0, "failed": [], "sha": _SHA, "dirty": False,
      "inconclusive": False, "at": "2026-01-01T00:00:00Z"}),
    ("stale-sha", json.dumps({"verify": DONE}),
     {"command": DONE, "exit": 0, "failed": [], "sha": _SHA, "dirty": False,
      "inconclusive": False, "at": "2026-01-01T00:00:00Z"}),
    ("stale-dirty", json.dumps({"verify": DONE}),
     {"command": DONE, "exit": 0, "failed": [], "sha": None, "dirty": True,
      "inconclusive": False, "at": "2026-01-01T00:00:00Z"}),
    ("verified", json.dumps({"verify": DONE}),
     {"command": DONE, "exit": 0, "failed": [], "sha": None, "dirty": False,
      "inconclusive": False, "at": "2026-01-01T00:00:00Z"}),
]

# `verification_block` prints the record's sha, which is this run's HEAD and
# therefore different every time. Anchored to 7 hex characters between word
# boundaries, which is what `sha[:7]` produces and what nothing else in these
# strings looks like.
_SHA_IN_TEXT = re.compile(r"\b[0-9a-f]{7}\b")


def _feature(root: Path, name: str, files: dict[str, str]) -> Path:
    """Exactly the named artifacts under a fresh feature dir, and nothing else."""
    feature = root / "features" / name / "314-feature"
    feature.mkdir(parents=True, exist_ok=True)
    for artifact_name, text in files.items():
        artifact = feature / artifact_name
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(text)
    return feature


def _repo(root: Path, name: str, *, tracker: bool, record: bool) -> Path:
    """A repo with one commit, so the two predicates that ask git get an answer.

    Without a commit there is no trunk, `touched_on_this_branch` returns None for
    every row, and the design gate reads `inconclusive` — a real state, but one
    that would make its *blocked* state unreachable in the whole matrix.

    The tracker's name goes in `.wf-skills-manifest.json` and only its
    `key_pattern` in `.agents/`. Writing the name into `.agents/` instead leaves
    `configured_key_pattern` returning None, and all four `decompose` rows then
    exercise the no-tracker path while appearing to cover four cases.
    """
    repo = git_repo(root / "repos" / name)
    if tracker:
        (repo / ".wf-skills-manifest.json").write_text(json.dumps({"tracker": "github"}))
        trackers = repo / ".agents" / "trackers"
        trackers.mkdir(parents=True, exist_ok=True)
        (trackers / "github.json").write_text(json.dumps({"key_pattern": r"\d+"}))
    if record:
        # Uncommitted, which is the case the gate is written for: a record
        # authored moments ago. `touched_on_this_branch` reads dirty first.
        arch = repo / "docs" / "architecture"
        arch.mkdir(parents=True, exist_ok=True)
        (arch / "a-decision.md").write_text("# A decision\n")
    return repo


def _scrub(text: str | None) -> str | None:
    """Replace this run's git sha so the snapshot is stable across machines."""
    return None if text is None else _SHA_IN_TEXT.sub("<sha>", text)


def _dump(feature: Path | None, repo: Path) -> list[dict[str, str | None]]:
    return [
        {
            "name": s.name,
            "state": s.state,
            "annotation": _scrub(s.annotation),
            "reason": _scrub(s.reason),
            "remedy": s.remedy,
        }
        for s in _infer_steps(feature, repo)
    ]


@contextlib.contextmanager
def _state_dir(path: Path) -> Iterator[None]:
    """Point `resolve_agent_dir` at `path` for the duration.

    `verification_block` resolves the state dir itself from the repo root and the
    branch, so a verification record cannot be placed by building a feature dir —
    the env override is the seam wfctl already publishes for exactly this.
    """
    path.mkdir(parents=True, exist_ok=True)
    before = os.environ.get("WFCTL_STATE_DIR")
    os.environ["WFCTL_STATE_DIR"] = str(path)
    try:
        yield
    finally:
        if before is None:
            os.environ.pop("WFCTL_STATE_DIR", None)
        else:
            os.environ["WFCTL_STATE_DIR"] = before


def _verify_rows(root: Path) -> dict[str, list[dict[str, str | None]]]:
    """One row per reason `verification_block` can return.

    The committed matrix writes no `wfctl.json`, so every row of it takes the
    "no definition of done" path and all seven blocking reasons went unexercised
    — the gap the review panel found, and the arms most likely to be broken by a
    change that recomposes `implement`'s annotation.
    """
    out: dict[str, list[dict[str, str | None]]] = {}
    feature = _feature(root, "verify", {**_ANALYZED, "tasks.md": CLOSED_TASKS})
    for name, config, record in VERIFY_ROWS:
        repo = git_repo(root / "verify-repos" / name)
        if config is not None:
            (repo / "wfctl.json").write_text(config)
            # Committed, not just written. `code_identity` counts an untracked
            # file as a dirty tree, so a config left uncommitted makes every row
            # here read `stale — uncommitted changes` and the eight other arms
            # become unreachable.
            for args in (["add", "-A"], ["commit", "-m", "config"]):
                subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)
        state = root / "verify-state" / name
        with _state_dir(state):
            if record is not None:
                if record["sha"] is None:
                    # This repo's real HEAD: the rows that must *not* read stale.
                    head = subprocess.run(
                        ["git", "rev-parse", "HEAD"], cwd=repo,
                        capture_output=True, text=True,
                    )
                    record = {**record, "sha": head.stdout.strip()}
                (state / "verify.json").write_text(json.dumps(record))
            if name == "stale-dirty":
                (repo / "uncommitted.txt").write_text("x\n")
            out[f"implement-{name}"] = _dump(feature, repo)
    return out


def build_payload(root: Path) -> dict[str, list[dict[str, str | None]]]:
    """Every row of the matrix against every repo shape that changes an answer."""
    plain = _repo(root, "tracker", tracker=True, record=False)
    untracked = _repo(root, "no-tracker", tracker=False, record=False)
    recorded = _repo(root, "recorded", tracker=True, record=True)

    payload: dict[str, list[dict[str, str | None]]] = {}
    for label, repo in (("", plain), (" (no tracker)", untracked)):
        for name, files in MATRIX:
            payload[name + label] = _dump(_feature(root, name + label, files), repo)

    # The design gate's two answered states: same feature dir, one repo carrying
    # a record and one not. `design-only` above is the same question asked of a
    # repo with no record, and is kept because the rest of its row differs.
    design = _feature(root, "design-gate", {"design.md": "x"})
    payload["design-no-record"] = _dump(design, plain)
    payload["design-with-record"] = _dump(design, recorded)

    # spec_dir=None returns before any predicate runs.
    payload["no-spec-dir"] = _dump(None, plain)

    payload.update(_verify_rows(root))
    return payload


def test_the_whole_payload_matches_the_snapshot(tmp_path: Path) -> None:
    """Every step's state, annotation, reason and remedy, unchanged.

    This is the assertion #314 could not otherwise make: the suite's other tests
    would all still pass if the restructure had quietly changed a verdict.
    """
    expected = json.loads(SNAPSHOT.read_text())
    actual = build_payload(tmp_path)

    assert set(actual) == set(expected), "the matrix gained or lost a row"
    for row in sorted(expected):
        assert actual[row] == expected[row], f"payload changed for {row!r}"


def test_the_matrix_reaches_every_decompose_arm(tmp_path: Path) -> None:
    """The four `decompose` readings are distinguishable, not four spellings of one.

    Written because the first version of this fixture put the tracker's name in
    the wrong file, so all four rows silently took the no-tracker path and the
    snapshot would have frozen a matrix that checked one arm four times.
    """
    payload = build_payload(tmp_path)

    def decompose(row: str) -> tuple[str | None, str | None]:
        step = next(s for s in payload[row] if s["name"] == "decompose")
        return step["state"], step["reason"]

    assert decompose("decompose-keyed") == ("done", None)
    assert decompose("decompose-unkeyed-tasks-open") == (
        "in_progress", "2 issue rows without a key",
    )
    # Closed work stops the finding standing in the way, and keeps saying it.
    assert decompose("decompose-unkeyed-tasks-closed") == (
        "done", "2 issue rows without a key",
    )
    # Both inconclusive readings proceed, and neither invents a reason.
    assert decompose("decompose-no-map") == ("done", None)
    assert decompose("decompose-unkeyed-tasks-open (no tracker)") == ("done", None)


def test_the_matrix_reaches_both_design_states(tmp_path: Path) -> None:
    """The design gate blocks without a record and clears with one.

    The blocked arm carries a remedy no other step has, and it is the one a
    restructure is most likely to drop — `_design_remedy` is keyed on the reason
    rather than on the step name.
    """
    payload = build_payload(tmp_path)
    blocked = next(s for s in payload["design-no-record"] if s["name"] == "brainstorm")
    cleared = next(s for s in payload["design-with-record"] if s["name"] == "brainstorm")

    assert blocked["state"] == "in_progress"
    assert blocked["reason"] == "no architecture record for this change"
    assert blocked["remedy"] is not None and "wfctl arch none" in blocked["remedy"]
    assert cleared["state"] == "done"
    assert cleared["reason"] is None


def test_the_snapshot_is_not_stale_against_the_step_table() -> None:
    """A step added to `_STEPS` without regenerating the snapshot is caught here.

    Otherwise the snapshot keeps passing while covering eight of nine steps, and
    the row it never checks is the new one.
    """
    from wfctl._pipeline import _STEP_NAMES

    expected = json.loads(SNAPSHOT.read_text())
    for row, steps in expected.items():
        assert [s["name"] for s in steps] == _STEP_NAMES, f"{row!r} predates the step table"
