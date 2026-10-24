# Quickstart: checking the feature end to end

## 1. The PR check

```bash
uv run wfctl check config
```

It passes once `wfctl.json` lists `"change_sections": ["Needs a spec?"]` and
`.github/pull_request_template.md` has that heading.

Then write five bodies from the template and run `check-body` on each:

```bash
uv run wfctl check-body /tmp/answered.md   # ✓ …: the drawings look right, exit 0
uv run wfctl check-body /tmp/na.md         # ⚠ "Needs a spec?" holds N/A. …, exit 1
uv run wfctl check-body /tmp/comment.md    # ⚠ "Needs a spec?" is empty. …, exit 1
uv run wfctl check-body /tmp/deleted.md    # ⚠ "Needs a spec?" is missing. …, exit 1
uv run wfctl check-body /tmp/bare-no.md    # ⚠ "Needs a spec?" answers yes or no with no reason. …, exit 1
```

Remove the key from `wfctl.json` and run the five again. Each prints what it
printed before this change.

## 2. The skill, for real

```bash
uv run wfctl install-skills --agent claude
```

On a throwaway branch, hand an agent only a handoff for a one-line fix whose
route line names `design-passes`. When it's done:

```bash
git log --reverse --format='%h %s' main..HEAD
```

The transcript shows the agent answering the spec question before it edits any
code. The first commit is a failing test that lands before the fix commit. No
file appears under `docs/architecture/declarations/`.

## 3. The pointers

```bash
uv run pytest tests/test_skill_cross_references.py -q
```

Both new tests pass. Then check that the first one can fail. Delete
`.agents/skills/design-passes` from the `architecture-design` "Not for"
paragraph in `wfctl/agents/`, and run the file again. The section test fails
and names that file. Restore the line.

## 4. The N/A message, for an agent

Start an agent with a fresh context. Give it `/tmp/na.md` from step 1 and the
`⚠ "Needs a spec?" holds N/A. …` line `check-body` printed for it, and ask it
to fix the body. Don't tell it what the section asks for.

```bash
uv run wfctl check-body /tmp/na.md
```

SC-005 passes when the agent's first rewrite holds a yes or no and a
one-sentence reason under "Needs a spec?", and `check-body` then prints the `✓`
line. A bare "No.", "None", or another N/A fails it. Only the first rewrite
counts.

## 5. The panel, on a fix that makes a design decision

On a throwaway branch, commit a fix that has the worktree guard read a new
setting from `wfctl.json`, with no record and no spec. Run the review panel
over it with `.agents/skills/fanning-out-code-review`.

At least one reviewer reports the new setting as a finding, and it shows in the
panel's table. Then commit the same fix with a record under
`docs/architecture/` that covers the setting, and run the panel again. No
reviewer reports the setting.
