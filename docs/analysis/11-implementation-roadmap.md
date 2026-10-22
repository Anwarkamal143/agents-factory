# 11 — Implementation Roadmap

Proposal only. Complexity: **L**ow / **M**edium / **H**igh. Mandatory = needed for the MVP defined in 14; Optional = enhancement. Phases are an ordering of work, not separate releases; Phases 2–4 can ship as one 0.1 release. Implementation language decision (recorded here, reversible because contracts are JSON Schema): **Python ≥3.11, stdlib-first** — subprocess/fsync/rename semantics, easy fixture tests, runs where super-board's helper scripts already ran (Python 3.9+/bash). Alternative (TypeScript) is acceptable if the team prefers; no contract depends on it.

## Phase 0 — Validate the architecture (M, mandatory)
- **Objective:** close the unknowns that change the design before writing code.
- **Scope:** three time-boxed spikes + decisions.
  1. *Hook/permission coverage:* do the first target harness's permission mechanisms apply to sub-agents/headless runs? (super-board U: hooks under Workflow sub-agents). Decides how much enforcement can be delegated to the harness vs sandbox.
  2. *Structured output + cancel:* can the target harness return schema-valid JSON non-interactively and be killed cleanly (process group)?
  3. *Merge/protection semantics:* behavior of `--match-head-commit`, required checks, merge queue in a sandbox GitHub repo (only if GitHub delivery is in MVP).
- **Prerequisites:** a throwaway repo, harness access, authorization for execution.
- **Deliverables:** `docs/decisions/ADR-001..` (language, store, workflow format, first adapter), signed-off non-goals, acceptance scenario spec, threat model v0 (from 08).
- **Dependencies:** none.
- **Acceptance:** each spike has a written result (yes/no/partial + evidence); ADRs merged; first adapter chosen.
- **Tests:** spike scripts committed under `spikes/` (not shipped).
- **Security:** decide default permission profile and network policy; list credentials the engine must never expose.
- **Exit:** unknowns table (below) has no "blocking" rows.

| Unknown | Source | Blocks |
|---|---|---|
| Sub-agent hook coverage | super-board U | enforcement design |
| Adapter structured-output reliability | not inspected | adapter contract strictness |
| Real merge semantics under protection | not run | delivery step |

## Phase 1 — Foundation (M, mandatory)
- **Objective:** repo skeleton, contracts, config, logging, test harness.
- **Scope/files:** `contracts/` (JSON Schemas: task-input, task-result, approval, verification, event, run-state, manifest, project config), `core/config` (load + validate + defaults), `core/events` (writer/reader, crc), `core/store` (log, snapshot, lease), `cli/` (`factory init|doctor|version`), `tests/unit`, `tests/contracts`, CI.
- **Prerequisites:** Phase 0 ADRs.
- **Dependencies:** none external beyond `jsonschema` (or vendored validator).
- **Acceptance:** schemas validate good/bad fixtures; event log survives torn-tail and bad-crc tests; `factory doctor` reports tools/permissions in read-only mode; config rejects trivial verify commands (`true`, empty) — fixes R-07.
- **Tests:** unit + property tests for log replay; contract tests; mutation of fixtures.
- **Security:** no shell string execution anywhere (argv only); redaction filter for logs; secrets never in events.
- **Exit:** CI green on Linux+macOS; replay of 10k synthetic events < target time (set in Phase 1).

## Phase 2 — Minimal execution engine (H, mandatory)
- **Objective:** deterministic engine proven with the fake adapter.
- **Scope/files:** `core/statemachine` (task/run tables from 10), `core/scheduler` (DAG, write-set disjointness, budgets, leases), `core/policy` (risk classes, autonomy levels), `core/verify` (engine-run checks in isolated worktree/env), `adapters/fake` (scripted scenarios), `workflows/default.yaml` loader.
- **Prerequisites:** Phase 1.
- **Acceptance:** scenario suite passes with no model: success, retry-then-success, retries exhausted → blocked, identical-failure-twice → blocked, malformed output → repair-once, timeout, cancel, crash-and-resume at every event boundary, conflicting parallel tasks refused/serialized, agent-claims-success-but-checks-fail ⇒ never `succeeded`.
- **Tests:** deterministic workflow tests + failure-injection harness (kill at event N, for all N).
- **Security:** policy decision logged for every side effect; default-deny unknown actions.
- **Exit:** invariants hold under property tests: no illegal transition; terminal states immutable; `succeeded ⇒ verification passed ∧ no blocking finding ∧ approvals satisfied`.

