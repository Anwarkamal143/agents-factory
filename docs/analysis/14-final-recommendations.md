# 14 — Final Recommendations and Decision Register

## The question
> *If we were starting from scratch today, knowing everything discovered in this factory, what exactly would we build, why would we build it that way, what would we deliberately avoid, and in what order would we implement it?*

### What we would build
A **small, vendor-neutral engine** (Python, stdlib-first) that owns the control plane in typed code: two explicit state machines (run, task), a scheduler over a task DAG with declared write sets, a policy engine with autonomy levels L0–L4 and risk classes, an engine-run verification runner, an integrator that alone merges/pushes, and an append-only event log + snapshot store. Agents (spec-writer, planner, builder, reviewer) are **prompt assets** executed through a **five-operation harness adapter** (`capabilities/start/events/cancel/result`), proven first against a **fake adapter** and then one real harness. The default lifecycle is spec → plan → execute → verify → review → integrate → deliver, with human approvals configurable per gate. (Designs: 10, 12; diagrams `diagrams/proposed-*.mmd`.)

### Why this shape (each tied to evidence)
| Design choice | Evidence in super-board | Finding |
|---|---|---|
| Control flow, retries, budgets in code | Rebuild cap, block-rate alert, zero-progress halt exist only as prose or unused variables; `ui-refine-loop.js` shows code-enforced bounds work | R-01, O-08 |
| Engine, not agent, runs verification and merges | Gate is a convention once `gh pr merge:*` is allow-listed; agents report test results | S-01, O-15, O-17 |
| Approvals from an authenticated human channel, pinned to hashes | Approval pinning is excellent; approver identity can equal agent identity | S-02, O-04, O-16 |
| Local durable event log, GitHub as optional projection | GitHub rate-limit incidents; non-atomic claims; split unversioned state | R-03, R-05, R-06, O-13 |
| One engine + adapters | Same logic in `wave.js`, `codex-*.sh`, `run.sh`; Claude-only guardrails | R-09, S-03, O-12 |
| Sandbox + permission profiles; hooks as defense in depth | Fail-open regex hooks, no Codex parity | S-03, S-04, O-14 |
| Schemas for config and contracts; docs generated | `config-schema.json` not parsed; six doc/code mismatches | R-07, R-08, O-10, O-11 |
| Fake-adapter test pyramid | Stub-harness workflow test is the repo's best testing idea | O-05 |
| Manifests + lockfile | hard-coded name lists; overwrite installer | S-11, 06 |

### What we would deliberately avoid
Prose as the control plane (816-line lifecycles); assignee-as-mutex; `eval` of config strings; `curl | bash` without verification; whole-directory overwrite installs; regex hooks as the primary security control; hard-coded personal/branding/model constants; a second hidden orchestration implementation; unpinned third-party skills; building intake, QA crawler, visual maps, or marketplace before the core loop is proven.

### In what order
Phase 0 spikes → schemas/log/config → engine with fake adapter (including crash-at-every-event tests) → first real adapter → lifecycle + approvals → hardening → extensibility → DX/second adapter (11).

## 16.1 Existing factory summary
- **What it does (V/D):** `super-board` v3.1.2 is a Claude Code plugin/installer that runs a GitHub Project board autonomously: pre-flight → classify → Build → QA → Review → deterministic merge gate, with human gates for risk classes.
- **How it works (V):** an LLM orchestrator session follows `run-workflow.md`; deterministic scripts plan waves and read/move GitHub; a host-provided Workflow runtime runs `super-board-wave.js`, spawning lane agents whose behavior is specified in prose (`run.md`); a script gate performs the merge.
- **Core ideas:** board-as-state, deterministic mechanics + LLM judgment, specialist lanes with independent review, fail-safe halts, head-pinned approvals, incident-driven hardening.
- **Well designed:** merge gate; wave planner; approval pinning; GitHub read validation/halting; cleanup safety; writing-standard contracts; stub-harness tests; release discipline.
- **Weak/risky:** see ranked list below.
- **Hard to maintain:** logic triplicated across three backends; 800+ line prose lifecycles; hard-coded name lists; docs drifting from code.
- **Missing:** engine-enforced loop bounds, structured event log/cost accounting, first-class spec/plan, write-set ownership model, graded autonomy, cancellation inside waves, uninstall, config validation.
- **Not verifiable from the archive (U):** anything requiring execution: lane quality, hook coverage under sub-agents, Workflow runtime behavior, Codex end-to-end, CI results, author-reported benchmarks and rate-limit figures.

