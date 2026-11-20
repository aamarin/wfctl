# Data model: Agent accepts with approval

## Prompted

One spelling the host asks for.

| Field | Type | Meaning |
| --- | --- | --- |
| `command` | `str` | The command it belongs to: `arch accept`, `review sign-off`, or `arch approve-imports` |
| `words` | `tuple[str, ...]` | The words the command starts with, compared exactly |

Derived values:

- Claude Code rule: `Bash(" ".join(words) + ":*")`.
- Codex rule: `prefix_rule(pattern = list(words), decision = "prompt", …)`.

`PROMPTED` holds five entries. A command matches an entry when its raw text,
trimmed, starts with the entry's words joined by single spaces, followed by a
space or the end, compared literally. The guard's other conditions are in
`plan.md §The guard`.

## Managed rule (from #407)

`_ManagedRule(path, rule, kind, cost)`. This feature adds five with `path =
.claude/settings.json`, `kind = "ask"`, and a `cost` naming which command
would stop prompting. Receipts land in `.wf-skills-manifest.json` as #407
records them.

## Accept Log line

| Run | `--agreed` | Line |
| --- | --- | --- |
| No terminal, `CLAUDECODE` set | given | `accepted — <citation>` |
| No terminal, `CLAUDECODE` set | absent | `accepted — approved at the permission prompt` |
| Terminal | given | `accepted — <citation>` |
| Terminal | absent | refused, naming `--agreed` |
| No terminal, no `CLAUDECODE` | either | refused, as today |
