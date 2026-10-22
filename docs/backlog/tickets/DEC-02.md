---
id: DEC-02
title: "Decide: first real harness adapter"
type: decision
labels: [type:decision, wayfinder:grilling, mode:HITL, phase:0, mvp]
blocked_by: []
skills: [grill-with-docs]
---
## Question
Which agent harness do we integrate first (after the fake adapter)? The adapter contract must not depend on this answer, but T-13 does.

## Options
| Option | Known from the analysis | Unknown until SPK-01/02 |
|---|---|---|
| **A. Claude Code** (`claude -p`) | Has a PreToolUse/PostToolUse hook model and allow-list rules; headless mode exists | Whether hooks and allow-lists apply to headless runs and sub-agents; native schema-constrained output |
| B. Codex CLI (`codex exec`) | Supports `--output-schema` and `--output-last-message` and a filesystem permission profile in the code we reviewed (a previous tool used it with approvals disabled and network on) | Current flags and versions; resume semantics; cancel behaviour |
| C. Generic CLI (stdin/stdout, prompt-requested JSON) | Lowest common denominator; always possible | No sandbox or structured-output guarantees; engine must validate and repair everything |

## Recommendation
Pick the harness you **already have access to and use daily**, because T-13 needs real runs. If both are available, choose by SPK-01/02 results (permission coverage and structured-output reliability). Absent other input, **A. Claude Code**.

## Default if unanswered
A. Claude Code. **Safe to proceed with default: yes for everything except T-13 and the two spikes**; those start only after this is resolved, so it is not a silent default.

## Blocks
SPK-01, SPK-02, T-13. Questions for you: (1) Which harness(es) do you have working credentials for? (2) Must the MVP work offline-from-vendor for CI (the fake adapter covers CI)? (3) Is a second real adapter needed soon (T-24 is post-MVP)?

## Resolution
_Pending._
