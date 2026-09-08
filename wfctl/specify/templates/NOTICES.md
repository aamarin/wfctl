# Third-party notices — the speckit runtime

wfctl is MIT-licensed; see the `LICENSE` shipped in the wfctl package — not
whatever `LICENSE` sits at the root of the repository you are reading this in,
which is yours. The
speckit runtime — the scripts under `scripts/bash/` and every template beside
this file — is derived from `github/spec-kit`, and that upstream's
notice is reproduced here, which is what MIT asks for beyond the copyright line
itself.

Each script names its upstream on its own second line. The templates do not,
and cannot: a template is copied verbatim to become the reader's own document —
`speckit-specify` copies `spec-template.md` to make `spec.md` — so a line in a
template would land in every spec, plan and task list the runtime generates,
asserting GitHub's copyright over the reader's own writing.

This file travels into projects wfctl installs, so every path in it is written
relative to `.specify/`. In wfctl's own repository they sit under
`wfctl/specify/`, `vendor-upstream-skills` in `docs/architecture/` lists which
of them came from where, and `tests/test_skill_attribution.py` checks that list
and this file against each other.

## github/spec-kit

<https://github.com/github/spec-kit> — `scripts/bash/check-prerequisites.sh`,
`scripts/bash/common.sh`, `scripts/bash/setup-plan.sh`,
`templates/checklist-template.md`, `templates/constitution-template.md`,
`templates/plan-template.md`, `templates/spec-template.md`,
`templates/tasks-template.md`.

    Copyright GitHub, Inc.

Every file above is measured against upstream `main`.

Four files this notice used to name are no longer shipped:
`scripts/bash/create-new-feature.sh`, `scripts/bash/update-agent-context.sh`
and `templates/agent-file-template.md` came from upstream but were invoked by
no skill, command or test, and `templates/github-issue-template.md` was
wfctl's own. Their removal takes their attribution with them.

## The permission notice

`github/spec-kit`'s licence is the MIT licence, and its text below the
copyright line is byte-identical to wfctl's own `LICENSE`. It is reproduced
once; it applies to the copyright holder named above, and to wfctl's own
copyright as stated in wfctl's `LICENSE`.

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