## 16.2 Rebuild versus reuse
| Subsystem | Existing approach | Decision | Reason | Proposed approach |
|---|---|---|---|---|
| Orchestration | LLM session prose + host JS workflow + Codex shell + legacy runner | **Replace** | triplicated, host-bound, loop bounds unenforced (R-01, R-09) | typed engine + declarative workflow |
| Wave planning | `wave-plan.sh` deterministic jq planner | **Keep concept, reimplement** | pure function, fail-safe defaults | scheduler over DAG + write sets |
| Task lifecycle/state machine | implicit in board columns + prose | **Replace** | no explicit transitions/retries | explicit state machines (10) |
| Agent execution | `agent()`/`codex exec`/`claude -p` with prompt strings | **Replace with adapters** | vendor-coupled | adapter contract (07, 12) |
| Skills | Markdown + hard-coded REGISTRY + unpinned external skills | **Improve** | good reuse idea, weak governance | manifests, pins, permissions |
| Roles (Build/QA/Review) | three sequential LLM lanes | **Keep concept** | independent review is valuable | roles as agents; reviewer separate from builder |
| Verification | agent-run except at merge gate | **Improve** | agent claims unchecked | engine-run checks every attempt |
| Merge/integration | `merge-gate.sh` | **Keep semantics, move into engine** | strongest component | integrator step with same guarantees |
| Approval/policy | `merge-policy.py` + `approval.py` | **Keep + extend** | pinned design; identity gap | approval objects, human channel, autonomy levels |
| State | GitHub board + assignees + local files + comments | **Replace** | non-atomic, rate-limited, unversioned | event log + snapshot; GitHub projection optional |
| GitHub I/O | `github-read.py`, `card.sh` | **Keep ideas** | validation, retry, halt, caching are good | integration module behind tracker interface |
| Hooks/guardrails | 5 fail-open Python hooks | **Demote** | heuristic, Claude-only | sandbox + permission profiles; hooks optional |
| Config | per-script jq reads; reference-only schema | **Replace** | no validation | JSON-Schema-validated layered config |
| Installer/distribution | copy installer, curl\|bash, plugin | **Replace** | overwrite hazard, no checksum | lockfile + signed releases |
| Intake (`super-collect`) | Sentry/PostHog/PR scanning → Backlog | **Defer** | useful but peripheral | optional integration post-MVP |
| QA crawler / visual / ui-refine | secondary skills | **Defer** | not core | optional components |
| Tests | 59 offline suites + 7 paid evals | **Adopt pattern** | strong two-tier idea | fake-adapter pyramid; evals for prompts |
| Observability | comments + manifest + status | **Replace** | no event log | JSONL events, `explain` |
| Docs | prose + diagrams site | **Improve** | drift | generate from schemas |

## 16.3 Critical findings (ranked)
| Rank | ID | Type | Finding | Level |
|---|---|---|---|---|
| 1 | S-01 | Potential vulnerability / architectural weakness | Merge gate bypassable by agent when `gh pr merge` is allow-listed | V facts, I bypass |
| 2 | R-01 | **Confirmed defect** (doc/code gap) | Loop bounds documented but not enforced in inspected code | V |
| 3 | S-02 | Potential vulnerability | Approval not bound to a distinct human identity in solo mode | V code, I exploit |
| 4 | S-06 | Potential vulnerability | PR-head code run by `eval` with ambient credentials | V |
| 5 | S-07 | Missing capability | No untrusted-content posture for issue/comment text | V (absence in inspected paths) |
| 6 | S-03 | Architectural weakness | Fail-open, Claude-only guardrails; no Codex parity | V; sub-agent coverage U |
| 7 | R-09 | Maintainability | Orchestration logic triplicated | V |
| 8 | R-08/R-07 | **Confirmed defects** | Six doc/code drifts; config unvalidated | V |
| 9 | R-02/R-03 | Confirmed defects | Merge refusal halts run; claim non-atomic and contradictory docs | V |
| 10 | S-08/S-11 | Weakness | Unsigned installer; overwrite install | V |
| — | — | Unverified assumptions | Lane quality, hooks under sub-agents, Workflow runtime, benchmarks | U |
| — | O-34 | Optional | Secondary skills packaging | — |

