# Glossary

Use these nouns exactly in code, tests, docs, issues and PRs. If a term is missing or two words mean the same thing, fix it here (rules in `docs/agents/domain.md`).

| Term | Meaning | Not to be confused with |
|---|---|---|
| **Run** | One execution of a workflow for one request; has states, a spec, a plan and tasks | a task, a CI job |
| **Request** | The human's original text that starts a run | the spec |
| **Spec** | The agreed requirements for a run, with numbered acceptance criteria `AC-n`; records decisions | the ticket graph for building this repo (SPEC-01) |
| **Acceptance criterion** | One observable, falsifiable behaviour in a spec, id `AC-n` | a test |
| **Plan** | The validated task graph for a run (tasks, dependencies, write sets) | a to-do list |
| **Task** | One unit of work in a plan, with its own state machine | a GitHub issue |
| **Attempt** | One adapter execution of a task; a task has up to `max_attempts` | a retry loop in an agent |
| **Verification** | Checks run **by the engine** on a task's changes; produces a verification result | an agent saying tests pass |
| **Finding** | A review issue with severity, axis and citation | a verification failure |
| **Axis** | A review dimension: `standards`, `spec` or `security`; reported separately, never merged | a severity |
| **Approval** | A human decision pinned to a subject hash and scope hash, with expiry | a code review |
| **Subject hash / Scope hash** | sha256 of what is being approved / of the approval scope; mismatch invalidates the approval | a commit hash only |
| **Event** | An immutable, checksummed log record with gapless `seq` | a log line |
| **Snapshot** | State derived from the event log; never authoritative | a backup |
| **Adapter** | The harness-specific module implementing the five operations | an integration |
| **Capability** | A declared adapter ability (structured output, cancel, sandbox, ...) | a permission |
| **Degradation** | The engine's fallback when an adapter lacks a capability; always logged | an error |
| **Policy** | The pure decision function `decide(action, context)` plus its data | a prompt |
| **Risk class** | A category of change that raises the approval bar: auth, money, schema, size, dependencies, ci-config, secrets | severity |
| **Autonomy level** | L0-L4: how much runs without a human | model tier |
| **Permission profile** | The concrete allowances (fs, net, shell, secrets) given to one task | policy |
| **Write set** | Declared paths a task may change; drives scheduling and the `write-set` check | a lock |
| **Integration branch** | Scratch branch where succeeded tasks are merged and re-verified | the base branch |
| **Delivery** | The engine-only fast-forward of the base branch (or PR) after approvals | deploy |
| **Lease** | An exclusive, expiring claim on a run or repository | a database lock |
| **Seam** | A public boundary where tests live | a module |
| **Door** | One-way (hard to reverse) or two-way (easy to reverse) change; stated in every PR | risk class |
| **Ticket** | A GitHub issue that is a vertical slice of this repo's own build, with a demo path | a Task |
| **Spec issue (SPEC-01)** | The parent issue recording decisions for building this repo | a run's spec |
| **Decision ticket** | An issue (DEC-xx) whose only output is a resolved decision | a question comment |
| **Frontier** | Tickets whose blockers are all closed and that carry `ready-for-agent` | the backlog |
