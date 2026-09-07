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
| [Measuring AI agent autonomy in practice](https://www.anthropic.com/research/measuring-agent-autonomy) | *"0.8% of actions appear to be irreversible"*, and oversight that *"prescribe[s] specific interaction patterns, such as requiring humans to approve every action, will create friction without necessarily producing safety benefits"* | An agent-initiated merge or force-push in this repo's reflog. #100 and #101 already hold merge authority out of the loop, so the local rate is lower than 0.8% rather than higher — which strengthens the row instead of refuting it |
| [Practices for Governing Agentic AI Systems](https://cdn.openai.com/papers/practices-for-governing-agentic-ai-systems.pdf) | *"When people are asked to approve too many actions without much bandwidth for doing so, the human may start rubber stamping the AI system's actions"* — reached without citing Anthropic | Nothing in this codebase. Second-vendor convergence is why the row is here, and refuting it needs evidence from outside wfctl |
| Bravo-Lillo et al., SOUPS 2014, and the browser-warning literature it sits in | 50–70% click-through on security warnings, about half dismissed inside two seconds; habituation is measurable after two or three exposures | A gate here fired rarely enough to stay salient. #277's row 3 is such a gate. Row 1 is not, and that asymmetry is the finding |
| [Capability Myths Demolished](https://papers.agoric.com/assets/pdf/papers/capability-myths-demolished.pdf), and the confused deputy it formalises | The failure is holding an authority, not choosing to use it. Documenting an intention never to force-push leaves the ability to force-push exactly where it was | A constraint wfctl installs that the agent's own tools cannot reach. `layer-model` makes every dotted tree generated and writable, so nothing wfctl installs today qualifies |
| NIST SP 800-53 [AC-3(3)](https://csf.tools/reference/nist-sp-800-53/r5/ac/ac-3/ac-3-3/) | A subject that can waive its own restriction is under discretionary control, not mandatory control. The test is whether the constrained party can self-exempt | The same condition, in its sharper form: `.claude/settings.json` is a file the agent edits with the same tool it edits anything else. A hook merged into it is advisory to an agent willing to remove it |
| [DL.LD.5](https://docs.aws.amazon.com/wellarchitected/latest/devops-guidance/dl.ld.5-enforce-coding-standards-before-commit.html) | A pre-commit hook is fast local pre-catching and not the gate, because `--no-verify` skips it. The gate is whatever runs where the actor is not | A wfctl check running where the agent has no write access — CI, or branch protection on the tracker. `wfctl-runs-the-verification` already argues this shape for a different question |
| [What hints can and can't do](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/) | A taxonomy is not an enforcement mechanism: *"An untrusted server can claim `readOnlyHint: true` and delete your files anyway"* | A classification in this repo that something verifies rather than declares. #277's three classes are declared |
| Orseau and Armstrong, *Safely Interruptible Agents* (UAI 2016) | Irreversibility was a formal property of agent safety a decade before coding agents, so #277's taxonomy is inherited rather than coined | A row in the split with no antecedent. "Outward-facing" is the candidate: the interruptibility literature is about an agent's own trajectory, not about third parties being notified |

### What the set argues, taken together

Every source that says anything categorical agrees the class is named by what an
action *does*, not by which command it is — and two vendors reach the same
failure independently: approval asked for too often stops being approval. That
makes **frequency**, not danger, the variable that decides delivery.

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
