---
id: MAP-01
title: "Map: settle MVP decisions before building"
type: map
labels: [wayfinder:map, phase:0, mode:HITL]
blocked_by: [DEC-01, DEC-02, DEC-03, DEC-04, DEC-05, DEC-06, DEC-07, SPK-01, SPK-02, SPK-03]
skills: [wayfinder, grilling, domain-modeling, to-spec]
---
This is a **wayfinder map**: an index, not a store. Each decision lives in exactly one place (its ticket); this issue only holds one-line summaries and links. Work one decision ticket per fresh session. Resolve by posting a resolution comment, closing the ticket, and adding one line under "Decisions so far".

## Destination
Every question that would change the shape of the MVP is decided or explicitly deferred, with evidence where a fact (not an opinion) was blocking. When this map clears, run `/to-spec #<this issue>` to collapse it into the final spec (SPEC-01), then `/to-tickets` is **not** needed again: the build tickets already exist and only their `blocked_by` decisions change from open to closed.

## Tickets on this map
Decisions: DEC-01 language and toolchain, DEC-02 first harness, DEC-03 autonomy and approval channel, DEC-04 GitHub in MVP, DEC-05 names/license/distribution, DEC-06 verification isolation, DEC-07 state store.
Evidence: SPK-01 permission coverage in headless and sub-agent runs, SPK-02 structured output/cancel/resume, SPK-03 GitHub merge semantics.
(These are created before this map because the map is blocked by all of them, so GitHub cannot list them as native sub-issues; the ids above become links when issues are created. Build tickets are sub-issues of SPEC-01.)

## Decisions so far
_(none yet; add one line per closed ticket: `<ticket> -> decision (one clause), link`)_

## Not yet specified
Fog that cannot be phrased sharply yet. Likely candidates, to graduate into tickets once the first decisions land:
- Which test/lint commands the factory runs against **itself** in CI (follows DEC-01).
- Whether approvals need cryptographic signing rather than a TTY check (follows DEC-03 and SPK-01).
- Whether a merge queue is needed on the target GitHub repos (follows DEC-04 and SPK-03).

## Out of scope
Implementation. Wayfinder tickets decide or gather evidence; they never deliver product code. Any ticket that reads "build the X" belongs in the build set, not here.
