# Evidence: Entry Points

Evidence levels: **V** Verified (direct inspection) · **D** Documented · **I** Inferred · **U** Unknown.
All paths relative to `super-board-main/` inside the archive. "Static" = read, not executed.

## Archive identity
- `FACTORY_ARCHIVE` = `/mnt/user-data/uploads/super-board-main.zip` (5,637,407 bytes)
- SHA-256: `383994657f9b432c4b646e17e8ade19d7152a6bf3c4cf4b7391b97641909ebcd` (V)
- 401 zip entries → 326 files, 74 directories after extraction; 2 symlinks (`evals/_stubs/bin/git`, `python3` → `_real`, relative, in-tree) (V)
- Extracted to `/home/claude/work/src/` (isolated). Original ZIP untouched. No archive script, test, or eval was executed.

## User-facing entry points (all are SKILL.md verb routes; no `commands/` or `agents/` directory exists — V)
| Entry | Defined in | Routes to | Level |
|---|---|---|---|
| `/super-board onboard` | `skills/super-board/SKILL.md` routing table | `references/onboard.md` + `scripts/super-board-setup.py` | V |
| `/super-board lint` | same | `references/lint.md` | V |
| `/super-board status` | same | `references/status.md` + `scripts/super-board-status.py` | V |
| `/super-board run [--low\|--high] [--codex[=model]]` | same | `references/run-workflow.md` (default) · `run.md` (claude-p) · "Codex runs" | V |
| `/super-board stop` | same | `references/stop.md` + `scripts/super-board-stop.sh` | V |
| `/super-collect [source] [--since]` | `skills/super-collect/SKILL.md` | `skills/super-collect/scripts/collect_*.py`, `super-collect-file.sh` | V |
| `/ui-refine-loop <route>` | `skills/ui-refine-loop/SKILL.md` | `workflows/ui-refine-loop.js` | V |
| `/visual`, `/git-sync` | respective SKILL.md | `skills/visual/scripts/visual.py`; prose-only | V |
| Codex: `$super-board run` | README "Models" section | skills found via `.agents/skills/` (symlink) | D |
| Distribution: `curl … get.sh \| bash` | `get.sh` → `install.sh` | copies to target `.claude/{skills,bin,hooks,workflows}` | V |
| Plugin: `/plugin install super-board@super-board` | `.claude-plugin/{plugin,marketplace}.json` | ships `skills/` only | V |

## Programmatic entry points
| Script | Invoker | Notes |
|---|---|---|
| `workflows/super-board-wave.js` | Host `Workflow` tool with `scriptPath` + `args {configPath, cards, tier}` (`run-workflow.md` step 4) | Needs host globals `args, agent, pipeline, log` (wave.js L19-359) V |
| `scripts/super-board-codex-wave.sh` → `super-board-codex-lane.sh` | Orchestrator background task | `codex exec` per lane V |
| `scripts/super-board-run.sh` | `nohup` by orchestrator, only if `worker_backend:"claude-p"`; exits 78 otherwise (run.sh L85-97) | legacy V |
| `skills/super-build/scripts/super-build-dispatch.sh` | standalone/legacy super-build | uses `claude -p --dangerously-skip-permissions` (L143) V |
| `scripts/super-board-merge-gate.sh` | Reviewer lane | only executable `gh pr merge` in code is L349 (V); sole-path is a prompt convention — no hook intercepts a bare `gh pr merge`, and `run-workflow.md` L368 recommends allow-listing `Bash(gh pr merge:*)` (V) |
| Hooks | `hooks/settings-snippet.json` merged into `.claude/settings.json` by `scripts/super-board-settings.py` | PreToolUse/PostToolUse/SessionStart V |

## Context loaded first (per `run-workflow.md` Preconditions)
Config `.claude/super-board/configs/<slug>.json` (active pointer `.claude/super-board/active`) → `verification-ready.py` → `gh auth` → worktree scan → `node --check` of wave.js → wave lock → crash-recovery sweep → DB reach checks. Lane agents additionally read `.claude/skills/super-board/references/run.md`, `writing-standard.md`, the issue + all comments, `PROJECT.md`, `CLAUDE.md`/`AGENTS.md` (D: run.md Builder step 3; reviewer step 3).
