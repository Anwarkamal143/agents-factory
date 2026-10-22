---
id: DEC-07
title: "Decide: state store (JSONL log + snapshot vs SQLite)"
type: decision
labels: [type:decision, wayfinder:grilling, mode:HITL, phase:0, mvp]
blocked_by: []
skills: [grill-with-docs, domain-modeling]
---
## Question
What persists run state, and how do we keep it crash-safe?

## Options
| Option | For | Against |
|---|---|---|
| **A. Append-only JSONL event log + derived snapshot + artifact files, single writer, behind a `Store` interface** | Human-readable, diffable, recoverable by replay, no server, portable | We own torn-write and corruption handling; multi-process concurrency is out of scope |
| B. SQLite (WAL) | Transactions and concurrency for free | Opaque binary file; migrations; less inspectable |

## Recommendation
**A** (rules in SPEC-01 "Event log and store"). Trigger to revisit: multiple concurrent engine processes, or logs beyond a few hundred MB. The `Store` interface isolates that change. This is an ADR candidate: hard to reverse (on-disk format), surprising without context, a real trade-off. Write it as `docs/adr/0001-event-log-store.md` when resolving.

## Default if unanswered
A. **Safe to proceed with default: yes.**

## Blocks
T-02, T-03.

## Resolution
_Pending._
