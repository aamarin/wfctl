# Contract — what `plan`, `tasks` and `implement` report

One line in each step's closing report, in the three states the record list
resolves to. The literal strings, because level 1's gate is answered as the
string a state renders and not as a description of it.

## Listed

```
Design records: 1 listed in design.md
  docs/architecture/design/326-contradiction-is-a-seventh-pass.md
```

```
Design records: 3 listed in design.md
  docs/architecture/design/326-contradiction-is-a-seventh-pass.md
  docs/architecture/design/326-the-report-line-is-one-line.md
  docs/architecture/design/326-severity-reads-frontmatter.md
```

The count is the number of entries, and the paths are every one of them. A step
that read fewer than it listed says so on the affected line rather than adjusting
the count:

```
Design records: 2 listed in design.md
  docs/architecture/design/326-contradiction-is-a-seventh-pass.md
  docs/architecture/design/326-a-record-that-moved.md — listed, not found
```

## None

```
Design records: none — design.md records no level-3 decision
```

## Unknown

```
Design records: unknown — no design.md at /Users/…/wfctl-specs/121-level3-records-in-pr
```

The path is printed. A reader who did not expect this state needs to know which
directory was looked in, because the likely cause is that `FEATURE_DIR` resolved
somewhere they did not expect.

## Why three states and not two

`none` and `unknown` are different truths. One says a design pass ran and
recorded no structural decision, which is a legitimate answer — the record
threshold exists precisely so that not every choice earns a file. The other says
no design pass ran, so nothing is known either way.

Collapsing them reproduces #307's defect one directory over: a step that found
nothing and a step whose input was missing render identically, and the pull
request cannot tell them apart.

## Where the line goes

In the step's own closing report, beside what it already prints — for
`/speckit.plan`, alongside the branch, `IMPL_PLAN` path and generated artifacts
its Outline step 4 already reports. Not in `plan.md`, `tasks.md` or the code. The
report is what a reader watching the run sees; the artifacts are what the next
step reads.
