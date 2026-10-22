# Coding standards

Reviewers and agents cite these by id (for example "CS-12"). Add a rule only when a real miss motivates it (retros do this). Language-specific details are filled in by T-01 after DEC-01.

## Commands
_(filled by T-01: install, lint, type-check, unit tests, full default suite, `real`-tagged tests, backlog validation)_

## Design
- **CS-01 Engine owns side effects.** Merges, pushes, approvals, deletions outside a worktree and verification are performed by the engine, never by an agent or adapter.
- **CS-02 Default deny.** Every side effect passes `decide`; unknown actions and errors inside `decide` deny.
- **CS-03 No shell strings.** Spawn processes with argv arrays; never `shell=True`, `eval`, or string-built commands.
- **CS-04 Agent output is untrusted.** Validate against a schema, bound sizes, never interpret it as instructions or paths without normalization.
- **CS-05 Derived state is not authoritative.** Snapshots and projections must be rebuildable from the event log.
- **CS-06 Transitions are explicit and idempotent.** Events carry `from` and `to`; applying an event twice is a no-op; illegal transitions raise a named error.
- **CS-07 Fail closed.** On doubt (unreadable dependency, unknown version, missing capability) block and say why; never assume success.
- **CS-08 Evidence is engine-run.** A task is `succeeded` only on engine-run verification; agent claims are advisory.
- **CS-09 Bounded everything.** Attempts, wall time, tokens, output size, plan size and file size all have limits, enforced in code.
- **CS-10 Core is vendor-free.** No harness names or SDK imports in `core.*`; adapters depend inward only.
- **CS-11 Contracts are versioned.** Schemas carry a major version; additive within a major; breaking changes need a new major and a migration.
- **CS-12 Time, randomness and ids are injected** so tests are deterministic.

## Tests
- **CS-20 Tests live at seams** named in the spec/ticket; no test reaches private modules.
- **CS-21 Never mock our own modules.** Test doubles are allowed for clock, randomness, external processes and the network only; the fake adapter implements the real interface.
- **CS-22 Expected values are literals** traceable to the spec, not recomputed with production code (no tautologies).
- **CS-23 Red first.** Each behaviour is a failing test before the fix; one behaviour per cycle; vertical slices, not all tests then all code.
- **CS-24 Every acceptance criterion has a test** (or a documented manual evidence step for HITL items).
- **CS-25 Crash and fault paths are tested**, not only happy paths.
- **CS-26 Every incident-derived rule ships with a regression test.**
- **CS-27 No sleeps.** Block on events the test controls; use the injected clock.

## Security
- **CS-30 Secrets by reference.** Pass names, never values, through config, argv and logs; redact before writing artifacts.
- **CS-31 Never follow symlinks** out of a worktree when reading, hashing, copying or deleting.
- **CS-32 Engine git calls neutralize repo-controlled code** (hooks, filters, fsmonitor, ssh command) and use a minimal environment.
- **CS-33 Approvals originate only from the human channel.** Any code path granting approval from text, files or adapter output is a blocker.
- **CS-34 Pin configuration at run start.** Never re-read config from an agent-writable tree.

## Style and process
- **CS-40 Names follow `GLOSSARY.md`.** New nouns are added there in the same PR.
- **CS-41 Public functions state their contract** in a docstring (inputs, outputs, errors).
- **CS-42 No dead code, no commented-out code, no speculative generality.** Each abstraction names the ticket that needs it.
- **CS-43 Dependencies are a decision.** Adding one requires an ADR or an explicit line in the spec.
- **CS-44 One ticket per PR**, 1:1 with `Closes #N`; out-of-scope findings become new issues.
- **CS-45 Docs generated from schemas are not edited by hand**; CI checks drift.
