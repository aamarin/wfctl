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
| Ch. 1, "The factory method", pp. 9 and 19 | Consider a factory *"if you realize that you cannot track the objects created by your application because the code that creates them is in many different places ..."* Between the two factories, *"we usually start with the factory method which is simpler"* and reach the abstract factory only once many factory methods exist | A factory in wfctl introduced while construction still happens in one place. The use case the book gives is a pressure that can be observed, which is the form the skill asks every pattern to carry |
| Ch. 3, "Singleton", pp. 38 and 45 | Singleton is useful *"when you need to create only one object or you need some sort of object capable of maintaining a global state for your program"* (p. 45), and the chapter opens by noting that *"some even consider it an anti-pattern"* (p. 38). | **wfctl departs here.** The skill rejects hidden Singleton access and asks for an explicit construction and lifetime owner. The book's use case, global state reached from anywhere, is the red flag "a process-wide dependency is reached through hidden global state". The departure would be wrong if a process-wide dependency in wfctl could not be given an owner that constructs it and passes it down |
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

## Where the level-4 constraints come from

Added 2026-09-25, while reading the sources the design levels were written
against. Harry Percival and Bob Gregory, *Architecture Patterns with Python*
(O'Reilly, 2020), cited by chapter and section, since the edition read carries
no page numbers.

This book is the main source of `python-pattern-selection`. Each chapter builds
one pattern and closes with a table of its trade-offs, and nearly every
constraint in the skill is the cons column of one of those tables, stated as a
default. The book says so itself in chapter 2's wrap-up: *"we're not saying
every single application needs to be built this way; only sometimes does the
complexity of the app and domain make it worth investing the time and effort in
adding these extra layers of indirection."*

The refutation column is written for a repository that installs the skill, since
wfctl itself has no ORM, no database, and no message bus.

| Source | Claim taken | What would refute it here |
|---|---|---|
| Ch. 2, "Wrap-Up", Table 2-1 and the tip beside Figure 2-6 | *"If your app is just a simple CRUD (create-read-update-delete) wrapper around a database, then you don't need a domain model or a repository."* Any extra layer of indirection *"always increases maintenance costs"* | A CRUD service whose repository and domain model paid for themselves with no invariant to hold. The constraint "a rich domain model only for meaningful behavior and invariants, not for CRUD ceremony" is this tip |
| Ch. 6, "Wrap-Up", Table 6-1 | Against a Unit of Work: *"Your ORM probably already has some perfectly good abstractions around atomicity ... You can go a long way just passing a session around."* | A Unit of Work added over a session with nothing the session could not hold; no second repository, no event collection, and no explicit commit boundary the session lacked. The constraint "an ORM session transaction as a viable baseline" is this con |
| Ch. 7, "Aggregates and Consistency Boundaries", recap | *"Aggregates are in charge of a consistency boundary. An aggregate's job is to be able to manage our business rules about invariants as they apply to a group of related objects."* | An aggregate whose boundary follows a foreign key and encloses no invariant. The constraint "define an aggregate from a consistency invariant, not from an object graph or a database relationship" is this recap |
| Ch. 3, "Why Not Just Patch It Out?", and ch. 2, "Building a Fake Repository for Tests Is Now Trivial!" | Patching a dependency out *"does nothing to improve the design."* *"Using mock.patch won't let your code work with a --dry-run flag ..."* And *"if it's hard to fake, the abstraction is probably too complicated."* | An abstraction whose only non-test use is imagined. The book's own reason for an abstraction is a second real caller, such as a dry run or a second storage backend, which is why the skill flags *"interfaces added only to enable mocks"* rather than every interface a fake implements |
| Ch. 8, "Wrap-Up", Table 8-1 | A unit of work that raises events *"is neat but also magic. It's not obvious when we call commit that we're also going to go and send email to people."* | A message bus that made a call graph clearer than the direct calls it replaced. The constraint "an explicit call before an event, observer chain, or message bus" and the red flag "a message bus hides a call graph" are this con |
| Ch. 10, "Wrap-Up", Table 10-2 | Commands and events are split because it *"helps us understand which things have to succeed and which things we can tidy up later,"* and the cost is that *"the semantic differences between commands and events can be subtle."* | A messaging design in which one message type is both a request and a fact, with no failure the split would have isolated |
| Ch. 11, "Distributed Ball of Mud, and Thinking in Nouns", and Table 11-1 | Splitting a system into one service per noun or per database table *"works fine for systems that are very simple, but it can quickly degrade into a distributed ball of mud."* Moving to events means *"message reliability and choices around at-least-once versus at-most-once delivery need thinking through."* | A service split chosen from nouns or functional areas that did not degrade, or an external publish that was safely atomic with a database commit with no delivery design. The constraints on microservices and on in-process versus durable delivery are these two claims |
| Ch. 12, "Wrap-Up", Table 12-2 | *"using the ORM, adding some read methods to your repositories, and using domain model classes for your read operations is just fine."* A separate read store is a *"complex technique."* | A read store built before the ordinary queries were shown to be slow or awkward. The constraint "ordinary query code before CQRS and a separate read store" is this row |
| Ch. 13, "Implicit Versus Explicit Dependencies" and "A Bootstrap Script" | Handlers *"declare an explicit dependency"* on what they use, and one bootstrap script declares the defaults, injects them, and hands back the application | A process-wide dependency reached through a module global that no bootstrap constructs. The constraint "give a process-wide dependency an explicit construction and lifetime owner" names the bootstrap script as that owner |

### What the set argues, taken together

Book 4 says when to reach for a pattern; this book says what each one costs,
and names the cheaper shape it replaced. The skill takes the cheaper shape as
the default and asks the implementer to state the pressure that justifies the
expensive one. That is also the book's order of events, since every pattern in
it is introduced by a failure of the simpler code the chapter starts from.

### The strongest argument against

The authors adopt every pattern in the book, and they wrote it to show that the
patterns pay off as a domain grows (Figure 2-6 draws that crossing point). The
skill reads their cons column as a default and their pros column as the burden
of proof, which is a direction they did not choose. Whoever cites this section
has to say that the book supports the cheaper shape only below the point where
domain complexity makes the pattern worth it, and that the skill's job is to make
the implementer say which side of that point the code is on.

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
| Percival and Gregory, *Architecture Patterns with Python*, ch. 3, "A Brief Interlude: On Coupling and Abstractions", Figures 3-1 and 3-2 | *"the number of arrows indicates lots of kinds of dependencies between the two. If we need to change system B, there's a good chance that the change will ripple through to system A."* With an abstraction in between, *"we can change the arrows on the right without changing the ones on the left."* | A pair of graphs whose arrow counts are equal while the prose claims less coupling. It is the same count Iglberger compares by, drawn one arrow per kind of dependency |
| Same, ch. 2, "Wrap-Up", Figure 2-6 | The trade-off between a decoupled domain model and a simple ORM pattern is drawn as a graph; the cost of each over domain complexity, with *"for simple cases, a decoupled domain model is harder work"* on the left and the payoff on the right | A trade-off whose answer flips with one variable, written as a pros and cons table. The table cannot show where the answer changes, and the crossing point is the finding |
| Same, ch. 11, Table 11-1, and Figures 9-4, 11-6, and 12-2 | Table 11-1 lists the cost of event-driven integration as *"The overall flows of information are harder to see,"* and the book draws each event flow as a sequence diagram | An event-driven decision drawn only as components. The components show who can talk to whom; only a sequence shows the order and the waiting that the cost is about |
| Same, ch. 4, "Our First Use Case: Flask API and Service Layer" | *"In our diagrams, we are using the convention that new components are highlighted with bold text/lines ..."* Every component diagram in the book marks what that chapter adds | A decision graph in which the reader cannot tell which component or edge the decision adds. The template treats a divider that appears for the first time as the sign of a level-2 decision, and a reader sees that only if new elements are marked |
| Same, Part I introduction, Figure I-1, and ch. 1, Figure 1-2 | Part I opens with a picture of the whole application it builds, and chapter 1 places the allocation service among the systems around it in a context diagram. Only then do the chapters draw its components, one box at a time | A record that draws a component's inside with no line saying what surrounds it. It is Richards and Ford's representational consistency, practiced rather than stated |

### Three questions, and the drawing that answers each

Each book draws to answer a question. A decision that asks one of these gets
the drawing beside it, and a decision that asks none of them does not need one
of these three.

| The decision asks | Draw | It asks this when | Source |
|---|---|---|---|
| When X changes, what else has to change, and can a new X be added without editing existing code? | A dependency graph, before and after, one arrow per kind of dependency | The decision exists to absorb a named future change; a new type, operation, backend, or renderer | Percival and Gregory, ch. 3, Figures 3-1 and 3-2; Iglberger, Guidelines 9, 16, and 17 |
| At what size does the expensive option start paying? | Two cost lines over the one variable, with the point where they cross marked | The answer flips as one thing grows, such as domain complexity, the number of callers, or the number of backends | Percival and Gregory, ch. 2, Figure 2-6 |
| In what order do things happen, who waits, and what is left if a step fails halfway? | A sequence, one column per actor, time running down the page | The decision puts an event, a message bus, a poll, or a retry between a cause and its effect | Percival and Gregory, Figures 9-4, 11-6, and 12-2, and Table 11-1 |

The second column is what makes the first one checkable. A graph with an equal
arrow count on both sides has not shown less coupling, a curve with no crossing
has not shown where the answer flips, and a sequence with no failure row has not
shown what is left behind.

#488 asks the first and the third. "Add a renderer without changing wfctl" is
the dependency question, and it is what separates option C from option B. "A
renderer polls `status --json`" is the sequence question.

### What the set argues, taken together

The first book gives the rules for a drawing someone else reads; context before
detail, a key for anything ambiguous, and one line style per kind of
communication. The third book gives the rule for a drawing that compares two
designs; the boundaries and cycles counted in each graph are the comparison.
wfctl already follows most of both, and cites neither. The fifth book adds what
wfctl did not yet say: the drawing is chosen by the question the decision asks,
and it marks what the decision adds.

### The strongest argument against

Richards and Ford say themselves that no standard exists beyond solid and dotted
lines, and that each architect builds a personal style. So these rows are one
style among several, and a repo that installs wfctl may already have its own.
The rows belong in wfctl's own records and sketches, and the skills state them
as defaults a repo can depart from, not as checks.

A decision can ask two of the three questions at once, and #488 does. The table
does not choose between them; it says a record that asks both draws both, which
makes the record longer. The alternative is to pick the one question the
decision turns on and draw only that, and it is the better choice for a record
where the second question has a trivial answer, such as a poll that has no
failure row worth drawing.

---

## What wfctl carries from Evans without citing him

Added 2026-09-26, while checking Eric Evans, *Domain-Driven Design: Tackling
Complexity in the Heart of Software* (Addison-Wesley, 2003), against the skills
and views that draw on it. `model-the-domain`'s source map already cites the
book chapter by chapter. These rows cover the three places it did not reach:
the module bands in `views/current-state.md`, the part of chapter 10 that
`clean-code` does not carry, and the difference between a drawing that teaches
and the model the code follows.

| Source | Claim taken | What would refute it here |
|---|---|---|
| Evans, ch. 16, "Responsibility Layers", pp. 286 - 288 | *"Look at the conceptual dependencies in your model and the varying rates and sources of change of different parts of your domain. If you identify natural strata in the domain, cast them as broad abstract responsibilities."* The layering he pairs it with is Buschmann's relaxed layered system, in which a layer may *"access any lower layer, not just the one immediately below."* | A band in `views/current-state.md` whose admission test is about imports rather than about what the band is responsible for. Evans calls layers that sort themselves out of a dependency drawing *"ad hoc layering"*, which *"doesn't give much insight into the model or guide modeling decisions"* (Figure 16.2, "What are these packages about?") |
| Same, ch. 16, "Evolving Order", pp. 283 - 284 | *"Let this conceptual large-scale structure evolve with the application, possibly changing to a completely different type of structure along the way."* | A band that is treated as a constraint rather than a description. `current-state.md` says in its opening paragraph that it describes and does not constrain, which is this claim held in practice |
| Same, ch. 10, "Assertions", p. 163 | *"State post-conditions of operations and invariants of classes and AGGREGATES. If ASSERTIONS cannot be coded directly in your programming language, write automated unit tests for them."* | A command whose side effects a caller can learn only by reading its body. `clean-code` asks for side effects to be explicit; it never asks for the outcome to be stated as a condition that holds afterwards |
| Same, ch. 10, "Conceptual Contours", p. 166 | *"Is this an expedient based on a particular set of relationships in the current model and code, or does it echo some contour of the underlying domain?"* | A split or a merge of a function or module justified by size alone. `clean-code` sizes a unit by one reason to change; Evans sizes it by the concept, and the two can disagree |
| Same, ch. 2, "Explanatory Models", pp. 24 - 25 | A drawing made to teach the domain is a different thing from the model the code follows, and *"it is actually helpful to avoid UML in these models, to avoid any false impression of correspondence with the software design."* | A domain sketch in `model-the-domain` that uses the same notation as the record's boundary drawing while showing something the code does not have |
| Same, ch. 2, "Documents Should Work for a Living and Stay Current", pp. 23 - 24 | *"If the terms explained in a design document don't start showing up in conversations and code, the document is not fulfilling its purpose."* | A domain model whose Ubiquitous Language table names terms that no spec, plan, or module uses. That is the case today, since no step after brainstorm reads the model; it is tracked on #470 |

### What the set argues, taken together

wfctl already follows more of Evans than it cites. Its module bands are his
responsibility layers under a relaxed layering rule, and its view of them
describes rather than constrains, as his evolving order asks. What it does not
yet do is hold its written language to the code, and the last row is where
that gap is named.

### The strongest argument against

The bands cite Evans for a layering that may have been found without him. The
view's history does not say, and a citation there claims only that the idea is
his, not that wfctl took it from him. That is the honest reading of a
references file, and it is the same claim this file makes for every other row.
