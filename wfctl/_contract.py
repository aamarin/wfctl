"""The path walker, the bump computation, and the five fixture states behind
the shape check (#423).

Three jobs: what paths a payload emits and at what type (`type_paths`, merged
across several payloads by `merge_type_paths`); what version bump a
difference between two recorded maps owes (`bump`); and the five throwaway
repos FR-013a's comparison needs, each placing `wfctl status --json` in one
condition a clean tree never reaches (`fixture_states`).

Neither of the first two reads or writes `wfctl/contracts/status-payload.json`
— the file is `test_status_contract.py`'s business and `wfctl contract
regenerate`'s. `fixture_states` is why the third job lives here rather than
only in `tests/conftest.py`: `regenerate` needs the same five states the test
compares against, at runtime, in an installed tree with no `tests/` package to
import — FR-014a's "the same union" is only true if both callers build it from
one function.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

# Checked in this order because `isinstance(True, int)` is true in Python and
# JSON has no such conflation — `bool` first is what keeps a boolean field
# from being recorded as `"number"`.
_JSON_TYPE_NAMES: tuple[tuple[type, str], ...] = (
    (bool, "boolean"),
    (int, "number"),
    (float, "number"),
    (str, "string"),
    (dict, "object"),
    (list, "array"),
)


def _json_type(value: object) -> str:
    """The JSON type name for one Python value, in the vocabulary
    data-model.md § Promised shape fixes — never a Python type name, and
    never `Optional[...]` (FR-012c).
    """
    if value is None:
        return "null"
    for py_type, name in _JSON_TYPE_NAMES:
        if isinstance(value, py_type):
            return name
    raise TypeError(f"no JSON type name for {value!r}")


def type_paths(value: object, prefix: str = "") -> dict[str, set[str]]:
    """Every dotted path inside `value`, mapped to the set of JSON type names
    observed there — one payload's own shape, not yet collapsed to a single
    string per path. `merge_type_paths` does that collapse, across as many of
    these as it is given.

    A set rather than a single type even from one call: a list's elements
    share one path (`steps[].reason`), and eight steps in a single payload —
    seven with `reason: null`, one held and reading a string — are eight
    observations of that one path, not seven that overwrite the eighth. A
    dict update in the loop below would keep only the last step's type,
    which happened to make `steps[].reason` read `"null"` even in the
    `blocked` fixture, where `decompose.reason` is very much a string.

    A nested object extends `prefix` with a dot; a list extends it with `[]`
    and walks each element under that same path, so a container is recorded
    beside what is inside it — `steps` is `"array"`, `steps[]` is `"object"` —
    and a list becoming an object is a change the comparison can see
    (data-model.md § Path notation).

    An empty list contributes nothing beneath it. That path still needs some
    payload where the list is non-empty to be recorded at all — silence here
    is correct, not a gap this function should paper over with a guessed type
    (FR-013a's own reason for five fixture states rather than one).
    """
    out: dict[str, set[str]] = {}
    if prefix:
        out[prefix] = {_json_type(value)}
    if isinstance(value, dict):
        for key, sub in value.items():
            child = f"{prefix}.{key}" if prefix else key
            for path, types in type_paths(sub, child).items():
                out.setdefault(path, set()).update(types)
    elif isinstance(value, list):
        child = f"{prefix}[]"
        for item in value:
            for path, types in type_paths(item, child).items():
                out.setdefault(path, set()).update(types)
    return out


def merge_type_paths(*maps: dict[str, set[str]]) -> dict[str, str]:
    """The recorded shape: every path any of `maps` carries, typed as the
    union of every type set seen there — across payloads, and within each one
    (`type_paths`'s own union over a list's elements).

    A single type stays bare. Two or more join with `" | "`, `null` sorted
    last when it is one of them — `"object | null"`, matching the vocabulary
    `quickstart.md` and the shipped file's draft already use, never
    `"null | object"`.
    """
    seen: dict[str, set[str]] = {}
    for m in maps:
        for path, types in m.items():
            seen.setdefault(path, set()).update(types)
    merged: dict[str, str] = {}
    for path, types in seen.items():
        others = sorted(types - {"null"})
        merged[path] = " | ".join((*others, "null") if "null" in types else others)
    return merged


def bump(recorded: dict[str, str], observed: dict[str, str]) -> str | None:
    """What version part a difference between `recorded` (the shipped file's
    `paths`) and `observed` (the live union) owes, or `None` when they agree
    (data-model.md § Version transitions).

    A path recorded but not observed, or observed at a different type than
    recorded, owes major — either is a promise the file made that no longer
    holds. A path observed but not recorded owes minor, and only when nothing
    above already owes major: a rename is an add and a remove in the same
    comparison, and it is one major change, not a major and a minor that
    happen to coincide.
    """
    unemitted = recorded.keys() - observed.keys()
    changed_type = {
        p for p in recorded.keys() & observed.keys() if recorded[p] != observed[p]
    }
    if unemitted or changed_type:
        return "major"
    if observed.keys() - recorded.keys():
        return "minor"
    return None


def apply_bump(version: str, which: str | None) -> str:
    """`version` (`"major.minor"`) with `which` applied — `major` increments
    the major part and resets minor to `0`; `minor` increments the minor
    part; `None` returns `version` unchanged, which is what `--hold-version`
    asks `wfctl contract regenerate` for (FR-014b).
    """
    if which is None:
        return version
    major, _, minor = version.partition(".")
    if which == "major":
        return f"{int(major) + 1}.0"
    return f"{major}.{int(minor) + 1}"


def diff_message(recorded: dict[str, str], observed: dict[str, str]) -> str | None:
    """The failure text FR-014 requires — every offending path named, and
    which part of the version the change owes — or `None` when there is
    nothing to report.
    """
    unrecorded = sorted(observed.keys() - recorded.keys())
    unemitted = sorted(recorded.keys() - observed.keys())
    changed = sorted(
        p for p in recorded.keys() & observed.keys() if recorded[p] != observed[p]
    )
    if not (unrecorded or unemitted or changed):
        return None
    lines = []
    if unemitted:
        lines.append(f"recorded but not emitted (owes a major bump): {unemitted}")
    if changed:
        lines.append(
            "recorded with a different type (owes a major bump): "
            + ", ".join(f"{p}: {recorded[p]} -> {observed[p]}" for p in changed)
        )
    if unrecorded:
        lines.append(f"emitted but not recorded (owes a minor bump): {unrecorded}")
    return "\n".join(lines)


# The branch every fixture repo checks out, explicitly, rather than trusting
# the system's default init branch: `resolve_branch` falls back to git when
# `WFCTL_BRANCH` is unset, and a fixed name is one fewer thing this module
# needs the caller to configure.
FIXTURE_BRANCH = "contract-fixture"


@dataclass(frozen=True)
class FixtureRepo:
    """One throwaway repo built by `fixture_states`, with everywhere a
    `PipelineReport` needs to be built or a `wfctl status --json` subprocess
    needs to be run against it."""

    repo_root: Path
    agent_dir: Path
    spec_dir: Path
    branch: str = FIXTURE_BRANCH


def wfctl_binary() -> str:
    """The console script installed beside this interpreter — `uv run
    wfctl`'s own binary, not whatever is first on `PATH`. One copy shared by
    `wfctl contract regenerate` and the test suite's own live runs, rather
    than the same one-liner re-derived at each call site."""
    import sys

    return str(Path(sys.executable).parent / "wfctl")


def isolated_subprocess_env(**overrides: str) -> dict[str, str]:
    """The invoking shell's environment with every `WFCTL_`-prefixed key
    cleared, then `overrides` set on top — so a developer's own
    `WFCTL_BRANCH`/`WFCTL_SPEC_DIR`/`WFCTL_ARCH_DIR`/`WFCTL_REPO_ROOT`
    (`wfctl/_paths.py`'s override set) never leaks into a throwaway repo's
    `wfctl status` subprocess the way `WFCTL_STATE_DIR` alone once did
    (#423). Stripping the whole prefix closes the class of leak rather than
    the one variable that happened to get caught by flakiness first.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("WFCTL_")}
    env.update(overrides)
    return env


def _init_throwaway_repo(prefix: str, branch: str) -> Path:
    """A fresh git repo under a new temp directory, one commit deep, `branch`
    checked out explicitly — the init sequence every throwaway repo below
    shares, whether or not it goes on to get a `specs/` directory.
    """
    import shutil
    import tempfile

    root = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        for cmd in (
            ["git", "init", "-q", str(root)],
            ["git", "-C", str(root), "config", "user.email", "test@test.com"],
            ["git", "-C", str(root), "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, check=True, capture_output=True)
        (root / "README.md").write_text("x\n")
        subprocess.run(
            ["git", "-C", str(root), "add", "README.md"], check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "commit", "-q", "-m", "init"],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "checkout", "-q", "-b", branch],
            check=True, capture_output=True,
        )
        return root
    except BaseException:
        # A git call failing partway through would otherwise leave this
        # `mkdtemp` directory on disk with nothing pointing at it — the same
        # leak `fixture_states`'s own callers guard against for the repos
        # they finish building, closed here at its actual source instead.
        shutil.rmtree(root, ignore_errors=True)
        raise


def build_fixture_repo(name: str) -> FixtureRepo:
    """A fresh, isolated git repo for one named fixture state — `git init`
    plus the two directories `wfctl` itself needs (`.agent-runs/` for state,
    `specs/contract-fixture/` for the feature).
    """
    root = _init_throwaway_repo(f"contract-fixture-{name}-", FIXTURE_BRANCH)
    agent_dir = root / ".agent-runs"
    agent_dir.mkdir()
    spec_dir = root / "specs" / FIXTURE_BRANCH
    spec_dir.mkdir(parents=True)
    return FixtureRepo(repo_root=root, agent_dir=agent_dir, spec_dir=spec_dir)


def build_live_probe_repo() -> Path:
    """A fresh, isolated git repo with no `specs/` directory at all — the
    sixth source FR-013b's union needs, run as a real `wfctl status --json`
    subprocess against it rather than through `payload_of`'s hand
    transcription.

    Deliberately not the repository `wfctl contract regenerate` is invoked
    in: that repo usually has a feature resolved, so `spec_dir` would never
    read `null` there, and the shipped file would silently narrow every time
    someone ran the command from a repo mid-feature. The live run's actual
    job — proving `payload_of`'s transcription still matches the real dict
    literal — needs no particular repo state, so an isolated one that always
    resolves nothing is the more reproducible choice, and the one the test
    suite's own live run already makes.
    """
    return _init_throwaway_repo("contract-live-", "no-feature")


def _clean_spec() -> str:
    """The smallest `spec.md` that clears both `specify` and `clarify` —
    every section `wfctl` requires, and the `## Clarifications` section
    `clarify` writes on every run including a clean scan. Built from
    `_REQUIRED_SPEC_SECTIONS` rather than typed out, so a change to that list
    moves this fixture with it instead of leaving `specify` reading it
    `in_progress` for a reason nothing here explains.
    """
    from wfctl._evidence import _REQUIRED_SPEC_SECTIONS

    sections = "".join(
        f"## {name} _(mandatory)_\n\nPlaceholder.\n\n" for name in _REQUIRED_SPEC_SECTIONS
    )
    return (
        "# Spec\n\nClean.\n\n" + sections
        + "## Clarifications\n\n### Session 2026-08-25\n\n"
        "- No critical ambiguities detected.\n"
    )


def _clean_plan() -> str:
    """The smallest `plan.md` that clears `plan` — every section `wfctl`
    requires, built from `_REQUIRED_PLAN_SECTIONS` for the same reason
    `_clean_spec` builds from its own list."""
    from wfctl._evidence import _REQUIRED_PLAN_SECTIONS

    sections = "".join(f"## {name}\n\nPlaceholder.\n\n" for name in _REQUIRED_PLAN_SECTIONS)
    return "# Plan\n\n" + sections


# Relative to `spec_dir`, in pipeline order — `stage_upstream_of` walks a
# prefix of this so a fixture staged "through tasks" carries every artifact a
# step upstream of it needs to be *reachable*, not only the one it is about
# (`_infer_steps` cascades on the first missing one).
_FIXTURE_ARTIFACTS: tuple[tuple[str, str], ...] = (
    ("brainstorm", "design.md"),
    ("specify", "spec.md"),
    ("plan", "plan.md"),
    ("analyze", "checklists/analysis-report.md"),
    ("decompose", "delivery.md"),
    ("tasks", "tasks.md"),
)


def stage_upstream_of(env: FixtureRepo, step: str, tasks: str = "- [x] T001 done\n") -> None:
    """Write every artifact upstream of `step`, inclusive — `tests/conftest.py`'s
    `storyctl_dir.stage_upstream_of`, rebuilt here so `fixture_states` needs no
    import from `tests/` (production code cannot reach a package the wheel
    does not ship).
    """
    names = [name for name, _ in _FIXTURE_ARTIFACTS]
    for name, rel in _FIXTURE_ARTIFACTS[: names.index(step) + 1]:
        path = env.spec_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if name == "specify":
            path.write_text(_clean_spec())
        elif name == "plan":
            path.write_text(_clean_plan())
        elif name == "tasks":
            path.write_text(tasks)
        else:
            path.write_text("x\n")


def fixture_states() -> dict[str, FixtureRepo]:
    """The five throwaway repos FR-013a's comparison needs — nothing
    outstanding, a standing block, an outstanding manual pass, a stall, and a
    step carrying declared passes (research.md § 3) — each isolated from the
    other four and from whatever repo the caller is actually running in.

    `manual` declares on `decompose` rather than `brainstorm`: `brainstorm`
    carries its own built-in `architecture`/`design-doc` passes, and a
    fixture staged only through `specify` or later satisfies `architecture`
    by the `spec.md` escape in `_architecture_answered` — but a fixture that
    stopped *before* `specify` would leave it genuinely outstanding and reach
    the wrong pass first in the cascade. `nested` stops before `specify` for
    the opposite reason: it is the one state that wants `architecture`
    genuinely outstanding, so that its own annotation — the one place a
    sub-step's `annotation` is ever a real sentence rather than `null` — is
    reachable at all.
    """
    import shutil

    from wfctl._paths import STEP_CLAIMS_DIR, arch_root
    from wfctl._session import record_blocked
    from wfctl._stall import digest

    states: dict[str, FixtureRepo] = {}
    try:
        # Staged the whole way through, nothing declared beyond the built-ins —
        # a finished story, the one state where `current`/`next_command`/`auto`
        # reach their `null` arm; every other state below is forced mid-pipeline
        # by a block or an outstanding pass.
        quiet = build_fixture_repo("quiet")
        states["quiet"] = quiet
        stage_upstream_of(quiet, "tasks")

        blocked = build_fixture_repo("blocked")
        states["blocked"] = blocked
        stage_upstream_of(blocked, "tasks")
        record_blocked(
            blocked.agent_dir, blocked.branch, "issue-comment", "org policy", "decompose",
        )

        manual = build_fixture_repo("manual")
        states["manual"] = manual
        stage_upstream_of(manual, "tasks")
        (manual.repo_root / "wfctl.json").write_text(json.dumps({
            "steps": {"decompose": [{"name": "review", "manual": True, "evidence": "ghost.md"}]},
        }))

        stalled = build_fixture_repo("stalled")
        states["stalled"] = stalled
        stage_upstream_of(stalled, "tasks", tasks="- [ ] T001 open\n")
        # Four identical `resume` observations, hand-written rather than run
        # through the CLI: `fixture_states` builds outside any command's own
        # session, with no session log to append a real one to yet. `find_stall`
        # needs `passes >= STALL_AFTER (3)`, which is `observations - 1`.
        from wfctl._evidence import build_evidence

        mark = digest(build_evidence(stalled.spec_dir, stalled.repo_root))
        events = "\n".join(
            json.dumps({
                "ts": "2026-01-01T00:00:00Z", "event": "resume",
                "step": "implement", "digest": mark,
            })
            for _ in range(4)
        ) + "\n"
        (stalled.agent_dir / "events.jsonl").write_text(events)

        nested = build_fixture_repo("nested")
        states["nested"] = nested
        stage_upstream_of(nested, "brainstorm")
        (nested.repo_root / "wfctl.json").write_text(json.dumps({
            "steps": {"decompose": [{"name": "sign-off", "manual": True, "evidence": "never.md"}]},
        }))
        claim = (
            arch_root(nested.repo_root) / STEP_CLAIMS_DIR / FIXTURE_BRANCH
            / "decompose.sign-off.md"
        )
        claim.parent.mkdir(parents=True, exist_ok=True)
        claim.write_text(
            f"# decompose.sign-off does not apply — {FIXTURE_BRANCH}\n\n"
            "not needed for this change\n",
        )

        return states
    except BaseException:
        # A git subprocess failing partway through (disk full, a future
        # fixture step raising) would otherwise leak every repo already built
        # before the one that failed — `contract_regenerate_cmd`'s own
        # `finally` can only clean up what this function actually returns.
        for repo in states.values():
            shutil.rmtree(repo.repo_root, ignore_errors=True)
        raise
