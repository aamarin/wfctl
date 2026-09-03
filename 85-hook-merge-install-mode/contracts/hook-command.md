# Contract: `wfctl hook user-prompt`

The command the managed entry installs. This is the interface `.claude/settings.json`
depends on — its stability matters more than any other surface in this feature,
because a break here is invisible until a session's next turn.

## Invocation

```
wfctl hook user-prompt
```

No arguments, no flags. Design ledger #6: the entry names no agent because its
location already scopes it; the same reasoning extends to naming no skill list —
the command reads what is installed, it does not receive it as input.

## Inputs

- The current working directory's repo root (same resolution every other wfctl
  command uses — `get_repo_root()`).
- `<repo_root>/.wf-skills-manifest.json`, for the skills it records as installed.
- `<repo_root>/.agents/skills/<recorded name>/digest.md`, read fresh on every call.

  The manifest, not the directory listing, decides which skills are read.
  `.gitignore` carries one line per *installed* skill, so a directory wfctl never
  installed is uncovered and travels in a clone, while the hook itself is wired
  by a committed `.claude/settings.json`. Reading the filesystem let a repository
  put text of its choosing into the reader's context on every turn, under a
  header saying that text governs the response.

## Output (stdout)

- One line naming what is active, then one bullet per skill that carries a
  digest, in directory-listing order:

  ```
  These skills are active and govern this response:
  - conversation-response-shape: === response shape — applies to this turn ===
  ...
  ```

  (Exact header text and per-line format are an implementation choice for
  `tasks.md`, not fixed by this contract — what is fixed is: header appears iff
  at least one digest exists, and one skill per line.)

  A digest is flattened to a single line and truncated. Both are trust
  boundaries, not formatting: one bullet per skill is the format's only
  structure, and a digest carrying newlines otherwise forged a second header and
  a bullet attributed to a skill that does not exist. Nothing else bounded what
  one file could spend of every turn's context.

  A `digest.md` that resolves outside the repo root is not read. Symlinked at a
  credentials file, it read that file into the model's context every turn.

- **Nothing**, when no installed skill carries a `digest.md`. No header, no
  blank line, no error. Per FR-012 and the reasoning in `research.md`'s command
  invocation section: a hook firing on every turn must be silent when it has
  nothing to say, not noisy about the absence.

## Output (exit code)

- Always `0`. This runs inside a `UserPromptSubmit` hook — a non-zero exit is a
  per-turn error surfaced to whoever is mid-session, for a condition (`digest.md`
  absent, repo root not found) that is not actionable from inside a turn and is
  already covered, once, by `wfctl doctor`.

## Failure modes and their handling

| Condition | Behavior |
| --- | --- |
| Not inside a git repo / no repo root | Exit 0, no output — same silent-degrade rule |
| `.agents/skills/` missing entirely | Exit 0, no output |
| A skill directory's `digest.md` is unreadable (permissions, not present) | That skill contributes nothing; every other skill's digest still prints |
| A `digest.md` that is not valid UTF-8 | That skill contributes nothing; exit stays 0 |
| `.agents/skills/` exists but cannot be listed | Exit 0, no output |
| No `git` on `PATH` at all | Exit 0, no output |
| A skill directory present but not recorded in the manifest | Not read at all |
| A `digest.md` resolving outside the repo root | Not read at all |
| A skill directory's `digest.md` is present but empty | Treated as absent — no bullet for that skill |

## Stability

This contract is what `doctor`'s freshness check and the manifest's `command`
field pin against (`data-model.md`). Changing the invocation shape (arguments,
subcommand name) is the one edit that requires bumping every installed entry —
`doctor` would report every existing install as behind, which is the intended
signal per `research.md`'s decision on the command name.
