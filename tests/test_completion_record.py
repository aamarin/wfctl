"""The completion record carries a copy of `tasks.md`, and a new task reopens
`implement` against it (#264).

Before this the record was a one-line file read by existence. Nothing removed
it, so a story that finished a round of implementation and then gained a task
kept reading finished. Without a definition of done, `wfctl status` printed the
step done and the story complete beside `1/2 done`.

The record is now written by `wfctl step complete implement`, with the task
list as it stood at that moment. A task that is incomplete now and was not
incomplete in the copy is new work, and it reopens the step. A record with no
copy, which is every record written before this change, closes the step only
when every box is ticked.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from datetime import date
from pathlib import Path

from tests.conftest import CLEAN_PLAN, CLEAN_SPEC, write_plan_review
from wfctl import _completion
from wfctl._evidence import quoted_out
from wfctl._pipeline import _infer_steps, _PipelineStep, build_report

TODAY = date(2026, 10, 9)

# A delivery plan whose one row names a key. Without it, a reopened story is
# sent to `/speckit.decompose` before `implement` (the limit
# `test_without_a_delivery_plan_a_reopened_story_goes_to_decompose_first`
# pins), so every test that expects `implement` current carries one.
KEYED_DELIVERY = """# Delivery

## Issue Grouping Map

| Issue | Tasks |
|-------|-------|
| #12 | T001 |
"""


# --- the record's format ------------------------------------------------------


def test_a_record_round_trips_a_task_list_that_holds_fences_of_its_own() -> None:
    """FR-004 and SC-005. `/speckit.tasks` writes fenced examples into every
    task list, so a fence the copy could close would truncate the copy at the
    first one, and every task after it would read as new work."""
    tasks = (
        "# Tasks\n\n- [x] T001 done\n\n"
        "```bash\nTask: \"T001 an example\"\n```\n\n"
        "~~~\n- [ ] T999 a tilde example\n~~~\n\n"
        "~~~~python\nprint('four')\n~~~~\n\n"
        "- [ ] T002 open\n"
    )
    record = _completion.render(tasks, TODAY)

    assert record.startswith("Implementation complete: 2026-10-09\n")
    assert _completion.copy_of(record) == tasks


def test_a_long_tilde_line_inside_a_backtick_block_cannot_cut_the_copy_short() -> None:
    """Plan review PR-003. Sizing the fence against tilde fences outside a walk
    is not enough: a `~~~~~~` line nested inside a backtick block is not a
    fence to `_md.walk`, but it closes a four-tilde fence around the copy."""
    tasks = "- [x] T001 done\n```\n~~~~~~\n```\n- [ ] T002 open\n"
    record = _completion.render(tasks, TODAY)

    assert _completion.copy_of(record) == tasks


def test_a_task_list_with_no_final_newline_reads_back_with_one() -> None:
    """Research R5. The added newline changes no task, so it changes no
    verdict, and FR-004 says so."""
    record = _completion.render("- [x] T001 done", TODAY)

    assert _completion.copy_of(record) == "- [x] T001 done\n"


def test_a_one_line_record_from_before_this_change_has_no_copy() -> None:
    """FR-007. Every record in the spec store today is this shape, and it has
    to read as a record that says nothing about which tasks existed."""
    assert _completion.copy_of("Implementation complete: 2026-09-01\n") is None


def test_a_record_whose_heading_has_no_fenced_block_after_it_has_no_copy() -> None:
    """A hand-edited record that kept the heading and lost the block. Reading
    whatever follows the heading as the copy would compare the live list
    against prose."""
    record = "Implementation complete: 2026-10-09\n\n## Tasks at completion\n\nlost\n"

    assert _completion.copy_of(record) is None


def test_a_record_whose_fence_never_closes_has_no_copy() -> None:
    """A record cut off part-way through its copy. The tasks past the cut
    would be missing from the copy, and a missing task reads as finished, so
    the truncated copy is refused rather than trusted."""
    full = _completion.render("- [x] T001 done\n- [ ] T002 open\n", TODAY)
    torn = full[: full.rindex("~~~~")]

    assert _completion.copy_of(torn) is None


def test_the_heading_quoted_inside_a_fence_is_not_the_copy() -> None:
    """The heading is found outside any fence, so a task list that quotes the
    record's own format does not make its quotation the copy."""
    tasks = "```\n## Tasks at completion\n\n~~~~\n- [ ] T001 fake\n~~~~\n```\n"
    record = _completion.render(tasks, TODAY)

    assert _completion.copy_of(record) == tasks


