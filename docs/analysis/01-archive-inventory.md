# 01 — Archive Inventory and Repository Map

Evidence levels used throughout: **V** verified (inspected) · **D** documented · **I** inferred · **U** unknown. "Static" = read only; nothing from the archive was executed (see `evidence/verification-status.md`).

## 1. Archive facts (V)
| Item | Value |
|---|---|
| `FACTORY_ARCHIVE` | `/mnt/user-data/uploads/super-board-main.zip` |
| Size / SHA-256 | 5,637,407 bytes / `3839946…1909ebcd` (full hash in `evidence/archive.sha256`) |
| Entries | 401 (326 files, 74 dirs) ; uncompressed ≈ 9.9 MB; 2 in-tree relative symlinks (`evals/_stubs/bin/git`, `python3` → `_real`) |
| Path safety | No absolute or `../` member paths |
| Product / version | `super-board` v3.1.2 (`VERSION`, `.claude-plugin/plugin.json`), MIT, author "Eric Tech"; 27 releases v1.2.0 (2026-05-24) → v3.1.2 (2026-10-11) (`RELEASE-NOTES.md`) |
| `ANALYSIS_OUTPUT` | `/home/claude/analysis/` (copied to `/mnt/user-data/outputs/analysis/`) |

**File types (V):** 98 Markdown · 68 shell · 68 Python · 32 JSON · 13 HTML · 12 PNG · 7 SVG · 7 YAML + 3 yml · 6 JS + 3 mjs · 2 CSS · 1 b64 blob.
**Package manifests / lockfiles:** none for the product (no `package.json`, `requirements.txt`, lockfile). Runtime deps are *system tools* (bash 3.2+, Python 3.9+ stdlib, `gh`, `jq`, `git`, `node`) plus **third-party skills not bundled** (see §4). Only plugin manifests exist: `.claude-plugin/plugin.json`, `marketplace.json`.
**Config formats:** JSON (`.claude/settings.json`, hook snippets, board config), YAML (eval `case.yaml`, GH workflows), JSON5-with-comments reference doc (`skills/super-board/references/config-schema.json`), Markdown (skills, references, templates), TOML only *read* by `skills-ready.py` for Codex skill activation.
**Secrets / suspicious content (V):** no secret-shaped strings matched (patterns in `evidence/verification-status.md`); no dotenv/pem/key files. Notable risky constructs: `eval "$cmd"` for config-supplied commands (`scripts/super-board-merge-gate.sh` L283, L307); `claude -p --dangerously-skip-permissions` in legacy `skills/super-build/scripts/super-build-dispatch.sh` L143; `curl … | bash` installer (`get.sh`, no checksum). Opaque: `diagrams/pstack/overview.b64` (U, not decoded).

## 2. Repository map
Sizes are file counts (du). "Runtime" = executed/used by a running factory; "Dev" = only for developing the pack; "Dist" = packaging.

