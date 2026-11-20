# Quickstart: checking #828 by hand

These steps check the feature end to end on a real worktree. The automated tests cover each case, and this is the manual check the spec's validation strategy asks for.

1. Run the checks and see each command's numbers in the event log:

   ```bash
   uv run wfctl verify
   tail -1 "$(uv run wfctl state-dir)/events.jsonl"
   ```

   The last line is a `verify` event with `seconds` and one `commands` entry per command. Its `seconds` is within 5 seconds of how long the run took on the clock (SC-001).

2. Read the summary:

   ```bash
   uv run wfctl timings
   uv run wfctl timings --since all
   uv run wfctl timings --since 3w
   ```

   The first prints the last 30 days, with this run counted in the verify table. The second's heading says it used every event. The third is refused and exits 1.

3. Check a span. The user runs this step, since the worktree guard refuses an agent that creates or removes a second worktree. Create a throwaway worktree with `workmux add`, remove it with `workmux remove`, and read the last line of that branch's event log. It's a `worktree-span` event whose `created` is within 5 seconds of when `workmux add` ran (SC-003).

4. In a pfms worktree, run `wfctl verify` and then `wfctl timings`. The pytest row's largest process should be close to one pytest worker's known size, which confirms the design's second key assumption.