# --- what a task's description is ---------------------------------------------


def test_the_box_the_id_and_the_spec_kit_tags_are_not_part_of_the_description() -> None:
    """FR-006's own example. `/speckit.tasks` renumbers and retags on every
    run, so a description carrying either would read an unchanged task as new
    after any re-run."""
    assert _completion.description("- [ ] T004 [P] [US2] Add the reader") == "- Add the reader"
    assert _completion.description("- [ ] T007 [US3] Add the reader") == "- Add the reader"


def test_a_task_id_later_in_the_text_stays_in_the_description() -> None:
    """Research R2. Only the ID spec-kit writes after the box is removed. A
    new task that differs from an old one only in what it depends on would
    otherwise hide as old work."""
    assert _completion.description("- [ ] T005 Wire it up after T012") == "- Wire it up after T012"


def test_whitespace_collapses_and_the_ends_are_stripped() -> None:
    assert _completion.description("  - [ ]  T001   Add\tthe   reader  ") == "- Add the reader"


def test_an_inline_code_span_keeps_its_text_in_the_description() -> None:
    """Research R3. `quoted_out` deletes inline spans, so a description taken
    from the quoted line would make "Add `foo`" and "Add `bar`" one task, and
    a new one could hide behind the old one."""
    foo = _completion.description("- [ ] T001 Add `foo`")
    bar = _completion.description("- [ ] T002 Add `bar`")

    assert foo == "- Add `foo`" and bar == "- Add `bar`"


def test_a_box_inside_an_inline_code_span_is_not_the_task_box() -> None:
    """A task that documents the checkbox syntax. Removing the quoted box
    instead of the real one leaves the ID in the description, so a renumber
    would reopen the step."""
    assert (
        _completion.description("- [ ] T001 Read `[x]` as ticked")
        == "- Read `[x]` as ticked"
    )


def _incomplete(live: str, copy: str) -> Counter[str]:
    return _completion.new_incomplete(live, quoted_out(live), copy, quoted_out(copy))


def test_a_line_whose_first_box_is_ticked_and_a_later_box_is_not_reads_incomplete() -> None:
    """Plan review PR-005. Reading a line by its first box would let
    `[x] … [ ] …` hide an incomplete task, which is the one direction every
    rule here is built never to fail in."""
    assert _incomplete("- [x] T001 first [ ] second\n", "") == Counter(
        {"- first [ ] second": 1}
    )


# --- the inference, against a feature on disk --------------------------------


def _feature(
    spec_tree: Callable[..., Path], tasks: str, *, delivery: bool = True, **extra: str
) -> Path:
    """Every artifact upstream of `implement`, with `tasks.md` and the
    completion record supplied per test.

    `_infer_steps` cascades, so a feature missing an upstream artifact reads
    `implement pending` for a reason that has nothing to do with the record.
    """
    content = {
        "spec.md": CLEAN_SPEC,
        "plan.md": CLEAN_PLAN,
        "checklists/analysis-report.md": "a report\n",
        "tasks.md": tasks,
        **extra,
    }
    if delivery:
        content["delivery.md"] = KEYED_DELIVERY
    feature = spec_tree(content=content)
    write_plan_review(feature)
    return feature


def _record(copy: str | None) -> dict[str, str]:
    """A completion record holding `copy`, or the one-line shape when None."""
    text = (
        "Implementation complete: 2026-09-01\n"
        if copy is None
        else _completion.render(copy, TODAY)
    )
    return {str(_completion.RECORD): text}


def _step(feature: Path, repo_root: Path, name: str) -> _PipelineStep:
    return next(s for s in _infer_steps(feature, repo_root) if s.name == name)


def _states(feature: Path, repo_root: Path) -> dict[str, str]:
    return {s.name: s.state for s in _infer_steps(feature, repo_root)}


def _position(feature: Path, repo_root: Path) -> tuple[str | None, str | None]:
    """The current step and the next command, from the one inference every
    view renders."""
    report = build_report(feature, repo_root, repo_root)
    return report.current, report.next_command


