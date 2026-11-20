# Research: Auto-approve has its own command

Every question below was answered by reading the code. None needed outside
research.

## 1. Where the refusal for another session's branch comes from

- **Decision**: Call `build_report(spec_dir, repo_root, agent_dir, caller)` and
  refuse when `session_holder == "other"`.
- **Rationale**: `session_holder` is the holder relation `status` already
  reports. The `session_open_for` function returns `"other"` in two cases: a
  different conversation holds the branch, or this conversation's own session
  was ended with `wfctl end`. The #200 design gives both cases the same message
  and the same fix. So the refusal says that no session is open for this
  conversation, which is true in both cases, and `/start-session` fixes both.
  A raw `last_session_id(...) != caller` comparison would let the ended case
  through, which is the #200 bug `start`'s comment describes. `"none"` and
  `"unknown"` are allowed, because the creation hook runs before any session
  exists, and a caller with no identity behaves as before.
- **Alternatives considered**: Comparing `last_session_id` directly. We didn't
  choose this because of the #200 case above. We also didn't give the two
  `"other"` cases separate messages, because that needs `ended` exported from
  evidence to tell apart two cases with the same fix. The `speckit-orchestrate`
  gate already words this state the same way.

## 2. Where the issue refusal comes from

- **Decision**: Call `_refuse_unless_the_issue_allows_a_session()` first, before
  `_resolve_context()`, the same as `start`.
- **Rationale**: It prints the verdict's lines verbatim with their fix command
  and exits 1, and it writes nothing. FR-005 asks for exactly the message `start`
  prints.
- **Alternatives considered**: A new check scoped to the mode. We didn't choose
  this because two checks would drift.

## 3. How the grant event carries the session

- **Decision**: `grant_auto_approve(agent_dir, granted, session=None)`. When
  `session` isn't None, the event gets `session=<id>`. The mode file is
  unchanged.
- **Rationale**: Evidence can't import session continuity, so the CLI resolves
  the caller with `presented_identity` and passes it in. Omitting the field when
  there's no identity matches how the `start` event treats `session_id`.
- **Alternatives considered**: Writing `session: null`. We didn't choose this
  because events written before this change have no field, and one absent
  shape is simpler to read than two.

## 3a. Why `on` writes nothing when the mode is already on

- **Decision**: The grant helper reads `mode.json` and the newest `mode` event
  first, the cap's revocation included. If the request is `on`, the mode is
  already on, and the newest event is a grant, the helper writes no file and
  appends no event, and the command still prints the notice. If `mode.json`
  reads on and the newest event isn't a grant, as after a hand edit, `on`
  writes as usual, so the review cap gets its starting point. That covers a
  hand edit after a revocation too, where the last grant a person made is
  older than the revocation. A revoked mode reads as off, so `on` after a
  revocation is a new grant.
- **Write order**: the helper appends the event first and writes `mode.json`
  second. When either write raises `OSError`, the command prints
  `✗ Couldn't record the auto-approve change: <error>` and exits 1. A failed
  append leaves everything as it was. A failed file write after the append
  leaves an event the file doesn't match. After `on`, the mode still reads off,
  which is the safe direction, and the bare command says "turned off outside
  wfctl". After `off`, the mode reads on with no grant as the newest event, so
  the bare command says no grant is on record. The
  next `on` or `off` repairs either. `off` always writes, since it
  never resets the review count. `start --auto-approve` calls the same helper,
  so the same rule applies to it.
- **Rationale**: `review_count` restarts at every `mode` event with
  `auto_approve: true`. If every `on` appended one, an agent could reset the
  review cap by running `on` again before the cap revoked the mode. That breaks
  the record's rule that only a grant after a revocation gives three more
  reviews. Skipping the write keeps that rule without changing `review_count`.
  It also keeps the earlier grant as the one `wfctl auto-approve` reports,
  which is the grant that turned the mode on.
- **Alternatives considered**: Changing `review_count` to ignore a grant while
  the mode is already on. We didn't choose this because the writer can avoid
  producing that event, and the log would otherwise record a grant that changed
  nothing. Refusing `on` while the mode is on. We didn't choose this because
  spec US1 scenario 3 asks it to succeed.

## 4. How the relation is worded when the caller has no identity

- **Decision**: "an unknown session" when either the mode change or the caller has no
  identity. "this session" when both are present and equal. "another session"
  when both are present and differ. The review cap's revocation event
  (`by: "wfctl"`) is not a mode change by a person and is never read as one.
- **Rationale**: wfctl can't compare against a caller that presents nothing.
  `status` already reports the holder as `unknown` in that case, so the grant
  line uses the same word.
- **Alternatives considered**: Saying "another session" when only the caller is
  missing. We didn't choose this because it claims a difference wfctl can't
  observe.

## 5. What the bare command prints when the cap revoked the mode

- **Decision**: The mode line is `_revocation_line`'s form, the one `status`
  and `resume` print: `auto-approve off — <revocation reason>`. Then the last
  mode change's line if one is on record.
- **Rationale**: `status` and `resume` already print the reason in place of the
  notice. The person who granted the mode needs to see both that it stopped and
  who started it.

## 6. How `post_create` is checked for a grant line

- **Decision**: `post_create_grants(text)` in `install/_workmux.py` returns True
  when a live line in the `post_create:` block contains `auto-approve on`.
- **Rationale**: `_live_lines` already scopes to the block and drops commented
  lines, which covers acceptance scenarios 2 and 3 of User Story 4.
  `post_create_wired` matches on `install-skills` the same way.
- **Alternatives considered**: A YAML parser. We didn't choose this because
  wfctl has no YAML dependency and the existing checks are text scans.

## 7. The grant line's shell form

- **Decision**:
  `- cd "$WM_WORKTREE_PATH" && [ "$WFCTL_AUTO_APPROVE" = 1 ] && wfctl auto-approve on || true`
  in the shipped seed, and `uv run wfctl` in this repository's copy. It goes
  last in `post_create`.
- **Rationale**: `[ "$X" = 1 ]` is a string comparison, so `true`, `yes`, `01`,
  and empty all fail it, which is the threat model's catch case 4. `|| true`
  keeps a refused grant from failing `workmux add`. It goes last because the
  issue check reads the tracker config that `install-skills` puts in the
  worktree.
- **Alternatives considered**: `${WFCTL_AUTO_APPROVE:+...}`. We didn't choose
  this because it tests for non-empty rather than for `1`, and `0` would grant
  the mode, as the issue body shows.

## 8. Whether `start` keeps its own refusal behavior

- **Decision**: `start --auto-approve` calls the shared helper with the caller's
  identity, and doesn't refuse on `"other"`.
- **Rationale**: `start` takes the branch over, so by the time its grant lands
  this session holds the branch. That is the threat model's accepted case 2.
  The grant stays before `build_report` and the "Already initialized" return,
  for the reason `start`'s comment gives.
