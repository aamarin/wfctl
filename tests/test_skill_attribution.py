"""A file taken from another project says so, and the record agrees.

Six superpowers-derived skills shipped in the wheel from v0.15.0 to v0.17.0 with
no copyright notice (#213), because the only thing recording provenance was a
table in `vendor-upstream-skills` maintained by hand, keyed on a `license:`
frontmatter key six of the seven do not carry. Nothing could report the table
was wrong.

The checks below are a pair on purpose. The notice has to be in the file,
because `MANIFEST.in` grafts `wfctl/agents` and `wfctl/specify` into the wheel
and that is the artifact the obligation attaches to; the list has to be in the
record, because that is where a reader looks for which files the project does
not own. Either one alone goes stale the way the table did.

The pair runs twice, over two populations that declare themselves differently.
Skills and shell scripts carry the line. The six spec-kit templates cannot: a
template is `cp`'d to become a project's own `spec.md`, so a line in one would
travel into documents GitHub had no hand in (#216). Their declaration is
`wfctl/specify/templates/NOTICES.md` naming them, and the second pair holds that
file and the record's rows together the way the first holds the line and the row.

What neither pair can do is notice #213 itself. A file arriving with no line
*and* no row is invisible to both directions — the checks keep two declarations
honest with each other, and neither is a declaration the arriving file has to
make. Finding an undeclared one is still a diff against upstream, done by hand.
"""
from __future__ import annotations

import re
from pathlib import Path

import wfctl
from wfctl import cli

# Resolved from the installed package for the same reason as
# `test_skill_frontmatter`: conftest's autouse `bundle` fixture repoints
# `_bundle.BUNDLE_ROOT` at a fixture tree, and this is about what wfctl ships.
SKILLS_ROOT = Path(wfctl.__file__).parent / "agents" / "skills"
SPECIFY_ROOT = Path(wfctl.__file__).parent / "specify"
REPO = Path(__file__).resolve().parent.parent
RECORD = REPO / "docs" / "architecture" / "vendor-upstream-skills.md"
LICENSE = REPO / "LICENSE"
NOTICES = SKILLS_ROOT.parent / "NOTICES.md"
# The specify tree's notice sits in `templates/` rather than at its root because
# that is the deepest directory `install-skills` mirrors into a project — see
# `vendor-upstream-skills`. A check that looked for it one level up would pass
# against a file no consumer repo ever receives.
SPECIFY_NOTICES = SPECIFY_ROOT / "templates" / "NOTICES.md"

# The licence and the `©` are both in the pattern rather than checked afterwards:
# a line naming a source but no copyright holder is not the notice MIT asks for,
# and one naming neither licence nor holder is not what the record says the line
# carries. A half-written line has to fail as an absent one, not pass as a whole.
_LINE = re.compile(r"^Derived from \[([^\]]+)\]\(https://\S+\) \(([^),]+), [^)]*© *[^)\s][^)]*\)\.$")
# Padding-tolerant: a table reformatted with aligned columns would otherwise
# match no row at all, and an empty `_listed()` reads as "nothing is declared"
# — which passes the direction that matters if a line went missing too.
_ROW = re.compile(r"^\|\s*`([a-z0-9./-]+)`\s*\|\s*`([^`]+)`\s*\|$", re.M)
# The templates' rows are told from the scripts' by their path and nothing else.
# A third "where the notice is" column would be derived data in a hand-kept
# table, free to disagree with the directory it describes — the class of defect
# the `license:` key was (#213).
_TEMPLATE_ROW = "specify/templates/"


def _attributed() -> dict[str, str]:
    """Skill name or script path → the upstream the file's own line names.

    Two positions, because two conventions. A `SKILL.md` ends with the line, and
    matching only the last line is what stops a skill that merely *discusses*
    attribution from counting as attributed. A shell script carries it on the
    line after the shebang, where a reader of a script actually looks; matching
    that one line rather than searching the body holds the same rule.
    """
    found = {}
    for skill_md in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8").rstrip()
        match = _LINE.match(text.rsplit("\n", 1)[-1])
        if match:
            found[skill_md.parent.name] = match.group(1)
    for script in sorted(SPECIFY_ROOT.glob("scripts/**/*.sh")):
        lines = script.read_text(encoding="utf-8").splitlines()
        match = _LINE.match(lines[1].removeprefix("# ")) if len(lines) > 1 else None
        if match:
            found[script.relative_to(SPECIFY_ROOT.parent).as_posix()] = match.group(1)
    return found