## 16.4 Minimum viable factory (MVP)
**Can do:** run the default lifecycle on a local git repo with one real adapter; produce spec and plan with human approval; execute tasks in isolated worktrees (parallel only for disjoint write sets); run engine-owned verification; run an independent review; integrate in a scratch tree and deliver via engine-performed merge/PR subject to policy; record everything in an event log; survive kill -9 at any event boundary; enforce attempt/time/token budgets; fully test with a fake adapter.
**Cannot (yet):** custom workflows, multiple harnesses beyond the fake + 1, browser QA, intake automation, org policy packs, UI, multi-process concurrency, deploys.
**Evidence required before "production-ready":** (1) Phase 6 soak with injected failures: zero state corruption/unauthorized side effects; (2) every S-/R- finding mapped to a passing test or recorded accepted risk; (3) adapter contract suite green on the real harness across two consecutive upstream versions; (4) independent security review of the permission profile and approval path; (5) 20+ real-repo runs with human audit of event logs.

## 16.5 Recommended architecture, rejected alternatives, trade-offs
Recommended: 10 §12.2 diagrams D1–D8. Key decisions: Python stdlib engine; JSON Schema contracts; declarative workflow with fixed primitives; JSONL event store behind `Store`; engine-owned side effects; adapter contract with fake adapter; autonomy levels; manifests + lockfile.
| Rejected | Why | Trade-off accepted |
|---|---|---|
| Keep board-as-state | rate limits, races, no transactions | lose free GitHub UI → provide projection later |
| Prose/Markdown workflows | unenforced bounds, untestable | less "hackable" by non-coders → declarative YAML stays readable |
| Fork super-board and patch | triple logic + prose control plane need replacement, not patching | discard sunk code; keep tests/ideas |
| SQLite from day one | adds migration/schema weight for a single-writer MVP | revisit when multi-process (store interface isolates it) |
| Hooks as main guardrail | fail-open, vendor-specific | sandbox dependency (optional extra) |
| Dynamic plugin marketplace | speculative | manifests only |

## 16.6 Next steps — ordered checklist (for an implementation agent)
| # | Action | Depends on | Acceptance | Refs |
|---|---|---|---|---|
| 1 | Run Phase 0 spikes; write ADR-001 (language), ADR-002 (store), ADR-003 (workflow format), ADR-004 (first adapter) | authorization to execute | spike results + ADRs merged | 11 P0, 07, 09 §4 |
| 2 | Create repo skeleton per 12 §1; CI with import-lint | 1 | CI green, empty suites | 12 |
| 3 | Write JSON Schemas C6–C10 + fixtures | 2 | contract tests pass | 12 §3 |
| 4 | Implement event log + snapshot + lease + torn-tail recovery | 3 | log tests incl. corruption | 10 §12.7 |
| 5 | Implement config loader with validation and verify-command lint | 3 | rejects `true`/empty | R-07 |
| 6 | Implement task/run state machines + invariants | 4 | property tests, no illegal transitions | 10 §12.4 |
| 7 | Implement scheduler (DAG, write-set disjointness, budgets, leases) | 6 | scenario tests | 10 |
| 8 | Implement fake adapter + scenario suite (success, flaky, malformed, timeout, crash, conflict) | 7 | all scenarios green offline | 07 Part E |
| 9 | Implement engine-run verification runner (scrubbed env, argv only) | 5,8 | "agent claims success, checks fail" ⇒ not succeeded | O-17 |
| 10 | Implement policy engine + approvals (CLI human channel, hash pinning) | 6 | forgery/stale-approval tests | O-04, O-16 |
| 11 | Implement integrator (scratch rebase, re-verify, merge/PR) porting merge-gate cases | 9,10 | cases from `tests/test-merge-gate.sh` reproduced | O-01 |
| 12 | Implement first real adapter + contract suite | 8, spikes | 20 fixture runs clean | 11 P3 |
| 13 | Write role prompts; spec/plan/review stages; end-to-end demo | 11,12 | demo scenario at L2 | 11 P4 |
| 14 | Hardening: sandbox profile, soak with failure injection, security suite | 13 | Phase 6 exit | 08 |
| 15 | `factory init/doctor/explain`, docs generation, upgrade/uninstall | 13 | 13 §1 steps 1–18 demonstrable | 13 |
| 16 | Second adapter; manifests/registry if a second component author exists | 14 | parity suite | 06, 11 P5 |
Reuse from the archive without re-analysis: test scenarios in `tests/test-merge-gate.sh`, `tests/test_approval.py`, `tests/test_github_reads.py`, `tests/test-workflow-halt.sh` (pattern); gate/approval/policy semantics from `scripts/super-board-merge-gate.sh`, `-approval.py`, `-merge-policy.py`; incident list in `RELEASE-NOTES.md`; `ui-refine-loop.js` as a model for code-enforced bounds.
