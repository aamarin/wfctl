# Third-party notices

wfctl is MIT-licensed; see the `LICENSE` shipped in the wfctl package — not
whatever `LICENSE` sits at the root of the repository you are reading this in,
which is yours. Some of the skills beside this file are derived from other
projects, and each such file names its upstream on its own last line, which
covers the rest of that skill's folder too. Two derived files carry no line, so
their sections below name them by path: one sits inside a skill of wfctl's own,
and the other is a helper script in `_lib`, which has no `SKILL.md`.
Each section names its upstream's licence. Four upstreams are MIT-licensed, and
their notices are reproduced here, which is what MIT asks for beyond the
copyright line itself. One is Apache-2.0, and its licence text ships beside
this file as `LICENSE-Apache-2.0`.

This file sits beside the skills it covers rather than one directory up,
because `install-skills` mirrors this directory into a project and nothing above
it. A notice at the top of the tree ships in the wheel and reaches no repository
the skills are installed into — which is where they are actually read.

`vendor-upstream-skills` in wfctl's own `docs/architecture/` lists which skill
came from which upstream; that list and the lines in the files are checked
against each other by `tests/test_skill_attribution.py`.

## obra/superpowers

<https://github.com/obra/superpowers> — `brainstorming`,
`finishing-a-development-branch`, `receiving-code-review`,
`requesting-code-review`.

Licence: MIT

    Copyright (c) 2025 Jesse Vincent

## addyosmani/agent-skills

<https://github.com/addyosmani/agent-skills> — `idea-refine`,
`security-and-hardening`.

Licence: MIT

    Copyright (c) 2025 Addy Osmani

## github/spec-kit

<https://github.com/github/spec-kit> — `speckit-analyze`, `speckit-checklist`,
`speckit-clarify`, `speckit-constitution`, `speckit-implement`, `speckit-plan`,
`speckit-specify`, `speckit-tasks`. The rest of that upstream is under
`specify/`, whose notice travels with it in `.specify/templates/NOTICES.md`
once installed, and `wfctl/specify/templates/NOTICES.md` in wfctl's own tree.

Licence: MIT

    Copyright GitHub, Inc.

## anthropics/claude-code-security-review

<https://github.com/anthropics/claude-code-security-review> —
`reviewing-security/references/security-review.md`, the prompt behind its
`/security-review` command. That file carries no line of its own, because it
ends on the instruction that sets the reviewer's whole reply, and a line after
it would be the last thing the reviewer reads. This section is its credit.

Licence: MIT

    Copyright (c) 2025 Anthropic

## anthropics/defending-code-reference-harness

<https://github.com/anthropics/defending-code-reference-harness> —
`threat-model`, and the helper it runs, `_lib/checkpoint.py`. The helper keeps
upstream's own SPDX header and carries no line of its own, since `_lib` has no
`SKILL.md`. This section is its credit. This upstream is licensed under the
Apache License, Version 2.0, not MIT. Its full text ships beside this file as
`LICENSE-Apache-2.0`, as section 4(a) of that licence asks.

Licence: Apache-2.0

    Copyright 2026 Anthropic PBC

## The permission notice

Every upstream licence above marked `Licence: MIT` is the MIT licence, and its
text below the copyright line is byte-identical to wfctl's own `LICENSE`. It is
reproduced once rather than five times; it applies to each MIT copyright holder
named above, and to wfctl's own copyright as stated in `LICENSE`. It doesn't
apply to `anthropics/defending-code-reference-harness`, whose licence is in
`LICENSE-Apache-2.0`.

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
