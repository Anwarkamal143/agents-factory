---
id: DEC-03
title: "Decide: default autonomy level and approval channel"
type: decision
labels: [type:decision, wayfinder:grilling, mode:HITL, phase:0, mvp, risk:security]
blocked_by: []
skills: [grill-with-docs, domain-modeling]
---
## Question
What autonomy level is the default (L0 plan only, L1 per-task approval, L2 approve spec/plan/delivery, L3 auto-deliver low-risk, L4 full), and through which channel can a human grant an approval?

## Options
Autonomy default: **L1** (safest, slow), **L2** (recommended), **L3** (only after hardening).
Approval channel:
| Channel | Strength | Weakness |
|---|---|---|
| **a. Interactive CLI with controlling TTY** | Simple; engine records OS user and TTY | An agent with shell access could invoke the same command unless the permission profile forbids it |
| b. Pre-signed approvals file (human signs with a local key) | Works in CI/non-interactive | Key management; more code |
| c. GitHub PR review / comment | Familiar UI | Agent-writable if the agent has the same GitHub identity (the exact weakness seen in the analyzed tool) |

## Recommendation
Default **L2**. MVP channel **a**, with: the `factory approve` command refuses without a controlling TTY; permission profiles never allow the `factory` binary; approvals pinned to subject and scope hashes with expiry. Document the residual risk. Revisit **b** after SPK-01 shows whether a stronger separation is possible.

## Default if unanswered
L2 + channel a. **Safe to proceed with default: yes**, because the policy engine takes autonomy as configuration, not code.

## Blocks
T-08, T-09, and indirectly T-10, T-14. Questions for you: (1) Will you run unattended (CI/cron) soon? That forces channel b. (2) Who are the approvers (just you, or a team)? (3) Is any action class always forbidden for agents (e.g. dependency installs, network)?

## Resolution
_Pending._
