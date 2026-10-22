# Evidence: Dependency Map

## Declared vs assumed
| Dependency | Where declared | Enforced by code? | Level |
|---|---|---|---|
| Tools: `gh`, `jq`, bash 3.2+, Python 3.9+, `node`, `git` | `README.md` note; `scripts/super-board-setup.py` L84-92; `tests/run-safety.sh` | setup `check` + install hints | V |
| Skill chain per label (bug→diagnosing-bugs+tdd; feature→implement+tdd+codebase-design; …) | `scripts/super-board-skills-ready.py` `REGISTRY` | **Yes** (exit 10 if missing) | V |
| Third-party skills `mattpocock-skills:*`, `ponytail:*`, `verification-before-completion`, `testing-strategy`, `vitest`, `playwright-best-practices` | same `REGISTRY` | existence check only (README: "certifies availability, not their content") | V |
| Fallbacks for `ponytail` (2) | `REGISTRY['fallbacks']` | yes | V |
| `Workflow` tool / dynamic workflows | `config-schema.json` comment ("requires dynamic workflows enabled in /config"); wave.js globals | no feature detect beyond "tool list has no Workflow tool" (prose) + `super-board-host.sh` env sniff | V/I |
| Config shape | `references/config-schema.json` | **No** — "REFERENCE DOC, not parsed at runtime" (L1-3); no loader references it | V |
| Directory layout `.claude/{skills,bin,hooks,workflows,worktrees,super-board}` | `install.sh`, `CLAUDE.md` | implicit; 59 files / 344 hits mention `.claude/` | V |
| Allow-list of `Bash(...)` rules | `run-workflow.md` "Mid-run permission prompts" | `tests/test_run_allowlist.py` (static check) | D/V |

## Component dependency edges (code-traced)
- `super-board-wave-plan.sh` → `super-board-verification-ready.py`, `super-board-github-read.py --check`, `super-board-card.sh items`, `super-board-deps.sh`.
- `super-board-merge-gate.sh` → `verification-ready.py`, `github-read.py` (head/merge-state/metadata/diff/--halt), `merge-policy.py`, `approval.py` (imports github-read via importlib), `cleanup-wt.py --post-merge`.
- `super-board-approval.py` → `super-board-github-read.py` (importlib, L19-21).
- `super-board-codex-lane.sh` → `verification-ready.py`, `github-read.py`, `skills-ready.py` (importlib), `codex exec`.
- `super-board-collect-state.py`, `skills/super-collect/scripts/*` → GitHub reads (Sentry/PostHog HTTP in `collect_*.py`).
- wave.js lane prompts → `.claude/bin/{super-board-card.sh,super-board-github-read.py,super-board-skills-ready.py,super-board-pr-body.sh,super-board-gh-guard.sh,super-board-preflight.sh}` and `references/{run.md,writing-standard.md,block-template.md}` (string references inside prompts — not import-time dependencies; breakage appears only at agent runtime) V.

## Circularity / duplication
- No import cycles found in the Python helpers inspected (V, limited to the files listed).
- **Duplicated logic**: shell tokenizer `segments()` in 3 hooks (2 byte-identical) V; run-tier ladders duplicated in `wave.js` `LADDERS` and `codex-lane.sh` `CODEX_LADDERS` V; lane lifecycle encoded in `run.md` (prose) + `wave.js` prompts + `codex-lane.sh` prompt + legacy `run.sh` V.
- **Global authorities**: GitHub Project board (card status), assignee (claim), `.claude/super-board/configs/<slug>.json` (config), `skills-ready.py REGISTRY` (skill chain), `writing-standard.md` (formats; `tests/test_writing_format.py` enforces).

## Hard-coded persona/branding
26 occurrences of the maintainer's first name in operational files (`block-template.md`, `run.md`, `run-workflow.md`, `writing-standard.md`, `super-build/SKILL.md`, `super-review/SKILL.md`, `ui-refine-loop/*`, 5 hooks) V (`grep -w`). e.g. Block template "Owner: Eric".