```
super-board-main/
├── .claude/settings.json              (dev) 2 hooks used when authoring THIS repo: README sync (PostToolUse), skill-eval gate (Stop)
├── .claude-plugin/                    (dist) plugin.json, marketplace.json — plugin ships skills/ only
├── .github/{workflows,scripts}        (dist/dev) cross-platform CI, pages, tag-triggered release + publish-release.sh
├── CLAUDE.md                          (runtime) agent-facing architecture rules for the pack itself
├── README.md, RELEASE-NOTES.md, RELEASING.md, LICENSE, VERSION
├── get.sh, install.sh                 (dist) remote bootstrap + copy installer into target .claude/
├── skills/                (73 files)  (runtime) 8 skills + families.json
│   ├── super-board/       21          orchestrator: SKILL.md + 17 references + VERSION + README
│   ├── super-build/        5          Builder lane (+ legacy dispatcher script)
│   ├── super-qa/          11          Tester lane (+ runtime browser scripts, project-verifier templates)
│   ├── super-review/       2          Reviewer lane (SKILL.md 451 lines)
│   ├── super-collect/     10          problem finder (Sentry/PostHog/PRs/architecture) + fetch scripts
│   ├── ui-refine-loop/    14          bounded critique→fix loop (+ briefs, rubric, scripts)
│   ├── visual/             7          HTML recap/plan/map generator (visual.py + template)
│   └── git-sync/           2          commit/pull/push helper
├── scripts/               (30 files)  (runtime) installed as target `.claude/bin/`: deterministic helpers
├── workflows/              (2 files)  (runtime) super-board-wave.js (359 L), ui-refine-loop.js (343 L)
├── hooks/                 (11 files)  (runtime) 5 guard-*.py, cleanup-wt.py, settings snippets, pre-commit-readme.sh; hooks/dev/ = dev-only
├── tests/                 (82 files)  (dev) 59 offline suites + fixtures
├── evals/                 (52 files)  (dev) 7 paid LLM eval cases + stubs for gh/git/python3
├── diagrams/              (55 files, 7.2 MB) (dev/docs) static website + map generator (build_skillmap.py, maps.json)
└── docs/                  (5 files)   README stub, blocked-column audit HTML, assets
```

| Directory | Responsibility | Depends on / depended on by | Status |
|---|---|---|---|
| `skills/super-board/references/` | The *specification* of the factory in prose: `run.md` (816 L lane lifecycles), `run-workflow.md` (415 L wave loop), `onboard.md` (504), `status.md` (441), `writing-standard.md` (394), block/ticket/PR templates, `config-schema.json` | Read by lane agents at runtime via path strings in prompts; consumed by tests (`test_writing_format.py`, `test_run_allowlist.py`) | Active |
| `scripts/` | Deterministic mechanics: planning, GitHub reads/moves, merge gate, approval, policy, setup, status, stop, throttle, codex launch | Called by prompts as `.claude/bin/<name>`; call each other (see `evidence/dependency-map.md`) | Active (legacy: `super-board-run.sh`) |
| `workflows/` | Programmatic orchestration for the host Workflow runtime | Launched by orchestrator; call lane skills through prompts | Active (wave), Active (ui-refine) |
| `hooks/` | PreToolUse guards, post-merge/session cleanup | Wired by `settings-snippet.json`; `cleanup-wt` also called by merge gate | Active; `hooks/dev/` dev-only |
| `skills/super-collect/` | Intake: external signals → Backlog cards | Writes to GitHub via `super-collect-file.sh`; state via `scripts/super-board-collect-state.py` | Active |
| `skills/visual`, `git-sync`, `ui-refine-loop` | Secondary standalone helpers | Optional; `visual` renders pack maps | Active (secondary) |
| `tests/` | Safety net: offline deterministic suites | Run by `tests/run-safety.sh`, CI | Dev |
| `evals/` | Paid prompt-behavior evals (`case.yaml`, graders, `seed.sh`) | Run via `claude plugin eval` (D) | Dev; result files absent |
| `diagrams/`, `docs/` | Public site/visual maps; pages deploy | `pages.yml` copies selected pages | Docs; not runtime |

## 3. Component inventory

Fields requested by the prompt are folded as: **I→O** (inputs → outputs), **Inv/Stage/Exec** (invocation, lifecycle stage, execution model), **State**, **Verif** (how it is tested). Unknown fields marked U.

