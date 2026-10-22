# 07 — Agent-Harness Agnosticism

Observed facts (Part A) are separated from proposed design (Parts B–E). **No compatibility with any harness other than Claude Code and Codex CLI is claimed or implied; even those two were not executed.**

## Part A — Existing coupling (measured by `grep -rIE` over `skills/ scripts/ hooks/ workflows/ install.sh get.sh CLAUDE.md README.md`)

| Coupling | Files / hits | Where it matters | Class |
|---|---|---|---|
| `.claude/` path convention | 59 / 344 | install target, bin path in every lane prompt, state dir, worktrees, hooks | filesystem layout |
| `claude -p` | 13 / 42 | legacy runner, dispatcher, docs | CLI invocation |
| `AskUserQuestion` | 4 / 20 | onboarding interaction | host UI tool |
| `CLAUDE_PROJECT_DIR` | 7 / 21 | hooks | host env var |
| `PreToolUse` / `permissionDecision` | 8 / 20 · 5 / 9 | all guard hooks | host hook protocol |
| `Workflow` tool, `agent()`, `pipeline()`, `log()` | 7 / 18 · 2 / 8 · 1 / 1 | `super-board-wave.js`, `ui-refine-loop.js`, run-workflow.md | host orchestration runtime |
| `ScheduleWakeup`, `TaskStop` | 1 / 1 each | run-workflow.md | host scheduling/cancel tools |
| status-line `rate_limits` | 2 / 11 | `super-board-usage.sh` reads Claude's recorded limits | host telemetry |
| `.agents/skills`, `CODEX_*`, `codex exec` | 17 / 27 · 6 / 24 · 4 / 4 | Codex discovery/launch | second harness |
| Model names (haiku/sonnet/opus, gpt-6-*) | wave.js `LADDERS`, codex-lane.sh `CODEX_LADDERS` | hard-coded constants | vendor model naming |
| Skills in Markdown with frontmatter | 8 SKILL.md | Claude/Codex skill discovery convention | host skill format |
| Slash verbs | `SKILL.md` | user interface | host UX |

**Assessment (V/I):** the *mechanics* (planner, GitHub reader, merge gate, approval, policy) are shell/Python and harness-free except for the `.claude/bin` path. The *orchestration* is host-bound (Workflow runtime) with a second, separate implementation for Codex. *Guardrails* are Claude-only. *Interaction* (onboarding) is host-UI-bound. *Telemetry/budget* is Claude-only.

### Existing harness-neutral abstractions worth reusing
- `STAGE_SCHEMA` result shape (status ∈ advanced/bounced/blocked/human-gate/failed/halted).
- Exit-code contracts of scripts.
- `host.sh` environment detection (Codex via `CODEX_THREAD_ID`/`CODEX_SESSION_ID`).
- Stub-harness tests of the workflow (`tests/test-workflow-halt.sh`) — proof that orchestration can run against an injected `agent`.

## Part B — Portable vs harness-specific split (proposed)
| Portable core (no vendor imports) | Harness adapter responsibility |
|---|---|
| Domain model, state machines, scheduler, dependency DAG | Start an agent session with a prompt + context bundle |
| Policy/permission/approval engine | Translate permission grants into the harness's tool allow-list/sandbox |
| Workflow definitions (data), skill/prompt assets | Discover/activate skills in the harness's native format (symlink/copy/inline) |
| Verification runner (the engine executes checks itself) | Stream events/progress; honor cancel; report usage |
| Event log, artifact store, run state | Structured-output enforcement (schema flag, tool, or post-parse) |
| Integrations (GitHub, CI) behind interfaces | Interactive prompts (or fall back to non-interactive config) |

## Part C — Portable contract (JSON Schema sketches; full set in 12)

```jsonc
// task-input
{"task_id":"T-12","run_id":"R-3","role":"builder","objective":"…","acceptance":["…"],
 "workspace":{"path":"/abs/worktree","base":"main","branch":"fac/T-12"},
 "context":[{"kind":"file","path":"…"},{"kind":"skill","id":"tdd@1.2"}],
 "permissions":{"fs":{"write":["worktree"]},"net":false,"shell":["git","npm test"],"secrets":[]},
 "budgets":{"wall_s":1800,"tokens":300000,"tool_calls":200},
 "output_schema":"factory.task-result/1","resume_token":null}
// task-result
{"task_id":"T-12","status":"succeeded|failed|blocked|needs_approval|canceled",
 "summary":"…","changes":{"files":["…"],"commit":"sha"},
 "evidence":[{"type":"command","cmd":"npm test","exit":0,"log":"artifacts/…"}],
 "findings":[],"questions":[],"usage":{"tokens_in":0,"tokens_out":0,"wall_s":0},
 "adapter":{"name":"codex","version":"…","capabilities_used":["shell","fs"]}}
```
Required adapter operations: `capabilities()`, `start(task_input) -> handle`, `events(handle)` (progress/tool/approval requests/errors), `cancel(handle)`, `result(handle)`, `resume(handle|token)` (optional). The engine, not the adapter, runs verification commands and records evidence; adapter-reported evidence is advisory.

## Part D — Capability detection and graceful degradation
| Capability | Detect by | If absent |
|---|---|---|
| Structured output | adapter flag `structured_output: native|prompt|none` | native schema; else instruct JSON + engine validate/repair once; else fail task |
| Subagents / parallelism | `subagents:true`, `max_parallel` | engine runs tasks as separate adapter sessions; or serialize |
| Tool allow-listing / sandbox | `sandbox: os|tool-allowlist|none` | `none` ⇒ policy refuses autonomy levels above L1 (see 10) |
| Hooks | `hooks:true` | engine-side permission checks only; warn |
| Interactive questions | `ask_user:true` | read answers from `.factory/answers.yaml` or stop in `needs_input` |
| Cancellation | `cancel:true` | process kill with timeout; mark task `canceled` |
| Resume | `resume:true` | restart task from last checkpoint artifact |
| Usage reporting | `usage:true` | estimate by wall-time; budgets use wall/tool-calls only |
| Skill discovery | `skills: native|inline|none` | inline skill text in prompt |
| Model selection | `models:[…]` | map abstract tier (fast/standard/deep) → adapter default |
Degradations are logged as `capability.degraded` events and shown in the run summary; the user can set `strict: true` to turn degradations into errors.

## Part E — Portability test matrix (planned; none executed)
| Test | Claude Code | Codex CLI | Generic CLI (stdin/out) | Fake adapter |
|---|---|---|---|---|
| Contract: capabilities() shape | ✔ planned | ✔ | ✔ | ✔ |
| Single task, structured result | planned | planned | prompt-JSON path | scripted |
| Parallel disjoint tasks | planned | planned | serialize | scripted |
| Permission denial surfaced | planned | planned | engine-side | scripted |
| Cancel/timeout | planned | planned | kill | scripted |
| Resume | planned | planned | n/a (restart) | scripted |
| Skill delivery | native | `.agents/skills` | inline | n/a |
| Malformed output repair | planned | planned | planned | scripted |
The **fake adapter** is the primary portability guarantee: the whole workflow suite runs against it in CI with no model calls (extension of the existing stub-harness pattern). Real harnesses get a thin nightly contract suite. **Explicit limits:** adapters for harnesses I have not inspected (e.g. Pi, Cursor, Gemini CLI) are design targets only; their capabilities (hooks, structured output, cancel) are Unknown until probed. Any harness lacking a non-interactive mode cannot be driven autonomously.
