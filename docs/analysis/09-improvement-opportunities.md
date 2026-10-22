# 09 — Improvement Opportunities

Each item separates **observed fact** (with evidence ID from 08 or the evidence files) from **proposed decision**. Classification (spec §11.1): **KEEP** adopt as-is · **ADAPT** keep idea, change form · **FIX** defect in a good idea · **REDESIGN** replace mechanism · **ADD** missing capability · **AVOID** do not copy. Priority = value ÷ (effort × risk): **P0** must-have for MVP, **P1** soon after, **P2** later, **P3** optional.

## 1. Classified opportunities

| ID | Class | Observed fact | Proposal | Value | Effort | Risk if skipped | Pri |
|---|---|---|---|---|---|---|---|
| O-01 | KEEP | Merge gate: lock, head pin, verify on current base, policy, approval, `--match-head-commit` (`merge-gate.sh` L173-351) | Re-implement as the engine's *integrate* step with the same semantics and exit-code-to-state mapping | Very high | M | Unsafe merges | P0 |
| O-02 | KEEP | Deterministic planner separated from LLM judgment (`wave-plan.sh`) | Planner as pure function over state → ready set | High | S | — | P0 |
| O-03 | KEEP | Fail-safe halts on missing evidence (exit 9/10/79; unreadable deps ⇒ not free) | Default-deny scheduling rules | High | S | Silent wrong action | P0 |
| O-04 | KEEP | Head-and-scope-pinned approval (`approval.py`) | Approval objects bound to `{task, artifact hash, scope hash}` | High | S | Stale approvals | P0 |
| O-05 | KEEP | Stub-harness testing of the workflow JS (`tests/test-workflow-halt.sh`) | Fake adapter + scripted scenarios in CI | Very high | M | Untestable orchestration | P0 |
| O-06 | KEEP | Incident-driven rules with dates in RELEASE-NOTES | Keep a `lessons/` register that links each guard to a regression test | High | S | Re-learning failures | P1 |
| O-07 | KEEP | Writing-standard + marker blocks tested by `test_writing_format.py` | Machine-parseable report formats as schemas | Medium | S | Parse drift | P1 |
| O-08 | FIX | Loop bounds prose-only (R-01) | Engine counters: per-task attempts, per-run budget, no-progress detector; failure → `blocked` with reason | Very high | S | Runaway cost/loops | **P0** |
| O-09 | FIX | Merge refusal halts run (R-02) | Map refusal categories to task-level states | Medium | S | Whole-run stalls | P1 |
| O-10 | FIX | Docs/code drift (R-08) | Generate reference docs from schemas/manifests; contract tests that fail on drift | High | M | Misleading operators | P1 |
| O-11 | FIX | Config unvalidated (R-07) | Load-time JSON Schema validation; lint that verification commands are meaningful (not `true`, exit-code-only) | High | S | Bad gates pass | P0 |
| O-12 | REDESIGN | Orchestration = host-specific JS + second Codex reimplementation + legacy (R-09, 03) | One engine; harness adapters implement the 5-call contract (07) | Very high | L | Triple maintenance | P0 |
| O-13 | REDESIGN | State in GitHub board + assignees + comments (R-03, R-05, R-06) | Local append-only event log + snapshot as truth; GitHub as optional projection | Very high | M | Rate limits, races | P0 |
| O-14 | REDESIGN | Guardrails = fail-open hooks (S-03) | Capability-based permissions enforced by engine + OS sandbox; hooks optional | Very high | L | Prompt-trust failures | P1 (policy model in P0) |
| O-15 | REDESIGN | Merge by agent following a convention (S-01) | Only the engine performs merge/deploy; agents never hold that permission | Very high | S | Bypass | P0 |
| O-16 | REDESIGN | Approval by agent-writable comment (S-02) | Approvals originate from an authenticated human channel (CLI/web) and are stored in the event log | High | M | Self-approval | P1 |
| O-17 | ADAPT | Verification delegated to agents except at merge | Engine runs verification commands itself after every task; agent claims are advisory evidence | Very high | M | Hallucinated "tests pass" | **P0** |
| O-18 | ADAPT | Skills as Markdown + hard-coded REGISTRY (`skills-ready.py`) | Manifest-declared skills with requirements, permissions and version pins | High | M | Unpinned third-party risk | P1 |
| O-19 | ADAPT | GitHub as only tracker | Tracker interface; GitHub first, local-file tracker for tests | Medium | M | Lock-in | P1 |
| O-20 | ADD | No first-class spec/plan artifacts | `spec.md` + `plan.json` (DAG, file ownership, acceptance mapping) with approval states | High | M | Ambiguity, collisions | P1 |
| O-21 | ADD | Same-file conflict handling by LLM judgment + late rebase | Declared write sets in plan; scheduler refuses overlapping parallel tasks; integration in a scratch tree | High | M | Rework | P1 |
| O-22 | ADD | No structured event log, cost/time accounting (V negative) | JSONL events with run/task IDs, usage, replay | High | S | Undebuggable runs | **P0** |
| O-23 | ADD | No per-task timeout/cancel (R-04) | Budgets and cancel in adapter contract | High | S | Hangs | P0 |
| O-24 | ADD | Installer overwrite hazard (S-11), no uninstall | Hash manifest, `factory doctor/upgrade/uninstall` | Medium | M | Data loss | P1 |
| O-25 | ADAPT | Model ladders as constants (R-11) | Abstract tiers (`fast/standard/deep`) mapped per adapter | Medium | S | Vendor lock | P1 |
| O-26 | ADAPT | Untrusted text goes straight to agents (S-07) | Mark external text as data, minimize tool grants for intake agents, spec-approval gate | High | M | Injection | P1 |
| O-27 | ADD | Graded autonomy absent (08 §10.3) | Autonomy levels L0–L4 mapped to approval gates per side-effect class (see 10) | High | M | All-or-nothing risk | P1 |
| O-28 | AVOID | 816-line prose lifecycles as the control plane | Prose limited to *role prompts*; control flow in code | — | — | — | — |
| O-29 | AVOID | Assignee-as-mutex | Local leases | — | — | — | — |
| O-30 | AVOID | `eval "$cmd"` of config strings | Argv arrays, no shell by default, run in sandbox | — | — | — | — |
| O-31 | AVOID | `curl | bash` without verification; `rm -rf dest/*` installs | Signed artifacts; manifest-based install | — | — | — | — |
| O-32 | AVOID | Hard-coded maintainer persona, paths and model names in shared assets | Parameterize | — | — | — | — |
| O-33 | AVOID | Copying heuristics-by-regex as the primary security control | Sandbox first | — | — | — | — |
| O-34 | ADAPT | Secondary skills (visual, ui-refine-loop, git-sync, super-collect) | Post-MVP optional plugins, not core | Medium | — | Scope creep | P3 |

