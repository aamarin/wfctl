# Contract: the CI `tag` job

Unchanged: it runs on `main` only, `needs: [test, wheel, lint]`, reads the
version with `tomllib`, creates the tag on the commit the job ran on when the
tag is missing, and creates the release when the release is missing, each
keyed on its own existence.

Changed: the job finds and checks the release text before it tags, and the
release text is that commit's body.

```
if git rev-parse -q --verify "refs/tags/v$v" >/dev/null \
   && gh release view "v$v" >/dev/null 2>&1; then
  echo "v$v already released"; exit 0
fi

rel=$(git log -1 --no-merges --format=%H --fixed-strings --grep "chore(release): cut $v" HEAD)
[ -n "$rel" ] || fail "no commit with the subject chore(release): cut $v"
[ "$(git log -1 --format=%s "$rel")" = "chore(release): cut $v" ] \
  || fail "the commit found for $v has a different subject"
[ "$(git show "$rel:pyproject.toml" | python3 -c '<tomllib version>')" = "$v" ] \
  || fail "the commit found for $v carries a different version"
git log -1 --format=%b "$rel" > "$RUNNER_TEMP/notes.md"
grep -q '[^[:space:]]' "$RUNNER_TEMP/notes.md" \
  || fail "the release commit for $v has no release notes in its body"

# then, as today: tag if missing, push the tag
gh release create "v$v" --notes-file "$RUNNER_TEMP/notes.md"   # if missing
```

`--no-merges` is load-bearing. This repository's merge commits carry the pull
request's title in their body, so the release pull request's own merge also
contains `chore(release): cut $v`, and without the flag the lookup returns that
merge, fails the subject check, and stops every release.

`fail` prints the message as an error annotation and exits 1. Every check runs
before the tag is created, so a failure leaves no tag and no release. There is
no `--generate-notes` anywhere in the job.

When a version changes on `main` without a release commit, for example a bump
made by hand before protection is on, the job fails with the first message. The
fix is to publish that one release by hand with its notes, after which the job
finds the release present on its next run.

The comment above the job says what it publishes and why the version call is a
person's, replacing the comment that says the bump belongs in the pull request
that makes the change.

# Contract: the CI `release-note` job

```
release-note:
  if: github.event_name == 'pull_request'
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - run: python3 .github/scripts/check_release_note.py
```

Not in the tag job's `needs`. It runs on pull requests only, and on `main` it
could only pass. Its job name, `release-note`, is one of the five checks the
ruleset requires, so renaming the job means editing
`.github/rulesets/main.json` and applying it again.

# Contract: `.github/rulesets/main.json`

```json
{
  "name": "main",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": { "ref_name": { "include": ["refs/heads/main"], "exclude": [] } },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false } },
    { "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": false,
        "required_status_checks": [
          { "context": "test (3.11)" },
          { "context": "test (3.13)" },
          { "context": "wheel" },
          { "context": "lint" },
          { "context": "release-note" } ] } }
  ]
}
```

Applied once, after this feature merges, with:

```
gh api -X POST repos/{owner}/{repo}/rulesets --input .github/rulesets/main.json
gh api -X PATCH repos/{owner}/{repo} -F allow_squash_merge=false -F allow_rebase_merge=false
```

Read back with:

```
gh api repos/{owner}/{repo}/rules/branches/main
gh api repos/{owner}/{repo}/rulesets --jq '.[] | select(.name == "main") | .id'
gh api repos/{owner}/{repo}/rulesets/<id> --jq '.bypass_actors'
gh api repos/{owner}/{repo} --jq '{merge: .allow_merge_commit, squash: .allow_squash_merge, rebase: .allow_rebase_merge}'
```

The first lists the rules in force on `main`, with the five required checks. The
second and third find the ruleset and show its bypass list is `[]`, which is
what includes administrators; neither the plain `rulesets` listing nor
`rules/branches/main` returns it. The last shows merge commits as the only
method.

A later edit to the file is applied with `-X PUT
repos/{owner}/{repo}/rulesets/<id>`. Nothing checks that the applied ruleset
still matches the file, so AGENTS.md says to read it back after applying.
