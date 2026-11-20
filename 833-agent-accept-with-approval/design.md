# The agent runs person-only commands after the user approves
Contexts: worktree-guard, architecture-records, install-and-drift, evidence-and-derivation

Written under auto-approve. Each gate's answer below carries its basis, and
the user approves the design at the PR. The level-2 record was accepted by the
user on #833 before auto-approve was turned on.

## Problem Statement

The user accepts records, signs off reviews, and approves imports without
going back to the computer. The agent runs each of the three commands, and the
user approves it at the agent host's permission prompt.

## Recommended Direction

Previously, `wfctl arch accept`, `wfctl review sign-off`, and `wfctl arch
approve-imports` all needed a person at a terminal. The worktree guard refused
them from an agent, and each command refused to run without a terminal.
Currently, that means the user returns to the computer for every record and
every sign-off, even when they know they'll agree. The user's words were that
they are "constantly blocked to get a computer to sign off commits ... even
though I know I would accept."

Claude Code and Codex can both ask the user before a command runs, and #407
already installs those rules for `wfctl auto-approve on`. This change reuses
that mechanism for the three commands. `wfctl install-skills` writes the rules,
the guard lets the plain spellings through so the prompt appears, and each
command drops its terminal check and its typed confirmation when the host is
one that asks. The guard keeps refusing every wrapped form, because the host's
rule can't match it and it would run with no prompt.

The prompt is the evidence that a person agreed, the same thing the terminal
stood for. wfctl can't see the user's answer, so `wfctl arch accept` with no
`--agreed` citation writes "accepted — approved at the permission prompt" and
claims nothing more.

## Boundaries and Ownership

1. The agent host decides whether a person agreed to a run, by showing the
   prompt. wfctl runs after the prompt and can't see the answer.
2. wfctl decides whether the prompt will appear. It installs the rules,
   `doctor` reports a missing one, and the guard refuses every form the rule
   can't match.
3. The user decides which forms the guard must keep refusing, by accepting
   the record's threat model.

## Key Assumptions to Validate

- [ ] Claude Code shows the prompt for each plain spelling once the `ask`
      rules are installed, including under its auto mode. Test: walk it with
      a throwaway proposed record.
- [ ] Codex shows the prompt for a command its sandbox allows, and doesn't
      run a wrapped form such as `bash -lc "wfctl arch accept s"` without one.
      Test: a session in Codex. Until it passes, Codex keeps the terminal
      check.
- [ ] Bob Shell's hook payload names its tool in `tool_name`, so the guard can
      tell it apart from Claude Code. Test: read a Bob payload. If it doesn't,
      the installer passes the host to the hook command.
- [ ] Claude Code sets `CLAUDE_CODE_SESSION_ID` in the shell it runs commands
      in, and Codex sets a variable of its own. Test: print the environment
      from each host.

## MVP Scope

In:

1. One table of prompted spellings in evidence and derivation, with the
   Claude Code rules built from it and a test holding the Codex rules file to
   it.
2. `install-skills` writes the rules, and `doctor` reports a missing one.
3. The guard lets through a command made of exactly one table entry, and only
   when the payload comes from Claude Code, the rule is in
   `.claude/settings.json`, and wfctl's auto-approve is off. It refuses every
   other form it refuses today.
4. Each command skips its terminal check and typed confirmation when its
   environment names Claude Code, or Codex once the Codex walk passes.
5. `--agreed` is optional, with the "approved at the permission prompt" Log
   line.
6. The threat model's lists in `prompt-approves-person-commands.md` each get a
   test.
7. `doctor` counts a superseded record as claimed when its own `superseded`
   Log line names its successor, so `guard-catches-literal-accept.md` stops
   warning. (Changed at plan: a `supersedes` list can't help, since the
   accepted record names only one.)

Out: everything under "Not Doing".

## Not Doing (and Why)

- Letting the agent accept its own records under auto-approve (#814) — a
  separate decision for `arch accept` only, since a sign-off under
  auto-approve would let the agent skip its own review panel.
- A personal setting listing commands that stay terminal-only — nobody needs
  it yet, and the user wanted all three to ask.
- Fixing the guard's false refusals on commands that only mention the accept
  (#796, #802 - #805) — the user chose to keep the text check, so those stay
  open.
- Detecting Claude Code's bypass mode — wfctl can't see the host's mode.
- Supporting hosts other than Claude Code, Codex, and Bob Shell — they keep
  the terminal check.

## Open Questions

- Whether `wfctl arch accept --dry-run` moves to a spelling outside the table,
  since the host's rule matches it and the user would be asked on every dry
  run. The plan decides.
- #407 hasn't merged, and implementation depends on its rule plumbing.
  Implementation starts once it merges.

## Software design decisions

- docs/architecture/design/prompted-spellings-one-table.md — one table lists the spellings the host prompts for, and the guard and the host rules follow it

Level 2 is answered by `docs/architecture/prompt-approves-person-commands.md`,
accepted on #833.