### 3.1 Skills (8) — Markdown prompts with 2–3 frontmatter keys (`name`, `description`, rarely `argument-hint`) (V)
| Component | Path | Responsibility | I→O | Inv/Stage/Exec | State | Verif | Status / evidence |
|---|---|---|---|---|---|---|---|
| super-board | `skills/super-board/SKILL.md` (47 L) + `references/*` | Orchestrator verbs onboard/lint/status/run/stop; routing table | user verb + config → dispatch, reports | `/super-board <verb>` · interactive · sequential wave loop | writes `.claude/super-board/*`, `docs/super-board/runs/*`, board | tests for helpers; LLM parts: none/evals | Active; V |
| super-build | `skills/super-build/SKILL.md` (303 L) | Builder lane: worktree, smallest safe change, TDD, draft PR | issue+comments+PROJECT.md → branch, PR, comments, card→QA | via workflow `agent()` or `codex exec`; per card; parallel across cards | worktree `.claude/worktrees/issue-N-build`, branch, PR | `tests/test_skill_dispatch.py`; no lane eval seen | Active; also legacy standalone mode (`super-build-dispatch.sh`) |
| super-qa | `skills/super-qa/SKILL.md` (699 L) | Tester lane + standalone BFS route crawler | branch+PR → tests, evidence, screenshots, bug issues | as above; standalone `/super-qa <url>` | `docs/super-board/runs/issue-N-qa-vN/` | `evals/test-gap`; runtime-compare tests | Active |
| super-review | `skills/super-review/SKILL.md` (451 L) | Reviewer lane + merge via gate; adversarial truth-check | PR+diff → report comment, bounce/block/merge | as above | PR report comment (marker `<!-- super-review:report -->`) | `evals/review-remembers`, `ponytail-overengineering`; `tests/test-wave-review-memory.sh` | Active |
| super-collect | `skills/super-collect/SKILL.md` (197 L) | Finds problems; files verified Backlog tickets | Sentry/PostHog/PR/arch data → issues | `/super-collect`; schedulable (D) | `.claude/super-board/collect/` receipts | 3 test suites + 4 evals | Active |
| ui-refine-loop | `skills/ui-refine-loop/SKILL.md` (99 L) + `workflows/ui-refine-loop.js` | Bounded UI polish loop | route + taste file → fixes, screenshots | `/ui-refine-loop`; JS workflow | ledger file | `tests/test-ui-refine-loop-*.sh` | Active, secondary |
| visual | `skills/visual/SKILL.md` | HTML recap/plan/map | repo/branch → `.html` | `/visual` | output file | `tests/test_visual_*.py` (7) | Active, secondary |
| git-sync | `skills/git-sync/SKILL.md` (96 L) | Commit-per-change, pull, push | working tree → commits | `/git-sync` | git | none seen (U) | Active, secondary |

### 3.2 Agents / lane roles
**No agent definition files exist** (no `agents/` dir, no `.claude/agents`) (V). Roles are created at runtime by `agent(prompt, {label, phase, schema, model})` inside `workflows/super-board-wave.js`: `preflight:<ids>`, `classify:#N`, `build|qa|review:#N`; or by `codex exec` in `codex-lane.sh`; or `claude -p` in the legacy runner. Review sub-agents (Code-grounder, Historian) are specified in `skills/super-review/SKILL.md` "Adversarial mode" (L403+) and spawned by the Reviewer lane (D).

### 3.3 Workflows (2)
| Component | Path | Responsibility | Inv/Exec | State | Verif |
|---|---|---|---|---|---|
| super-board-wave | `workflows/super-board-wave.js` | One wave: pre-flight → classify → per-card build→qa→review pipeline; halt propagation; summary | Workflow tool; parallel across cards (host caps concurrency, D) | in-memory `halted`; results returned | `tests/test-workflow-halt.sh`, `test-wave-preflight.sh`, `test-wave-review-memory.sh` (stub harness) |
| ui-refine-loop | `workflows/ui-refine-loop.js` | ≤N rounds check→fix→verify, parallel checkers, revert on red | Workflow tool | rounds array | `tests/test-ui-refine-loop-workflow.sh` |

