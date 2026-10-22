---
id: SPEC-01
title: "Spec: vendor-neutral Software Factory (MVP)"
type: spec
labels: [type:spec, phase:0, mode:HITL]
blocked_by: [MAP-01]
skills: [to-spec, domain-modeling]
---
> **Status: DRAFT until MAP-01 clears.** Decisions marked **[proposed]** carry a recommendation from the analysis package and become binding only when the matching DEC ticket is resolved. Where a DEC is resolved differently, edit this spec in the same PR that closes the DEC. Committed copy: `docs/spec/SPEC.md` (read that, not the issue, if the issue text is truncated).

## Problem
Teams that drive coding agents through a backlog get plausible-looking work with weak guarantees: loop bounds written as prose, "tests pass" claims nobody re-ran, merges an agent can bypass, approvals an agent can forge, state spread over a tracker and chat, and orchestration tied to one vendor's harness. The factory is a **small, harness-neutral engine** that owns the control plane in typed code and treats agents as untrusted workers behind a narrow contract.

Goals: (1) turn a written request into reviewed, verified, integrated changes in a local git repo; (2) every transition and side effect is recorded in an append-only event log; (3) engine, not agent, runs verification, merges and records approvals; (4) survive `kill -9` at any event boundary; (5) bounded cost: attempts, wall time, tokens; (6) runs identically against a fake adapter (no model) and one real harness.
Non-goals (MVP): UI, marketplace, distributed workers, deploy pipelines, self-modifying workflows, auto-merge to protected branches by default, intake automation, browser QA.

Glossary lives in `GLOSSARY.md` (seeded by T-01). Use those nouns exactly: **Run, Spec, Plan, Task, Attempt, Verification, Finding, Approval, Event, Adapter, Capability, Policy, Risk class, Autonomy level, Write set, Seam, Door**.

## Seams
Tests live only at these public boundaries. Prefer the highest.
1. **Engine API / CLI (primary).** `engine.run(project, request, adapter)` and the `factory` CLI. Black-box: given a project config and a scripted fake adapter, assert the event log, final run/task states, artifacts and exit code. Most tests live here.
2. **Adapter contract.** The five operations in "Adapter contract". One reusable contract suite runs against `fake` and every real adapter.
3. **Store interface.** `append(event)`, `read_all()`, `snapshot()`, `lease()`. Crash and corruption tests live here because they must inject faults between operations.
4. **Policy decision function.** `decide(action, context) -> allow | deny | needs_approval(reason)`. Pure; table-driven tests.
5. **Schemas.** Good/bad fixtures per JSON Schema (`contracts/`).
No test may reach into private modules, mock our own modules, or assert call counts. Mocks only for time, randomness, external processes (git binary is real; network is stubbed).

## Implementation decisions
### Module map (names, not file paths)
`contracts` (JSON Schemas + examples) ← `core.config`, `core.events`, `core.store`, `core.statemachine`, `core.scheduler`, `core.policy`, `core.verify`, `core.integrator`, `core.review`, `core.workflow`, `core.approvals`, `cli`. Adapters (`adapters.fake`, `adapters.<harness>`) and integrations (`integrations.github`) depend inward only. An import-lint test enforces: contracts ← core ← adapters/integrations; nothing imports tests.

### Language and storage **[proposed]**
Python >=3.11, stdlib-first with exactly two runtime dependencies, `jsonschema` and `PyYAML` (`safe_load` only) (DEC-01; the stdlib has no YAML parser). JSONL event log + derived snapshot behind a `Store` interface (DEC-07). Contracts are JSON Schema 2020-12 (language-neutral), so the language choice stays reversible.

### Run state machine
`created -> specifying -> awaiting_spec_approval -> planning -> awaiting_plan_approval -> executing -> delivering -> completed`; side states `paused`, `blocked`, `failed`, `canceled`. `executing -> delivering` requires every task `succeeded`. `completed` requires a recorded delivery. Cancel: stop scheduling, cancel running attempts (adapter `cancel`), keep worktrees.

### Task state machine
States: `pending, ready, running, verifying, reviewing, integrating, succeeded`; side states `awaiting_approval, blocked, failed, canceled`. Terminal: `succeeded, failed, canceled`.
| From | To | Trigger | Precondition |
|---|---|---|---|
| pending | ready | deps succeeded | all `depends_on` succeeded; no write-set overlap with running tasks |
| ready | running | scheduler picks | budget available; adapter capability match; lease acquired |
| running | verifying | adapter result received | result schema-valid (invalid => retry, counts an attempt) |
| running | ready | attempt timeout or crash | attempts < max (default 3); event `attempt.interrupted` |
| verifying | running | engine-run checks fail | attempts < max; failure log passed as context |
| verifying | failed | checks fail, attempts exhausted | run becomes `blocked` |
| verifying | reviewing | all required checks pass **as run by the engine** | agent claims never suffice |
| reviewing | running | blocking findings | attempts < max |
| reviewing | integrating | no blocking findings | |
| integrating | succeeded | rebased and re-verified on current base; approvals satisfied | scratch-tree checks green |
| integrating | running | rebase conflict | routed back as a rebase task |
| integrating | awaiting_approval | policy requires human | |
| any non-terminal | blocked | needs human, dependency failed, budget exhausted | explicit `factory resume` to leave |
| any non-terminal | canceled | user cancel | |
**Invariant:** a task is `succeeded` only if engine-run verification passed on the integrated head, no blocking finding is open, and every required approval exists. Identical failure signature twice in a row => `blocked` (root-cause cap, enforced in code).