## 2. Prioritization (spec §11.2)
**P0 (MVP, in this order):** O-22 event log → O-13 local state → O-08/O-23 budgets & cancel → O-12 engine + adapter contract → O-05 fake adapter tests → O-17 engine-run verification → O-11 config validation → O-15 engine-owned merge → O-01/O-02/O-03/O-04 ported semantics.
**P1:** policy/autonomy levels (O-14, O-27), human-channel approvals (O-16), manifests (O-18), spec/plan artifacts (O-20/O-21), tracker interface (O-19), installer (O-24), injection posture (O-26), doc generation (O-10), lessons register (O-06).
**P2/P3:** secondary skills, richer review agents, dashboards.

## 3. Avoiding overengineering (spec §11.3)
Observed: super-board grew 27 releases in ~5 months, much of it responding to real failures — accretion is partly justified. For the new factory:
- Do **not** build a plugin marketplace, multi-tenant server, distributed workers, or UI in MVP.
- Do **not** support more than 2 real adapters + the fake adapter before the engine's contracts are stable.
- Do **not** model every workflow as configurable YAML at first; ship one default lifecycle (spec→plan→execute→verify→review→integrate) and extract configurability only when a second workflow actually exists.
- Do **not** add a database server; start with files (JSONL + snapshots), keep a storage interface so SQLite can replace it.
- Do **not** port the QA crawler, `visual`, or `super-collect` until the core loop is proven.
- Each added abstraction must name the observed failure it addresses (use R-/S- IDs); otherwise defer.

## 4. Open questions worth a quick spike
1. Does the host Workflow runtime run PreToolUse hooks for `agent()` sub-agents? (decides how much to trust hook-based guardrails on Claude)
2. How much of lane quality comes from the 800 lines of lifecycle prose vs the skills? (run the 7 evals with ablations)
3. What is the real merge-queue/branch-protection behavior with `--match-head-commit` under required checks? (sandbox repo test)
