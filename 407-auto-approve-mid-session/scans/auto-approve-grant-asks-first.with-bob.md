---
status: accepted
diagram: data-flow
governs: install-and-drift, session-continuity, agent-host
---

# Auto-approve turns on only with the person's approval

## Decision

When the agent runs `wfctl auto-approve on` in Claude Code, Claude Code asks
the person first. `install-skills --agent claude` adds three rules to the
`permissions.ask` list in `.claude/settings.json`:

```json
"permissions": { "ask": [
  "Bash(wfctl auto-approve on:*)",
  "Bash(uv run wfctl auto-approve on:*)",
  "Bash(uv run --project * wfctl auto-approve on:*)"
] }
```

The third rule is there because wfctl's own remedy lines print `uv run
--project <dir> wfctl`, so an agent that copied one runs wfctl that way.
Claude Code then prompts the person every time the agent runs one of these commands,
even when a broader `allow` rule covers wfctl, since an `ask` rule overrides an
`allow` rule. The rules don't cover the creation hook, since the command typed
there is `workmux add`.

wfctl manages these rules the same way it manages its deny rule `Bash(cd:*)`.
`install-skills` adds them and records each one in the manifest with the kind
`ask`. `uninstall-skills` removes them. If a repo deletes a rule wfctl
installed, `doctor` reports it and `install-skills` refuses, as it does for the
deny rule today. A receipt with no kind is treated as `deny`, so manifests
written before this change still match.

In Codex, `install-skills --agent codex` copies one rules file to
`.codex/rules/wfctl.rules`. It holds a `prefix_rule` with the decision `prompt`
for each of the first two commands:

```
prefix_rule(pattern = ["wfctl", "auto-approve", "on"], decision = "prompt")
prefix_rule(pattern = ["uv", "run", "wfctl", "auto-approve", "on"], decision = "prompt")
```

Codex loads the project's `.codex/rules/` only after the person trusts the
project, so `install-skills` tells them that. It writes only `wfctl.rules`, so
any other rules file the project keeps there is left alone. The manifest
records it like any other installed file, and `doctor` reports it when it
drifts.

Bob Shell can't ask, since it has only an allowlist and a deny list. So in Bob
Shell, the worktree guard refuses `wfctl auto-approve on` when the agent runs
it. The refusal tells the person to run the command in their own terminal. The
guard identifies Bob Shell by the hook payload's `tool_name`, which is
`execute_command` or `run_shell_command` in Bob Shell and `Bash` in Claude
Code. It refuses a simple command only when `wfctl` comes before `auto-approve
on` in it, so a search such as `rg 'auto-approve on' docs/` goes through.

`wfctl start --auto-approve` is refused in every agent, and the refusal names
`wfctl auto-approve on`. The flag can sit anywhere in `start`'s arguments, such
as `start --force --auto-approve`, so no rule matching the command's leading
words could ask about it. Refusing it leaves `wfctl auto-approve on` as the
only way to turn the mode on (`approval-mode-is-stored-intent`).

Other agents get nothing. They rely on their own permission settings and on the
`using-wfctl` instruction to run `on` only when a person asked.

This record adds a control beside `approval-mode-is-stored-intent` (accepted)
and doesn't replace it. That record's checks stay as they are. This one narrows
its accepted case 1, an agent granting itself the mode without being asked, for
agents running in Claude Code, Codex, and Bob Shell.

## Boundary

![The agent never turns the mode on without the person approving a prompt](drawings/auto-approve-grant-asks-first-data-flow.svg)

A solid arrow is a command the sender waits on, and the dotted arrow is a file
read later. The red edge is what the permission prompt refuses: the agent
running the command and the grant landing without the person's yes.

## Context

`approval-mode-is-stored-intent` lets the agent run `wfctl auto-approve on`
when a person asks for an unattended run. It accepts that the agent could also
run it unasked, since wfctl can't tell the two apart. It limits the damage with
a `mode` event naming the session, and with the review cap.

The plan walkthrough for #407 found that neither limit reaches a reviewer. The
event log sits in the local state dir. There, a grant the agent made unasked
shows "this session", the same as a grant the person asked for. As a result, an
unasked grant is neither stopped nor visible to anyone reviewing the PR.

The user asked whether the agent could be required to ask first. In Claude
Code, it can. Claude Code's permission layer already prompts the person for
any command matching an `ask` rule, and wfctl already writes managed rules into
`.claude/settings.json`.

## Threat model

### Defends against

The prompt stops an agent in Claude Code that runs `wfctl auto-approve on`
without being asked, whether by mistake, by habit, or because a document told
it to. The person sees the prompt and decides. In an unattended run nobody is
at the prompt, so the run waits until the person comes back.

Claude Code's docs say an ask rule prompts in every permission mode, including
`bypassPermissions` and auto mode, and that the auto mode classifier can't
approve a call an ask rule matches. Two settings deny the call instead of
asking: `dontAsk` mode, and a headless `claude -p` run with no permission host.
Either way the mode stays off. The plan's validation includes a manual run in
the default mode and in auto mode, since wfctl's tests can check only that the
rules are written.

wfctl's part is installing the three rules and keeping them in place. Claude Code
matches the command and shows the prompt, so the matching is transferred to
Claude Code. Its rules decide which forms the prompt catches.

Codex's prompt works the same way, with two limits:

1. Codex's docs say rules are experimental.
2. The docs don't say what a `prompt` rule does when approvals are off
   (`--ask-for-approval never`) or under
   `--dangerously-bypass-approvals-and-sandbox`.

When Codex is installed, a test runs `codex execpolicy check` against the
shipped file. It checks that both forms prompt and that `off` doesn't.

In Bob Shell, the refusal comes from the guard, so wfctl does the matching
itself. The guard reads the command's text, so it also catches forms Claude
Code's matcher misses, such as `bash -c "wfctl auto-approve on"`. The cost is
that the person in Bob Shell types the command every time, since there's no
prompt to approve.

The prompt and the refusal don't stop an agent that hides the command on
purpose, and they don't apply to other agents.

### Must keep catching

1. The command as written: `wfctl auto-approve on`
2. Behind the runner this repo uses: `uv run wfctl auto-approve on`
3. After a variable assignment: `FOO=1 wfctl auto-approve on`
4. Inside a compound command: `cd x && wfctl auto-approve on`
5. A repo that deleted a rule wfctl installed, which `install-skills` refuses and `doctor` reports: `wfctl install-skills --agent claude`
6. Behind the runner wfctl's remedy lines print: `uv run --project /repo wfctl auto-approve on`

Forms 1 to 4 and 6 depend on Claude Code's matcher. Its docs say an ask rule
matches past a leading assignment and applies to each part of a compound
command. wfctl's tests check that the three rules are written to
`permissions.ask`, and form 5 has its own test, the same way the deny rule's
refusal does.

In Codex, forms 1 and 2 prompt, and a test checks both with `codex execpolicy
check`. In Bob Shell, the guard refuses forms 1 to 4 and 6, and a test checks
each one.

### Accepts

1. Behind a runner the rules don't name: `env wfctl auto-approve on`
2. Inside a shell the agent starts: `bash -c "wfctl auto-approve on"`
3. Through an absolute path: `/Users/me/.local/bin/wfctl auto-approve on`
4. An agent other than Claude Code, Codex, or Bob Shell, or Codex in a project the person hasn't trusted: `wfctl auto-approve on`
5. A hand-written mode file, which no prompt sees: `echo '{"auto_approve": true}' > mode.json`
6. An agent creating a worktree with the creation hook's variable set: `WFCTL_AUTO_APPROVE=1 workmux add 812-foo`
7. In Codex, after a variable assignment or inside a compound command: `FOO=1 wfctl auto-approve on`
8. In Bob Shell, a command that names wfctl and quotes the phrase without running it, which the guard refuses: `git commit -m "docs: explain wfctl auto-approve on"`
9. In Claude Code and Codex, a double dash before the argument: `wfctl auto-approve -- on`
10. In Codex, or in Claude Code with any other `uv run` option: `uv run --frozen wfctl auto-approve on`

Forms 1 to 3 require deliberately changing the plain command. Claude Code's
docs say its matcher doesn't strip `env`, doesn't look inside `bash -c`, and
matches the command as typed, so Claude Code catches none of the three. In Bob
Shell, the guard catches all three, since it searches the command's text. Form 4 falls
back to that agent's permission settings and the `using-wfctl` instruction.
Form 5 is `approval-mode-is-stored-intent`'s accepted case 2. A later `wfctl
auto-approve on` writes the grant event, and the review cap counts from it.

Form 6 grants the mode only in the new worktree, and the grant carries the
agent's session, so the new worktree's session reads it as "another session".
We didn't add an ask rule for it, because Claude Code matches past the leading
assignment, so the rule would have to be `Bash(workmux add:*)` and would prompt
on every worktree an agent creates.

Form 7 is a gap in Codex's matcher. `codex execpolicy check` finds no rule for
`FOO=1 wfctl auto-approve on`, and Codex's docs don't say how it splits a
compound command, so this record doesn't claim either form prompts there.

Form 8 is the cost of reading text in Bob Shell. The guard can't tell a command
that runs wfctl from one that quotes it, so it refuses both, and the person
runs the refused command in their own terminal.

Forms 9 and 10 are rewrites of the plain command, like forms 1 to 3. The CLI
still reads `on` after `--`, and `uv run` takes options before `wfctl`, but
neither host's rules can match every such form. Codex's rules have no wildcard,
so the `--project` form isn't covered there either. In Bob Shell, the guard
refuses both, since it allows a `--` before `on` and finds `wfctl` anywhere
before the phrase.

For all ten, records still start as `proposed`, merging still needs a person,
and the review cap still turns the mode off.

### Must let through

1. Turning the mode off, with no prompt: `wfctl auto-approve off`
2. Reading the mode, with no prompt: `wfctl auto-approve`
3. The creation hook, when a person runs it: `WFCTL_AUTO_APPROVE=1 workmux add 812-foo`
4. The person typing the command themselves: `! wfctl auto-approve on`
5. In Bob Shell, a search for the phrase that doesn't run wfctl: `rg 'auto-approve on' docs/`

## Direct baseline

Add no rule. The `using-wfctl` instruction tells the agent to run `on` only when
a person asked, and nothing else changes. That costs nothing, and it's what the
plan had before the walkthrough. It loses because the instruction is the only
thing between an agent and an unasked grant, and an agent that ignores it leaves
no trace a reviewer sees.

## Owns truth

The person decides whether the agent may turn auto-approve on right now.
Claude Code's or Codex's permission prompt asks them each time, and in Bob
Shell they type the command themselves.

wfctl can't decide this, because whether a person asked is visible only in the
agent's conversation, and wfctl never sees that conversation. The agent
shouldn't decide it either, since it would be approving its own request for
less oversight.

wfctl checks whether the ask rules it installed are still in
`.claude/settings.json`, and `doctor` reports a `.codex/rules/wfctl.rules` that
has drifted. wfctl installed both, so it's the one side that can tell a rule it
put there from one the repo wrote.

## Considered

- **A worktree guard refusal of the agent's grant.**
  `approval-mode-is-stored-intent` already rejected this, because the user
  asked for an agent-driven grant. A refusal would require the person to type
  the command every time. The prompt keeps the agent-driven grant and adds the
  person's yes. Bob Shell has no prompt, so the decision uses the refusal there.
- **Showing the grant in the PR body.** The agent writes the PR body, so it
  could leave the grant out. We didn't choose this because it records the grant
  after the fact instead of asking first, and the user asked for the second.
- **One rule for any wfctl command, `Bash(wfctl:*)`.** We didn't choose this
  because it would prompt on every pipeline step, and people would allowlist
  wfctl to get rid of it, which removes the prompt for `on` too.
- **Bob Shell's deny list, `allowedExecutors[].deniedCommands`.** It blocks a
  command even when execute is auto-approved, which is what the guard refusal
  does. We didn't choose it because Bob Shell reads it only from the user's
  `~/.bob/settings/settings.json`, and wfctl doesn't write that file
  (`approval-settings`). The guard is already installed in the project, so it
  needs no new file.
- **A guard refusal in Codex.** We didn't choose this because Codex can ask,
  and a refusal would make the person type the command every time, the same
  reason the first option above lost in Claude Code.

## Consequences

The managed permission table now has a list kind, so `_managed_permissions`,
the `_settings.py` helpers, and the manifest receipt carry `deny` or `ask` with
each rule. Every existing receipt is treated as `deny`.

Codex now has a layer of its own, `.codex/rules/`, where before it had none.
The guard reads the payload's `tool_name` for the first time, and only for this
check.

An unattended run in Claude Code, Codex, or Bob Shell can't turn the mode on
mid-run without the person. A run meant to start unattended uses the creation
hook, which isn't prompted.

## Log

- 2026-11-19  proposed    — the #407 plan walkthrough found an unasked grant is neither stopped nor visible to a reviewer
- 2026-11-20  proposed    — extended to Codex, with a rules file, and Bob Shell, with a guard refusal, at the user's request during the T034 check
- 2026-11-20  proposed    — security review: `wfctl start --auto-approve` is refused everywhere, the Bob Shell guard refuses only a command that runs wfctl, and Codex's unmatched forms move to Accepts
- 2026-11-20  proposed    — second security review: a third ask rule for `uv run --project`, the Bob Shell guard catches `-- on`, and the forms neither host matches move to Accepts
- 2026-11-20  accepted    — Agreed for #407 on 11/20/2026 · drawing drawings/auto-approve-grant-asks-first-data-flow.svg sha256:4eea401da81a
