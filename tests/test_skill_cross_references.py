"""Every skill a shipped file tells the agent to read is a skill that ships.

Skills reference each other by path — a command wrapper points at the skill it
activates, and `start-session` loads the two output-style skills by name. Those
reads fail silently on purpose: `start-session` says to skip an uninstalled
skill rather than stop the session. So a renamed or dropped skill costs the
session a rule and reports nothing, which is #23's shape one directory over.
"""
import re
from importlib.resources import files
from pathlib import Path


# Resolved through `files("wfctl")` for the same reason as
# `test_pipeline_commands`: conftest's autouse `bundle` fixture repoints
# `_bundle.BUNDLE_ROOT` at a fake tree, and reading the real shipped one is this
# file's whole purpose.
_AGENTS = Path(str(files("wfctl"))) / "agents"

# Trailing `/` excluded from the name so a bare `.agents/skills/` — prose about
# the directory, not a reference to one skill — doesn't read as a skill called "".
_REFERENCE = re.compile(r"\.agents/skills/([a-z0-9][a-z0-9-]*)")


def _references() -> dict[str, list[str]]:
    """Skill name → the shipped files naming it."""
    found: dict[str, list[str]] = {}
    for md in sorted(_AGENTS.rglob("*.md")):
        for name in _REFERENCE.findall(md.read_text()):
            found.setdefault(name, []).append(str(md.relative_to(_AGENTS)))
    return found


def test_every_referenced_skill_ships() -> None:
    missing = {
        name: sources
        for name, sources in _references().items()
        if not (_AGENTS / "skills" / name / "SKILL.md").exists()
    }
    assert not missing, f"referenced but not shipped: {missing}"


def test_the_output_style_skills_are_both_loaded_at_session_start() -> None:
    """`i-have-adhd` sets length, `conversation-response-shape` sets order and
    depth. Both have to be on from turn 0 and nothing else turns them on there —
    `i-have-adhd` carries upstream's `disable-model-invocation`, and the other is
    model-invocable but only once a turn has already been shaped wrong. Dropping
    either from step 1 disables it for every session, quietly."""
    start = (_AGENTS / "skills" / "start-session" / "SKILL.md").read_text()
    loaded = set(_REFERENCE.findall(start))
    assert {"i-have-adhd", "conversation-response-shape"} <= loaded


def test_each_output_style_skill_is_typeable_on_every_layer() -> None:
    """Turning one back on mid-session — after a session that started without
    `/start-session`, or said "stop adhd mode" — is a human typing its name, so
    every layer needs a route to it.

    Two routes, because no single one covers every layer, which is the thing
    #170's first fix got wrong. The wrapper is the route wherever no mirror
    exists, and for bob it is the only working route to `i-have-adhd`:
    `.bob/skills/` gets upstream's `disable-model-invocation` verbatim and
    `.bob/commands/` gets it stripped. The mirror is the route on the layer that
    has one, where the wrapper is suppressed as a collision.

    Both halves asserted, because either alone stays green through the change
    that removes the other.
    """
    from wfctl.cli import _MIRRORED_SKILLS

    for name in ("i-have-adhd", "conversation-response-shape"):
        assert (_AGENTS / "commands" / f"{name}.md").exists(), name
        assert name in _MIRRORED_SKILLS, name


def test_start_session_loads_the_in_force_set() -> None:
    """FR-009's whole delivery path is this one line in one skill.

    A `SessionStart` hook would have been the obvious route and is not one wfctl
    controls: the hook file belongs to the consumer (#85). So nothing else puts
    accepted records in front of an agent, and dropping the call would leave the
    projection shipping, tested, and read by nobody.
    """
    start = (_AGENTS / "skills" / "start-session" / "SKILL.md").read_text()
    assert "wfctl arch context" in start


def test_the_record_template_ships_beside_the_adr_skill() -> None:
    """The skill tells the agent to copy a template that MANIFEST.in has to
    graft. A skill directory whose non-SKILL.md files were never packaged
    installs cleanly and then fails at the moment a record is being written."""
    skill = _AGENTS / "skills" / "architecture-decisions"
    assert (skill / "SKILL.md").exists()
    assert (skill / "record-template.md").exists()


