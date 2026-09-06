# Third-party notices — the speckit runtime

wfctl is MIT-licensed; see `LICENSE` at the root of the distribution. The
speckit runtime — the scripts under `scripts/bash/` and every template beside
this file but one — is derived from `github/spec-kit`, and that upstream's
notice is reproduced here, which is what MIT asks for beyond the copyright line
itself.

Each script names its upstream on its own second line. The templates do not,
and cannot: a template is copied verbatim to become the reader's own document —
`create-new-feature.sh` runs `cp` on `spec-template.md` to make `spec.md` — so a
line in a template would land in every spec, plan and task list the runtime
generates, asserting GitHub's copyright over the reader's own writing.

This file sits in `templates/` rather than at the top of the tree because
`templates/` is an install target. `install-skills` mirrors it to a project's
`.specify/templates/`, so a notice one directory up would ship in the wheel and
never reach a repository wfctl installed the derived templates into.

This file travels into projects wfctl installs, so every path in it is written
relative to `.specify/`. In wfctl's own repository they sit under
`wfctl/specify/`, `vendor-upstream-skills` in `docs/architecture/` lists which
of them came from where, and `tests/test_skill_attribution.py` checks that list
and this file against each other.

## github/spec-kit

<https://github.com/github/spec-kit> — `scripts/bash/check-prerequisites.sh`,
`scripts/bash/common.sh`, `scripts/bash/create-new-feature.sh`,
`scripts/bash/setup-plan.sh`, `scripts/bash/update-agent-context.sh`,
`templates/agent-file-template.md`, `templates/checklist-template.md`,
`templates/constitution-template.md`, `templates/plan-template.md`,
`templates/spec-template.md`, `templates/tasks-template.md`.

    Copyright GitHub, Inc.

`templates/github-issue-template.md` is wfctl's own and is deliberately absent:
it describes `/speckit.decompose`, a command spec-kit does not have, and scores
nothing against any upstream template.

`update-agent-context.sh` and `agent-file-template.md` are derived from paths
that no longer exist upstream. Both were removed in `github/spec-kit@fc3d124`;
against the commit before it they are 82% and 100% upstream.

## The permission notice

`github/spec-kit`'s licence is the MIT licence, and its text below the
copyright line is byte-identical to wfctl's own `LICENSE`. It is reproduced
once; it applies to the copyright holder named above, and to wfctl's own
copyright as stated in `LICENSE`.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
