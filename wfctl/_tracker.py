"""Issue-tracker dispatch — run the active backend's command for a verb.

The active backend is named by the ``tracker`` key in ``.wf-skills-manifest.json``
and defined by ``.agents/trackers/<name>.json``, a map of verb -> argv template.
The supported-verb set IS the map's keys, so a backend cannot misdeclare its
capabilities. Substitution builds argv *tokens* (never a shell string), so a
``{comment}`` containing ``$(...)`` or quotes is inert.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from rich.console import Console

from wfctl._io import append_event
from wfctl._manifest import load_manifest

# highlight=False: don't let rich wrap quoted tokens (issue ids, verb names) in
# ANSI — this output is parsed by agents, so keep it plain.
console = Console(highlight=False)

_PLACEHOLDER = re.compile(r"\{(\w+)\}")

# The verb contract: verb -> the placeholders its argv may use. The key set here
# IS the set of valid verbs; a config using anything else is rejected. Kept in
# sync with the scaffold-tracker skill's table. `{me}` (from `identity`) is
# allowed in any verb, so it isn't listed per-verb.
ALLOWED = {
    "list": set(), "view": {"id"}, "close": {"id", "comment"},
    "comment": {"id", "body"}, "create": {"title", "body"},
    "label": {"id", "action", "label"},
    # `labels` reads what `label` writes, and is separate because reading is the
    # half a backend can decline. A tracker with no way to list an issue's labels
    # leaves it out; the caller falls back to the surface that needs no tracker
    # at all rather than guessing from whatever `view` happened to print.
    "labels": {"id"},
    # `start`/`stop` say when work on an issue began and stopped; what a backend
    # does with that is its own business. A tracker with a board moves a column,
    # one without it declines the verb and the caller carries on — which is why
    # the pair is named for the event rather than for the column, and why
    # neither takes a status to write.
    "start": {"id"}, "stop": {"id"},
}
# The `changes` section (PRs / patchsets) supports a smaller verb set.
ALLOWED_CHANGES = {"list": set(), "view": {"id"}}


# The verbs that tell someone outside the repo, from the middle row of
# `wfctl-classes-the-action-not-the-command`. Each of these reaches people who
# are notified, and deleting the result later does not un-notify them.
#
# `close` is not here, and its absence is the decision rather than an omission.
# Closing an issue is the irreversible row, which no grant reaches — so gating it
# on the grant would be the wrong shape twice over: it would refuse the human who
# is the only one allowed to do it, and wfctl cannot tell a human from an agent
# anyway (`approval-mode-is-stored-intent`). What keeps that row safe is that
# nothing here ever consults a grant for it.
#
# `start` and `stop` move a board column, which the spec assumes reaches nobody.
# That assumption is recorded as unverified: if a column move does notify, these
# two belong here and every worktree creation has been taking a notifying action
# unprompted.
_NOTIFYING_VERBS = {"comment", "create", "label"}


def _refuse_notifying(agent_dir: Path, verb: str) -> int | None:
    """Refuse a notifying verb the run was never granted, or None to proceed.

    The two skills that take these actions already gate on the same answer in
    prose, and this is the same rule expressed where it cannot be skipped
    (`a-rule-is-expressed-as-a-check`): a violation shows up in an artifact the
    work produces — the tracker changed — so the rule is a check rather than a
    comment. An agent that never reads the skill still cannot comment, label or
    open an issue on a feature nobody granted.

    Reads the answer the run resolved at `wfctl start`; it asks the tracker
    nothing, so putting it in front of every write costs no round-trip.

    Exit 1 rather than the 0 that a missing backend returns. That 0 means
    "nothing was configured to do this", and a session must not fail for it. This
    is the opposite fact — something was configured, and the run may not use it —
    and a caller that reads a refusal as a completed write would report the
    tracker updated when it was not.
    """
    from wfctl._session import resolved_notify

    grant = resolved_notify(agent_dir)
    if grant.granted:
        return None
    # Three short lines rather than two long ones: rich wraps at the terminal
    # width, and a remedy split across a wrap arrives as a fragment. The first
    # draft ran to 84 characters and broke mid-sentence in a real terminal.
    console.print(
        f"[yellow]⚠[/yellow] '{verb}' would tell people outside this repo, "
        "and nobody allowed it"
    )
    console.print(
        "  Allow it: [bold]wfctl start --allow-notify[/bold], "
        "or the [bold]authority:notify[/bold] label"
    )
    console.print(f"  Refused because: {grant.source}")
    return 1


def _check_section(label: str, verbs: dict, allowed: dict, errs: list[str]) -> bool:
    """Validate one verb map; append problems to errs. Returns whether it uses {me}."""
    uses_me = False
    for verb, argv in verbs.items():
        if verb not in allowed:
            errs.append(f"{label} '{verb}': unknown verb (allowed: {sorted(allowed)})")
            continue
        if not isinstance(argv, list) or not argv or not all(isinstance(t, str) for t in argv):
            errs.append(f"{label} '{verb}': must be a non-empty list of strings")
            continue
        used = {m for tok in argv for m in _PLACEHOLDER.findall(tok)}
        uses_me |= "me" in used
        bad = used - allowed[verb] - {"me"}  # {me} is allowed everywhere
        if bad:
            errs.append(
                f"{label} '{verb}': placeholder(s) {sorted(bad)} not allowed "
                f"(allowed: {sorted(allowed[verb] | {'me'})})"
            )
    return uses_me


def validate_config(config: object) -> list[str]:
    """Return a list of problems with a tracker config; empty list means valid.

    A malformed config doesn't crash ``wfctl issue`` — the loader treats it as
    "no config" and every verb silently no-ops. This surfaces the problems
    instead. Checks what the /scaffold-tracker skill documents: a top-level
    JSON object, a non-empty ``verbs`` map, an optional ``changes`` map, known
    verb names, argv as non-empty string lists, only allowed placeholders
    (``{me}`` allowed everywhere), a compilable ``key_pattern``, and that
    ``{me}`` is only used when ``identity`` is set.
    """
    if not isinstance(config, dict):
        # Every "fix it with tracker-check" message leads here, so the one
        # document shape that reaches this function without being a mapping has
        # to come back as a finding rather than an AttributeError.
        return ["config must be a JSON object"]

    errs: list[str] = []
    kp = config.get("key_pattern")
    if kp is not None:
        if not isinstance(kp, str):
            errs.append("key_pattern must be a string")
        else:
            try:
                re.compile(kp)
            except re.error as e:
                errs.append(f"key_pattern is not a valid regex: {e}")

    identity = config.get("identity")
    if identity is not None and not isinstance(identity, str):
        errs.append("identity must be a string")

    uses_me = False
    verbs = config.get("verbs")
    if not isinstance(verbs, dict) or not verbs:
        errs.append("missing non-empty 'verbs' object")
    else:
        uses_me |= _check_section("verbs", verbs, ALLOWED, errs)

    changes = config.get("changes")
    if changes is not None:
        if not isinstance(changes, dict) or not changes:
            errs.append("'changes' must be a non-empty object if present")
        else:
            uses_me |= _check_section("changes", changes, ALLOWED_CHANGES, errs)

    if uses_me and identity is None:
        errs.append("a command uses {me} but no 'identity' is set")

    return errs


class _MissingParam(Exception):
    def __init__(self, key: str) -> None:
        self.key = key


def _load_tracker_config(repo_root: Path, name: str) -> dict | None:
    path = repo_root / ".agents" / "trackers" / f"{name}.json"
    if not path.exists():
        return None
    try:
        config = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    # A parse that succeeded says the file is JSON, not that it is a config.
    # A verb map written without its enclosing object parses fine and arrives
    # as a list, which every caller then calls `.get` on. Deciding it here is
    # what makes the `dict | None` above true for the two callers rather than
    # once per caller.
    return config if isinstance(config, dict) else None


def load_key_pattern(repo_root: Path) -> str:
    """Return the active tracker's issue-key regex, or the default.

    Degrades to DEFAULT_KEY_PATTERN when no tracker is configured, its config is
    missing/invalid, the field is absent, isn't a string, or won't compile — key
    resolution must never fail because a tracker step couldn't run.
    """
    from wfctl._paths import DEFAULT_KEY_PATTERN

    name = load_manifest(repo_root).get("tracker")
    if not name:
        return DEFAULT_KEY_PATTERN
    config = _load_tracker_config(repo_root, name)
    pattern = (config or {}).get("key_pattern")
    # A config is JSON, so this is whatever the author typed. `re.compile`
    # answers a non-string with TypeError, not re.error, so the type is checked
    # here rather than caught below — the same shape `validate_config` reports.
    if not isinstance(pattern, str) or not pattern:
        return DEFAULT_KEY_PATTERN
    try:
        re.compile(pattern)
    except re.error:
        return DEFAULT_KEY_PATTERN
    return pattern


def configured_key_pattern(repo_root: Path) -> str | None:
    """The active tracker's issue-key regex, or None when the repo has no tracker.

    `load_key_pattern` answers a neighbouring question and must not be used for
    this one: it degrades to the GitHub-shaped default so that resolving a key
    never fails. A caller deciding whether keys are *expected to appear* needs
    the case that hides behind — a repo that declined a tracker creates no
    issues, so a check that waits for keys there waits forever.
    """
    if not load_manifest(repo_root).get("tracker"):
        return None
    return load_key_pattern(repo_root)


def _substitute(token: str, params: dict) -> str:
    """Replace every {name} in one argv token from params; missing -> _MissingParam."""
    def repl(m: re.Match) -> str:
        key = m.group(1)
        val = params.get(key)
        if val is None:
            raise _MissingParam(key)
        return str(val)

    return _PLACEHOLDER.sub(repl, token)


def dispatch(
    agent_dir: Path,
    repo_root: Path,
    verb: str,
    params: dict,
    section: str = "verbs",
    event: str = "issue",
) -> int:
    """Run the configured backend's command for verb; return an exit code.

    ``section`` selects the verb map in the config: ``"verbs"`` for issues,
    ``"changes"`` for PRs/patchsets. ``event`` is the name logged for the run.
    A ``{me}`` placeholder in any argv is filled from the config's top-level
    ``identity`` field (e.g. ``@me``, a username, an email), so a backend can
    scope a list to the current user (``--author {me}``, ``owner:{me}``).

    Degrades gracefully (returns 0) when no backend is configured, its config
    is missing/invalid, or the verb is unsupported — a session must not fail
    because a tracker step could not run.
    """

    name = load_manifest(repo_root).get("tracker")
    if not name:
        console.print(
            f"ℹ No tracker configured — skipping '{verb}'. "
            "Author one with the /scaffold-tracker skill."
        )
        return 0

    config = _load_tracker_config(repo_root, name)
    if config is None:
        console.print(
            f"[yellow]⚠[/yellow] Tracker '{name}' config missing or invalid "
            f"(.agents/trackers/{name}.json) — skipping '{verb}'. "
            "Fix it with the /scaffold-tracker skill (or `wfctl tracker-check "
            f"{name}` to see what's wrong)."
        )
        return 0

    verbs = config.get(section, {})
    if verb not in verbs:
        console.print(f"ℹ Tracker '{name}' does not support '{verb}' — skipped")
        return 0

    # After the config checks and before argv is built, so a refusal reads as a
    # refusal rather than as a backend that could not run: a repo with no
    # `comment` verb and a run with no authority are different answers, and only
    # one of them is about permission.
    if section == "verbs" and verb in _NOTIFYING_VERBS:
        refused = _refuse_notifying(agent_dir, verb)
        if refused is not None:
            return refused

    # {me} comes from the config's identity, not a CLI flag — inject it so a
    # backend can filter a list to the current user.
    identity = config.get("identity")
    if identity is not None:
        params = {"me": identity, **params}

    try:
        argv = [_substitute(tok, params) for tok in verbs[verb]]
    except _MissingParam as e:
        if e.key == "me":
            console.print(
                f"[red]✗ '{verb}' uses {{me}} but no 'identity' is set in "
                f".agents/trackers/{name}.json[/red]"
            )
        else:
            console.print(f"[red]✗ '{verb}' requires --{e.key}[/red]")
        return 1

    result = subprocess.run(argv, capture_output=True, text=True, cwd=repo_root)
    if result.stdout:
        print(result.stdout, end="")  # passthrough; no rich markup/reflow
    if result.returncode != 0:
        console.print((result.stderr or "").rstrip(), style="red", markup=False)
        return result.returncode

    append_event(agent_dir, event, verb=verb, tracker=name)
    if section == "verbs" and verb in _NOTIFYING_VERBS:
        # FR-010, and unprompted is the point: a run that used the authority
        # reports what it did whether or not anyone asked. Recorded here rather
        # than by each caller because this is the one place that knows the write
        # succeeded — the `issue` event above says the verb ran, not that anyone
        # was told anything by it.
        from wfctl._session import record_notify_action

        record_notify_action(agent_dir, verb)
    return 0


def read_issue_labels(repo_root: Path, issue: str) -> tuple[set[str] | None, str | None]:
    """The labels on one issue, through the backend's own `view` verb.

    Returns `(labels, detail)`. `labels` is None when there is no answer:
    `detail` then says why the read failed, or is None when nothing was asked —
    no tracker configured, or one that declines `view`. A caller gating on a
    label must keep those apart. "Nobody answered" is the ordinary state of a
    repo with no tracker (FR-012); "the answer did not arrive" decides a whole
    run and is reported as its own event (FR-015).

    One label per line of stdout, because the verb is declared to produce that
    and not because any backend's default output happens to look that way. An
    earlier version ran `view` and looked for the `labels:` header `gh` prints:
    it read every other backend as having no labels, silently, and searching the
    whole output instead would have let an issue *about* a label grant that
    label — #280's own body names `authority:notify` several times.
    """
    name = load_manifest(repo_root).get("tracker")
    if not name:
        return None, None
    config = _load_tracker_config(repo_root, name)
    if config is None or "labels" not in config.get("verbs", {}):
        return None, None

    params: dict = {"id": issue}
    identity = config.get("identity")
    if identity is not None:
        params = {"me": identity, **params}
    try:
        argv = [_substitute(tok, params) for tok in config["verbs"]["labels"]]
    except _MissingParam as e:
        return None, f"'labels' requires --{e.key}"

    try:
        result = subprocess.run(argv, capture_output=True, text=True, cwd=repo_root)
    except OSError as e:
        return None, str(e)
    if result.returncode != 0:
        return None, (result.stderr or result.stdout or "").strip()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}, None
