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
_LINE = re.compile(
    r"^Derived from \[([^\]]+)\]\((https://\S+)\) \(([^),]+), ([^)]*© *[^)\s][^)]*)\)\.$"
)
# Padding-tolerant: a table reformatted with aligned columns would otherwise
# match no row at all, and an empty `_listed()` reads as "nothing is declared"
# — which passes the direction that matters if a line went missing too.
_ROW = re.compile(r"^\|\s*`([a-z0-9./-]+)`\s*\|\s*`([^`]+)`\s*\|$", re.M)
# The templates' rows are told from the scripts' by their path and nothing else.
# A third "where the notice is" column would be derived data in a hand-kept
# table, free to disagree with the directory it describes — the class of defect
# the `license:` key was (#213).
_TEMPLATE_ROW = "specify/templates/"


def _declared() -> dict[str, dict[str, str]]:
    """Skill name or script path → every fact its own attribution line states.

    A mapping and not a tuple, and every group kept rather than the one a caller
    happens to want. Three findings on this branch were the same defect: the
    pattern required a field, the parser discarded it, and the field could then
    say anything — a wrong holder, a wrong licence, and a link to a repository
    the label did not name all shipped with a green suite. What closes that is
    comparing the whole declaration against the whole notice entry, so a field
    added to `_LINE` later is compared without anyone remembering to write a
    check for it.

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
            found[skill_md.parent.name] = _fields(match)
    for script in sorted(SPECIFY_ROOT.glob("scripts/**/*.sh")):
        lines = script.read_text(encoding="utf-8").splitlines()
        match = _LINE.match(lines[1].removeprefix("# ")) if len(lines) > 1 else None
        if match:
            found[script.relative_to(SPECIFY_ROOT.parent).as_posix()] = _fields(match)
    return found


def _attributed() -> dict[str, str]:
    """Skill name or script path → the upstream the file's own line names."""
    return {name: fields["upstream"] for name, fields in _declared().items()}


def _fields(match: re.Match[str]) -> dict[str, str]:
    """One attribution line's four facts, named and normalised for comparison."""
    upstream, url, licence, holder = match.groups()
    return {"upstream": upstream, "url": url, "licence": licence, "holder": _holder(holder)}


def _holder(statement: str) -> str:
    """A copyright statement reduced to the part that identifies the holder.

    An attribution line writes `© 2025 Jesse Vincent` and a notice writes
    `Copyright (c) 2025 Jesse Vincent` — the marks are interchangeable and carry
    nothing, so comparing the statements whole would fail on every entry that is
    correct. What survives is the year, where upstream states one, and the name.
    """
    return " ".join(re.sub(r"©|Copyright|\(c\)", " ", statement, flags=re.I).split())


def _rows() -> list[tuple[str, str]]:
    """Every (name, upstream) pair in the record's tables, parsed once.

    Both filters below read this rather than the file, so a change to `_ROW`
    cannot move one of them and leave the other matching the old shape.
    """
    return _ROW.findall(RECORD.read_text(encoding="utf-8"))


def _listed() -> dict[str, str]:
    """Skill name or script path → the upstream the record's tables name."""
    return {name: upstream for name, upstream in _rows() if not name.startswith(_TEMPLATE_ROW)}


def _listed_templates() -> dict[str, str]:
    """Template path → the upstream the record's second table names for it."""
    return {name: upstream for name, upstream in _rows() if name.startswith(_TEMPLATE_ROW)}


def _noticed_templates() -> dict[str, str]:
    """Template path → the upstream whose section in the specify notice names it.

    Read off the notice rather than passed in, so a template dropped from the
    notice and left in the record fails rather than being assumed present. The
    notice writes them relative to the specify tree, which is how they read in a
    project's own `.specify/` — the record writes them relative to `wfctl/`.

    Every section is walked rather than `github/spec-kit`'s alone. Hard-coding
    the one upstream this tree happens to have today discards which section a
    path was found under, and a row moved to a different upstream then agrees
    with a notice that never said so.

    A path is read only from above its section's copyright line: the prose below
    it names `templates/github-issue-template.md` in order to say it is *not*
    derived, and a scan of the whole section would read that denial as a claim.
    """
    return dict(_template_claims())


def _template_claims() -> list[tuple[str, str]]:
    """Every (template path, upstream) claim the specify notice makes, in order.

    A list and not a dict, because a path can appear under two headings — while
    it is being moved between upstreams, most plausibly — and collapsing that to
    a mapping keeps whichever came last. The notice then ships attributing one
    file to two owners with every check green, so the duplicate has to survive
    as far as the check that looks for it.
    """
    claims = []
    for section in re.split(r"^## ", SPECIFY_NOTICES.read_text(encoding="utf-8"), flags=re.M)[1:]:
        heading, _, body = section.partition("\n")
        covered = body.split("\n    Copyright", 1)
        if len(covered) == 1:
            continue   # a section with no copyright line claims nothing; `_noticed` fails on it
        for path in re.findall(r"`(templates/[a-z0-9-]+\.md)`", covered[0]):
            claims.append((f"specify/{path}", heading.strip()))
    return claims


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


