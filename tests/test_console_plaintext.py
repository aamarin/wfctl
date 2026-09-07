"""Console output reaches assertions unstyled, wherever the suite runs.

`conftest.py` pins two environment variables for this, and the second one reads
as redundant next to the first until it is gone. These tests keep the reason
attached to it.
"""

from __future__ import annotations

import io
import os

from rich.console import Console


def test_no_color_leaves_bold_and_dim_escapes_behind() -> None:
    """The gap that made `NO_COLOR` alone insufficient.

    Rich reads NO_COLOR as being about color, which is what it says on the tin:
    the green `✓` goes away and the `[bold]` and `[dim]` markup does not. Every
    one of the 30 tests that failed on a machine exporting FORCE_COLOR=3
    asserted on a line styled one of those two ways — a `#418  418-storyctl`
    header, a `────` rule, a dim `(no spec dir found)`.

    Constructed with an explicit `force_terminal` rather than read from the
    environment, so this records the mechanism on every machine including the
    ones where the bug never reproduced.
    """
    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, no_color=True, highlight=False)
    console.print("[bold]header[/bold] [dim]detail[/dim] [green]check[/green]")
    out = buf.getvalue()

    assert "\x1b[1m" in out, "bold survived NO_COLOR — that is the premise here"
    assert "\x1b[2m" in out, "dim survived NO_COLOR — that is the premise here"
    assert "\x1b[32m" not in out, "green did not survive; NO_COLOR covers color"


def test_force_color_is_unset_for_the_whole_suite() -> None:
    """Fails the moment `conftest.py` stops popping FORCE_COLOR.

    Only on a machine that exports it — Claude Code does, some CI images do,
    some shell profiles do. That is the machine the assertion is for; where the
    variable was never set there is nothing to catch and this costs nothing.

    Deliberately not asserting through a Console: by the time a test body runs,
    `wfctl.cli` has already built its module-scope Console and resolved the
    color system, so the variable is the only thing left to observe.
    """
    assert "FORCE_COLOR" not in os.environ