def test_the_level_2_gate_names_the_record_skill() -> None:
    """The gate is the only thing that turns a level-2 answer into a record.
    Eleven designs carried the instruction to write the answer into a
    `design.md` section and none of them did; the reference is what replaces
    that instruction with a skill the agent actually opens."""
    gate = (_AGENTS / "skills" / "design-levels" / "SKILL.md").read_text()
    assert "architecture-decisions" in set(_REFERENCE.findall(gate))


def test_the_level_2_gate_names_the_design_method_skill() -> None:
    """Two skills answer level 2, and the gate has to name both: one works out
    what the boundary should be, the other writes it down. #150 shipped the
    method and only the second reference, so `architecture-design` installed
    into every repo and was named by nothing — `design-levels` mentioned it
    zero times and no wrapper wrapped it.

    `test_every_referenced_skill_ships` cannot stand in for this, for the reason
    its level-3 twin already gives: it checks that a referenced skill exists,
    and a skill nothing references is the one case it cannot see.

    The second assertion is the same route read from the other end, and it is
    the half nothing else pins. #150 shipped the skill saying "Level 2 does not
    route here yet ... a human opens this skill directly"; restoring that
    sentence leaves every other test in this file green while the two files give
    opposite accounts of how the agent reading one of them got there.

    Scoped to the overview, and that scope is the whole assertion. Over the
    file, `design-levels` is named by path in step 6 regardless — the sentence
    that sends the iteration's output back to *Where the levels land* — so a
    whole-file match passes on the restored denial and pins nothing. Checked by
    mutation rather than by reading: the first version of this test asserted
    over the file and the reverted overview still went green."""
    gate = (_AGENTS / "skills" / "design-levels" / "SKILL.md").read_text()
    assert "architecture-design" in set(_REFERENCE.findall(gate))

    skill = (_AGENTS / "skills" / "architecture-design" / "SKILL.md").read_text()
    overview = skill.split("## When to use")[0]
    assert "design-levels" in set(_REFERENCE.findall(overview))


def test_the_design_method_skill_is_model_invocable() -> None:
    """It ships no command wrapper, so the only route that does not go through
    an agent reading `design-levels` as text is the mirror. The gate names the
    skill by path; an agent that read that pointer and reached for
    `Skill(architecture-design)` instead is refused without membership, which is
    #204's fork one skill over.

    Membership alone does not settle it, and the name of this test is the claim
    that overreaches if it stands alone. `mirror-supersedes-the-wrapper` draws
    the line — "Membership decides reachability; the file decides invocability"
    — and `disable-model-invocation` on this SKILL.md would refuse the skill on
    the discovery path membership just put it on, leaving no route at all.
    `i-have-adhd` is mirrored and refused for exactly that reason, so this is a
    live failure mode rather than a hypothetical, and the key is a plausible
    copy-paste from any of the wrappers carrying it.

    Three assertions, because each one alone stays green through the change that
    breaks the others.
    """
    from wfctl import _arch
    from wfctl.cli import _MIRRORED_SKILLS

    assert not (_AGENTS / "commands" / "architecture-design.md").exists()
    assert "architecture-design" in _MIRRORED_SKILLS

    front = _arch._frontmatter(
        (_AGENTS / "skills" / "architecture-design" / "SKILL.md").read_text()
    )
    assert "disable-model-invocation" not in front


def test_the_design_record_template_ships_beside_its_skill() -> None:
    """The level-3 counterpart of the ADR pair, and the half that shipped alone.

    The template was grafted and installed for a release with no `SKILL.md`
    beside it, so nothing referenced it and no agent reached it (#198). The
    directory is the failure mode: a template packaged without the file that
    tells anyone to open it looks identical to a working skill on disk."""
    skill = _AGENTS / "skills" / "software-design-decisions"
    assert (skill / "SKILL.md").exists()
    assert (skill / "design-record-template.md").exists()


def test_the_level_3_gate_names_the_design_record_skill() -> None:
    """Same shape as the level-2 gate, and for the same reason: the reference is
    the only thing that turns a level-3 answer into a record.

    `test_every_referenced_skill_ships` cannot stand in for this. It checks that
    a referenced skill exists; a skill nothing references is exactly what it
    cannot see, which is how the template shipped unreachable in the first
    place."""
    gate = (_AGENTS / "skills" / "design-levels" / "SKILL.md").read_text()
    assert "software-design-decisions" in set(_REFERENCE.findall(gate))


