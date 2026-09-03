"""The three commands in AGENTS.md resolve their tools from `uv.lock`.

`uv run` falls back to PATH when a command is missing from the project
environment, and it installs a `dev` dependency group by default while never
installing an extra. With the tools declared only as an extra, a cold venv ran
whatever the machine happened to have: mypy was absent and errored, pytest and
ruff were present and reported a pass from unpinned copies (#105). The group is
what closes that, and the two `dev` keys read as a duplicate to anyone who did
not hit it — so the invariant is pinned here rather than left to the comment.
"""

import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _config() -> dict:
    with PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)


def test_the_dev_tools_are_reachable_without_a_flag() -> None:
    """Deleting the group restores the silent PATH fallback the extra caused."""
    config = _config()
    assert config["dependency-groups"]["dev"], "no default group installs the dev tools"


def test_the_group_defers_to_the_extra_rather_than_copying_it() -> None:
    """Two literal lists drift, and `pip install -e ".[dev]"` reads only the extra."""
    config = _config()
    name = config["project"]["name"]
    assert config["dependency-groups"]["dev"] == [f"{name}[dev]"]
    assert config["project"]["optional-dependencies"]["dev"]
