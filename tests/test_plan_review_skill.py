"""The `plan-review` skill and the `/plan-review` command stay on their own
sides of the line `plan-review-boundaries` draws.

The skill holds the review method and names no runner. The command holds
everything tied to this pipeline: which mode a run is in, where the report and
the plan copy go, and the scan file. Both are prose under `wfctl/agents/`, which
`install-skills` copies and nothing else reads, so a line that drifts across the
boundary, or a report example that drifts from the two lines wfctl reads, ships
green unless a test here reads the shipped files.
"""
from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

from wfctl import _arch
from wfctl._plan_review import COPY_NAME, REPORT_NAME, read_report

# Resolved through `files("wfctl")` for `test_skill_cross_references`' reason:
# conftest's autouse `bundle` fixture repoints `_bundle.BUNDLE_ROOT` at a fake
# tree, and reading the real shipped one is this file's whole purpose.
_AGENTS = Path(str(files("wfctl"))) / "agents"
_SKILL_DIR = _AGENTS / "skills" / "plan-review"
_WRAPPER = _AGENTS / "commands" / "plan-review.md"

# The runner's vocabulary, which the method must never carry (FR-019). The
# first three are the ones the design record's Verification names. `wfctl` is
# the runner itself, and a method that names it reads correctly under one
# pipeline only, which is the baseline the record rejected.
_RUNNER_WORDS = ("/speckit.", "[NEEDS CLARIFICATION", "checklists/", "wfctl")

# A bold list head in upper case, such as `1. **BLOCKER** means ...`. The
# skill writes its priorities in this form and nothing else in it, so the
# pattern reads the priority list without depending on its surrounding words.
_PRIORITY_HEAD = re.compile(r"^\s*(?:\d+\.|-) \*\*([A-Z]{3,})\*\*", re.M)

_IDENTITY = re.compile(r"^[0-9a-f]{40}$")
_PATH = re.compile(r"^[A-Za-z0-9_.][A-Za-z0-9_./-]*$")


def _method_files() -> list[Path]:
    """`SKILL.md` and every reference beside it, which together are the method."""
    skill = _SKILL_DIR / "SKILL.md"
    assert skill.exists(), f"the plan-review skill does not ship: {skill}"
    return [skill, *sorted((_SKILL_DIR / "references").glob("*.md"))]


def _wrapper() -> str:
    assert _WRAPPER.exists(), f"the /plan-review command does not ship: {_WRAPPER}"
    return _WRAPPER.read_text()


def _example() -> str:
    """The report example in `references/report-format.md`: the one fenced
    markdown block that carries a `## Reviewed inputs` section."""
    text = (_SKILL_DIR / "references" / "report-format.md").read_text()
    blocks = [
        b for b in re.findall(r"```markdown\n(.*?)```", text, re.DOTALL)
        if "## Reviewed inputs" in b
    ]
    assert len(blocks) == 1, f"expected one report example, found {len(blocks)}"
    return blocks[0]


