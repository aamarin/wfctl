# Quickstart: verifying the change

`AGENTS.md` is explicit that the suite is not sufficient here — *"A change to
anything under `wfctl/agents/` is not verified by the test suite alone: run
`wfctl install-skills` and exercise the thing you changed."* This is that
exercise, plus the automated gates around it.

## Gotcha first — which wfctl you are running

A globally installed `wfctl` resolves to the **released wheel**, not this branch
(#75). Every command below uses `uv run wfctl` from inside the worktree, which
resolves the local source. Running bare `wfctl` will install the old bundle and
the manual checks will pass or fail for the wrong reason.

```bash
uv run wfctl --version      # expect the version in this branch's pyproject.toml
```

## 1. Automated gates

The full bar for a code change, per `AGENTS.md`:

```bash
uv run pytest -q                          # expect green; ~521 tests, ~27s
uv run ruff check wfctl/ tests/
uv run mypy wfctl/
```

Then the drift check. It compares what wfctl installed in *this* repo against
what it now ships, so after changing six skills it is expected to report them
behind until reinstalled:

```bash
uv run wfctl doctor
```

## 2. Conformance — the reason the change exists

Confirm the counts the spec claims (SC-001, SC-002). This is the one-off run; the
suite's own assertion is offline and does not fetch anything.

```bash
for d in wfctl/agents/skills/*/; do
  r=$(uvx --from 'git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref' \
        skills-ref validate "$d" 2>&1)
  case "$r" in
    "Valid skill:"*) ;;
    *) echo "FAIL $(basename $d) :: $(echo "$r" | sed -n '2p' | sed 's/^ *- //')" ;;
  esac
done
```

Note the glob: `Valid*` also matches `Validation failed`, which silently reports
a clean sweep over a broken bundle.

```
expected after the change
─────────────────────────
FAIL i-have-adhd :: Unexpected fields in frontmatter: disable-model-invocation

27 valid · 1 failed
```

Any other line is a regression.

## 3. Manual — the Claude layer gains one skill

```bash
SCRATCH=$(mktemp -d) && git -C "$SCRATCH" init -q
uv run wfctl install-skills --agent claude --yes    # run from the worktree
ls "$SCRATCH/.claude/skills/"
```

Expected — 7 entries, the addition being the vendored skill:

```
architecture-decisions
conversation-response-shape
design-levels
i-have-adhd                      ← new
receiving-code-review
using-superpowers
verification-before-completion
```

And no skill in the installed tree carries the removed key:

```bash
grep -rl '^deployment:' "$SCRATCH/.agents/skills/" ; echo "exit=$?"
# expect no output, exit=1
```

## 4. Manual — the mark survives an upstream replacement (FR-004)

The point of moving the switch out of the file. Overwrite the vendored skill with
a copy carrying nothing wfctl wrote, reinstall, and confirm it is still there.

```bash
python3 - <<'PY'
from pathlib import Path
p = Path("wfctl/agents/skills/i-have-adhd/SKILL.md")
p.write_text("---\nname: i-have-adhd\ndescription: upstream copy\nlicense: MIT\n---\n\nBody.\n")
PY
uv run wfctl install-skills --agent claude --yes
ls "$SCRATCH/.claude/skills/i-have-adhd"     # expect it present
git checkout -- wfctl/agents/skills/i-have-adhd/SKILL.md
```

Restore the file before committing — the checkout on the last line is not
optional.

## 5. Manual — no other agent is affected (FR-006)

```bash
SCRATCH2=$(mktemp -d) && git -C "$SCRATCH2" init -q
uv run wfctl install-skills --agent bob --yes
ls "$SCRATCH2/.claude" 2>&1        # expect: No such file or directory
ls "$SCRATCH2/.bob/skills/" | wc -l # expect 28
```

## 6. Manual — uninstall removes the native copies (FR-007)

```bash
uv run wfctl uninstall-skills --agent claude --yes
ls "$SCRATCH/.claude/skills" 2>&1  # expect: No such file or directory
ls "$SCRATCH/.agents/skills/" | wc -l   # expect 28 — the base layer survives
```

The last line is the one worth reading: uninstalling an agent must not take the
agent-neutral store with it.

## 7. Clean up

```bash
rm -rf "$SCRATCH" "$SCRATCH2"
git status --short          # expect clean apart from intended changes
```

## What is deliberately not verified here

- **Removing a name from the discoverable set.** The stale `.claude/skills/<name>`
  is left on disk and no command reports it — known, out of scope, tracked as
  #110.
- **Unprompted invocation of the vendored skill.** It declines model-initiated
  invocation in its own frontmatter, so it is listed and loadable on request but
  never self-invoking. #108's remaining half.
