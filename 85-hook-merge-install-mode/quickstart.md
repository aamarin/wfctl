# Quickstart: merge install mode

For verifying the feature works once implemented — not a tutorial to publish,
a script to run.

## Install into a clean repo

```bash
cd some-consumer-repo
cat .claude/settings.json 2>/dev/null   # confirm baseline (may not exist)
wfctl install-skills --agent claude
cat .claude/settings.json
```

Expect: a `hooks.UserPromptSubmit` array containing exactly one entry, `command:
"wfctl hook user-prompt"`. Every permission and every other hook the file had
before is present, byte-identical.

## Confirm the hook has something to say

```bash
wfctl hook user-prompt
```

Expect: silent (exit 0, no output) until at least one installed skill under
`.agents/skills/` carries a `digest.md`. Once one does:

```
These skills are active and govern this response:
- <skill name>: <digest text>
```

## Reinstall is idempotent

```bash
wfctl install-skills --agent claude   # again, nothing changed
git diff .claude/settings.json        # expect: no diff — file not reopened
```

## Doctor reports drift

```bash
# Hand-edit the entry to something wrong, simulating drift:
jq '.hooks.UserPromptSubmit[0].hooks[0].command = "wfctl hook old-name"' \
  .claude/settings.json > /tmp/s.json && mv /tmp/s.json .claude/settings.json

wfctl doctor
```

Expect: a line reporting the `claude` hook entry as behind, naming
`wfctl install-skills --agent claude` as the fix.

## Uninstall leaves foreign hooks alone

```bash
# Add a hand-written hook to the same event first:
jq '.hooks.UserPromptSubmit += [{"hooks":[{"type":"command","command":"./my-hook.sh"}]}]' \
  .claude/settings.json > /tmp/s.json && mv /tmp/s.json .claude/settings.json

wfctl uninstall-skills --agent claude
cat .claude/settings.json
```

Expect: `./my-hook.sh` still present in `hooks.UserPromptSubmit`; wfctl's entry
gone; the group itself still present (not pruned, because it isn't empty).

## Malformed settings file doesn't block the rest of the install

```bash
echo '{not valid json' > .claude/settings.json
wfctl install-skills --agent claude
```

Expect: a warning naming `.claude/settings.json` as not modified, and every
other install target (skills, commands, `.specify/`) still reports installed.
