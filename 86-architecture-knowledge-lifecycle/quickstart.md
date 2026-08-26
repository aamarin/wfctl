# Quickstart: Architecture Knowledge Lifecycle

How to verify each story works, in the order they ship.

## Definition of done

Every change in this feature passes the documented three, then `doctor`:

```bash
uv run pytest -q
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
wfctl doctor          # exit 0
```

Changes under `wfctl/agents/` are **not** covered by that. The suite checks
skills ship and cross-reference; it does not check they work. Those need:

```bash
wfctl install-skills
# then exercise the changed skill in a live session
```

## Story 1 — a decision survives the session (issue A)

```bash
wfctl arch-root
# → /path/to/repo/docs/architecture

# run a design session that reaches an ownership decision, then:
ls docs/architecture/
# → wfctl-runs-the-check.md
```

Confirm the record carries `Owns truth` with both halves — which side owns the
question, and why the other cannot compute it. A record missing that field has
reproduced the failure this feature exists to fix.

Out-of-tree check:

```bash
WFCTL_ARCH_DIR=/tmp/elsewhere wfctl arch-root
# → /tmp/elsewhere
# → ⚠ Root is outside the working tree. …
```

Supersession leaves the predecessor's body untouched:

```bash
git diff HEAD~1 -- docs/architecture/agent-runs-the-check.md
# → only `status:` and one appended Log line
```

Retirement of the orphaned command:

```bash
wfctl promote
# → Error: No such command 'promote'.
grep -rn "memory-candidates\|WFCTL_CANDIDATES_FILE" . --exclude-dir=.git
# → no hits
```

## Story 2 — the agent sees only what's in force (issue B, step 1)

Set up one record in each status, then:

```bash
wfctl arch context
# → exactly the accepted one listed
# → "4 records not shown (1 proposed, 1 superseded, 1 rejected, 1 retired)"
```

Three cases that must not fail:

```bash
# empty root
wfctl arch context     # → "no accepted decisions", exit 0

# record with no status
wfctl arch context     # → excluded, and named in a warning, exit 0

# record with a garbage status
wfctl arch context     # → excluded, never treated as accepted
```

That last one is the load-bearing test. Defaulting an unparseable record to
in-force would present an unreviewed decision as binding.

Delivery to the agent:

```bash
/start-session
# → the in-force set appears in the session report
```

## Story 3 — the design step cannot skip its boundary (issue B, step 2)

```bash
# at the design step, no record present
wfctl next
# → ✗ design: no architecture record for this change.

wfctl arch none --reason "copy edit, no new state"
# → ✓ Recorded: no boundary changed — "copy edit, no new state"

wfctl next
# → advances
```

Confirm the declaration lands in the change under review — a reviewer must be
able to see the claim and disagree with it.

## Story 4 — knowledge lives in one place (issue B, step 3)

Run only after Story 2 passes. Moving content before the projection exists puts
it where nothing reads it.

After relocating the layer model out of `AGENTS.md`:

```bash
grep -n "layer model\|install output" AGENTS.md
# → no hits

wfctl arch context | grep -A2 layer-model
# → present in the in-force set
```

The real test is behavioural, and it is SC-004. In a fresh session, ask an agent
to fix a typo in a skill. It must edit `wfctl/agents/skills/…`, not
`.agents/skills/…`. Three of three trials.

Editing `.agents/` reads correctly, passes the suite, and ships nothing —
`.agents/` is gitignored install output. That silent failure is exactly what the
relocated knowledge exists to prevent, so it is the only trial that proves the
move was safe.
