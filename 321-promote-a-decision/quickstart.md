# Quickstart — #321

What to run to see the feature work, and what each command should print. This is
the manual exercise the test suite does not perform: `AGENTS.md` says a change
under `wfctl/agents/` is not verified by the suite, and the same is true of a
console surface whose value is what a person reads.

Run everything through `uv run` — this repository has two wfctls on PATH and only
`uv run` answers "does the installed tree match the source I am editing".

## 1. The gap, before

```bash
uv run wfctl arch context | tail -1
```

Expect a count line naming the withheld records — 15 proposed once this branch's
own two records are on it.

## 2. Name the backlog

```bash
uv run wfctl arch accept
```

Expect the promotable slugs listed, and exit 1. Check it:

```bash
uv run wfctl arch accept; echo "exit=$?"
```

## 3. Accept one

```bash
uv run wfctl arch accept a-human-accepts-a-decision --agreed "<where you agreed>"
```

Expect `✓ … is accepted` and the `Log` line quoted back.

## 4. The record changed by exactly two lines

```bash
git diff docs/architecture/a-human-accepts-a-decision.md
```

Expect one `-status: proposed` / `+status: accepted` pair and one added `Log`
line. Anything else is a VR-005 violation.

## 5. The contract grew, and the count dropped

```bash
uv run wfctl arch context | grep a-human-accepts-a-decision
uv run wfctl arch context | tail -1
```

Expect the slug to appear, and the count to be one lower than step 1.

## 6. The negative case

```bash
uv run wfctl arch context | grep promised-evidence-blocks-on-silence
```

Expect nothing. A rule that promotes everything is the same as no rule.

## 7. The refusals

```bash
uv run wfctl arch accept a-human-accepts-a-decision --agreed "again"   # already accepted
uv run wfctl arch accept no-such-record --agreed "x"                   # unknown slug
uv run wfctl arch accept a-branch-is-claimed-not-inherited             # no citation
uv run wfctl arch accept a-branch-is-claimed-not-inherited --agreed "<where>"
```

Each exits 1 and prints its own sentence. After all four:

```bash
git status --short docs/architecture/
```

Expect only the record from step 3 to differ.
