# Quickstart — record leads with drawing

**Feature**: `109-record-leads-with-drawing`

What someone does differently once this ships, end to end. This is also the
manual pass the Validation Strategy requires: the suite cannot prove that a
skills change reads well, and it cannot open github.com.

## Write a record that can be accepted

1. Copy `record-template.md`. Its frontmatter now carries a `diagram:` line and
   its `## Boundary` section is no longer marked optional.
2. Choose the kind from what the decision is about:

   | The decision settles | Kind |
   |---|---|
   | who computes a value, who may assert it | `data-flow` |
   | what is inside a component and what is outside | `component` |
   | a lifecycle, a transition, a gate | `state` |

3. Draw it under `## Boundary`, in a fenced block. Mermaid renders on GitHub;
   anything else is a drawing too, and the label check will read nothing out of
   it.
4. `wfctl arch accept <slug> --agreed "<where the human agreed>"`.

## See the refusal

```bash
uv run wfctl arch accept <any proposed record with no drawing> --agreed "test"
```

`the-drawing-is-required-at-acceptance` was this example while it was itself
undrawn; it carries a drawing now, which is why the slug here is not pinned to
one record — the corpus moves as records gain drawings, and a name fixed at
spec time drifts out from under the example the first time someone accepts it
or draws it in. Expect the refusal from `contracts/cli.md`, exit 1, and the
file unchanged:

```bash
git diff --stat docs/architecture/    # empty
```

Then add a drawing and run it again.

## See the findings

```bash
uv run wfctl doctor
```

A proposed record whose drawing introduces a label the rest of the record never
uses is listed as `⚠`. Exit code is unchanged by it.

## Verify nothing else moved

```bash
uv run wfctl arch context > /tmp/after.txt   # compare against a run from main
```

Identical. No drawing and no declared kind reaches the projection (FR-011).

## The manual pass the suite cannot do

- `uv run wfctl install-skills --prune --yes --agent claude`, then write a record
  from the installed template start to finish. A change under `wfctl/agents/` is
  not verified by a green suite — the suite checks that skills ship and
  cross-reference, not that an author can follow them (AGENTS.md).
- Open a record carrying a mermaid `## Boundary` on github.com and confirm it
  renders. No automated check covers this and none is proposed.
- Read every `⚠` the label check produces over this repository's records and
  judge it. SC-004 is the threshold: more than two a reader calls wrong and the
  check does not ship.