def _input_rows(example: str) -> list[list[str]]:
    """The cells of every data row in the example's `## Reviewed inputs` table,
    header and separator left out."""
    lines = example.splitlines()
    start = lines.index("## Reviewed inputs")
    rows = []
    for line in lines[start + 1:]:
        if line.startswith("#"):
            break
        if line.startswith("|"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return [r for r in rows[1:] if not all(set(c) <= {"-", ":"} for c in r)]


def _verdict_rule() -> str:
    """The wrapper's verdict rule, from its `**Verdict` lead to the paragraph's end."""
    text = _wrapper()
    start = text.index("**Verdict")
    end = text.find("\n\n", start)
    return text[start:] if end == -1 else text[start:end]


def test_the_method_names_no_runner() -> None:
    """FR-019 and SC-005, as `plan-review-boundaries` § Verification states them.

    The way the split fails is drift back into the skill: a later edit adds a
    `/speckit.tasks` line to the method because it was the nearest file, and
    nothing flags that edit at review time. The skill then reads correctly under
    one pipeline only, and a renamed step has to touch the method again.
    """
    offenders = [
        f"{path.relative_to(_SKILL_DIR)}:{n}: {word}"
        for path in _method_files()
        for n, line in enumerate(path.read_text().splitlines(), 1)
        for word in _RUNNER_WORDS
        if word in line
    ]
    assert not offenders, offenders


def test_the_report_example_carries_both_lines_wfctl_reads(tmp_path: Path) -> None:
    """FR-007: the constants in `_plan_review` hold against the example the
    same wheel ships.

    `BLOCKER_COUNT_LINE` takes the whole line and `PLAN_IDENTITY_ROW` takes
    exactly `plan.md` in the first cell and 40 lowercase hex characters in the
    second. An example written as `BLOCKER: 0 (none open)` or with a placeholder
    identity teaches every review to write a report the reader cannot read, and
    the pass then holds on "records no BLOCKER count" after every clean review.
    """
    report = tmp_path / REPORT_NAME
    report.write_text(_example())

    read = read_report(report)

    assert read.plan_identity is not None and _IDENTITY.match(read.plan_identity)
    assert read.open_blockers is not None


def test_the_other_input_rows_are_spelled_the_way_the_wrapper_checks_them() -> None:
    """contracts/report-format.md § The other input rows.

    wfctl never reads these rows, but the wrapper does, to choose between
    revising and reviewing. A row whose identity cell says `missing`, or holds a
    placeholder, is one the input check reads as changed on every run, so every
    `/plan-review` with a BLOCKER open reviews instead of revising, with no error
    to say why. The candidate skill spelled an absent input `missing`.

    The report records no row for itself, since a row naming the file it sits
    in can never match.
    """
    rows = _input_rows(_example())
    others = [r for r in rows if r[0] != "plan.md"]

    assert others, "the example records no input beside plan.md"
    bad = [
        r[:2] for r in others
        if not _PATH.match(r[0]) or not (_IDENTITY.match(r[1]) or r[1] == "absent")
    ]
    assert not bad, bad
    assert any(r[1] == "absent" for r in others), "no row shows how an absent input is spelled"
    assert not any("missing" in r[1] for r in rows)
    assert REPORT_NAME not in [r[0] for r in rows]


def test_the_skill_and_the_verdict_rule_name_the_same_three_priorities() -> None:
    """FR-013 and FR-016, as `plan-review-severity` § Verification states them.

    A fourth priority added to the skill and not to the verdict rule is a
    finding the verdict never reads, which is the QUESTION the record removed,
    back under another name. The report's summary count lines are the third
    place the list is written, so they are held to it too.
    """
    skill = (_SKILL_DIR / "SKILL.md").read_text()
    priorities = _PRIORITY_HEAD.findall(skill)
    summary = _example().split("## Summary", 1)[1].split("\n## ", 1)[0]

    assert priorities == ["BLOCKER", "MAJOR", "MINOR"]
    assert set(re.findall(r"\b[A-Z]{4,}\b", _verdict_rule())) == set(priorities)
    assert re.findall(r"^([A-Z]+): ", summary, re.M) == priorities


def test_no_question_priority_survives_anywhere_in_the_pass() -> None:
    """`plan-review-severity`: a missing answer is a `Missing Information`
    finding graded by what it blocks, never a grade of its own.

    Checked across every file rather than only in the priority list, because
    the candidate named QUESTION in its rubric, its report format, its summary
    step, and a lens, and a single survivor tells a reviewer the grade exists.
    """
    offenders = [
        str(path.relative_to(_AGENTS))
        for path in [*_method_files(), _WRAPPER]
        if "QUESTION" in path.read_text()
    ]
    assert not offenders, offenders


def test_the_command_names_the_skill_by_path_and_the_agent_may_invoke_it() -> None:
    """FR-020, and `plan-review-boundaries` § Verification's second test.

    A wrapper that names the skill by phrase rather than path reaches it only
    when the agent happens to search for the phrase, and a wrapper carrying
    `disable-model-invocation` is refused on exactly the unattended route
    `wfctl status` hands it (#473). Either one stops the pipeline at the pass
    with the pass still reading outstanding.
    """
    assert ".agents/skills/plan-review/SKILL.md" in _wrapper()
    assert "disable-model-invocation" not in _arch._frontmatter(_wrapper())


def test_the_command_writes_where_the_reader_reads() -> None:
    """The report and copy names are `_plan_review`'s constants, and the
    wrapper is the only place a path for either is written (research R7).

    A rename on one side alone leaves the reader looking for a report no review
    writes, and every feature then reads "no report" after a finished review.
    """
    text = _wrapper()

    assert f"FEATURE_DIR/{REPORT_NAME}" in text
    assert f"FEATURE_DIR/{COPY_NAME}" in text


def test_the_command_is_granted_every_command_it_tells_the_agent_to_run() -> None:
    """contracts/plan-review-command.md § Frontmatter.

    `allowed-tools` is a ceiling on the whole turn, so an instruction without its
    grant reads correctly and cannot run. Under auto-approve that is a permission
    prompt nobody answers, one tool call into the pass. `cp` and
    `git diff --no-index` are the two research R7 added for the plan copy, and
    `git hash-object` is the one the input check and the copy check both need.
    """
    allowed = _arch._frontmatter(_wrapper()).get("allowed-tools", "")
    needed = (
        "Read", "Glob", "Write", "Edit",
        "Bash(wfctl status*)", "Bash(wfctl feature-paths*)", "Bash(wfctl arch-root*)",
        "Bash(wfctl arch check*)", "Bash(git hash-object*)", "Bash(mkdir*)",
        "Bash(git add*)", "Bash(git commit*)", "Bash(cp*)", "Bash(git diff --no-index*)",
    )
    missing = [grant for grant in needed if grant not in allowed]
    assert not missing, missing


def test_the_skill_is_never_mirrored() -> None:
    """Research R13. `mirror-supersedes-the-wrapper` drops a mirrored skill's
    wrapper on the Claude layer and requires that the wrapper carry nothing its
    skill does not. This wrapper carries the pipeline half of the pass by
    design, so mirroring the skill would delete the mode choice, the paths, and
    the scan file on the layer where the pass is used most, and nothing would
    report it.
    """
    from wfctl.cli import _MIRRORED_SKILLS

    assert "plan-review" not in _MIRRORED_SKILLS


def test_none_of_the_candidates_runner_files_ship() -> None:
    """FR-021. The candidate carried a Codex `agents/` metadata file, a
    `wfctl.json.fragment` declaring the pass, a JSON sidecar, and a
    `wfctl-integration.md` reference. The pass is built in, so the fragment
    would declare a pass that collides with wfctl's own, and the integration
    notes are the wrapper's content under a name the method would read.
    """
    _method_files()
    shipped = [p.relative_to(_SKILL_DIR) for p in _SKILL_DIR.rglob("*") if p.is_file()]
    offenders = [
        str(p) for p in shipped
        if "agents" in p.parts
        or p.suffix == ".json"
        or p.name in {"wfctl.json.fragment", "wfctl-integration.md"}
    ]
    assert not offenders, offenders
