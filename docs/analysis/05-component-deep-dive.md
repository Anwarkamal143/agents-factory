# 05 — Component Deep Dive

Levels: V/D/I/U as before. Everything is static review.

## 7.1 Agents and subagents
No agent files exist. "Agents" are runtime-constructed prompts. Treat each lane as an agent type:

| Agent | Defined at | Model | Tools / permissions | Input | Output | Failure behavior | Level |
|---|---|---|---|---|---|---|---|
| Orchestrator | `skills/super-board/SKILL.md` + `run-workflow.md` | session model | everything in the session; rule "never edit code" is prose | user verb, board | wave results, report | prose | V/D |
| Pre-flight | `wave.js` L214-285 | sonnet (haiku `--low`) | Bash (preflight script, gh, card.sh) | batch ≤5 Ready cards | `PREFLIGHT_SCHEMA` verdicts | missing ⇒ `skipped` | V |
| Classifier | `wave.js` L288-310 | haiku (sonnet `--high`); Codex: gpt-6-luna | reads card | card | `{kind, complexity}` | label wins | V |
| Builder | `skills/super-build/SKILL.md` + `run.md` | `LADDERS[tier][complexity]` | session defaults/allow-list | issue+comments | branch, draft PR, comment | `failed`/`blocked`/`human-gate` | V (prompt)/D |
| Tester | `skills/super-qa/SKILL.md` | inherited from Build model | + browser tooling scripts | branch/PR | test plan, evidence, bug filings | `bounced` | V/D |
| Reviewer | `skills/super-review/SKILL.md` | inherited | + merge gate | PR | report, merge or bounce | `halted` stops wave | V/D |
| Code-grounder / Historian (sub-agents) | `super-review` Adversarial mode | unspecified (U) | read-only intent | claim + diff | confidence | n/a | D |
| Verifier (collect) | `super-collect` L123 | U | read | candidate | verdict | drop candidate | D |
| Critic/Fixer (ui-refine) | `ui-refine-loop.js` | per script | per skill | route | ledger | `fixFails≥2` stop | V |

Context handling: each `agent()` call starts fresh; continuity is carried by PR comments and `priorFindings` (wave.js) rather than conversation history. Isolation: git worktree per lane, but *no OS/sandbox isolation found* in the Claude path; Codex path sets a filesystem permission profile with network enabled (V `codex-lane.sh`). Maximum agents: host-limited; planner width. Delegation depth: lanes may spawn review sub-agents (D).
Negative findings: no hand-off schema beyond `STAGE_SCHEMA`; no agent-level cost/time budget found; no per-agent tool allow-list definition found in the inspected files (permissions come from project `.claude/settings.json` allow rules recommended in `run-workflow.md`).

## 7.2 Skills
| Skill | Triggers | Size | References loaded | Side effects | Tests | Notes |
|---|---|---|---|---|---|---|
| super-board | verb routing table | 47 L + 17 refs (3,768 L) | one per verb | board, config, files | helper tests | doc-heavy; `run.md` 816 L |
| super-build | invoked by lane prompt; legacy standalone | 303 L | `run.md` Builder | git, PR | `test_skill_dispatch.py` | hosts legacy dispatcher |
| super-qa | lane + standalone crawler | 699 L | evidence refs, runtime scripts | files, issues | evals/test-gap | largest skill |
| super-review | lane | 451 L | `run.md` Reviewer | merge | evals/review-remembers | owns merge call path |
| super-collect | explicit | 197 L | 3 reference files | creates issues | 4 evals | external API reads |
| ui-refine-loop, visual, git-sync | explicit | 99/…/96 L | — | files/commits | tests | secondary |

Frontmatter uses only `name`, `description`, `argument-hint` (V). Loading is progressive (routing table). Automatic invocation: **not claimed here** — `description` fields are written for host-side triggering (D); whether the host triggers them is unverified (U). Reuse vs project-specific: Eric-specific strings and `.claude/` paths are embedded (V).

## 7.3 Commands and entry points
See `evidence/entry-points.md`. No `commands/` directory; commands are skill verbs. Arguments parsed by LLM; validation in scripts (`--config` required, exit 64 on usage). No help-text system beyond README/SKILL.md routing.

## 7.4 Hooks and lifecycle integrations
| Hook | Event / matcher | Purpose | Mechanism | Fail mode | Bypass / gaps (I = inferred) |
|---|---|---|---|---|---|
| `guard-worktree-path.py` | PreToolUse Bash | `git worktree add` only under `.claude/worktrees` | shell tokenization (`segments()`) | open on exception | unusual quoting/indirection (I) |
| `guard-delete-outside.py` | PreToolUse Bash | `rm`-class deletes inside repo only | tokenizer + path resolve | open; unknown `$(…)` vars allowed (V) | variable-built paths (V by comment) |
| `guard-secrets.py` | PreToolUse Bash/Read/Grep | block `.env`, keys, credentials | regexes over command/path text | open | `python -c`, `printenv`, split strings (I); no Glob matcher (V) |
| `guard-key-literals.py` | Pre+PostToolUse Edit/Write/Bash | block secret-literal writes | regex | open | encoding tricks (I) |
| `guard-protected-push.py` | PreToolUse Bash (opt-in via `settings-protect-main.json`) | block `git push` to protected branches | tokenizer | open; `SB_ALLOW_PROTECTED_PUSH=1` bypass (V) | does not cover `gh pr merge` (V) |
| `cleanup-wt.py` | SessionStart `--auto`; merge gate `--post-merge` | remove merged worktrees/branches | git inspection; dry-run default; recovery TSV | skip on error | n/a |
| `pre-commit-readme.sh`, `hooks/dev/*` | git/dev only | README sync, skill-eval gate | — | — | dev-repo only |
All hooks are Claude Code PreToolUse/PostToolUse/SessionStart contracts. **No Codex hook configuration found in the archive.** Whether hooks fire for `agent()` sub-agents in the Workflow runtime: U.

