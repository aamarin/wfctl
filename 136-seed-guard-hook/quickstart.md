# Phase 1 — the by-hand round trip

The suite cannot cover this. `tests/test_settings_merge.py` is dict literals, and
a round trip over three dicts has never met a real settings file with its own key
order, its own hooks and its own permissions. Run this before opening the PR.

## Set up a scratch repo

```bash
cd "$(mktemp -d)" && git init -q .
mkdir -p .claude
cat > .claude/settings.json <<'JSON'
{
  "permissions": {
    "allow": ["Bash(npm test)", "Bash(git status)"],
    "deny": ["Bash(rm -rf /*)"]
  },
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "./scripts/audit.sh" }] }
    ]
  },
  "model": "opusplan"
}
JSON
cp .claude/settings.json /tmp/settings.before.json
```

Their own `PreToolUse` Bash hook, their own deny list, a key wfctl knows nothing
about, and `permissions` first — wfctl writes `hooks` first, so key order is
genuinely theirs and not accidentally ours.

## Install

```bash
uv run --project <wfctl checkout> wfctl install-skills --agent claude --yes
```

Confirm, by reading the file:

- [ ] `./scripts/audit.sh` is still there, in its own group
- [ ] wfctl's guard hook is a separate group with `"matcher": "Bash"`
- [ ] `Bash(rm -rf /*)` survived, and `Bash(cd:*)` joined it
- [ ] `"model": "opusplan"` is untouched
- [ ] `.wf-skills-manifest.json` records `{"rule": "Bash(cd:*)", "added": true}`

## Re-install

```bash
cp .claude/settings.json /tmp/settings.after-install.json
uv run --project <wfctl checkout> wfctl install-skills --agent claude --yes
diff /tmp/settings.after-install.json .claude/settings.json
```

- [ ] `diff` is empty — nothing duplicated, and the file was not rewritten

## Uninstall

```bash
uv run --project <wfctl checkout> wfctl uninstall-skills --agent claude
diff /tmp/settings.before.json .claude/settings.json
```

- [ ] `diff` is empty except for whitespace the first install reflowed

That caveat is real and expected: the install that first adds an entry rewrites
the file, and a JSON round trip normalises indentation. Compare parsed content if
the whitespace diff is noisy:

```bash
python3 -c "import json,sys;a,b=[json.load(open(p)) for p in sys.argv[1:]];print(a==b)" \
  /tmp/settings.before.json .claude/settings.json
```

- [ ] prints `True`

## The rule they already had

Start again with `Bash(cd:*)` already in their `deny` list before wfctl ever runs.

- [ ] install records `{"added": false}`
- [ ] uninstall leaves the rule in place

## The rule they edited

Install, then change `Bash(cd:*)` to `Bash(cd:/tmp/*)` by hand.

- [ ] `wfctl doctor` reports it gone, and **exits 0**
- [ ] `install-skills --agent claude` refuses, names both ways forward, and copies
      nothing — check the skills tree is untouched, not just that it printed
- [ ] `install-skills --agent claude --force` re-asserts the rule and proceeds
- [ ] after re-installing without `--force`, `uninstall-skills` names the file,
      the text found, and `Bash(cd:*)`

## The hand-wired guard

Start again with the README's old block pasted in but `"matcher": "*"`.

- [ ] install corrects the matcher to `Bash`
- [ ] the entry keeps its original position in the array
