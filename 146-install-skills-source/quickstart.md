# Quickstart: install-skills source

The end-to-end exercise the test suite cannot perform. AGENTS.md is explicit that
a change under `wfctl/agents/` is not verified by the suite alone, and the
handoff for #146 is explicit that a run which only installed from the default has
not tested this feature.

Run every command through `uv run --frozen`, per AGENTS.md — the same wfctl for
installing and checking.

## Setup

A second checkout to install from. Any worktree of this repo works:

```bash
git fetch origin pull/116/head:pr-116
workmux add 116-pr --base pr-116
```

Change something visible in it, so the two sources are distinguishable:

```bash
echo "" >> ../116-pr/wfctl/agents/skills/start-session/SKILL.md
```

## 1. Install from the named source

```bash
uv run --frozen wfctl install-skills --from ../116-pr
```

Expect `✓ Installed from ../116-pr`. Confirm the installed file carries the edit:

```bash
tail -1 .agents/skills/start-session/SKILL.md
```

## 2. The check reports it as a state, not as drift

```bash
uv run --frozen wfctl doctor
```

Expect `✓ base: skills current (from <abs path to ../116-pr>)` — `doctor`
prints the resolved path, not the one you typed — and **exit 0**. This is the
assertion the whole feature exists for — before this change, the same situation
reported drift on every run.

```bash
echo "exit: $?"
```

## 3. The check notices the source moving on

```bash
echo "" >> ../116-pr/wfctl/agents/skills/start-session/SKILL.md
uv run --frozen wfctl doctor
```

Expect `⬆ base: source changed since install — <abs path>`, exit 1, and a remedy
line that **contains `--from <that same abs path>`**, single-quoted if it holds
a space. Read the printed command; the point of
the feature is that running it does not undo the test.

## 4. The remedy repairs rather than replaces

Run exactly what step 3 printed, then check again:

```bash
uv run --frozen wfctl doctor
```

Expect green, and still `(from <abs path>)`. If it says `wfctl 0.16.0` here, FR-008
has failed.

## 5. An unreachable source degrades honestly

```bash
mv ../116-pr ../116-pr-moved
uv run --frozen wfctl doctor
```

Expect `⚠ base: installed from … — source is gone, can't check`, and the run must
not fail on account of this alone. Restore it:

```bash
mv ../116-pr-moved ../116-pr
```

## 6. A bare install replaces, and says so

```bash
uv run --frozen wfctl install-skills --prune --yes
```

Expect the `⚠ Will replace an install from <abs path> …` line **despite `--yes`**,
then a normal install. Then:

```bash
uv run --frozen wfctl doctor
```

Expect `✓ base: skills current (wfctl 0.16.0)` — the drift finding is gone
because the project is genuinely back on the default. Confirm the record dropped
the key:

```bash
grep -c '"source"' .wf-skills-manifest.json    # expect 0
```

## 7. A bad source refuses

```bash
uv run --frozen wfctl install-skills --from /tmp
```

Expect a non-zero exit naming both locations it looked in, and the repo
unchanged — no copy, no manifest write.

## 8. A repo with no wfctl source tree can install from a checkout

This is SC-005, and it is the half of the justification that survived #75. Every
step above ran inside this repo, where `uv run wfctl` exists. A consumer has no
such thing.

```bash
mkdir -p /tmp/wfctl-consumer && git -C /tmp/wfctl-consumer init -q
cd /tmp/wfctl-consumer
```

Install from an absolute path to a wfctl checkout, using the **released** wfctl
on PATH — a consumer has no other.

Until this feature ships, the release on PATH has no `--from`, so the step cannot
be run as written. Substitute `uv run --frozen --project <this worktree> wfctl`
for the two commands below: the current repo still holds no wfctl source tree,
which is the whole of what the step asserts.

```bash
wfctl install-skills --from ~/Development/wfctl/wt/146-install-skills-source --yes
wfctl doctor
```

Expect the install to report the named source, and `doctor` to exit 0 naming it.
The point is that neither command needed a wfctl source tree in the current repo.

```bash
cd - && rm -rf /tmp/wfctl-consumer
```

## Teardown

```bash
workmux remove 116-pr
git branch -D pr-116
uv run --frozen wfctl install-skills --prune --yes
uv run --frozen wfctl doctor
```

Leaves the worktree installed from the release and green.