## 7.5 Scripts and tools
| Script | Contract (inputs → outputs; exits) | Side effects | Deterministic | Error handling | Tests |
|---|---|---|---|---|---|
| `wave-plan.sh` | config [+items/deps JSON] → plan JSON; 64/65/66/9/79 | none (read-only) | Yes | fail-safe on unreadable deps | `test-wave-plan.sh` |
| `github-read.py` | `--kind K -- gh…` → validated output; 64, 79 | halt file | Yes | 3 attempts, shape validation | `test_github_reads.py` |
| `card.sh` | `items`/`move` → GraphQL cached | board writes | mostly | cache + throttle | no dedicated suite seen (U) |
| `merge-gate.sh` | see 04 | merge, worktree, lock | Yes | exits 2-9, 79 | `test-merge-gate.sh` |
| `merge-policy.py` | plan JSON w/ categories | none | Yes | — | no dedicated suite found; exercised via `test-merge-gate.sh` (I) |
| `approval.py` | request/validate | none (reads comments) | Yes | hold on ambiguity | `test_approval.py` |
| `skills-ready.py` | cards → readiness; 10 | `--hydrate` (effect not traced, U) | Yes | — | `test_skills_readiness.py` |
| `verification-ready.py` | config → ok / exit 9 | none | Yes | non-blank only | `test_verification_readiness.py` |
| `preflight.sh`, `deps.sh`, `pr-body.sh`, `gh-guard.sh` | helpers | PR body edits | Yes | — | tests |
| `stop.sh`, `throttle.sh`, `usage.sh`, `host.sh` | run control | comments, signals, config edit | Yes | — | tests |
| `codex-wave.sh`, `codex-lane.sh` | Codex execution | `codex exec`, comments | Partly | writes `--output-last-message` | `test-codex-lane.sh`, `test-codex-stop.sh` |
| `setup.py`, `settings.py`, `agents-md.py` | onboarding mechanics | files in target repo | Yes | resumable | `test-setup.sh`, `test-settings.sh` |
| `status.py`, `readme-sync.py`, `calibration.py`, `project-verifier.py`, `collect-state.py`, `env-check.sh` | reporting/maintenance | files | Yes | — | tests |
Hidden coupling: scripts expect `.claude/bin` path, `gh` auth scopes (project), `jq` (absent in my sandbox, so I could not run them even with authorization).

## 7.6 Configuration and context files
`CLAUDE.md` (agent-facing rules for editing the pack), `AGENTS.md` managed block (`references/agents-md-block.md`, refreshed by `agents-md.py`), `PROJECT.md` (project facts read by Builder), board config JSON (keys such as `repo`, `project`, `base`, `verify_commands`, `bot_identity`, `merge_policy`, `migrations`, `worker_backend`, `max_workers`, `rebuild_cap`, `block_rate_alert_pct`, `truth_threshold`, tiering), `.claude/settings.json` allow rules (recommended, merged by `settings.py`). Precedence: no formal precedence model found; `active` pointer selects one config per project. Validation: ad hoc per script (see 03/08). Secrets: no secret store; `gh` auth ambient; Sentry/PostHog tokens read from env (D).

## 7.7 State and artifact management
| State | Location | Writer | Reader | Source of truth? | Atomicity / locking | Cleanup |
|---|---|---|---|---|---|---|
| Card status, claim | GitHub Project + assignee | card.sh/lanes | planner | **Yes** | none (GraphQL mutations) | n/a |
| Wave lock | `.claude/super-board/wave.lock` (name per docs) | orchestrator `set -C` | orchestrator | lock | atomic create | `stop.sh`, replace-stale prose |
| Merge lock | `.claude/super-board/inflight/merge.lock` | merge-gate | merge-gate | lock | mkdir atomic; reap TOCTOU | trap, stale reap |
| GitHub halt | `.claude/super-board/github-halt.json` (git-common-dir shared) | github-read | planner/gate | flag | file write | `--resume` |
| Config | `.claude/super-board/configs/<slug>.json` + `active` | setup | all | **Yes** | none | n/a |
| Run manifest | `docs/super-board/runs/<date>-<slug>.md` | orchestrator | humans | report | none | committed |
| QA evidence | `docs/super-board/runs/issue-N-qa-vN/` | Tester | Reviewer | evidence | none | committed |
| Worktrees/branches | `.claude/worktrees/issue-N-*` | lanes | lanes | working state | git | `cleanup-wt.py` |
| Reports/approvals | PR/issue comments with markers | lanes | lanes/gate | record | none | n/a |
| Collect receipts | `.claude/super-board/collect/` | collect scripts | collect | dedupe | none | — |
Negative findings: no transactional state store; no schema versioning for config or run state found; no structured audit/event log found in the state-path inventory. Concurrent orchestrator runs rely on wave lock (prose + `set -C`).
