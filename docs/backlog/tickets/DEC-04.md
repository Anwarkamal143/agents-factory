---
id: DEC-04
title: "Decide: is GitHub integration part of the MVP?"
type: decision
labels: [type:decision, wayfinder:grilling, mode:HITL, phase:0]
blocked_by: []
skills: [grill-with-docs]
---
## Question
Does the MVP deliver via GitHub (issues in, PRs out, check status), or is it local-git only with GitHub as a later projection? (This is about the **product**. This repo's own development already uses GitHub issues and PRs.)

## Options
| Option | For | Against |
|---|---|---|
| **A. Local-git only in MVP** (engine merges a branch locally or leaves a reviewed branch); GitHub projection is T-23 | No rate-limit or race problems (the analyzed tool hit documented GraphQL quota incidents); simpler tests; keeps state local | Users wanting PRs wait for T-23 |
| B. GitHub in MVP | Familiar workflow | Adds network dependence, auth handling, merge-semantics unknowns (SPK-03) before the core loop is proven |

## Recommendation
**A.** Deliver to a local branch and print the diff and evidence. Add PR creation behind the tracker/integration interface in T-23.

## Default if unanswered
A. **Safe to proceed with default: yes.**

## Blocks
SPK-03, T-23. Question for you: do you need PR creation in the first release?

## Resolution
_Pending._