def _noticed(notice: Path) -> dict[str, dict[str, str]]:
    """Upstream → the same four facts, as that upstream's section in `notice` states them.

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
        link = re.search(r"<(https://\S+?)>", body)
        if holder:
            found[heading.strip()] = {
                "upstream": heading.strip(),
                "url": link.group(1) if link else "",
                "licence": _licence_the_notices_carry(),
                "holder": _holder(holder.group(1)),
            }
    return found


def _licence_the_notices_carry() -> str:
    """The licence whose permission text both notice files reproduce.

    Read off `LICENSE`'s first line rather than pinned here, and load-bearing
    through `test_each_notice_carries_the_permission_text_it_claims_to`: the
    notices reproduce that file's block and nothing else, so it is the only
    licence anything in the wheel grants under. A line naming a different one
    names a licence no notice in its tree carries — and the day a genuinely
    Apache-2.0 upstream is vendored, the notice needs a second permission block
    before its files can declare one.
    """
    return LICENSE.read_text(encoding="utf-8").splitlines()[0].removesuffix(" License")


def _permission_block() -> str:
    """`LICENSE`'s permission notice, indented as a notice file quotes it."""
    body = LICENSE.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(body) if line.startswith("Permission is hereby"))
    return "\n".join(("    " + line).rstrip() for line in body[start:]).rstrip()


def test_no_template_is_claimed_by_two_upstreams_in_the_specify_notice() -> None:
    """A file has one owner, and the notice is the templates' only declaration.

    The three checks around this one all read the notice as a mapping, so a
    template listed under two `##` sections collapsed to whichever came last —
    and where the record named that one, every check passed while the shipped
    file said a template belonged to two projects at once. The half-finished
    move that produces it is the same shape as the half-finished cleanup
    `test_no_file_claims_an_upstream_the_record_does_not_list` exists for."""
    seen: dict[str, list[str]] = {}
    for path, upstream in _template_claims():
        seen.setdefault(path, []).append(upstream)
    duplicated = {path: owners for path, owners in seen.items() if len(owners) > 1}

    assert not duplicated, f"claimed by more than one upstream in {SPECIFY_NOTICES.name}: {duplicated}"


def test_the_specify_notice_and_the_record_name_the_same_upstream() -> None:
    """`test_the_file_and_the_record_name_the_same_upstream` one tree over.

    The two set checks above compare paths, so a template row reassigned to a
    different upstream stayed in both and neither fired — the record and the
    shipped notice disagreed about whose copyright a file carries, silently.
    That is the failure the skills' equivalent exists for, and the templates are
    the population where it matters most: the notice is their only declaration.
    """
    listed, noticed = _listed_templates(), _noticed_templates()
    disagree = {
        path: (noticed[path], listed[path])
        for path in set(listed) & set(noticed)
        if noticed[path] != listed[path]
    }

    assert not disagree, f"notice and record name different upstreams (notice, record): {disagree}"



def test_no_file_is_listed_twice_in_the_record() -> None:
    """`_listed()` is a dict comprehension over the rows, so a file listed under
    two upstreams kept whichever row came last. With the correct row second, the
    record made two contradictory provenance claims and nothing read the first.

    The same defect as the specify notice's duplicate sections, in the other
    declaration — and a row inserted rather than edited is how a half-finished
    move between upstreams leaves it."""
    seen: dict[str, list[str]] = {}
    for name, upstream in _rows():
        seen.setdefault(name, []).append(upstream)
    duplicated = {name: owners for name, owners in seen.items() if len(owners) > 1}

    assert not duplicated, f"listed more than once in vendor-upstream-skills: {duplicated}"



def test_every_attribution_line_agrees_with_its_notice_entry() -> None:
    """The line and the notice state the same four facts; they have to match on
    all four, not on whichever one a check was written for.

    This replaces a check per field, and the reason is three findings of one
    shape on this branch. `_LINE` required an upstream, a URL, a licence and a
    holder; the parser kept one of them, so a file could name the right
    repository at the wrong link, under the wrong licence, owned by the wrong
    person, and stay green until someone wrote a fourth check. Comparing the
    declarations whole means a field added to `_LINE` is compared the day it is
    added — the failure mode was never the individual field, it was that
    verifying one required remembering to."""
    noticed = {NOTICES: _noticed(NOTICES), SPECIFY_NOTICES: _noticed(SPECIFY_NOTICES)}
    disagree = {}
    for name, declared in _declared().items():
        entries = noticed[SPECIFY_NOTICES if name.startswith("specify/") else NOTICES]
        entry = entries.get(declared["upstream"])
        if entry is None:
            continue   # `…has_its_copyright_in_the_same_tree` owns the absent case
        differing = {k: (v, entry[k]) for k, v in declared.items() if v != entry[k]}
        if differing:
            disagree[name] = differing

    assert not disagree, f"file and notice disagree (file, notice): {disagree}"


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
    missing = sorted(set(_listed_templates()) - set(_noticed_templates()))

    assert not missing, (
        f"listed in vendor-upstream-skills but not named in {SPECIFY_NOTICES.name}: {missing}"
    )


def test_the_specify_notice_names_no_template_the_record_does_not_list() -> None:
    """The other direction, which is where this tree differs from the skills: a
    template has no line of its own to drop, so a file that stops being derived
    leaves the notice as the only place still claiming GitHub owns it."""
    unlisted = sorted(set(_noticed_templates()) - set(_listed_templates()))

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
