"""Nothing wfctl ships tells an author to write the review panel into a change
description.

The panel still runs before every change opens; its table goes to the person in
the conversation. What went wrong was the text around it. On MarinVentures/pfms#680
the description took a row per review round until it held 15, 12 of them
already applied, and on #511 an agent following the digest to the letter put
findings back into the body after the maintainer had asked for none (#472). Each
test here is one of the two routes that did it.
"""
import re
from importlib.resources import files
from pathlib import Path

# Through `files("wfctl")` for the reason `test_opening_a_change_panel` gives:
# conftest repoints `_bundle.BUNDLE_ROOT` at a fake tree, and what ships is the
# question here.
_AGENTS = Path(str(files("wfctl"))) / "agents"
_TEMPLATE = _AGENTS / "configs" / "github" / ".github" / "pull_request_template.md"
_DIGEST = _AGENTS / "skills" / "opening-a-change" / "digest.md"

_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def test_the_shipped_template_leaves_no_mention_of_the_panel_in_a_body() -> None:
    """A comment block is deleted before the body is submitted, so it may say
    what it likes. Everything outside one reaches the reader, and the checklist
    item this replaced ("A review panel ran over this diff ...") was the status
    line the maintainer asked to be rid of, shipped as a box to tick.

    "review panel" rather than "panel", so a template that later documents an
    admin panel does not fail here for a reason unrelated to the review. Every
    wording that has reached a body so far, the checklist item and the legacy
    `## Review Panel` heading, carries the full phrase."""
    body = _COMMENT.sub("", _TEMPLATE.read_text()).lower()
    assert "review panel" not in body


def test_the_digest_sends_the_panel_output_nowhere_near_the_description() -> None:
    """The digest arrives every turn under "these break first", so an agent
    obeys it before it reads SKILL.md. Its old rule 1 sent every unapplied
    finding to Additional Context, and fixing SKILL.md alone left the agent on
    #511 doing exactly that."""
    digest = _DIGEST.read_text()
    assert "Additional Context" not in digest
    assert "None of its output goes in the description" in digest
