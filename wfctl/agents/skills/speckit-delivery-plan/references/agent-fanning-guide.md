# Agent Fanning Guide — Wave-Based Parallelization

## When to Fan Agents

Fan agents when:
- Feature is M or larger (5+ files) AND independent waves exist
- You have a single wave with 3+ parallel-safe tasks
- Time savings > overhead of coordinating multiple agents

Do NOT fan for:
- XS features (2 files) — single agent is faster
- Waves where all tasks are sequential — no benefit
- Tasks that share state mid-execution

---

## Wave Identification

### Step 1: Build the dependency graph

For each task pair (A, B): does B require A's output to exist?
- YES → A must complete before B (sequential edge)
- NO → A and B are parallel candidates

### Step 2: Topological sort → wave assignments

All tasks with no remaining dependencies = same wave.

```
Example:
T003 (no deps)                    → Wave 0
T001, T002 (depend on Wave 0 done) → Wave 1 [parallel]
T004, T005 (depend on Wave 0 done) → Wave 2 [parallel]
T006 (depends on T004 AND T005)   → Wave 3 (fan-in gate)
T007 (depends on T006)            → Wave 4
T008 (depends on T007)            → Wave 4 (sequential after T007)
T009, T010, T011 (deps on T008)   → Wave 5 [parallel]
T012, T013 (deps on Wave 5)       → Wave 6 [parallel]
```

### Step 3: Identify fan-worthwhile waves

A wave is worth fanning when:
- It has 3+ parallel-safe tasks, OR
- Each task takes >30 minutes and they total >1 hour

---

## Agent Prompt Templates

### Single-file creation agent

```
You are implementing task {T_ID} for feature {NNN}-{feature-name}.

Task: Create {file_path}
Spec: {feature_dir}/spec.md
Plan: {feature_dir}/plan.md (see Implementation Sequence, Step {N})

Requirements:
- {requirement 1 from task description}
- {requirement 2 from task description}

When complete:
- Signal "T{ID} complete" in your final message
- Do NOT run type-check yet — parallel agents are modifying other files
- Fan-in gate: all Wave {N} agents must complete before type-check runs
```

### Single-file modification agent

```
You are implementing task {T_ID} for feature {NNN}-{feature-name}.

Task: Modify {file_path}
Current file content available at: {file_path}

Changes required:
- {specific change 1}
- {specific change 2}

Constraints:
- Leave {unchanged section} exactly as-is
- Verify change with: {validation command} (run ONLY after receiving fan-in signal)

Signal "T{ID} complete" when edits are saved.
```

### Verification agent (grep/type-check)

```
You are running verification task {T_ID} for feature {NNN}-{feature-name}.

Run these commands in order:
1. {command 1} — expected output: {expected}
2. {command 2} — expected output: {expected}

Report: "T{ID} PASS" if all outputs match, "T{ID} FAIL: {discrepancy}" if not.
Do not modify any files.
```

---

## Fan-in Protocol

After dispatching Wave N parallel agents, wait for all to signal completion
before proceeding to Wave N+1.

```
Dispatcher: "Agents T004 and T005 — begin Wave 2"

[agents work in parallel]

Agent T004: "T004 complete — registration module created"
Agent T005: "T005 complete — entry point modified"

Dispatcher: "Both T004 and T005 complete. Running Wave 3 gate:
             the project's type or build check"
```

---

## Worked Example: Two-Agent Wave

A small feature is usually a single-agent job. This is what fanning one wave looks
like when it is worth doing — two agents extracting a registration module out of an
entry point, each owning one file.

The shape to copy is the **concurrent-edit constraint**: neither agent runs the
project's check, because the other agent is mid-edit and the tree is transiently
inconsistent. The check belongs to the fan-in gate, not to either agent.

**Agent A (T004):**
```
Create the new registration module at {path to the new module}, exporting a
single function that takes the application instance and registers every domain
route on it.
Import the same route modules the entry point imports today, and register them
in the same order.
Do NOT run the project's type or build check — Agent B is modifying the entry
point simultaneously.
Signal "T004 complete" when the file is saved.
```

**Agent B (T005):**
```
Modify the entry point at {path to the entry point}:
1. Remove the per-domain route module imports.
2. Add the import for the new registration function.
3. Replace the block of per-route registration calls with a single call to it,
   in the same position the block occupied.
4. Leave everything else in the entry point unchanged.
Do NOT run the project's type or build check — Agent A is creating the
registration module simultaneously.
Signal "T005 complete" when the file is saved.
```

**After both complete:** run the project's type or build check as the fan-in gate.
It is the first point at which the tree is consistent, and the first point at which
a failure is attributable.