def _rows() -> list[tuple[str, str]]:
    """Every (name, upstream) pair in the record's tables, parsed once.

    Both filters below read this rather than the file, so a change to `_ROW`
    cannot move one of them and leave the other matching the old shape.
    """
    return _ROW.findall(RECORD.read_text(encoding="utf-8"))


def _listed() -> dict[str, str]:
    """Skill name or script path → the upstream the record's tables name."""
    return {name: upstream for name, upstream in _rows() if not name.startswith(_TEMPLATE_ROW)}


def _listed_templates() -> set[str]:
    """The template paths the record's second table names."""
    return {name for name, _ in _rows() if name.startswith(_TEMPLATE_ROW)}


def _noticed_templates() -> set[str]:
    """The template paths `wfctl/specify/templates/NOTICES.md` names.

    Read off the notice rather than passed in, so a template dropped from the
    notice and left in the record fails rather than being assumed present. The
    notice writes them relative to the specify tree, which is how they read in a
    project's own `.specify/` — the record writes them relative to `wfctl/`.
    """
    text = SPECIFY_NOTICES.read_text(encoding="utf-8")
    # Only the upstream's own section counts. The prose below the copyright line
    # names `templates/github-issue-template.md` in order to say it is *not*
    # derived, and a whole-file scan would read that mention as a claim.
    _, heading, rest = text.partition("## github/spec-kit")
    if not heading:
        return set()   # no section is no claim, and the record's rows then have nothing to meet
    return {
        f"specify/{path}"
        for path in re.findall(r"`(templates/[a-z0-9-]+\.md)`", rest.split("\n    Copyright", 1)[0])
    }


def test_every_file_the_record_lists_carries_its_attribution_line() -> None:
    """The direction that catches a notice dropped by an edit or an upstream
    re-pull — the file ships without it and only the record still says the
    project does not own that file."""
    missing = sorted(set(_listed()) - set(_attributed()))

    assert not missing, f"listed in vendor-upstream-skills but carry no attribution line: {missing}"


def test_no_file_claims_an_upstream_the_record_does_not_list() -> None:
    """The direction a half-finished cleanup takes: a file that has genuinely
    become the project's own drops its line and its row together, never one, and
    a line added without the row is a provenance claim the record contradicts."""
    unlisted = sorted(set(_attributed()) - set(_listed()))

    assert not unlisted, f"carry an attribution line but vendor-upstream-skills does not list them: {unlisted}"


def test_the_file_and_the_record_name_the_same_upstream() -> None:
    """Two homes for one fact only stay honest while they agree. `i-have-adhd`
    is why this is not folded into the checks above: the record named it without
    naming `ayghri/i-have-adhd`, so it was listed, it carried a line, and the
    record was still wrong about where it came from."""
    attributed, listed = _attributed(), _listed()
    disagree = {
        name: (attributed[name], listed[name])
        for name in set(attributed) & set(listed)
        if attributed[name] != listed[name]
    }

    assert not disagree, f"file and record name different upstreams (file, record): {disagree}"


def _noticed(notice: Path) -> dict[str, str]:
    """Upstream → the copyright line that upstream's section in `notice` carries.

    Sectioned on the `## <upstream>` heading and read down to the next one,
    rather than searched for the upstream's name anywhere in the file. The name
    is *also* in the section's own URL, so a whole-file search reports an
    upstream as noticed when its heading and link survive an edit that deleted
    the copyright line beneath them — which is the one line the section exists
    to carry. Proven by mutation: deleting `Copyright GitHub, Inc.` from
    `wfctl/agents/NOTICES.md` passed every check this file had.
    """
    found = {}
    for section in re.split(r"^## ", notice.read_text(encoding="utf-8"), flags=re.M)[1:]:
        heading, _, body = section.partition("\n")
        holder = re.search(r"^ {4}(Copyright .+)$", body, re.M)
        if holder:
            found[heading.strip()] = holder.group(1)
    return found


def _permission_block() -> str:
    """`LICENSE`'s permission notice, indented as a notice file quotes it."""
    body = LICENSE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(body) if line.startswith("Permission is hereby"))
    return "\n".join(("    " + line).rstrip() for line in body[start:]).rstrip()


