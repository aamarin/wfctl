# No new boundary — 121-level3-records-in-pr

Level-3 records gain a visibility check, and it draws no line. The check asks git
whether it tracks the record it just wrote, in this working tree — a question the
skill answers about its own output, so no truth moves between sides and no
component gains authority over another.

Two candidates were weighed and both drew a line, which is why declaring the
absence is the finding rather than the default. `wfctl start` refusing to begin a
session moves authority for *may this session proceed* from the agent to the
tool; a `PreToolUse` hook blocking the write moves it to the harness, and only
for the agent that reads that config. Both were dropped once the post-write
question was found to answer every case on its own, including the one they were
each introduced for — a record written into a different checkout of the same
repository, which every path comparison passes and `git ls-files` rejects because
that checkout is not this one.

`a-rule-is-expressed-as-a-check` governs the form and is not amended: the
violation is visible in an artifact the work already produces, so the rule ships
as a check rather than as prose in the skill.