def test_the_design_record_skill_asks_git_whether_the_record_landed() -> None:
    """A record nobody can open is the failure the format exists to prevent, and
    it is invisible: the file is on disk, the session reports success, and the
    reviewer sees nothing.

    Pinned as the command rather than as any line of git, because the near-miss
    an agent reaches for is `git ls-files --error-unmatch` and it is wrong twice:
    it reads the index, so a record staged and never committed passes, and it
    exits 128 for a path outside the repository and for no repository at all
    alike — the failure and its exemption sharing one exit code."""
    skill = (_AGENTS / "skills" / "software-design-decisions" / "SKILL.md").read_text()
    assert "wfctl arch check" in skill


def test_brainstorm_orders_the_records_before_the_one_pager() -> None:
    """`design.md` lists records by path, so they have to exist before the file
    that points at them. Nothing else states the order: `design-levels` says a
    record is written, not when relative to `idea-refine`.

    The reference is also the only thing that reaches the skill from the
    pipeline — `design-levels` names it, but a command that never invokes it
    leaves the level-3 answer wherever the agent happened to put it.

    Named bare rather than by path, which is how this file already names its
    other three skills; `_REFERENCE` matches the path form and finds nothing
    here."""
    command = (_AGENTS / "commands" / "speckit.brainstorm.md").read_text()
    assert "`software-design-decisions`" in command
    assert "## Software design decisions" in command
    handoff = "invoke the `idea-refine` skill"
    assert handoff in command, "the sentence this test orders against was reworded"
    assert command.index("software-design-decisions") < command.index(handoff), (
        "records are written before the one-pager lists them"
    )


def test_brainstorm_allows_the_commands_its_records_need() -> None:
    """The command's `allowed-tools` is a ceiling on the whole turn, so a step
    added to the prose without its command is a step that reads correctly and
    cannot run. Silent: the agent reports the tool refusal, not a missing rule.

    `wfctl arch none` is the one this list was missing, and it is not optional
    prose: `design-levels` requires a level that drew no boundary to *declare*
    that — "a declared absence is an answer; silence is not" — and the
    declaration is that command. Without it the only level-2 answer brainstorm
    could give was a record, so a change the skill explicitly excludes from
    needing one had no way to finish the step. This command is also the only
    place in the shipped tree that names `wfctl arch none` at all.

    `wfctl arch context` is the second, and it arrived with the level-2 route to
    `architecture-design` (#151). That skill reads the in-force set through this
    command and holds that "a record found any other way is not in force", so
    under the old ceiling its first step was refused inside the one command that
    reaches level 2 at all. `/start-session` having printed the set earlier does
    not substitute — a session that never ran it is the case the skill's own
    sentence is written against.
    """
    front = (_AGENTS / "commands" / "speckit.brainstorm.md").read_text().split("---")[1]
    allowed = next(ln for ln in front.splitlines() if ln.startswith("allowed-tools:"))
    for needed in (
        "wfctl arch check",
        "wfctl arch context",
        "wfctl arch none",
        "git add",
        "git commit",
        "wfctl arch-root",
    ):
        assert f"Bash({needed}*)" in allowed, needed


def test_decompose_allows_the_commands_its_notify_gate_needs() -> None:
    """Same ceiling as brainstorm's, on the step #240 made unattended.

    The list was `Read Glob`, which names neither the `Write` that puts
    `delivery.md` on disk nor the read that decides whether this run may create
    issues. Attended that cost a permission prompt someone answered. Unattended
    the two halves fail differently and only one of them is safe: the step-6 read
    fails closed, so no issue is created — but an unwritten `delivery.md` leaves
    decompose `pending` and unblocked, which is `auto: true` again, and
    `speckit-orchestrate` re-emits the command with nothing counting the
    attempts.

    `wfctl notify` is here for the arm nobody reaches on the happy path: a run
    that *was* granted and declined records why, and a decline it cannot record
    is indistinguishable from a refusal it never met.
    """
    front = (_AGENTS / "commands" / "speckit.decompose.md").read_text().split("---")[1]
    allowed = next(ln for ln in front.splitlines() if ln.startswith("allowed-tools:"))
    assert "Write" in allowed, "delivery.md is this step's own artifact"
    for needed in ("wfctl status", "wfctl issue create", "wfctl notify"):
        assert f"Bash({needed}*)" in allowed, needed


