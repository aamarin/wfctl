"""Read and write `.wf-skills-manifest.json`, the per-repo config file.

Its own module because both `cli` and the lower-level modules need it. Living in
`cli`, it forced `_paths` and `_tracker` to import `cli` back at call time —
a cycle papered over with lazy in-function imports, which meant path resolution
could not be exercised without pulling in typer, rich, and every command.

The file holds two kinds of key: layer entries written by `install-skills`
(objects with `items` plus the `wfctl_version` and `content_hash` that installed
them) and bare scalars recording a repo's choices (`tracker`, `spec_root`).
Anything enumerating layers must skip the scalars — see `_NON_LAYER_KEYS` in
`cli`.
"""
from __future__ import annotations

import json
from pathlib import Path

MANIFEST_PATH = ".wf-skills-manifest.json"


def load_manifest(repo_root: Path) -> dict:
    """The manifest at `repo_root`, or `{}` when there is none.

    Raises `json.JSONDecodeError` on a manifest that exists but cannot be parsed.
    Deliberately not caught: a malformed manifest is a broken repo, not a missing
    setting, and defaulting silently would resolve paths to somewhere the user
    never configured.
    """
    manifest_file = repo_root / MANIFEST_PATH
    if manifest_file.exists():
        return json.loads(manifest_file.read_text())
    return {}


def save_manifest(repo_root: Path, manifest: dict) -> None:
    """Write the manifest, or delete it when nothing is left to record."""
    manifest_file = repo_root / MANIFEST_PATH
    if manifest:
        manifest_file.write_text(json.dumps(manifest, indent=2) + "\n")
    elif manifest_file.exists():
        manifest_file.unlink()
