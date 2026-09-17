# Quickstart — #200, is a session open now?

How to see the defect, and how to see it fixed. Every command runs from a
worktree; `uv run` is not optional in this repository (`AGENTS.md`).

## See the defect on today's build

```bash
export WFCTL_STATE_DIR=$(mktemp -d)
uv run wfctl status --json | grep session_started     # false
uv run wfctl start
uv run wfctl status --json | grep session_started     # true
```

Now open a second conversation on the same branch — or just imagine one, since
nothing distinguishes them. Run the gate again:

```bash
uv run wfctl status --json | grep session_started     # still true
```

That `true` is the defect. It is the same answer for the conversation that opened
the session and for one that has never run anything, and every gate reading it
treats them alike.

## See it fixed

```bash
export WFCTL_STATE_DIR=$(mktemp -d)

# Conversation A opens the session
WFCTL_SESSION_ID=aaa uv run wfctl start
WFCTL_SESSION_ID=aaa uv run wfctl status --json | grep -E 'session_(open|holder)'
#   "session_open": true
#   "session_holder": "self"

# Conversation B has never announced itself
WFCTL_SESSION_ID=bbb uv run wfctl status --json | grep -E 'session_(open|holder)'
#   "session_open": false
#   "session_holder": "other"

# B is refused by the commands that gate
WFCTL_SESSION_ID=bbb uv run wfctl resume; echo "exit=$?"
#   No wfctl session for this conversation — …
#   exit=1

# B takes the branch over with the one move it has
WFCTL_SESSION_ID=bbb uv run wfctl start
#   ✓ Session started — took over from another conversation

# and A is now the one refused
WFCTL_SESSION_ID=aaa uv run wfctl resume; echo "exit=$?"
#   exit=1
```

## See that an unwired repository is untouched

The row that carries FR-006 and SC-002. With no identity presented at all, on a
branch that has a holder:

```bash
unset WFCTL_SESSION_ID
uv run wfctl status --json | grep -E 'session_(started|open|holder)'
#   "session_started": true
#   "session_open": true        ← mirrors session_started
#   "session_holder": "unknown"

uv run wfctl resume; echo "exit=$?"     # exit=0 — proceeds, as released
uv run wfctl start                      # no takeover; holder unchanged
```

A caller presenting nothing must never displace a holder. Check that it did not:

```bash
grep '"event": "start"' "$WFCTL_STATE_DIR"/*/events.jsonl | tail -1
#   still carries "session_id": "bbb"
```

## Wire your own host

Map the host's variable to wfctl's, once, in your shell profile — beside
`WFCTL_AGENT`, and for the same reason: committed config names no host
(`no-hardcoded-agent`).

```bash
# ~/.zshrc
export WFCTL_SESSION_ID="$CLAUDE_CODE_SESSION_ID"
```

If your host's identity turns out to rotate more often than a conversation does,
you will see it as repeated takeovers inside one sitting. That is the symptom to
watch for, and the fix is this line, not a change to wfctl.

## Run the bar

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
uv run wfctl doctor
```

Then, because this feature changes two shipped skills and the suite checks that
skills ship rather than that they read well:

```bash
uv run wfctl install-skills
```

and exercise the changed `/start-session` and the orchestrate gate by hand.
