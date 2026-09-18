# Refactoring workflow

Use this reference to improve structure while preserving externally observable
behaviour.

## What a refactor adds to the contract

Refactoring changes how code expresses behaviour, not the behaviour promised to
callers, so the contract inventory any change starts from is the whole of what
must stay stable here — nothing is added to it by the work being structural.

Where the task also changes behaviour, identify the behavioural change
explicitly and keep its proof distinguishable from the structural cleanup.

## Prepare a safety net

Use the cheapest reliable evidence available:

- existing focused tests;
- characterisation tests around the current behaviour;
- contract tests at a dependency boundary;
- representative fixtures or snapshots, where they assert meaningful output;
- a reproducible command or runtime observation, where automated tests are not
  yet practical.

Do not freeze an obvious defect by accident. Record whether a surprising
current behaviour is contractual, tolerated, or intended to change.

## Work by successive refinement

Repeat:

1. Choose one observed problem.
2. Describe the improvement in conceptual terms.
3. Make one small transformation.
4. Run the narrowest relevant verification.
5. Inspect the new structure and its call sites.
6. Commit or checkpoint a coherent state, where the workflow supports it.
7. Select the next problem only once the code is again understood and passing.

Useful transformations:

- rename a misleading concept;
- extract or inline a function where it clarifies the abstraction;
- replace a selector or flag with separate operations or types;
- move behaviour toward the knowledge it uses;
- introduce an explanatory value or a domain type;
- isolate an external dependency;
- make an ordering or a state transition explicit;
- remove proven dead code;
- consolidate duplication once the shared concept has been identified.

The transformation is not the goal. Stop and reassess where it does not improve
the reader's model.

## Work from behaviour toward structure

For rough or legacy code:

1. Make it reliably reproducible.
2. Make the required behaviour work, or characterise what already works.
3. Identify the concepts hidden inside conditionals, flags, parsing or repeated
   mechanics.
4. Give those concepts stable names.
5. Separate policy from mechanics, and construction from use.
6. Remove an obsolete path once evidence shows it is unreachable or no longer
   required.

Do not postpone all cleanup until a hypothetical future rewrite. Equally, do
not interrupt a focused repair with an unlimited redesign. Improve the touched
path enough that the next change is safer.

## Small steps, and what they are not

Small steps localise mistakes and keep the program runnable. They are not an
instruction to create tiny commits with no coherent meaning, nor to split one
invariant across unsafe intermediate states.

Use tooling for mechanical renames and moves where it exists. After a
mechanical change, search for string-based references, configuration,
serialisation, reflection, documentation and generated surfaces the tool does
not cover.

## Stop conditions

Stop when:

- the requested change is clear and safely supported;
- the selected problem no longer creates a material comprehension or change
  risk;
- further cleanup would cross the authorised scope or an architecture
  boundary;
- the tests no longer distinguish a proposed redesign from speculation;
- a public or persisted contract requires a separate decision or a migration;
- the next step would add an abstraction with no present evidence for it.

Capture larger work separately rather than smuggling it into the current patch.

## Final verification

Run focused tests after each meaningful transformation, and the broader suite
the change justifies at the end. Beyond the diff inspection any finished change
gets, a structural one leaves two traces of its own:

- duplicated paths left by a partial move;
- changed error or ordering semantics.

Report the behaviour preserved, the structural problems addressed, the checks
run, and any uncertainty that remains.