def test_every_upstream_named_in_a_file_has_its_copyright_in_the_same_tree() -> None:
    """The line names a licence; `NOTICES.md` is the licence.

    `MANIFEST.in` grafts `wfctl/agents` and `wfctl/specify` as two separate
    trees, so each carries its own notice and the text travels in the wheel with
    the files it covers — the thing a root-level notice does not do (#213).
    Checked per tree rather than against both texts joined: `github/spec-kit` is
    named in each, and a union would let one tree ship derived files whose
    licence is only in the other."""
    noticed = {NOTICES: _noticed(NOTICES), SPECIFY_NOTICES: _noticed(SPECIFY_NOTICES)}
    missing = sorted(
        f"{name} → {repo}"
        for name, repo in _attributed().items()
        if repo not in noticed[SPECIFY_NOTICES if name.startswith("specify/") else NOTICES]
    )

    assert not missing, f"attributed upstreams with no copyright line in their tree's NOTICES.md: {missing}"


def test_each_notice_carries_the_permission_text_it_claims_to() -> None:
    """MIT asks for the permission notice and not only the copyright line, and
    both files say in their own prose that they reproduce it byte-for-byte from
    `LICENSE`. Nothing held them to that: a notice could lose the whole block
    and every other check here still passed. Compared against `LICENSE` rather
    than against a copy pinned here, because generating it from `LICENSE` is
    what the record requires — #213's hand-typed draft corrupted the warranty
    sentence, and a notice that is subtly wrong looks discharged."""
    permission = _permission_block()
    missing = sorted(
        notice.name for notice in (NOTICES, SPECIFY_NOTICES)
        if permission not in notice.read_text(encoding="utf-8")
    )

    assert not missing, f"notice files not carrying LICENSE's permission text verbatim: {missing}"


def test_every_template_the_record_lists_is_named_in_the_specify_notice() -> None:
    """The templates' stand-in for an attribution line, checked in the direction
    a rename breaks: the record still lists the file, and the notice that is the
    only thing shipping its provenance no longer names it."""
    missing = sorted(_listed_templates() - _noticed_templates())

    assert not missing, (
        f"listed in vendor-upstream-skills but not named in {SPECIFY_NOTICES.name}: {missing}"
    )


def test_the_specify_notice_names_no_template_the_record_does_not_list() -> None:
    """The other direction, which is where this tree differs from the skills: a
    template has no line of its own to drop, so a file that stops being derived
    leaves the notice as the only place still claiming GitHub owns it."""
    unlisted = sorted(_noticed_templates() - _listed_templates())

    assert not unlisted, (
        f"named in {SPECIFY_NOTICES.name} but vendor-upstream-skills does not list them: {unlisted}"
    )


def test_every_template_the_record_lists_is_a_file_that_ships() -> None:
    """The templates are the one population whose declarations are both
    documents. A skill or a script that is deleted or renamed drops out of
    `_attributed()` and the record's row fails immediately; a template has no
    line of its own to lose, so the record and the shipped notice would go on
    asserting GitHub's copyright over a path that is no longer in the tree, with
    every other check here green."""
    missing = sorted(p for p in _listed_templates() if not (SPECIFY_ROOT.parent / p).exists())

    assert not missing, f"listed in vendor-upstream-skills but not in the tree: {missing}"


def test_the_specify_notice_is_where_install_skills_will_carry_it() -> None:
    """`wfctl/agents/NOTICES.md` ships in the wheel and stops there — a top-level
    file in a grafted tree belongs to no install layer (#213). The specify tree's
    copy is inside `templates/` so it makes the trip the templates make.

    That only holds while `templates/` is still mirrored, which is why the
    install target is asserted and not just the path: narrow `_RUNTIME_TARGETS`
    to a list of named templates, or drop the entry, and the notice quietly
    stops reaching any project while a check on two paths stays green."""
    assert SPECIFY_NOTICES.exists(), f"{SPECIFY_NOTICES} is missing"
    assert not (SPECIFY_ROOT / "NOTICES.md").exists(), (
        "a notice at the top of wfctl/specify/ ships in the wheel and reaches no project; "
        "install-skills mirrors specify/scripts and specify/templates and nothing above them"
    )
    assert ("specify/templates", ".specify/templates") in cli._RUNTIME_TARGETS, (
        "the notice's placement depends on this directory being mirrored whole; "
        f"_RUNTIME_TARGETS is now {cli._RUNTIME_TARGETS}"
    )
