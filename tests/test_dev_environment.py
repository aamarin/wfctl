"""The three commands in AGENTS.md resolve their tools from `uv.lock`.

`uv run` falls back to PATH when a command is missing from the project
environment, and it installs a `dev` dependency group by default while never
installing an extra. With the tools declared only as an extra, a cold venv ran
whatever the machine happened to have: mypy was absent and errored, pytest and
ruff were present and reported a pass from unpinned copies (#105). The group is
what closes that, and the two `dev` keys read as a duplicate to anyone who did
not hit it — so the invariant is pinned here rather than left to the comment.

Shape only. Whether the group still *resolves* is uv's behaviour, not this
file's, and it is CI's bare `uv sync` that covers it.
"""

import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def test_the_dev_group_defers_to_the_extra_rather_than_copying_it() -> None:
    """Both halves are load-bearing, and each fails a different way.

    Without the group, `uv run` resolves the tools against PATH again. With a
    second literal copy of the requirement list, it resolves them correctly and
    then drifts from the extra that `pip install -e ".[dev]"` installs from.
    """
    with PYPROJECT.open("rb") as fh:
        config = tomllib.load(fh)

    name = config["project"]["name"]
    assert config["dependency-groups"]["dev"] == [f"{name}[dev]"]
    assert config["project"]["optional-dependencies"]["dev"]
