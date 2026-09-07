# No new boundary — 121-level3-records-in-pr

Level-3 records gain a visibility check, and it draws no line. `wfctl arch check`
wraps `touched_on_this_branch`, which `arch none` already asks of a level-2
declaration for the same reason — the tool has held authority for "is this claim
part of the change under review" since that command shipped. Adding a second
caller moves nothing.

Two candidates were weighed and both drew a line, which is why declaring the
absence is the finding rather than the default. `wfctl start` refusing to begin a
session moves authority for *may this session proceed* from the agent to the
tool; a `PreToolUse` hook blocking the write moves it to the harness, and only
for the agent that reads that config. Both were dropped once the question could
be asked of the committed file, which answers every case they were each
introduced for — including a record written into a different checkout of the same
repository, which every path comparison passes.

`a-rule-is-expressed-as-a-check` governs the form and is not amended: the
violation is visible in an artifact the work already produces, so the rule ships
as a check rather than as prose in the skill. The first version of this change
shipped it as prose naming a git command, and a review panel found that command
answering a different question twice over — which is the record's argument, not
this one's.
