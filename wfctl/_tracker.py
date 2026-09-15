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
    # leaves it out, rather than a reader guessing from whatever `view` printed.
    "labels": {"id"},
    # `fields` reads an issue's or a change's attributes as data, where `view`
    # returns whatever the backend's client prints for a human. Separate from
    # `view` for the reason `labels` is separate from `label`: reading is the
    # half a backend can decline, and a caller that fell back to parsing `view`
    # would read every other backend as having nothing set — silently, which is
    # the mistake a label read parsing `view` once made.
    "fields": {"id"},
    # `start`/`stop` say when work on an issue began and stopped; what a backend
    # does with that is its own business. A tracker with a board moves a column,
    # one without it declines the verb and the caller carries on — which is why
    # the pair is named for the event rather than for the column, and why
    # neither takes a status to write.
    "start": {"id"}, "stop": {"id"},
}
# The `changes` section (PRs / patchsets) supports a smaller verb set.
ALLOWED_CHANGES = {"list": set(), "view": {"id"}, "fields": {"id"}}


# The write verbs whose success is recorded as an action, under the name the
# skills file a block against: `issue-<verb>`. The name is the writer's to get
# right, not the reader's to normalise (`384-an-action-is-named-by-the-verb-that-
# takes-it`) — `standing_blocks` matches on it as written, so a successful retry
# lifts the hold its own refusal put there, and `_restart` prints the same name
# the handoff uses.
#
# `close` is here because a block is filed against it (`end-session`), and a
# close that succeeded and recorded nothing left that hold standing with only a
# hand-typed release to lift it. Recording is not gating: nothing in wfctl
# refuses any of these.
#
# `start` and `stop` are not. They run from worktree hooks rather than from a
# session's turn, nothing files a block against a board move, and recording them
# would put one into every restarted session's handoff.
_RECORDED_VERBS = {"comment", "create", "label", "close"}


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
    if section == "verbs" and verb in _RECORDED_VERBS:
        # Recorded here rather than by each caller because this is the one place
        # that knows the write succeeded — the `issue` event above says the verb
        # ran, and carries the bare verb a hold was never filed under.
        from wfctl._session import record_notify_action

        record_notify_action(agent_dir, f"issue-{verb}")
    return 0


def _read_verb(
    repo_root: Path, section: str, verb: str, item_id: str
) -> tuple[str | None, str | None]:
    """One reading verb's stdout, or why there is none. Never raises.

    The half `dispatch` cannot do. That one prints stdout and hands back an exit
    code, which is right for a verb whose output a person reads and useless for
    one whose output a caller parses — so a reading verb comes through here
    instead of gaining a capture flag on the writer's path.

    Returns `(stdout, detail)`, and the two None cases are not the same fact.
    `(None, None)` is nobody answered: no tracker, an unreadable config, or a
    backend that declines the verb — the ordinary state of a repo that opted
    out. `(None, detail)` is the answer did not arrive, which decides the run
    that asked. A caller that collapses them reports a silence as a pass.
    """
    name = load_manifest(repo_root).get("tracker")
    if not name:
        return None, None
    config = _load_tracker_config(repo_root, name)
    if config is None:
        return None, None
    # `.get(section, {})` returns the value when the key is present, so a config
    # carrying `"verbs": null` hands back None and the membership test below
    # raises. Nothing validates a hand-edited config at load, so the crash lands
    # on whichever command reads first. `validate_config` already guards the
    # shape this way; this reader had not.
    verbs = config.get(section)
    if not isinstance(verbs, dict) or verb not in verbs:
        return None, None

    # A config that parsed is a config that is JSON, not one that is well-formed.
    # `"labels": 3` reached the comprehension below and raised TypeError out of a
    # function whose caller documents that it never raises — a traceback on a
    # branch whose only fault was a typo in a file nothing validates at load.
    template = verbs[verb]
    if not isinstance(template, list) or not all(isinstance(t, str) for t in template):
        return None, f"'{verb}' must be a list of strings"

    params: dict = {"id": item_id}
    identity = config.get("identity")
    if identity is not None:
        params = {"me": identity, **params}
    try:
        argv = [_substitute(tok, params) for tok in template]
    except _MissingParam as e:
        return None, f"'{verb}' requires --{e.key}"

    try:
        # Bounded because callers run unattended: `fields` is invoked by a skill
        # that has nobody watching it. Unbounded, it hangs forever;
        # refused-on-timeout is the same verdict an unreachable tracker gets.
        result = subprocess.run(
            argv, capture_output=True, text=True, cwd=repo_root, timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, str(e)
    if result.returncode != 0:
        return None, (result.stderr or result.stdout or "").strip()
    return result.stdout, None


def _is_flat(value: object) -> bool:
    """Can this value be compared without knowing what field it belongs to?

    Scalars and arrays of scalars can. An object cannot: telling two of them
    apart means knowing which key inside identifies it — `name` for a GitHub
    label, `login` for an assignee — which is one tracker's vocabulary inside
    wfctl, and the whole reason the verb is contracted to flatten.
    """
    if isinstance(value, (str, int, float, bool)) or value is None:
        return True
    if isinstance(value, list):
        return all(
            isinstance(v, (str, int, float, bool)) or v is None for v in value
        )
    return False


def read_fields(
    repo_root: Path, section: str, item_id: str
) -> tuple[dict | None, str | None]:
    """One issue's or change's attributes as data, through its `fields` verb.

    `section` is `"verbs"` for an issue and `"changes"` for a change; the key
    names in the payload are the backend's own, and nothing here enumerates
    them.

    Same three-state return as `_read_verb`, and the third state carries one
    case that reader has no equivalent for: a payload wfctl cannot compare.
    That is a hand-edited config rather than a tracker being unreachable, so it
    comes back as a `detail` naming the key — a traceback out of the comparison
    would send the reader to the wrong file.
    """
    out, detail = _read_verb(repo_root, section, "fields", item_id)
    if out is None:
        return None, detail
    try:
        payload = json.loads(out)
    except json.JSONDecodeError as e:
        return None, f"'fields' did not return JSON: {e}"
    if not isinstance(payload, dict):
        return None, "'fields' must return a JSON object"
    for key, value in payload.items():
        if not _is_flat(value):
            return None, (
                f"'fields' returned a nested value for '{key}' — the verb must "
                "flatten to scalars or arrays of scalars"
            )
    return payload, None
