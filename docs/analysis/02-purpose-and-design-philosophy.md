# 02 — Purpose and Design Philosophy

Levels: **V** verified · **D** documented · **I** inferred · **U** unknown. Rationale is labeled *documented* (author states it) or *interpretation* (mine).

## 1. Product purpose
| Question | Answer | Level |
|---|---|---|
| What is it? | A Claude Code plugin + installer that drains a GitHub Project board autonomously: Build → QA → Review → merge, with proof attached to each PR | D (README tagline "Add tasks, walk away, get merged PRs with proof") |
| Users | Solo developers / small teams using GitHub Projects who want unattended overnight runs; the maintainer is the implied primary user (26 hard-coded "Eric" references, "Owner: Eric" in Block template) | V/I |
| Problem | Turn a backlog of well-specified tickets into merged, tested PRs without a human relaying work between agents; keep humans only at policy gates (money/auth/schema/size, live-DB migrations) | D |
| Inputs / outputs | In: issues with `## Acceptance Criteria`, board columns, labels `qa/bug/feature`, optional `Skills:` line. Out: draft→merged PRs, structured PR/issue comments, evidence under `docs/super-board/runs/`, run manifest | V/D |
| Automation level | High: orchestrator never does product work; lanes are autonomous; humans (a) move Backlog→Ready, (b) approve policy-gated merges via pinned `done` comment, (c) resolve Blocked cards | D |
| Target | Reusable across projects: installs into each target repo's `.claude/`; per-project config + `verify_commands` | V |
| Explicit vs inferred goals | Explicit: unattended drain, evidence, safe merge, GitHub-quota thrift, Codex fallback. Inferred: portability beyond Claude/Codex is *not* a goal (heavy `.claude/` coupling) | D/I |

## 2. Architectural principles
For each: what it means · where implemented · enforced? · trade-off · our decision.

| # | Principle | Implementation (evidence) | Enforced by | Trade-off | Decision |
|---|---|---|---|---|---|
| P1 | **Orchestrator ≠ worker** ("cardinal rule") | `CLAUDE.md`, `SKILL.md` §cardinal rule, `run-workflow.md` | Prose only; nothing prevents the orchestrator session from editing code (no tool restriction found) | Keeps orchestrator context small; relies on LLM obedience | **Keep concept; enforce via separate process/permissions** |
| P2 | **State on the board, not in memory** | GitHub Project columns + assignee claims + PR comments; `wave-plan.sh` re-derives each wave; resume = run again | Code (planner) + prose | Free resumability & human visibility; GitHub rate limits become the bottleneck (documented 2,850 pts/3-card wave) | **Keep idea (external visible state) but add local durable event log** |
| P3 | **Deterministic mechanics, LLM judgement** | 30 scripts with exit-code contracts; LLM only for semantic calls | Code | Strong; but lane lifecycles still 800+ lines of prose | **Keep; push more of lifecycle into code** |
| P4 | **Specialist lanes (Build/QA/Review)** with independent review | skills `super-build/qa/review`; Reviewer forms hypotheses before reading builder summary; reruns tests | Prose + merge-gate verify | Adversarial separation improves quality (D); 3 sequential LLM sessions per card = cost | **Keep, make count/roles configurable** |
| P5 | **Small bounded tasks** | PR size cap 400 lines (`merge_policy.auto_max_lines`), pre-flight "too big" hold | Gate exit 7 for size (code) ; split advice prose | Reduces review risk; forces ticket slicing | **Keep; enforce at plan time** |
| P6 | **Verify before merge on current base** | `merge-gate.sh` | **Code** | One serialized verification per merge | **Keep (best component)** |
| P7 | **Human gates by policy, not by agent promise** | `merge-policy.py` categories (money/auth/schema/size/default), `approval.py` | **Code** at merge only | Gate sits at merge only; earlier destructive actions rely on hooks | **Keep; generalize to every side-effect class** |
| P8 | **Fail-safe halting on missing evidence** | exit 9 (verification), 10 (skills), 79 (GitHub); unreadable `Blocked by` ⇒ not free; no verdict ⇒ skipped | Code | Safer than guessing; halts need manual `--resume` | **Keep** |
| P9 | **Progressive context loading** | SKILL.md routing table loads one reference file per verb | Convention | Cheap tokens; hidden dependency on path strings | **Keep; add manifests** |
| P10 | **Model tiering by complexity** | `LADDERS` in wave.js; haiku/gpt-6-luna router | Code | Saves cost; model names hard-coded | **Keep as policy config, not code constants** |
| P11 | **Writing standard / formats as contract** | `writing-standard.md`, `tests/test_writing_format.py` | Tests | Machine-parseable comments (`<!-- marker -->` blocks) enable idempotent edits | **Keep** |
| P12 | **Skills as reuse mechanism** | `skills-ready.py` REGISTRY, third-party skills | Code check of file existence only | External content unpinned/unverified | **Redesign with manifests + pins** |
| P13 | **Spec-driven development** | Tickets with AC; `lint` flags vague ACs; no spec-generation stage in the loop (`to-spec`, `to-tickets` live in external skills) | Partly | Intake is outside the factory | **Add first-class spec stage** |
| P14 | **Harness independence** | Codex path only | — | Partial; see 07 | **Replace with adapter contract** |

