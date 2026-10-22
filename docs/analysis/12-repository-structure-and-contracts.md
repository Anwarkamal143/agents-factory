# 12 — Repository Structure and Component Contracts

Proposal. Format choices: **JSON Schema (draft 2020-12)** for every machine contract (language-neutral, validates at load, generates docs); **YAML** for human-authored declarative files (workflow, project config, manifests); **Markdown + YAML frontmatter** for prompts (agents, skills). Typed code (Python dataclasses generated from or checked against the schemas) lives only in `core/`.

## 1. Factory repository layout
```text
software-factory/
├── core/                 engine, state machines, scheduler, policy, store, verify, integrator, CLI
├── contracts/            JSON Schemas + versioned examples (the only cross-boundary truth)
├── workflows/            default lifecycle YAML (+ examples)
├── components/
│   ├── agents/           role definitions (.md + frontmatter)
│   ├── skills/           skill definitions (SKILL.md + manifest)
│   └── tools/            declared tool integrations (manifest + implementation)
├── adapters/
│   ├── fake/             scripted scenarios (MVP)
│   ├── claude-code/      (MVP or P1)
│   ├── codex/            (P1)
│   └── generic-cli/      (P2, prompt-JSON path)
├── integrations/         github/ (optional projection)
├── policies/             default risk classes + autonomy profiles
├── project-templates/    `factory init` templates per ecosystem
├── scripts/              dev-only maintenance (release, doc generation)
├── tests/                unit/ contracts/ workflows/ adapters/ fixtures/ security/ e2e/
├── docs/                 generated reference + ADRs + guides
└── examples/             sample repos and runs
```
| Directory | Why | Belongs | Must NOT contain | May depend on | MVP |
|---|---|---|---|---|---|
| `core/` | one engine, vendor-free (fixes R-09) | state machines, scheduler, store, policy, verify runner, CLI | harness SDK imports, prompts, project-specific logic | `contracts/` | yes |
| `contracts/` | single source of truth for interfaces | schemas, example payloads, schema version policy | code | nothing | yes |
| `workflows/` | declarative lifecycles | YAML using engine primitives only | prompts, shell | `contracts/` | yes (default only) |
| `components/agents` | role prompts | Markdown role specs + manifests | control flow | `contracts/` | yes |
| `components/skills` | reusable know-how | SKILL.md, references, manifest with requirements/permissions | executable code that bypasses permission profile | `contracts/` | minimal |
| `components/tools` | declared deterministic helpers | manifest + implementation invoked by engine/adapters | agent prompts | `contracts/` | optional |
| `adapters/*` | the *only* place vendor specifics live | launch, permission mapping, output parsing, capabilities | workflow logic, policy decisions | `contracts/`, `core` interfaces (not internals) | fake + 1 |
| `integrations/` | optional external systems | GitHub client, projections | engine state authority | `contracts/` | no |
| `policies/` | defaults for risk/autonomy | YAML policy packs | code | `contracts/` | yes |
| `project-templates/` | onboarding output | `.factory/` templates | factory internals | none | yes (1–2) |
| `scripts/` | repo maintenance | release, docgen | runtime code | any | no |
| `tests/` | verification | per layer | production logic | all | yes |
| `docs/`, `examples/` | learning, ADRs | generated + prose | specs that contradict schemas | — | minimal |

Dependency rule (enforced by an import-lint test): `contracts ← core ← adapters/integrations`; components depend only on contracts; nothing depends on `tests`.

## 2. Target-repository layout (project-owned vs factory-managed)
```text
<project>/
└── .factory/
    ├── project.yaml        PROJECT-OWNED  commands, base branch, policy overrides, adapter choice
    ├── overrides/          PROJECT-OWNED  local agent/skill overrides (shadow managed ones)
    ├── factory.lock        MANAGED        installed component versions + sha256 of every managed file
    ├── managed/            MANAGED        installed components (never hand-edit; doctor detects drift)
    └── state/              GENERATED      events.jsonl, snapshot.json, artifacts/, worktrees/  (gitignored)
```
Fixes S-11: upgrades touch only files listed in `factory.lock`; drift in managed files is reported, never silently overwritten.

## 3. Contracts

### C1 Agent definition (`components/agents/<id>.md`)
```markdown
---
id: builder
kind: agent
version: 1.0.0
contract: factory.agent/1
role: builder                # stage role this agent can fill
skills: [tdd@^1, repo-conventions@^1]
requires: {capabilities: [fs.write, shell], structured_output: preferred}
permissions: {fs: {write: [worktree]}, net: false, shell: [git, "{project.verify}"]}
budgets: {wall_s: 1800, tool_calls: 200}
output_schema: factory.task-result/1
---
You are the builder. Implement only the task objective within the declared write set…
```
Validation: frontmatter against `agent.schema.json`; body ≤ N tokens; no tool names not in `permissions`.

### C2 Skill definition (`components/skills/<id>/{SKILL.md, component.yaml}`)
```yaml
id: tdd
kind: skill
version: 1.2.0
contract: factory.skill/1
entry: SKILL.md
applies_to: {roles: [builder], labels: [bug, feature]}
requires: {components: [], tools: [], capabilities: []}
delivery: {native: true, inline_fallback: true}   # how adapters without native skill support get it
permissions: {}            # skills grant nothing; they cannot widen the agent's profile
```
### C3 Tool integration (`components/tools/<id>/component.yaml`)
```yaml
id: run-tests
kind: tool
version: 1.0.0
contract: factory.tool/1
invoke: {argv: ["{python}", "-m", "pytest", "-q"], cwd: worktree, env_allow: [PATH, CI], timeout_s: 900}
inputs: {type: object, properties: {paths: {type: array, items: {type: string}}}}
outputs: {exit_code: int, log_artifact: path}
side_effects: none        # none | fs-worktree | net | git-write (policy engine keys off this)
```
Argv arrays only — no shell strings (replaces `eval "$cmd"`, S-06).