# --- Story 1: a task added after the story finished reopens implement --------


def test_a_task_added_after_completion_reopens_implement_without_a_definition_of_done(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """FR-005, FR-010, FR-013 and SC-002, and the arm the issue says lies.

    With no definition of done, this tree read `implement` done and the story
    complete beside `1/2 done`, because the record existed. Going back to
    trusting the record by its existence fails this test.
    """
    feature = _feature(
        spec_tree,
        "- [x] T001 Build it\n- [ ] T002 Handle the new case\n",
        **_record("- [x] T001 Build it\n"),
    )
    step = _step(feature, tmp_path, "implement")

    assert (step.state, step.annotation) == ("in_progress", "1/2 done")
    assert _position(feature, tmp_path) == ("implement", "/speckit.implement")


def test_only_the_task_added_since_completion_is_new_work(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """Story 1 #3. T002 was incomplete when the step finished, and the record
    accepted it then. Only T003 is work the record never saw."""
    copy = "- [x] T001 Build it\n- [ ] T002 Deferred\n"
    live = copy + "- [ ] T003 Added later\n"

    assert _incomplete(live, copy) == Counter({"- Added later": 1})


def test_a_new_task_that_takes_an_old_tasks_id_still_reads_as_new(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """FR-006 and Story 1 #4. A task inserted in the middle shifts every ID
    after it, so matching by ID would read the new T002 as the old one."""
    copy = "- [x] T001 Build it\n- [ ] T002 Deferred\n"
    live = "- [x] T001 Build it\n- [ ] T002 Inserted\n- [ ] T003 Deferred\n"
    feature = _feature(spec_tree, live, **_record(copy))

    assert _incomplete(live, copy) == Counter({"- Inserted": 1})
    assert _states(feature, tmp_path)["implement"] == "in_progress"


def test_a_tag_change_on_an_incomplete_task_leaves_the_step_closed(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """Clarification 1. A re-run of `/speckit.tasks` moves `[P]` and `[USn]`
    tags without changing the work, and reopening on it would send a finished
    story back for nothing."""
    copy = "- [x] T001 Build it\n- [ ] T002 [P] [US1] Deferred\n"
    live = "- [x] T001 Build it\n- [ ] T005 [US2] Deferred\n"
    feature = _feature(spec_tree, live, **_record(copy))

    assert _states(feature, tmp_path)["implement"] == "done"


def test_a_second_incomplete_task_with_the_same_description_reopens_the_step(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """FR-006. Tasks are matched by count, so a duplicate added since is new,
    where matching by set would read it as already accounted for."""
    copy = "- [x] T001 Build it\n- [ ] T002 Check it\n"
    live = copy + "- [ ] T003 Check it\n"
    feature = _feature(spec_tree, live, **_record(copy))

    assert _states(feature, tmp_path)["implement"] == "in_progress"


def test_a_task_inside_a_code_example_is_not_counted_in_either_list(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """FR-009. The tally already reads the file with code quoted out, and a
    comparison that did not would reopen on a worked example."""
    copy = "- [x] T001 Build it\n"
    live = copy + "\n```\n- [ ] T999 what a task looks like\n```\n"
    feature = _feature(spec_tree, live, **_record(copy + "```\n- [ ] T998 old\n```\n"))

    assert _incomplete(live, copy) == Counter()
    assert _states(feature, tmp_path)["implement"] == "done"


def test_without_a_delivery_plan_a_reopened_story_goes_to_decompose_first(
    spec_tree: Callable[..., Path], tmp_path: Path
) -> None:
    """The limit this change records rather than fixes (spec Edge Cases).

    With no `delivery.md`, `decompose` is skipped only while the tasks read
    closed. A reopened story makes them open, so `decompose` becomes current
    and `implement` waits behind it. Changing that would widen the change into
    the `decompose` reader, and every feature in the spec store that holds a
    completion record also holds a delivery plan.
    """
    feature = _feature(
        spec_tree,
        "- [x] T001 Build it\n- [ ] T002 Handle the new case\n",
        delivery=False,
        **_record("- [x] T001 Build it\n"),
    )

    assert _position(feature, tmp_path) == ("decompose", "/speckit.decompose")