Principles *absent*: persistent plan artifact beyond cards; cancellation inside a wave (stop is process/host level); structured audit log; cost accounting.

## 3. Architecture decision register
| ID | Decision | Evidence | Likely rationale (interpretation unless D) | Benefits | Costs | Alternatives | Recommendation |
|---|---|---|---|---|---|---|---|
| AD1 | GitHub Projects as the state store | README; `card.sh`; run.md "board is state" (D) | Zero infra, human-visible, resumable | Free UI, audit via comments | Rate limits (D: 20× reduction needed in v3.1.0), no transactions, vendor lock to GitHub | Local DB/files + GitHub as projection | Local authoritative state; GitHub as optional integration |
| AD2 | Skills (Markdown) as the implementation language for lanes | SKILL.md 300–700 lines | Fast iteration, host-native | Easy edit | Untestable without paid evals; drift vs code | Typed workflow code calling small prompts | Typed core + Markdown prompts |
| AD3 | Dynamic workflow JS as orchestrator | `super-board-wave.js` | Parallelism + schemas + halt flag | Structured results, resumeFromRunId (D) | Host-specific globals | Own engine with adapter | Own engine |
| AD4 | Separate Codex implementation in shell/Python | `codex-wave.sh/lane.sh` | Usage-limit fallback (D) | Works without Workflow tool | Triple logic (wave.js, codex, legacy) | One engine, two adapters | Single engine |
| AD5 | Assignee as mutex | run.md/run-workflow.md | Visible lock | Cheap | Not atomic (docs admit); contradictory docs | Local lock + lease file | Local lease with owner/heartbeat |
| AD6 | Merge via script gate | `merge-gate.sh` | Incident 2026-08-20 (D) | Strong semantics | Convention only when `gh pr merge` allow-listed | Server-side required checks + merge queue | Gate + branch protection/merge queue |
| AD7 | Hooks for guardrails | `hooks/` | Claude Code-native | Cheap | Fail-open regex heuristics, Claude-only | OS/container sandbox + tool allow-lists | Sandbox first, hooks as defense in depth |
| AD8 | Prose halt gates | run-workflow.md step 7 | Quick to write | Flexible | Unenforced | Engine counters | Engine-enforced budgets |
| AD9 | Hard-coded skill registry | `skills-ready.py` | Early-fail on missing skills | Pre-execution check (good) | Code edit to change chain | Manifest-declared | Manifests |
| AD10 | Copy-install into `.claude/` | `install.sh` | Simple | Works offline | `rm -rf` + copy overwrites local edits, no manifest | Versioned package + lockfile | Managed-file manifest with hashes |
| AD11 | Offline test suite + paid evals | `tests/`, `evals/` | Prompts need evals (documented in `gate-skill-evals.py`) | Good discipline | Evals unrun in archive | — | Adopt same two tiers |
| AD12 | Incident-driven hardening | RELEASE-NOTES, comments citing dates | Real failures | Hard-won rules (rebase pass, head pin) | Complexity accretion (run.md 816 L) | — | Port lessons as tests |

## 4. Strengths / weaknesses of the philosophy
Strong: external durable state, fail-safe halting, incident learning, deterministic merge safety, thrift on rate limits. Weak: the rules that matter most for autonomy (loop bounds, retry caps, orchestrator restraint) are prose; guardrails are vendor-specific and fail open; spec/plan are not first-class artifacts.
