# Research index

External sources an argument may cite. **Nothing here binds anything.**

`knowledge-placement` routes a constraint on the system to `docs/architecture/`
and guidance for the worker to `AGENTS.md`. This is neither: it is material a
design pass is expected to *argue against*, and a source that cannot be argued
with has been promoted to a constraint by accident.

Placed outside the arch root on purpose. A subdirectory under
`docs/architecture/` is counted by the level-2 design gate as if it held records
(#171), so a branch that only edited research would satisfy a gate about
boundaries.

Each entry names the source, the claim taken from it, and **what would refute
the claim in this codebase**. An entry with no refutation condition is not
research; it is a belief with a citation.

---

## Abstraction and module boundaries

Added 2026-09-05, while deciding how the five `proposed` records from #149
should express the boundaries they draw. Raised by the observation that every
boundary in wfctl is a naming convention Python does not check.

| Source | Claim taken | What would refute it here |
|---|---|---|
| [Published Interface](https://martinfowler.com/bliki/PublishedInterface.html) | *"The distinction between published and public is actually more important than that between public and private."* An interface is published when it is used outside the codebase that defines it — the problem case is only when *"you can't reach the calling code."* | A consumer importing `wfctl.*` from outside the wheel. Today: none. `grep "from wfctl"` outside `wfctl/` and `tests/` returns nothing |
| [Yagni](https://martinfowler.com/bliki/Yagni.html) | *"Yagni only applies to capabilities built into the software to support a presumptive feature, it does not apply to effort to make the software easier to modify."* And: *"if you do something for a future need that doesn't actually increase the complexity of the software, there's no reason to invoke yagni."* | A boundary expression that does add complexity for current readers — an interface hierarchy, a plugin registry, a second vocabulary to keep in sync |
| [Yagni](https://martinfowler.com/bliki/Yagni.html) | *"Any abstraction that makes it harder to understand the code for current requirements is presumed guilty."* | Nothing. This is `architecture-design`'s own "never invent an abstraction as a third outcome", from a second direction |
| Rule of Three (Fowler, *Refactoring*) | The third usage justifies the abstraction; the first is a concrete implementation and the second is a copy | A second tracker backend shipping. Today `wfctl/agents/trackers/` holds one file: `github.json` |
| Parnas, via [Fowler's architecture guide](https://martinfowler.com/architecture/) | A module is *"characterized by knowledge of a design decision"*, and the target is *"the elimination of inter-module relations towards those decisions"* | A module whose hidden decision cannot be named. `_io`'s is "how bytes reach disk without a torn write" — which is why `events.jsonl` living there is a finding |

### What the set argues, taken together

wfctl has exactly one published interface and it is not in Python. The CLI
surface — `wfctl status --json` in particular, parsed by `speckit-orchestrate`
and `start-session`, which run inside repos wfctl cannot reach — is published in
Fowler's sense. `pipeline-state-is-one-payload` already governs it.

Every Python name in the package is public-but-not-published. So a module
boundary here does not need to be *stable*; it needs to be *legible*. That is a
weaker requirement than `the-underscore-is-the-module-contract` argues from, and
it admits cheaper answers.

### The strongest argument against

Fowler's published/public distinction is about **refactoring cost**, and the
underscore record's real value may not be refactoring cost at all — it is
telling the next reader which names are load-bearing. If comprehension rather
than breakage is the driver, the record's boundary survives untouched and only
its expression is in question, which is what #149's amendment already concluded.

Whoever runs the level-2 pass must answer this rather than cite the row above.

---

## Agent action gating: guidance, enforcement, or both

Added 2026-09-07, while deciding where #277's three irreversibility classes live
and what would make them binding. Raised by the observation that `end-session`
asks before a commit and never asks before a push — an ordering nobody chose,
and one no source below would defend.

| Source | Claim taken | What would refute the claim here |
|---|---|---|
| [Claude Code Auto Mode](https://www.anthropic.com/engineering/claude-code-auto-mode) | *"Claude Code users approve 93% of permission prompts."* A gate fired constantly is answered reflexively, so its scope has to stay narrow to keep meaning anything | `events.jsonl` growing a record of prompt outcomes, showing `end-session`'s commit prompt declined often enough to be doing work. Nothing measures this today, which is why the number is quoted rather than assumed |
| [Claude Code Auto Mode](https://www.anthropic.com/engineering/claude-code-auto-mode) | Four blocked categories named by what an action does rather than which command it is: destroy or exfiltrate, degrade security posture, cross trust boundaries, *"bypass review or affect others"* | A class in #277's split that fits none of the four. Row 2 is the candidate — a comment notifying watchers sits under "affect others" only on a reading, since the harm is noise rather than a bypassed review |
| [Measuring AI agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) | *"0.8% of actions appear to be irreversible"*, and oversight that *"prescribe[s] specific interaction patterns, such as requiring humans to approve every action, will create friction without necessarily producing safety benefits"* | An agent-initiated merge or force-push in this repo's reflog, at a rate anywhere near a commit's. The row rests on irreversible actions being *rare enough to gate without fatigue*, so finding them common here is what breaks it |
| [Practices for Governing Agentic AI Systems](https://cdn.openai.com/papers/practices-for-governing-agentic-ai-systems.pdf) | Poses as an **open question**, not a finding: *"What are the best practices for users reviewing approvals for high-cost actions (such as minimum review times) to avoid their turning into a 'rubber stamp' for agentic AI systems that cannot catch harmful actions?"* So a second vendor treats approval fatigue as unsolved rather than as measured | The row claims only that the question is open. A published practice that answers it — a review protocol with evidence behind it — retires the row, and `end-session` adopting one would be the local form |
| [Alice in Warningland](https://www.usenix.org/conference/usenixsecurity13/technical-sessions/presentation/akhawe) (Akhawe and Felt, USENIX Security 2013) | Measured across 25 million warnings: users clicked through **70.2%** of Chrome's SSL warnings. A warning shown routinely stops being read, and the number comes from field traffic rather than a lab | A gate here fired rarely enough to stay salient. #277's row 3 is such a gate; row 1 is not, and that asymmetry is what the row is cited for. A measurement showing wfctl's prompts are *read* — declined at a rate unlike 70/30 — refutes the transfer |
| [Capability Myths Demolished](https://papers.agoric.com/assets/pdf/papers/capability-myths-demolished.pdf), and the confused deputy it formalises | The failure is holding an authority, not choosing to use it. Documenting an intention never to force-push leaves the ability to force-push exactly where it was | A constraint wfctl installs that the agent's own tools cannot reach. `layer-model` makes every dotted tree generated and writable, so nothing wfctl installs today qualifies |
| NIST SP 800-53 [AC-3(3)](https://csf.tools/reference/nist-sp-800-53/r5/ac/ac-3/ac-3-3/) | A subject that can waive its own restriction is under discretionary control, not mandatory control. The test is whether the constrained party can self-exempt | The same condition, in its sharper form: `.claude/settings.json` is a file the agent edits with the same tool it edits anything else. A hook merged into it is advisory to an agent willing to remove it |
| [DL.LD.5](https://docs.aws.amazon.com/wellarchitected/latest/devops-guidance/dl.ld.5-enforce-coding-standards-before-commit.html) | What the page says: integrate the same checks *"into pre-commit hooks, integrated development environments (IDEs), and continuous integration pipelines so that changes are consistently and continuously checked at all stages."* It recommends the local hook and the pipeline both, and never claims the local one suffices. **That `--no-verify` is what makes the difference load-bearing is this repo's inference, not AWS's** | A local check the actor cannot skip. `wfctl-runs-the-verification` argues the same shape for a different question, and its answer — the check runs where the actor is not — is what would have to fail |
| [What hints can and can't do](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/) | A taxonomy is not an enforcement mechanism: *"A server can claim `readOnlyHint: true` and delete your files anyway"*, and *"They aren't enforcement. If you need a guarantee that a tool can't exfiltrate data, that's a job for network controls or sandboxing, not a boolean hint."* | A classification in this repo that something verifies rather than declares. #277's three classes are declared, which is what puts this record on the near side of the line the post draws |
| Orseau and Armstrong, *Safely Interruptible Agents* (UAI 2016) | Formalises **safe interruptibility** — whether an agent can be stopped without learning to resist it — not irreversibility itself. Taken here only for the weaker claim that "can this be undone" was a named axis of agent safety a decade before coding agents, so the vocabulary is inherited rather than coined | A row in the split with no antecedent anywhere. "Outward-facing" is the candidate: interruptibility is about the agent's own trajectory, and says nothing about third parties being notified |

### What the set argues, taken together

Every source that says anything categorical agrees the class is named by what an
action *does*, not by which command it is. Severity is what puts an action in a
class, and every source above uses it that way.

What none of them uses severity for is the *delivery*, and that is the step this
set argues. Anthropic measures the fatigue directly, OpenAI records it as an
open question, and the warning literature quantifies it in a field study: a
prompt shown routinely stops being read. So severity decides the class and
**frequency decides how the class is delivered** — two questions that look like
one until a gate on the commonest row costs the rarest row its meaning.

#277's rows sit at opposite ends of it. An edit fires many times an hour; a
force-push fires approximately never in a repo where #100 and #101 already hold
merge authority out of the loop. So the mapping is not a compromise between
prose and a check. It is one criterion applied twice, in opposite directions.

### The strongest argument against

wfctl cannot build enforcement here — only something shaped like it. The MAC/DAC
row and the `--no-verify` row reach the same fact from two sides: every file
wfctl installs is a file the agent working in the repo can rewrite, `layer-model`
says so in as many words, and a hook merged into `.claude/settings.json` is one
edit away from gone. `approval-mode-is-stored-intent` already reached this for
the adjacent question — *"There is no wfctl command an agent cannot run
unprompted, so choosing one for its inaccessibility is choosing an illusion."*

That does not collapse the distinction, but it moves it. What a hook buys is not
prevention; it is that removal takes a deliberate act which leaves a diff. The
level-2 pass has to say whether that is worth the machinery, or whether the
honest answer for a single-operator repo is prose plus the tracker's own branch
protection — rather than citing the rows above as though they settled it.

---

## Naming a value that lives inside more than one parent

Added 2026-09-16, while deciding #339's Question 1 — a sub-step's declaration
carries `command` and `evidence` and no name field at all, and `wfctl status`
and `wfctl step none` both need one to print and to take. Raised by the
observation that two different steps can each declare a pass called the same
thing, which is not hypothetical: wfctl's own `ui-design`-shaped pass and a
repository's could collide under different parents on day one.

| Source | Claim taken | What would refute it here |
|---|---|---|
| [Command Line Interface Guidelines](https://clig.dev) | *"Don't have ambiguous or similarly-named commands."* Cautions against confusable names generally, but stops short of this question — it never addresses the same short name legitimately existing under two different parents | A revision of the guide that rules on cross-scope collision directly. None exists as searched |
| [Kubernetes: Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces) | Resource names must be unique within a namespace; the same name can be reused in a different namespace. A bare name resolves against the current namespace, and `namespace/name` disambiguates | A sub-step's parent step turning out not to be a stable identity to scope against — steps reordered or renamed mid-declaration. `_STEPS` is a fixed built-in table, so this does not apply |
| [Terraform: Resource Addressing](https://developer.hashicorp.com/terraform/cli/state/resource-addressing) | The address is always `type.name`; no command anywhere accepts a bare `name`. Uniqueness is enforced by never offering the ambiguous case a syntax | An existing ergonomic bare form already shipping in this CLI for a comparably-scoped value. `wfctl arch none` and its declaration are typed and read with no qualifier, because there is exactly one of them per branch — the precedent this repo already set is a bare form where the scope is unambiguous, not always-qualified |
| [Dealing With Git Tag & Branch Collisions](https://www.conradakunga.com/blog/dealing-with-git-tag-branch-collissions/) | Git resolves a bare ref name across `refs/heads/` and `refs/tags/` by silent precedence, and the practical fix teams adopt is a naming convention nobody tools enforce — "never name a tag and a branch the same" | A namespace at git's scale — many refs, no load-time check possible. A repository's declared sub-steps are a short list read once at config load, where refusing a collision outright costs nothing and needs no convention to remember |

### What the set argues, taken together

Kubernetes' shape fits a value with a real, fixed parent, which a sub-step has —
FR-002 already keys the declaration to the step it lives inside. Terraform's
stricter always-qualified rule is what a namespace needs once bare names stop
being safely unambiguous at its scale; wfctl's own precedent (`wfctl arch none`)
shows the CLI already prefers a bare form wherever the scope makes one
unambiguous, so adopting Terraform's rule here would be tightening past what the
problem's size requires. Git is the cautionary case for doing nothing: a
collision space left to convention instead of a load-time check is exactly the
shape of bug this codebase can refuse for free, since the declaration is static
configuration read once rather than refs created continuously by many actors.

### The strongest argument against

The kubectl analogy quietly assumes the current step is as legible as the
current namespace, and it is not — a namespace is set once per shell session and
named on every prompt; a step is inferred by wfctl from artifacts on disk and an
author does not carry it in working memory the way `kubectl config
current-context` makes visible. So a bare `wfctl step none ui-design` that
"resolves against the current step" may resolve against a step the author is not
actually thinking of, silently — the Kubernetes precedent transfers the
convenience without the context cue that keeps it safe. Whoever settles Question
1 has to weigh that against always requiring `<step>.<name>`, not treat the
Kubernetes row as though it settled the ergonomics question by itself.

---

## What makes a decision level 2

Added 2026-09-25, while deciding #488, whose question is who draws a screen
over every worktree. Raised by the observation that `design-levels` names its
four levels without citing where the line between level 2 and level 3 comes
from.

| Source | Claim taken | What would refute it here |
|---|---|---|
| Richards and Ford, *Fundamentals of Software Architecture* (O'Reilly, 2020), ch. 19, "Architecturally Significant", pp. 284 - 285 | Michael Nygard's test: *"architecturally significant decisions are those decisions that affect the structure, nonfunctional characteristics, dependencies, interfaces, or construction techniques."* Interfaces *"usually involve defining contracts, including the versioning and deprecation strategy of those contracts."* | A decision that meets one of the five and is cheap to reverse here. A private helper's signature is an interface in the loose sense and costs a rename, so the test has to be read as a published interface, which is what the Published Interface row under *Abstraction and module boundaries* supplies |
| Richards and Ford, ch. 2, "Architecture Versus Design", pp. 24 - 25 | *"So where does architecture end and design begin? It doesn't. They are both part of the circle of life within a software project and must always be kept in synchronization with each other in order to succeed."* The book rejects a handoff from architect to developer, and it says the one-way arrow between them *"shows exactly why architecture rarely works."* | A level-3 finding that `design-levels` refuses to send back up to level 2. The skill's "The descent is not one-directional" section is the synchronization the book asks for, so a design pass that works around a boundary instead of revising it would be the refutation |

### What the set argues, taken together

The book gives a test rather than a layer. A decision is level 2 because of what
it touches, and not because of who makes it or when. `design-levels` already
separates the levels by reversal cost, and Nygard's five categories are the
usual reasons a decision is expensive to reverse; hence the two agree.

### The strongest argument against

The book says there is no line, and `design-levels` runs the two as separate
passes with separate gates. The defense is that the gates are about order, not
ownership: the same person answers both, and a lower level is allowed to reopen
a higher one. Whoever cites this section has to show that a level-3 finding
went back up to level 2 when it should have, rather than cite the chapter as
though it endorsed the split.

---

## Keeping an architecture true while it changes

Added 2026-09-25, while reading the sources the design levels were written
against. Ford, Parsons, Kua, and Sadalage, *Building Evolutionary
Architectures* (O'Reilly, 2nd ed., 2022), cited by chapter and section since
the edition carries no stable page numbers across formats.

| Source | Claim taken | What would refute it here |
|---|---|---|
| Ch. 1, "Evolutionary Architecture" | *"An evolutionary software architecture supports guided, incremental change across multiple dimensions."* And a second test for what counts as architectural: *"Architectural decisions are ones in which each choice offers significant trade-offs."* | A decision that meets Nygard's five categories and offers no real trade-off, so that the two definitions disagree about whether it is level 2. None is known; the two are read here as one test stated twice |
| Ch. 2, "What Is a Fitness Function?" | *"An architectural fitness function is any mechanism that provides an objective integrity assessment of some architectural characteristic(s)."* Fitness functions *"are to architecture characteristics as unit tests are to the domain."* | An accepted record whose violation is visible in an artifact and that still ships as prose. `a-rule-is-expressed-as-a-check` is this claim stated for wfctl, so a record that fails its test and is accepted anyway is the refutation |
| Ch. 3, consumer-driven contracts | The consumers of a provider *"put together a suite of tests that encapsulate what they need from the provider and hand off those tests to the provider, who promises to keep the tests passing at all times."* The provider can then change anything those tests do not cover | A consumer of `wfctl status --json` outside this repository that cannot hand wfctl a test. The shape check on `wfctl/contracts/status-payload.json` is provider-written today, and it misses a change of meaning that keeps every key and type |
| Ch. 5, "Contracts" | A contract is *"the format used by parts of an architecture to convey information or dependencies,"* and strict contracts *"create brittleness in integration architecture."* Adding information to a loose contract *"doesn't break what's there."* | A consumer that breaks on an added key. #424's evaluation found the opposite failure, a consumer that breaks on a missing one (`version` absent before 1.0), which a loose contract does not prevent |
| Ch. 7, "Last Responsible Moment" and "Build Anticorruption Layers" | Delay a decision *"as long as you can, but no longer,"* and ask *"Do I have to make this decision now?"*, *"Is there a way to safely defer this decision without slowing any work?"*, and *"What can I put in place now that will suffice but I can easily change later if needed?"* | A deferred decision that forced rework in the milestone that deferred it. The supervisory epic defers the keyboard question to its second milestone on exactly this argument, so a first milestone that has to read a keypress would be the refutation |

### What the set argues, taken together

The first book says what makes a decision level 2. This one says how a level-2
decision stays true after it is made: a fitness function guards it, and a
contract that other parts read is guarded from the consumer's side as well as
the provider's. wfctl already has the first half as an accepted record and
has only the provider's half of the second.

### The strongest argument against

The book is written for teams with a deployment pipeline, many services, and
consumers they can talk to. wfctl is one package, one maintainer, and consumers
it mostly cannot reach. Consumer-driven contracts assume the consumer can hand
over a test, and a workmux plugin or an editor extension will not. Whoever
cites the contracts rows has to say which consumer supplies the test, rather
than cite the practice as though every consumer could.

---

## Where the three lower levels come from

Added 2026-09-25, while reading the sources the design levels were written
against. Klaus Iglberger, *C++ Software Design* (O'Reilly, 2022), cited by
guideline and section since the edition carries no printed page numbers. The
book is about C++, and every claim taken here is one it states as
language-independent.

| Source | Claim taken | What would refute it here |
|---|---|---|
| Guideline 1, "The Three Levels of Software Development" (Figure 1-1) | Software development has three levels: Software Architecture, Software Design, and Implementation Details. Architecture is *"the aspects of your software that are among the hardest things to change in the future"*, and the book quotes Ralph Johnson on it. Design *"primarily deals with the interaction of software entities"* and their *"physical and logical dependencies"*. Implementation details handle *"how a solution is implemented"*, including implementation patterns such as a factory function; Figure 1-1 places idioms at either of the two lower levels. The boundary between architecture and design *"appears to be fluid and is not clearly separated."* | A level in `design-levels` that does not map to one of the three. Levels 2, 3, and 4 are these three in order, and level 1 (behavior) is wfctl's addition in front of them. A fourth level added below implementation, or a split of design into two, would break the mapping |
| Guideline 1, same section | Design patterns such as Visitor, Strategy, and Decorator belong to *"the level of design patterns ... that define a dependency structure among software entities"*, which is the Software Design level, not Implementation Details | `level-4-owns-pattern-selection` (accepted) puts Python pattern selection at level 4, and `python-pattern-selection` weighs *"a callable before a Strategy hierarchy"* there. By Iglberger's line, choosing Strategy is a level-3 decision. The record survives because what it governs at level 4 is the Python mechanism that expresses a pattern already chosen, not the choice of pattern. A skill at level 4 that decides *whether* to use Strategy, rather than how to write it, would refute it |
| Guideline 9, "Pay Attention to the Ownership of Abstractions" | *"Since abstractions represent requirements on the implementations, they should be part of the high level to steer all dependencies toward the high level."* Moving an abstraction to the other side *"is a reassignment of ownership."* | A published contract in wfctl whose shape is set by a consumer instead of by wfctl. `wfctl status --json` is the abstraction, and a consumer rendering it is an implementation that depends on it, so a field added to suit one renderer would reverse the direction |
| Guideline 10, "Consider Creating an Architectural Document" | The document *"should contain the overall structure, the connections between key players, and the major technological decisions"* and should rarely change. The book calls it *"a bank deposit safe"*, invaluable when needed and not opened every day | A record under `docs/architecture/` edited as often as the code it constrains. `architecture-decisions` freezes an accepted body for this reason, and `views/current-state.md` is the only file there meant to track the code |

### What the set argues, taken together

This is the book the lower three levels were named after, and it is where the
reversal-cost column comes from: architecture is what is hardest to change,
design is how entities depend on each other, and implementation details are how
a solution is written. It agrees with the first book that the line between
architecture and design is fluid, and it adds the one rule the other books do
not state, which is that the high level owns the abstraction the low level
implements. That is level 2's question of who owns truth, read as a dependency
direction.

### The strongest argument against

Iglberger admits the three levels are separated by size, and that *"there is
no definition of 'big.'"* The first book separates them by what a decision
touches, and `design-levels` separates them by reversal cost. Three books give
three criteria for the same line. Whoever cites this section has to say which
criterion decided a given level, rather than cite the figure as though the line
were settled.

---

## What the Python pattern catalog says, and where level 4 departs from it

Added 2026-09-25, while reading the sources the design levels were written
against. Kamon Ayeva and Sakis Kasampalis, *Mastering Python Design Patterns*
(Packt, 2nd ed., 2018), cited by printed page.

The book is a catalog. Each chapter names a pattern, its use cases, and a Python
implementation, and it says when a pattern applies far more often than when a
cheaper shape is enough. So it supports `python-pattern-selection` in four rows
and argues against it in two, and the two are kept as they are.

| Source | Claim taken | What would refute it here |
|---|---|---|
| Ch. 13, "Strategy pattern", p. 152 | *"In languages where functions are not first-class citizens, each Strategy should be implemented in a different class ... In Python, we can treat functions as normal variables and this simplifies the implementation of Strategy."* The standard library's own example is `sorted()`'s `key` parameter (p. 151) | A Strategy in wfctl written as a class hierarchy whose subclasses each hold one method and no state. That is the shape the constraint "a function or callable before a Strategy or Template Method class hierarchy" exists to prevent |
| Ch. 10, "The Command Pattern", p. 119 | *"a command does not necessarily need to be a class."* The chapter's delete utility is a plain function placed in the same command list as the classes | A command in wfctl that is a class only so that it can sit in a list beside other commands. The book shows a function sits there as well |
| Ch. 2, "The Builder Pattern", p. 27 | The telescopic constructor problem *"does not exist in Python"*, because named parameters and argument list unpacking solve it. Builder is for an object that *"must be created in multiple steps, and different representations of the same construction are required"* | A Builder in wfctl that assembles its object in one step and has one representation. The constraint "direct construction and named arguments before Factory or Builder machinery" is the book's own line |
| Ch. 1, "The factory method", pp. 9 and 19 | Consider a factory *"if you realize that you cannot track the objects created by your application because the code that creates them is in many different places."* Between the two factories, *"we usually start with the factory method which is simpler"* and reach the abstract factory only once many factory methods exist | A factory in wfctl introduced while construction still happens in one place. The use case the book gives is a pressure that can be observed, which is the form the skill asks every pattern to carry |
| Ch. 3, "Singleton", pp. 38 and 45 | Singleton is useful *"when you need to create only one object or you need some sort of object capable of maintaining a global state for your program,"* and the chapter notes that *"some even consider it an anti-pattern."* | **wfctl departs here.** The skill rejects hidden Singleton access and asks for an explicit construction and lifetime owner. The book's use case, global state reached from anywhere, is the red flag "a process-wide dependency is reached through hidden global state". The departure would be wrong if a process-wide dependency in wfctl could not be given an owner that constructs it and passes it down |
| Ch. 15, "The Microservices pattern", p. 191 | Microservices fit *"every time"* an application has at least one of these characteristics; different clients, a third-party API, messaging with other applications, database access, or *"logical components corresponding to different functional areas."* | **wfctl departs here too.** The skill's constraint "do not conclude microservices from code size, several clients, several functional areas, or database access alone" rejects three of those five triggers by name. The departure would be wrong if one of them, alone, were enough to justify a second deployable in a project wfctl serves |

Two more rows are close enough to the skill that they are recorded without a
column of their own. Flyweight (ch. 8, p. 79) repeats the Gang of Four's
requirements, which begin with *"a large number of objects"* that are *"too
expensive to store/render"*, and that is a measured pressure in the sense the
skill asks for before caching or Flyweight. Retry (ch. 15, p. 198) is *"not
recommended for handling failures such as internal exceptions caused by errors
in the application logic itself,"* and frequent busy faults are *"a sign that the
service being accessed has a scaling issue."* The book then applies retry and
circuit breaker as decorators (pp. 202 and 206), which is the habit the skill
names; it states the failure policy correctly and still reaches for the
decorator first.

### What the set argues, taken together

The book shows that Python moves several Gang of Four patterns down into the
language. A first-class function is a Strategy, a named argument replaces a
Builder, and a function can be a Command. That is the reading
`level-4-owns-pattern-selection` relies on, since the pattern is still chosen at
level 3 and only its Python mechanism changes. Where the book gives a use case
as an observable pressure, the skill agrees with it; where it gives one as a
property most applications have (global state, several clients, a database), the
skill does not.

### The strongest argument against

A catalog is the wrong kind of source for a skill whose whole stance is that the
cheaper shape comes first. The book says when to use each pattern and almost
never when not to, so four supporting rows are four places where it happens to
agree, and not an argument for the default. Its microservices chapter treats a
list of common properties as sufficient, which is the reasoning the skill was
written to stop. Whoever cites this section cites it for the Python mechanism
rows, and cites the two departures as the position the skill argues against,
rather than as support.

---

## How the drawings are drawn

Added 2026-09-25, while reading the sources the design levels were written
against. The drawing guidance lives in four places, since wfctl has no single
diagram skill: `design-levels` for a sketch drawn while a gate is answered,
the `architecture-decisions` record template for the level-2 boundary, the
`software-design-decisions` record template for the level-3 graphs, and
`model-the-domain`'s visual language for domain sketches.

| Source | Claim taken | What would refute it here |
|---|---|---|
| Richards and Ford, *Fundamentals of Software Architecture*, ch. 21, p. 315 | *"Representational consistency is the practice of always showing the relationship between parts of an architecture, either in diagrams or presentations, before changing views."* | A record whose drawing shows one component's inside and never says where that component sits in wfctl. `views/current-state.md` is the whole picture a record can point back to |
| Same, pp. 316 - 317, "Irrational Artifact Attachment" | Attachment to an artifact is proportional to *"how long it took to produce,"* so low-fidelity artifacts come first and a polished tool comes after *"the team has iterated on the design sufficiently."* | A gate answered in mermaid before the ASCII sketch was agreed. `design-levels` already draws in ASCII while a gate is open and redraws in mermaid when the decision lands in a record, and this is the argument for that order |
| Same, p. 319, "Lines" | Arrows show direction, arrowheads are used consistently, and *"solid lines tend to indicate synchronous communication and dotted lines indicate asynchronous communication,"* one of the few standards architecture diagrams share | A wfctl record that draws a value read later from disk with the same edge as a direct call. A renderer polling `wfctl status --json` is asynchronous in this sense, and the edge should say so |
| Same, pp. 320 - 321, "Labels" and "Keys" | Label every item *"if there is any chance of ambiguity,"* and when shapes are ambiguous include a key, since a diagram that leads to misinterpretation *"is worse than no diagram."* | A drawing that uses a glyph whose meaning is stated nowhere in the file. wfctl's sketches use `──✗`, `--x`, and `═══` with meanings the skills define, but a record read on its own carries none of those definitions |
| Same, ch. 20, p. 300 | Asked what an up arrow means, *"almost 50% of people"* read it as getting worse and almost 50% as getting better. A key does not fix it either, since *"once the user scrolls beyond the key, confusion happens once again."* The book marks direction with a plus or minus sign beside the value instead | A wfctl view that encodes direction in an arrow alone. It applies to trend glyphs rather than to dependency arrows, whose meaning the templates already fix |
| Iglberger, *C++ Software Design*, Guidelines 5, 9, 16, and 17, Figures 1-6, 2-4, 4-3, and 4-4 | Designs are compared by their dependency graphs, split by an architectural boundary into a high level and a low level, and *"all arrows now run from the low level to the high level"* is what makes the architecture proper. Two solutions are compared by their graphs: the `std::variant` graph *"has a second architectural boundary"* and *"no cyclic dependency,"* and that difference is the finding | A `software-design-decisions` record whose two graphs differ and whose prose does not say how. The template already draws the divider and the stability axis this way, and Iglberger is where that convention comes from |
| Iglberger, Guideline 38, Figures 10-2 and 10-3 | The Singleton chapter draws the dependency graph twice; the *"desired"* graph, which *"is only an illusion,"* and the actual one, in which *"all dependency arrows point toward the lower level."* | A record whose graph draws the dependency the design intends while the code has the other one. The drawing states what the code does, and a gap between the two is a finding to write down rather than a picture to tidy |

### What the set argues, taken together

The first book gives the rules for a drawing someone else reads; context before
detail, a key for anything ambiguous, and one line style per kind of
communication. The third book gives the rule for a drawing that compares two
designs; the boundaries and cycles counted in each graph are the comparison.
wfctl already follows most of both, and cites neither.

### The strongest argument against

Richards and Ford say themselves that no standard exists beyond solid and dotted
lines, and that each architect builds a personal style. So these rows are one
style among several, and a repo that installs wfctl may already have its own.
The rows belong in wfctl's own records and sketches, and the skills state them
as defaults a repo can depart from, not as checks.
