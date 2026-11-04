# Quickstart: check #698 by hand

Two checks the test suite can't run: the listing a real session loads, and an
upgrade over a project that already has the dropped skills.

## The listing

1. Clone `main` and this branch into a scratch folder.
2. In each clone, run `uv run wfctl install-skills --yes --agent claude --tracker github`.
3. In each clone, run `claude -p hi --output-format stream-json --verbose` and add
   up `input_tokens`, `cache_creation_input_tokens`, and
   `cache_read_input_tokens` on the first assistant message.
4. `main` read 39,789 on 2026-11-03. This branch should read less, and its
   `.claude/skills/` should hold no `brainstorm`, `speckit-brainstorm`,
   `using-superpowers`, or `verification-before-completion`.

## The upgrade

1. In an empty git repo, install from the `main` clone with `--agent claude
   --tracker github`.
2. Add `.claude/skills/my-own/SKILL.md` by hand.
3. Install from this branch's clone with `--agent claude`. It lists the dropped
   paths as no longer shipped and removes nothing.
4. Run `doctor` from this branch's clone. It names the same paths and the
   `--prune` command for each layer.
5. Run `install-skills --agent claude --prune`. The dropped paths are gone from
   `.agents/` and `.claude/`, `my-own` and `.agents/trackers/github.json` are
   still there, and `doctor` is green.
