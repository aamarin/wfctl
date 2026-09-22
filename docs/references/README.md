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
