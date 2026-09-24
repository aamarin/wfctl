# wfctl domain vision

<!-- The product-level page: the vision statement and which capability is
     core, supporting or generic. A capability that earns a model gets its own
     domain/<capability>.md and links back here. This page describes; the
     records under the arch root decide. -->

State: exploratory
Person who knows the domain: Andre Marin
Last checked against the code: 2026-09-24, 5dcf6fb
Records this model draws on: `session-state-is-re-derived`, `wfctl-runs-the-verification`, `a-run-cursor-is-execution-state-not-evidence`, `pipeline-state-is-one-payload`

## Domain vision statement

Others can run the work. wfctl answers: what does the durable evidence prove
happened?

wfctl's unique core is evidence-derived workflow truth. It reads durable
feature artifacts, verification results, and architecture records to determine
what obligations have actually been satisfied, what is still pending, what is
inapplicable, and what needs human attention. It does not let an agent, runner
cursor, session file, dashboard, or terminal state certify completion for
itself.

The states it names are done, pending, not applicable with a reason,
verification state, architecture obligations, and human attention required.
The last three are what make it more than a progress tracker. Its verbs are
derive, verify, explain and project — never orchestrate, remember or execute.

The core is that capability, not the current command set. Commands may move
or shrink while the capability stays. `resume` belongs to the core only as a
projection of derived state; if it ever owns a remembered execution position,
it competes with Spec Kit and leaves the core.

The second thing wfctl carries that nobody else does is the method around Spec
Kit. Its purpose is to reduce AI slop: brainstorm the architecture and design
up front, and think the structure of the code through well enough before it is
formalized into a spec, then carried through Spec Kit into implementation. It
also has to leave enough detail and understanding behind, across sessions, that
the agent does not go off the rails. The design passes before Spec Kit
(brainstorm, the four design levels, domain modeling) and the passes after it
(decompose, refactor) are that method today.

The method is opinionated on purpose. It scales one developer's preferred
process: the formal architecture, design and domain modeling before coding
that real-life schedules rarely leave time for, done every time because an
agent does the legwork and wfctl holds the work to what was decided.

This is where the learning has not stopped. Gaps in the design process, in the
systematic way decisions are made, and in how agents report back keep turning
up. Each one changes what an agent is told to do and what evidence it leaves,
and the evidence is what connects this half to the first: a design decision
that reaches disk is one wfctl can later hold the work to.

Across many worktrees, the same truth answers one more question: which of them
needs a human now. That judgment is core; the screen that shows it is not.

**Where it sits beside Anthropic's long-running harness.** The problem is the
same one — work that outlives a context window, handed from one fresh session
to the next through durable artifacts rather than memory. The answer differs in
who interprets the artifacts. In Anthropic's harness the agent itself flips a
feature's `passes` field after testing
([effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents),
checked 2026-09-24). In wfctl the agent may write evidence, but it is never the
authority that interprets that evidence as completion.

## Subdomains

| Capability | Core, supporting or generic | Why | Owner | What changes it |
| --- | --- | --- | --- | --- |
| Status and gate derivation — done, pending, not applicable, attention | core | Q1: the distinctive answer; nothing bought off the shelf computes it | wfctl | A new kind of evidence, or a new state a step can be in |
| `verify` and its recorded verdict | core | Q1: the agent never certifies its own completion | wfctl | A repo's verification shape wfctl cannot run |
| Architecture records read as obligations — `arch context`, `arch none`, placement | core | Q1: obligations are among the states it names | wfctl | A new kind of record, or a new reader of the arch root |
| Attention across worktrees — which one needs a human, and why | core | Q2: the derived truth applied to N worktrees; #424 | wfctl | A new reason a worktree can need a human |
| The design method around Spec Kit — brainstorm and the design levels before it, decompose and refactor after it | core | Q4: still evolving as gaps in the design process are found (#463, #464) | wfctl's skills | A gap found in the process, the decisions or the agent's output |
| install-skills and doctor drift | supporting | Q3: important because the method ships through it, but a plain build loses nothing distinctive; Q4: stable once every agent discovers skills correctly | wfctl | A new agent host, or a change in how agents discover skills |
| `/start-session` and `/end-session` handoff, and the restart hook | supporting | Q3/Q4: critical to continuity and unchanged in practice; they project derived state and carry the one thing that cannot be derived — the handoff prose | wfctl | A new host whose sessions end differently |
| The dashboard TUI — rows, keys, refresh | supporting | Q2: custom because nothing reads wfctl, but a plain build would do; it never certifies anything | wfctl | The attention question it renders |
| Worktree discovery and lifecycle — workmux, tmux | generic | Q2: workmux is the only lifecycle authority; the dashboard hands requests to it | workmux | — |
| Tracker adapters — GitHub, Jira, Gerrit | generic | Q2: nothing distinctive in talking to a tracker | the tracker's CLI | — |
| Spec Kit step sequencing | generic | Q2: Spec Kit runs the steps; wfctl reads what they left | Spec Kit | — |

## Open questions

| Row | Question or conflict | Why it matters | Who can answer | Next evidence |
| --- | --- | --- | --- | --- |
| O1 | Install-skills is stable only once skills are discovered correctly on hosts other than Claude, which has not been tested | Until then a new host may reopen it as more than supporting | Andre | A run on a second agent host |
| O2 | The design method is core and ships as skill prose, while the other core rows are code | Core prose has no check behind it unless `a-rule-is-expressed-as-a-check` finds an artifact to read | Andre | The follow-up gate on this page's own classification |

## What reopens this page

- A capability a branch touches that has no row above.
- `resume`, or any other command, starting to keep a position it did not derive.
- The dashboard, or any other view, starting to decide something rather than show it.
