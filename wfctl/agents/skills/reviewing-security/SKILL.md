---
name: reviewing-security
description: 'Run both security reviews wfctl ships over one review run''s commits, and write one report wfctl can count. Use when you are a reviewer in the security group of a review panel and have been given a reviewer id, a commit range, and a reports folder from `wfctl review start`.'
---

# Reviewing security

A security reviewer on a wfctl panel runs two reviews over the same commits and
writes one report. Both reviews come from other projects and ship beside this
skill unedited:

1. `../security-and-hardening/SKILL.md`, from `addyosmani/agent-skills`. It is a
   hardening guide with a threat model, red flags, and a checklist.
2. `references/security-review.md`, the prompt behind the `/security-review`
   command in `anthropics/claude-code-security-review`. It looks for
   high-confidence vulnerabilities that someone could actually exploit.

Read both files by those paths. Don't run `/security-review` as a command,
because Claude Code has a built-in command with the same name, and it would run
in place of the file here and review a different set of commits.

Both files were written for a different setting, so this skill says where they
don't apply. Where this skill and either file disagree, this skill wins.

## What you're given

The agent that launched you passes on three values from `wfctl review start`:

1. Your reviewer id, such as `s1`.
2. The commit range, such as `a1b2c3d..9f8e7d6`. The second sha is the head.
3. The reports folder, such as `<state>/reviews/security/runs/003/`.

Your report goes in that folder as `<id>.md`, such as
`<state>/reviews/security/runs/003/s1.md`.

## Run the `/security-review` prompt over the range

Skip the prompt's git section, the four blocks from `GIT STATUS` to
`DIFF CONTENT`. They compare against `origin/HEAD`, so they show every commit on
the branch rather than the ones this run covers. Get the same information for
the range instead:

```bash
git log --no-decorate a1b2c3d..9f8e7d6
git diff --name-only a1b2c3d..9f8e7d6
git diff a1b2c3d..9f8e7d6
```

Then follow the rest of the prompt as written: its objective, categories,
exclusions, method, false-positive filtering, and the cut at a confidence of 8.

The prompt's last three steps launch sub-tasks. If you can launch them, do. If
you can't, run the three steps yourself in order. Find the vulnerabilities,
check each one against the `FALSE POSITIVE FILTERING` block, and then drop any
with a confidence below 8.

## Run the hardening review over the same range

Read the `security-and-hardening` skill as a reviewer, not as the author of the
change. Map the trust boundaries the change crosses, then check the diff against
the skill's Red Flags and its Review Checklist. Its `hardening-patterns.md`
reference shows what a fix looks like.

The skill cites its checklist as `../../references/security-checklist.md`. That
path points outside the installed skills folder and finds nothing. The checklist
ships at `../security-and-hardening/references/security-checklist.md`, beside
`hardening-patterns.md`.

## Write one report

Both reviews go in one report, written to the file named above. This outranks
three things in the `/security-review` prompt:

1. Its last line, which says your reply holds the markdown report and nothing
   else. You write the report to the file instead.
2. The line in its false-positive block that says "Do not use the bash tool or
   write to any files." You run the `git` commands above and write the file.
3. Its sub-task steps, when you can't launch sub-tasks, as the section above
   says.

The prompt's `allowed-tools` frontmatter doesn't apply either. You read the file
as a reference, and it never runs as a command.

wfctl counts a report only when it has two lines:

1. `Reviewed: <sha>`, naming the head of the range with at least seven hex
   digits.
2. A verdict as the last non-blank line, either `Verdict: Approve` or
   `Verdict: Request changes`.

A report missing either one counts as missing, so the security group can't
complete. Request changes when a finding from either review should be fixed
before the change merges, and approve when none should.

```markdown
Reviewed: 9f8e7d6

## /security-review

# Vuln 1: Command injection: `app/export.py:42`

* Severity: High
* Description: …
* Exploit Scenario: …
* Recommendation: …

## security-and-hardening

No findings.

Verdict: Request changes
```

## If you can't write the file

If your host refuses the write, don't retry it another way. Make the report your
whole reply, in the same shape, and add one line before it saying what refused
the write. The agent that launched you saves the report with `wfctl relay`.