### 3.4 Scripts (`scripts/`, installed to `.claude/bin/`) — 30 files, 8,170 lines
| Group | Components (path prefix `scripts/super-board-`) | Notes (V from headers; behavior static) |
|---|---|---|
| Planning & board IO | `wave-plan.sh`, `deps.sh`, `card.sh`, `preflight.sh`, `status.py`, `pr-body.sh` | planner pure/read-only; card moves cached (1 GraphQL pt); PR body edited per marker block |
| Safety & gates | `github-read.py`, `gh-guard.sh`, `verification-ready.py`, `skills-ready.py`, `merge-gate.sh`, `merge-policy.py`, `approval.py` | exit-code contracts: 9 verification, 10 skills, 79 GitHub halt, 2–8 merge gate |
| Run control | `stop.sh`, `throttle.sh`, `usage.sh`, `host.sh`, `run.sh` (legacy) | usage reads Claude status-line `rate_limits` |
| Codex | `codex-wave.sh`, `codex-lane.sh` | `codex exec --output-schema`, fs profile, `approval_policy=never` |
| Setup & docs | `setup.py`, `settings.py`, `agents-md.py`, `readme-sync.py`, `env-check.sh`, `calibration.py`, `project-verifier.py`, `collect-state.py` | setup is the "deterministic half" of onboard |
| Filers | `super-qa-file-bug.sh`, `super-review-file-refactor.sh` | create issues with fixed templates; `--check-body` dry validation |

### 3.5 Hooks (V)
`guard-worktree-path.py` (PreToolUse Bash), `guard-delete-outside.py` (Bash), `guard-secrets.py` (Bash|Read|Grep), `guard-key-literals.py` (Edit|Write|…|Bash; also PostToolUse), `guard-protected-push.py` (opt-in), `cleanup-wt.py` (SessionStart `--auto`, merge-gate `--post-merge`), `pre-commit-readme.sh` (git hook for this repo), `hooks/dev/gate-skill-evals.py` (dev Stop hook). Wiring: `hooks/settings-snippet.json`, `settings-protect-main.json`. README says "6 guard hooks"; 5 `guard-*.py` files exist (documentation count mismatch, cause U).

### 3.6 Tests and evals
59 offline suites (`tests/test-*.sh` 34, `tests/test_*.py` 25) executed by `tests/run-safety.sh` (runs all, aggregates failures); 7 paid evals. Neither executed here.

## 4. External dependencies resolved at runtime (V, `skills-ready.py` REGISTRY)
`mattpocock-skills:{diagnosing-bugs,tdd,implement,codebase-design,code-review,resolving-merge-conflicts,domain-modeling,ask-matt,to-spec,to-tickets,improve-codebase-architecture}`, `ponytail:{ponytail,ponytail-review}` (two declared fallbacks), `verification-before-completion`, `testing-strategy`, `vitest`, `playwright-best-practices`, optional `calibrate`. Per-label chain: bug → diagnosing-bugs+tdd; feature → implement+tdd+codebase-design; ux → implement+tdd; refactor/tech-debt → codebase-design+tdd; tests → tdd; docs → none; default → tdd.

## 5. Active / unused assessment
- **Legacy but present:** `scripts/super-board-run.sh` (claude -p dispatcher; refuses unless `worker_backend:"claude-p"`), `super-build-dispatch.sh`. Not unused: documented fallback and still tested (`tests/test-run-gates.sh`).
- **Dev-only:** `hooks/dev/`, `.claude/settings.json`, `evals/`, `diagrams/`.
- **Config drift candidates:** `variant` removed in v3.0.0 but still refused/handled in 3 places (wave.js, wave-plan.sh, config-schema comment) — intentional upgrade guard (V).
- No component was declared unused by text-search alone; dynamic discovery (SKILL.md discovery by the host, `.claude/bin` path strings in prompts) was considered.

## 6. Unknowns
Contents/behavior of the 7 `diagrams/` map generators beyond headers; `visual.py` internals; `collect_*.py` request shapes; exact `status.py` rendering; whether the host `Workflow` runtime inherits hooks for sub-agents (U).