### C4 Workflow definition (`workflows/<id>.yaml`)
Schema essentials: `workflow: <id>/<major>`, `stages[]` each with `id`, exactly one of `role|engine|for_each_task`, optional `gate`, `after[]` (verify/review steps), `loop {max, until}`, `on_failure: block|fail|escalate`. Validator rules: stage ids unique; every gate names a policy; loops have `max`; no unreachable stage; only declared primitives (example in 10 §12.6).

### C5 Harness adapter (`adapters/<id>/adapter.yaml` + implementation of 5 operations)
```json
{ "id":"codex","contract":"factory.adapter/1","version":"0.1.0",
  "capabilities":{"structured_output":"native","subagents":true,"max_parallel":4,
                  "sandbox":"os","hooks":false,"ask_user":false,"cancel":true,"resume":true,
                  "usage":true,"skills":"native","models":["fast","standard","deep"]},
  "requires":{"binaries":["codex"],"min_version":"TBD-by-spike"} }
```
Operations (Python protocol / CLI JSON-RPC over stdio): `capabilities()`, `start(task_input)→handle`, `events(handle)→stream`, `cancel(handle, grace_s)`, `result(handle)→task_result`, optional `resume(token)`. Values such as `min_version` are filled by Phase 0 spikes — not asserted here.

### C6 Component manifest — see 06 Part B (`component.yaml`): `id, kind, version, contract, entry, requires, permissions, triggers, inputs, outputs, supports, tests, deprecates`. Schema `manifest.schema.json` with `kind` discriminator.

### C7 Task input / output (shared with 07 Part C)
```json
// contracts/task-input.schema.json (abridged)
{"$id":"factory.task-input/1","type":"object",
 "required":["task_id","run_id","role","objective","acceptance","workspace","permissions","budgets","output_schema"],
 "properties":{
  "task_id":{"type":"string","pattern":"^T-[0-9A-Z]+$"},
  "role":{"enum":["spec-writer","planner","builder","tester","reviewer"]},
  "acceptance":{"type":"array","items":{"type":"object","required":["id","text"]}},
  "scope":{"type":"object","properties":{"write_set":{"type":"array"},"exclusions":{"type":"array"}}},
  "context":{"type":"array"},
  "permissions":{"$ref":"permission-profile.schema.json"},
  "budgets":{"type":"object","properties":{"wall_s":{"type":"integer"},"tokens":{"type":"integer"},"tool_calls":{"type":"integer"}}},
  "resume_token":{"type":["string","null"]}}}
// contracts/task-result.schema.json (abridged)
{"$id":"factory.task-result/1","required":["task_id","status","summary"],
 "properties":{"status":{"enum":["succeeded","failed","blocked","needs_approval","canceled"]},
  "changes":{"type":"object","properties":{"commit":{"type":"string"},"files":{"type":"array"}}},
  "evidence":{"type":"array","items":{"required":["type","ref"]}},
  "findings":{"type":"array"},"questions":{"type":"array"},"usage":{"type":"object"}}}
```
The engine ignores `status:"succeeded"` unless its own verification passes (state machine, 10 §12.4).

### C8 Approval request
```json
{"$id":"factory.approval-request/1","approval_id":"AP-01H…","run_id":"R-…","task_id":"T-12",
 "action":"deliver.merge","subject":{"type":"commit","id":"<head sha>","hash":"sha256:…"},
 "scope":{"risk_classes":["schema"],"files_changed":12,"lines_changed":340},"scope_hash":"sha256:…",
 "reason":"policy:risk_class=schema requires human approval at L2","expires_at":"2026-…Z",
 "decision":null,"approver":null}
```
Granting requires an authenticated human channel; `subject.hash` and `scope_hash` re-checked at use (generalizes `approval.py`).

### C9 Verification result
```json
{"$id":"factory.verification-result/1","verification_id":"V-…","task_id":"T-12","attempt":2,
 "base":"<sha>","head":"<sha>","environment":{"image":"…|host","env_keys":["PATH","CI"],"network":false},
 "checks":[{"name":"unit","argv":["pytest","-q"],"exit_code":0,"duration_s":41.2,"log":"artifacts/…/unit.log"}],
 "passed":true,"started_at":"…","finished_at":"…"}
```
Always produced by the engine; agent-submitted evidence is stored but never counts toward `passed`.

### C10 Persistent workflow state
```json
// state/events.jsonl — one object per line
{"seq":104,"ts":"…","run":"R-…","type":"task.transitioned","actor":"engine",
 "payload":{"task":"T-12","from":"verifying","to":"reviewing","cause":"verification V-77 passed"},"crc32":"a1b2c3d4"}
// state/snapshot.json (derived; rebuildable)
{"schema":"factory.run-state/1","run":"R-…","last_seq":104,"status":"executing",
 "tasks":{"T-12":{"status":"reviewing","attempts":2,"lease":null}},"approvals":{},"budgets":{"tokens_used":120344}}
```
Rules: schema version in every snapshot; unknown future versions refuse to load; migrations are explicit functions with tests.

## 4. Contract governance
Versioning: `factory.<name>/<major>`; additive changes within a major; breaking change ⇒ new major + migration + adapter capability gate. Every schema has good/bad fixtures under `tests/contracts/`. Docs under `docs/reference/` are generated from schemas (addresses R-08 doc drift).