## Phase 3 — First real harness adapter (M–H, mandatory)
- **Objective:** run real tasks through one harness (Claude Code or Codex).
- **Scope/files:** `adapters/<name>/` (`capabilities.json`, launcher, permission-profile mapper, output parser/repair, cancel), context bundler, approval-request relay, adapter contract suite.
- **Prerequisites:** Phase 0 spikes 1–2, Phase 2.
- **Acceptance:** contract suite passes against the adapter; one fixture repo task completes; permission-denial and cancel verified; degradations logged (`capability.degraded`).
- **Tests:** adapter contract tests (nightly, real calls), plus fake-adapter parity test (same scenarios produce same event shapes).
- **Security:** worktree-only write profile; network off; env scrubbed; agent never receives merge/push credentials.
- **Exit:** 20 consecutive fixture runs without engine-state corruption; adapter swap (fake↔real) requires no core change.

## Phase 4 — Development lifecycle (H, mandatory)
- **Objective:** spec → plan → execute → verify → review → integrate → deliver.
- **Scope/files:** roles/prompts (`components/agents/*.md`), spec + plan artifacts and validators (acyclic DAG, acceptance coverage, write sets), review coordinator + finding model, integrator (scratch-tree rebase, re-verify, merge/PR), approval flow via CLI prompt, delivery policy.
- **Prerequisites:** Phase 3.
- **Acceptance:** demo scenario (feature + bug + two overlapping tasks) completes end-to-end at L2 with approvals; integration conflict routes back to a rebase task; delivery blocked without approval where policy demands; port of super-board merge-gate semantics proven by cases derived from `tests/test-merge-gate.sh` (O-01).
- **Tests:** workflow tests (fake) + one real-adapter e2e; injection fixtures (issue text containing instructions must not change permissions).
- **Security:** engine-only merge; approval objects pinned to head+scope hashes; untrusted-text boundary markers.
- **Exit:** MVP definition in 14 met.

## Phase 5 — Extensibility (M, optional until a second component author exists)
Component manifests + registry, skill loader with version pins, validation (`factory component validate`), compatibility/capability checks, add/remove/replace commands (06 Part B), lockfile with hashes. **Acceptance:** adding a skill requires one directory + manifest; removal refuses when depended on; upgrade preserves project overrides. **Security:** third-party components declare permissions; unpinned remote components rejected. **Exit:** swap a role's skill without core edits and tests prove contract parity.

## Phase 6 — Hardening (H, mandatory before "production-ready")
Concurrency (multiple runs per repo via leases), permission enforcement tests, OS/container sandbox profile (optional dependency), audit log export, resource budgets (tokens/wall/tool calls), GC of worktrees, security test suite (escape, forgery, leak), chaos runs. **Acceptance:** 100-run soak with injected failures shows zero state corruption and zero unauthorized side effects. **Exit:** threat-model v1 reviewed, every S-/R- finding in 08 mapped to a test or an accepted-risk entry.

## Phase 7 — Developer experience (M, mostly optional)
`factory init` detection + templates, second adapter, GitHub integration (issues/PR/check projection), `factory status|logs|explain`, docs and examples, upgrade/uninstall (see 13). **Acceptance:** new repo onboarded in <15 minutes by following docs; `factory doctor` pinpoints each seeded misconfiguration.

## Dependency graph and sequencing
`P0 → P1 → P2 → P3 → P4 (MVP)`; `P6` partly parallel with P4 (security tests); `P5`, `P7` after MVP. Do not start P3 before P2's fake adapter passes the full scenario suite; do not start P5 before a second real component author exists (avoid speculative generality).

## Cross-cutting definition of done
Every task: unit tests, schema updates versioned, events documented, security note, no unverified claim in docs (docs generated from schemas where possible).
