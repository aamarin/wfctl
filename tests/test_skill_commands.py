"""A shell command a shipped skill tells the agent to run does what its prose says.

Every other test here checks that skills ship, cross-reference, and declare the
right frontmatter — all properties of the file. This one runs what is inside it.

The lookup in `opening-a-change` was wrong twice before it was tested. First it
was an `ls` over a path list containing globs, which under `zsh` aborts the whole
command line when one glob matches nothing and reports *no template* in a repo
that has one. Then it matched `-iname` against basenames, which finds the
`PULL_REQUEST_TEMPLATE/` directory and none of the files inside it. Both failures
are silent and both end the same way: the agent takes the fallback shape and the
project's template goes unread, which is the failure #124 exists to prevent.
"""
import re
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path

_SKILL = (
    Path(str(files("wfctl"))) / "agents" / "skills" / "opening-a-change" / "SKILL.md"
)

# The one fenced block that finds templates. Keyed on the content rather than on
# "the first bash fence": Step 4's `gh pr create` is also a bash fence, and an
# edit reordering the sections must not silently retarget this test.
_FENCE = re.compile(r"```bash\n(.*?)```", re.DOTALL)


def _lookup_command() -> str:
    blocks = [b for b in _FENCE.findall(_SKILL.read_text()) if "template" in b]
    assert len(blocks) == 1, f"expected one template-lookup fence, found {len(blocks)}"
    return blocks[0]


def _fixture(root: Path) -> None:
    """The three layouts a real repo uses, plus a decoy inside `.git`."""
    for rel in (
        ".github/PULL_REQUEST_TEMPLATE/bug.md",
        ".github/PULL_REQUEST_TEMPLATE/feature.md",
        ".gitlab/merge_request_templates/Default.md",
        ".git/objects/ab/pull_request_template.md",
    ):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# t\n")


def _run(shell: str, root: Path) -> list[str]:
    out = subprocess.run(
        [shell, "-c", _lookup_command()], cwd=root, capture_output=True, text=True
    )
    return sorted(line for line in out.stdout.splitlines() if line)


def test_the_lookup_finds_multi_template_directories(tmp_path: Path) -> None:
    """The skill's own prose tells the agent to ask which template applies when a
    repo has a `PULL_REQUEST_TEMPLATE/` directory. A lookup that cannot see into
    that directory makes the instruction unreachable and reports no template at
    all — the command and the prose have to agree."""
    _fixture(tmp_path)

    assert _run("sh", tmp_path) == [
        "./.github/PULL_REQUEST_TEMPLATE/bug.md",
        "./.github/PULL_REQUEST_TEMPLATE/feature.md",
        "./.gitlab/merge_request_templates/Default.md",
    ]


def test_the_lookup_finds_a_single_template_and_ignores_git(tmp_path: Path) -> None:
    """The common case, and the pruning that keeps a blob in the object store from
    being offered as the project's template."""
    _fixture(tmp_path)
    (tmp_path / ".github" / "pull_request_template.md").write_text("# t\n")

    found = _run("sh", tmp_path)

    assert "./.github/pull_request_template.md" in found
    assert not [f for f in found if ".git/" in f]


def test_the_lookup_survives_zsh(tmp_path: Path) -> None:
    """zsh aborts a command line when a glob matches nothing, which is how the
    first version of this lookup failed. Skipped where zsh is absent — CI runs
    Ubuntu — so this is the macOS half of the guarantee, and `sh` above is the
    half that always runs."""
    if not shutil.which("zsh"):
        return
    _fixture(tmp_path)

    assert _run("zsh", tmp_path) == _run("sh", tmp_path)