### Event log and store
Event: `{v, seq, ts, run, type, actor, payload, crc32}`. `v` is the event schema version (starts at 1); `seq` is gapless per run; `crc32` covers the canonical JSON (sorted keys, no spaces) of every other field. Types (initial): `run.created`, `run.transitioned`, `task.created`, `task.transitioned`, `attempt.started`, `attempt.finished`, `attempt.interrupted`, `verification.recorded`, `finding.recorded`, `approval.requested`, `approval.granted`, `approval.denied`, `approval.expired`, `policy.decision`, `capability.degraded`, `budget.exhausted`, `lease.acquired`, `lease.released`, `artifact.recorded`.
Rules: single writer via exclusive lease file (create-exclusive, holds pid + heartbeat, stale takeover after expiry); each line written then `fsync`; snapshot written to temp file, `fsync`, atomic rename; on startup truncate a torn final line, verify seq continuity and crc, rebuild snapshot from log on any mismatch; transitions are idempotent (event carries `to` and expected `from`; replaying an applied event is a no-op); artifacts addressed by sha256 recorded in events. Unknown future snapshot schema versions refuse to load.

### Contracts (abridged; full JSON Schemas are produced in T-02..T-09 and live in `contracts/`)
- **task-input:** `task_id, run_id, role, objective, acceptance[{id,text}], scope{write_set[], exclusions[]}, context[], workspace{path, base, branch}, permissions{fs, net, shell[], secrets[]}, budgets{wall_s, tokens, tool_calls}, output_schema, resume_token`.
- **task-result:** `task_id, status in {succeeded, failed, blocked, needs_approval, canceled}, summary, changes{commit, files[]}, evidence[{type, ref}], findings[], questions[], usage{tokens_in, tokens_out, wall_s}`. Evidence from agents is advisory only.
- **verification-result:** `verification_id, task_id, attempt, base, head, environment{env_keys[], network}, checks[{name, argv[], exit_code, duration_s, log}], passed`. Produced only by the engine.
- **approval-request:** `approval_id, run_id, task_id, action, subject{type,id,hash}, scope, scope_hash, reason, expires_at, decision, approver`. Valid only while `subject.hash` and `scope_hash` still match.
- **adapter capabilities:** `structured_output (native|prompt|none), subagents, max_parallel, sandbox (os|tool-allowlist|none), hooks, ask_user, cancel, resume, usage, skills (native|inline|none), models[]`.

### Scheduler
`ready` = `pending` with all deps `succeeded`. Parallel tasks must have **pairwise-disjoint write sets**; overlapping tasks are serialized in plan order. `max_parallel` default 4. Unreadable or missing dependency data means "not ready" (fail-safe). Starvation guard: oldest ready first.

### Policy and autonomy
Default-deny. Every side effect (git write, merge, file write outside worktree, network, secret read, process spawn outside allow-list) is a policy decision recorded as `policy.decision`. Risk classes: `auth`, `money`, `schema`, `size` (lines changed over `size_lines`, default 400), `dependencies`, `ci-config`, `secrets`. Autonomy levels: **L0** plan only; **L1** execute in sandbox worktree, human approves each task result and delivery; **L2 (default [proposed], DEC-03)** auto execute/verify/review, human approves spec, plan, delivery; **L3** as L2 but auto-deliver low-risk classes; **L4** full autonomy within budgets. Approvals are created only from the human channel (CLI with controlling TTY), never from agent-writable text.

### Verification
Engine runs project `verify` commands as **argv arrays** (never shell strings) in an isolated worktree with an allow-listed environment and a timeout. Config lint rejects empty, `true`, `:`, `exit 0` and echo-only commands. Isolation level (host vs container) per DEC-06.

### Adapter contract
Operations: `capabilities()`, `start(task_input) -> handle`, `events(handle) -> stream`, `cancel(handle, grace_s)`, `result(handle) -> task_result`, optional `resume(token)`. Missing optional capability => degrade and log `capability.degraded`; missing required capability => block at start. The engine never trusts adapter-reported success.

### Workflow
One default lifecycle in declarative YAML using only engine primitives: `stage`, `for_each_task`, `loop(max, until)`, `gate(policy)`, `parallel(disjoint_write_sets)`. Stages: spec -> plan -> execute (build, verify, review) -> integrate -> deliver. Roles and skills are Markdown prompt assets (no control flow in prose).

### Project layout in a target repo
`.factory/project.yaml` (project-owned), `.factory/overrides/` (project-owned), `.factory/factory.lock` + `.factory/managed/` (factory-managed), `.factory/state/` (generated, gitignored).

## Testing decisions
- Pyramid: unit (state machine, scheduler, policy, store) -> schema contract -> deterministic workflow tests against the fake adapter -> failure injection -> security fixtures -> one real-adapter end-to-end (nightly/manual).
- Red-green at the seams above, one behaviour at a time; expected values are literals traceable to this spec, never recomputed the way the code computes them.
- Fake adapter scenarios (scripted): success, flaky-then-success, malformed output, slow/timeout, crash, conflicting edits, claims-success-but-checks-fail.
- Crash tests kill the engine at **every** event boundary and assert recovery reaches the same final state.
- Every incident-derived rule ships with a regression test.
- Tests that require a model are tagged `real` and excluded from the default run.

## Out of scope
UI or web dashboard; marketplace and third-party component distribution; distributed or remote workers; deploy pipelines; intake automation (collect from monitoring); browser QA crawler; org-wide policy server; auto-merge into protected branches by default; supporting harnesses other than the fake adapter and the one chosen in DEC-02 (a second is post-MVP, T-24); multi-process engine concurrency (leases prevent it; true support is post-MVP).

## Open decisions (see the DEC tickets and `01-DECISIONS-AND-QUESTIONS.md`)
DEC-01 language/toolchain, DEC-02 first harness, DEC-03 default autonomy + approval channel, DEC-04 GitHub in MVP, DEC-05 naming/license/distribution, DEC-06 verification isolation, DEC-07 store.
