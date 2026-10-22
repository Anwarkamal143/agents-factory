---
id: DEC-05
title: "Decide: names, license and distribution"
type: decision
labels: [type:decision, wayfinder:grilling, mode:HITL, phase:0, mvp, risk:one-way-door]
blocked_by: []
skills: [grill-with-docs, domain-modeling]
---
## Question
What are the product name, CLI command, package/import names, license, and distribution channel?

## Options
- **Names:** repo is `agents-factory`. CLI command candidates: `factory` (short; may collide with existing tools on PATH), `agents-factory`, `afactory`. Python import package: `agents_factory`.
- **License:** MIT (simple, permissive), Apache-2.0 (explicit patent grant), proprietary/none (blocks outside contribution).
- **Distribution:** (1) install from git with `pipx`/`uv tool`, (2) GitHub Releases with checksums and signed tags, (3) PyPI later.

## Recommendation
CLI `factory` unless a PATH collision is found (T-01 checks); package `agents_factory`; **MIT** unless you want a patent grant; distribute via git tag + GitHub Release with a `SHA256SUMS` file first, PyPI after the API stabilises. Public names and licenses are hard to walk back, so confirm explicitly.

## Default if unanswered
**No default.** **Safe to proceed: no** for the license; T-01 may use a placeholder name internally but must not publish a license until this is resolved.

## Blocks
T-01. Questions for you: (1) Final CLI name? (2) License choice? (3) Public from day one or private until MVP?

## Resolution
_Pending._