def test_the_design_record_skill_is_model_invocable() -> None:
    """It ships no command wrapper, so the mirror is the only route in.

    Same shape as `test_the_panel_skill_is_model_invocable`, and the same
    reason: the trigger is a structural choice just settled in conversation,
    which is a moment nobody types a command. Without membership the skill is
    reachable only by an agent already reading `design-levels` as text — the
    template's own defect (#198) moved one hop along the chain that fixed it.
    """
    from wfctl.cli import _MIRRORED_SKILLS

    assert not (_AGENTS / "commands" / "software-design-decisions.md").exists()
    assert "software-design-decisions" in _MIRRORED_SKILLS


def test_the_session_gates_remedy_is_reachable_without_a_human() -> None:
    """`speckit-orchestrate` halts a branch with no session and offers only
    `/start-session`. The wrapper behind that name carries
    `disable-model-invocation`, so an agent reaching for the Skill tool is
    refused and stops at the gate it was sent to clear — three worktrees did on
    2026-09-06 (#204). A fourth read the wrapper as a file, followed its pointer
    and ran the workflow, which is why the claim is route-dependence and not
    impossibility. Membership in `_MIRRORED_SKILLS` is what removes the fork.

    That the gate still *names* `/start-session` belongs to
    `test_the_gate_sends_the_reader_to_start_session_not_wfctl_start`, which
    owns the orchestrate side and reads the `Display:` line. Asserting it here
    too would put one invariant in two files.

    `disable-model-invocation` is the second way to lose the route silently: the
    mirror puts the skill on the discovery path and that key would refuse it
    there as well, leaving none. `i-have-adhd` is mirrored and unreachable for
    exactly that reason — vendored, carrying upstream's key — so this is a live
    failure mode rather than a hypothetical one.

    `allowed-tools` is the third. Suppression drops the wrapper whole, so the
    pre-approval that used to ride on it has to live here or nowhere, and
    nothing else in the suite would notice it leaving.
    """
    from wfctl import _arch
    from wfctl.cli import _MIRRORED_SKILLS

    assert "start-session" in _MIRRORED_SKILLS

    front = _arch._frontmatter(
        (_AGENTS / "skills" / "start-session" / "SKILL.md").read_text()
    )
    assert "disable-model-invocation" not in front
    assert "allowed-tools" in front


def test_the_record_template_carries_every_section_a_record_needs() -> None:
    """`Owns truth` is the field this feature exists to capture, and the
    template is where the agent gets it from — a template missing it produces
    records missing it, which is the failure being corrected with a new
    filename.

    `Direct baseline` is the same shape found later (#162): `architecture-design`
    step 3 mandates a no-new-structure baseline in every iteration, and the
    template it hands off to had nowhere for one to land."""
    template = (
        _AGENTS / "skills" / "architecture-decisions" / "record-template.md"
    ).read_text()
    for section in (
        "Context",
        "Direct baseline",
        "Decision",
        "Owns truth",
        "Considered",
        "Log",
    ):
        assert f"## {section}" in template, section


def test_the_change_description_skill_defers_to_the_finishing_skill() -> None:
    """`opening-a-change` layers a description step over the integration
    decision rather than owning it.

    `vendor-upstream-skills` says to layer over the derived skill rather than
    edit it, so the whole
    layering depends on this one reference. Drop it and the new skill quietly
    becomes a second, competing account of how a branch gets integrated — the
    duplication the record exists to prevent, one skill over.
    """
    skill = (_AGENTS / "skills" / "opening-a-change" / "SKILL.md").read_text()
    assert "finishing-a-development-branch" in set(_REFERENCE.findall(skill))


def test_the_change_description_skill_names_the_review_panel() -> None:
    """By path, not by phrase. A skill is otherwise discovered by matching its
    description against what a reader typed, and an unattended run types nothing
    — so the panel never started and the change reached a PR reporting success
    (#187). This one reference is the whole of the replacement, and dropping it
    restores the defect without failing anything else here.
    """
    skill = (_AGENTS / "skills" / "opening-a-change" / "SKILL.md").read_text()

    assert "fanning-out-code-review" in _REFERENCE.findall(skill)


