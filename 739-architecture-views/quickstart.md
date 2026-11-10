# Quickstart: checking the change by hand

Run these after `uv run wfctl install-skills`, from the worktree. They cover what the test suite can't: whether the templates are enough on their own, and what a person sees.

## 1. The view templates

Open each template under `.agents/skills/architecture-design/views/` and fill it for a made-up capability, such as a library that lends books. Check that each one:

1. Opens with a plain summary and states the one question the view answers.
2. Asks for one drawing.
3. For the container and component templates, explains the stability layout in its own words: stable parts above a labeled line, arrows toward the stable side, and a wrong-way arrow in red.
4. Carries a `covers` frontmatter line in bracket form.
5. For the container and component templates, asks for a label on every arrow naming the import or call that creates it.

## 2. Session start

```bash
uv run wfctl arch context
```

On this branch, the output ends with the `Views` block in `contracts/cli.md`: two present views, and two missing component views for architecture-records and design-method. If a commit to `wfctl/` landed after the container view was drawn, such as a fix from the review panel, the container view prints as `stale:` with the commit count. That's the mark working, not a defect. Commit an update to the view and run the command again to see it print as a plain path.

## 3. A record with two kinds

Write a throwaway record under `docs/architecture/` declaring `diagram: [data-flow, sequence]`, with a `### data-flow` and a `### sequence` heading under `## Boundary`, each holding a mermaid drawing. Give the sequence drawing an `alt` block.

```bash
uv run wfctl arch accept --dry-run -- <slug>
```

It reports the record would be accepted. Delete the sequence drawing and run it again. The refusal names the missing sequence drawing and the fix. Run `uv run wfctl doctor` and check it shows the same problem as a warning. Delete the throwaway record.

## 4. Nothing new from the health checks

```bash
uv run wfctl doctor
uv run wfctl check config
```

Neither reports anything that wasn't there before the change.
