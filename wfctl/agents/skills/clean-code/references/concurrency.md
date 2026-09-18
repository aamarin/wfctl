# Concurrency

Use this reference for threads, async tasks, processes, actors, workers,
reactive streams, callbacks, queues — any code whose operations may overlap or
interleave.

## Begin with the execution model

State explicitly:

- what can run concurrently;
- what state is shared;
- who owns each mutable value;
- what ordering is required;
- where work may block, fail, retry, cancel or time out;
- how startup and shutdown complete;
- what provides backpressure or bounds resource use.

Concurrency is not a performance annotation added after ordinary code. It
changes the set of possible executions, which is why the model comes first.

## Separate concurrent policy from the work

Keep scheduling, synchronisation, retry, cancellation and coordination
distinguishable from the domain work they protect. That is what lets the domain
behaviour be tested without every test reproducing a scheduler.

Prefer designs that reduce shared mutable state:

- immutable values or snapshots;
- message passing and explicit ownership transfer;
- partitioned state with one owner per partition;
- local copies, where reconciliation is defined;
- isolated workers communicating through narrow channels.

Where sharing is necessary, limit its scope and document the invariant each
synchronisation mechanism protects.

## Make synchronisation coherent

- Keep critical sections small in duration and responsibility, but large enough
  to protect the whole invariant.
- Avoid acquiring a lock through an unclear call chain.
- Define a lock ordering where several locks can be held.
- Treat a dependency between separately synchronised operations as a possible
  atomicity defect: two individually safe calls can form an unsafe sequence.
- Do not call unknown, blocking or reentrant code while holding a lock unless
  the design requires and documents it.
- Prefer library primitives with understood guarantees over hand-built
  synchronisation.

The classic deadlock conditions are exclusive ownership, holding while waiting,
inability to preempt, and circular dependency. Where deadlock is possible,
break at least one by design.

## Name the coordination pattern

Identify the pattern rather than improvising shared-state rules:

- producers and consumers need queue capacity, ownership, completion and
  failure policy;
- readers and writers need a fairness and consistency policy;
- peer resource acquisition needs an ordering or arbitration policy;
- fan-out and fan-in need cancellation and partial-failure semantics;
- async request handling needs timeout, backpressure and lifecycle limits.

Use names and types that expose these roles.

## Shutdown is behaviour

Define what happens to newly arriving work, queued work, in-flight work, held
resources, retries and timers, partial results, and callers awaiting
completion.

Test clean shutdown, forced shutdown, timeout, cancellation, and failure during
shutdown where they matter. A service that starts correctly and cannot stop
predictably is not correct.

## Test beyond the happy schedule

Prove the underlying non-concurrent behaviour first where possible. Then vary
what exposes interleavings:

- worker counts, including one and more workers than processors;
- queue sizes and backpressure thresholds;
- repeated runs and randomised schedules;
- injected delays or yields at meaningful coordination points;
- different supported runtimes or platforms;
- cancellation, timeout, retry and shutdown timing;
- race, thread, memory or scheduler instrumentation the ecosystem provides.

Treat a sporadic failure as concurrency evidence until it is disproven. Do not
dismiss it because the next run passed.

Avoid tests that depend on an arbitrary sleep. Prefer barriers, latches,
controllable clocks, deterministic schedulers, hooks, or observable state
transitions.

## Review prompts

- Is shared mutable state necessary, and is its owner clear?
- What invariant does each lock or atomic operation protect?
- Can two individually safe calls form an unsafe sequence?
- Is work bounded under overload?
- Can cancellation leave state or resources inconsistent?
- Can a callback or an external call reenter synchronised code?
- Is shutdown specified and tested?
- Are background failures surfaced, or lost?
- Has the code been exercised under varied schedules with appropriate tooling?