def test_the_change_description_skill_does_not_restate_the_template() -> None:
    """The skill says to go read the project's template; it must not carry the
    sections itself.

    A section list copied into the skill is a second home for a fact wfctl
    already ships one copy of, and #50 is that exact duplication drifting
    between two repos. The copy that falls behind does not announce itself, so
    the check is here rather than left to whoever notices the contradiction.
    """
    template = (
        _AGENTS / "configs" / "github" / ".github" / "pull_request_template.md"
    ).read_text()
    # Every heading depth, `# Pull Request` included. The template nests: #174
    # demoted `Before / After` under Summary, and a `## `-only match would have
    # dropped it from this guard on the way past — narrowing the check by
    # exactly the section most likely to be restated. Nothing in the template
    # opens a line with `#` except a heading, so the widest match is also exact.
    headings = {line for line in template.splitlines() if line.startswith("#")}
    skill = (_AGENTS / "skills" / "opening-a-change" / "SKILL.md").read_text().splitlines()
    restated = sorted(h for h in headings if h in skill)

    assert restated == []


def _quoted_after(text: str, slug: str) -> list[str]:
    """The block-quoted lines that follow the first mention of `slug`.

    Scoped to that run rather than every `> ` line in the file, because the
    skill is free to quote something else later and a guard that read those as
    the record's words would fail on a change with nothing wrong with it. A test
    that fails for the wrong reason is one somebody deletes, which costs the
    guard rather than fixing it.
    """
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if slug in line), None)
    if start is None:
        return []
    out: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("> "):
            if line[2:].strip():
                out.append(line[2:].strip())
        elif line.strip() and out:
            break
    return out


def test_a_skill_quoting_an_architecture_record_still_matches_it() -> None:
    """A shipped skill may quote a record; it may not paraphrase one.

    `opening-a-change` Step 1 explains why the review-panel rule is prose rather
    than a check, and the explanation rests on `a-rule-is-expressed-as-a-check`'s
    decision test. Retelling that test in the skill's own words drifted twice on
    #347 — first into "not visible in any artifact the work produces", which is
    false, then into "no artifact a reader can reach", a criterion the record
    does not have. Both readings invert the record's verdict, and both survived
    until a reviewer held the two files side by side.

    So the skill quotes, and this compares the quote against the source. It is
    `test_the_change_description_skill_does_not_restate_the_template` one source
    over: a fact with two homes, where the copy that falls behind does not
    announce itself.

    `docs/architecture/` is not package data, so the record does not ship and a
    consuming repo cannot resolve the slug. That is the second reason the skill
    carries the words rather than a pointer, and the reason this test resolves
    the record from the repository rather than through `files("wfctl")`.
    """
    record = (
        Path(__file__).resolve().parent.parent
        / "docs/architecture/a-rule-is-expressed-as-a-check.md"
    ).read_text(encoding="utf-8")
    skill = (_AGENTS / "skills" / "opening-a-change" / "SKILL.md").read_text()

    quoted = _quoted_after(skill, "a-rule-is-expressed-as-a-check")
    assert quoted, "Step 1 no longer quotes the record; it must quote or say nothing"

    # Re-wrapped to one line before comparing: the skill hard-wraps at 79 columns
    # and the record wraps at its own width, so a faithful quote differs from its
    # source by line breaks alone. Comparing verbatim would fail on reflow and
    # teach the next reader to delete the test.
    flat = " ".join(record.split())
    missing = [q for q in quoted if " ".join(q.split()) not in flat]

    assert missing == [], (
        "opening-a-change quotes lines that are not in "
        f"a-rule-is-expressed-as-a-check.md: {missing}"
    )


def test_no_shipped_digest_is_truncated_by_the_hook_that_reads_it() -> None:
    """A digest over `_DIGEST_MAX_CHARS` loses its last rules to an ellipsis.

    The hook truncates rather than errors, on purpose — in a clone the digest's
    author is whoever wrote the repo. That is right for a digest wfctl did not
    write and wrong for one it ships: the file still reads as an authoritative
    short list, and the rules past the cap are gone from every turn of every
    session with nothing said. Asserted through the real `_digest_text` so a
    change to how it flattens is caught here rather than in a live session.
    """
    from wfctl.cli import _DIGEST_MAX_CHARS, _digest_text

    over = {
        d.parent.name: len(" ".join(d.read_text().split()))
        for d in sorted(_AGENTS.glob("skills/*/digest.md"))
        if _digest_text(d.parent, _AGENTS).endswith("…")
    }
    assert not over, f"truncated at {_DIGEST_MAX_CHARS} chars: {over}"
