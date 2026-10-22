# 00 — Executive Summary

## What was analyzed
`super-board-main.zip` (SHA-256 `3839946…1909ebcd`, 326 files after extraction, v3.1.2, MIT): a Claude Code plugin and installer that runs a GitHub Project board autonomously. The analysis was **static**: I read the specification prompt, documentation, skills, 30 scripts, 2 workflows, 5 guard hooks, tests, evals, CI and release notes, and traced the actual code paths. **No script, test, eval or installer from the archive was executed**, and the original archive was not modified. Every claim carries an evidence level (Verified / Documented / Inferred / Unknown); see `evidence/verification-status.md`.

## What the factory actually does
A human moves well-specified GitHub issues to *Ready*. An LLM orchestrator session runs a *wave*: a deterministic shell planner picks dependency-free cards; a host-provided Workflow runtime (`super-board-wave.js`) runs pre-flight → classify → **Build → QA → Review** lane agents per card, each following prose lifecycles in `run.md`; a script (`merge-gate.sh`) then verifies the PR on the current base, applies a risk policy, checks a head-pinned human approval where required, and squash-merges. State lives on the GitHub board, assignees, PR comments and a few lock files. A second, separate implementation drives Codex; a third legacy runner uses `claude -p`.

## Most important architectural characteristics
1. **Thin deterministic shell around prose-defined LLM lanes**: scripts are crisp; lane behavior and loop control are Markdown.
2. **External state, no local store**: board-as-state gives free resumability but causes rate-limit incidents (documented) and non-atomic claims.
3. **Heavy Claude Code coupling**: 344 `.claude/` references in 59 files; host Workflow globals; Claude-only hooks; Codex path is a reimplementation.
4. **Incident-driven evolution**: 27 releases in ~5 months, each rule traceable to a failure.
5. **No agent files, manifests, or schema loader**: roles are prompt strings; inventories are hard-coded lists.

## Strongest features
Merge gate (lock, head pin, verify on current base, policy, `--match-head-commit`); deterministic wave planner with fail-safe defaults; head-and-scope-pinned approval; validated/retrying GitHub reads with a run-halt mechanism; safe worktree cleanup; machine-checked report formats; a stub-harness test pattern for the workflow; disciplined release process.

## Most significant weaknesses and risks
- **S-01** The merge gate is a convention: no hook stops a bare `gh pr merge`, and the docs recommend allow-listing it.
- **R-01** Retry/rebuild caps, block-rate alert and zero-progress halt are not enforced in inspected code (variables assigned, never used; prose only).
- **S-02** Approval is not tied to a distinct human identity in solo mode.
- **S-06** PR-head code runs through `eval` with ambient credentials; verification-readiness only checks non-blank commands.
- **S-07** No untrusted-content posture for issue/comment text feeding privileged agents.
- **S-03** Guard hooks fail open, are Claude-only, and have no Codex equivalent.
- **R-08** Six confirmed doc/code mismatches; config is never schema-validated; orchestration logic is triplicated.

## Most valuable opportunities
Engine-enforced budgets and retries (O-08); engine-run verification (O-17); engine-owned merge (O-15); local event log as the source of truth (O-13); one engine with harness adapters and a fake adapter for tests (O-12, O-05); validated config (O-11); manifests with a hash lockfile (O-18, O-24). Full list: `09-improvement-opportunities.md`.

## Recommended approach for our own factory
**Rebuild the control plane; reuse the ideas and the tests.** A small Python engine with explicit run/task state machines, a DAG scheduler with declared write sets, a policy engine with autonomy levels L0–L4, engine-run verification, an engine-only integrator, a JSONL event log + snapshot store, declarative YAML workflows with fixed primitives, and a five-operation harness adapter contract proven first against a fake adapter. Agents and skills remain Markdown prompt assets. Details: `10`, `12`, `14`.

## First implementation milestone
Phase 0 spikes (hook/permission coverage, structured output + cancel, merge semantics) then Phases 1–2: schemas, config validation, event log with crash recovery, state machines, scheduler and a fake adapter whose scenario suite — including **kill at every event boundary** and "agent claims success but checks fail" — passes offline with no model calls. (`11-implementation-roadmap.md`)

## Important unknowns and unverified claims
- Whether lane agents follow `run.md` as intended (only paid evals could show; no results in the archive).
- Whether hooks apply to Workflow `agent()` sub-agents; Workflow runtime behavior; Codex end-to-end behavior; CI results.
- Whether the offline test suites (59) pass; author-reported figures (GraphQL cost, model benchmarks) are unreproduced.
- Exploitability of S-01/S-02 is inferred from code structure, not demonstrated.
- Harnesses other than Claude Code and Codex were not inspected; the portability design is a proposal with their capabilities unknown.
Next steps to close these require authorization to run tests in a disposable container and a sandbox GitHub repository (`evidence/verification-status.md`, "Gaps to close").

## Package map
`01` inventory · `02` philosophy · `03` architecture · `04` workflow · `05` components · `06` lifecycle · `07` harness portability · `08` security/reliability · `09` improvements · `10` new architecture · `11` roadmap · `12` structure & contracts · `13` install/DX · `14` final recommendations · `evidence/` · `diagrams/`.
