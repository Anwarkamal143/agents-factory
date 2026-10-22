---
id: DEC-01
title: "Decide: implementation language and toolchain"
type: decision
labels: [type:decision, wayfinder:grilling, mode:HITL, phase:0, mvp]
blocked_by: []
skills: [grill-with-docs, domain-modeling]
---
## Question
Which language and toolchain do we build the engine in, and what are the CI gates for the factory's own repo?

## Options
| Option | For | Against |
|---|---|---|
| **A. Python >=3.11, stdlib-first** | `subprocess`, `fsync`, atomic rename, `sqlite3`, `json` in stdlib; easy fixture tests; widely installed; the archive's helper scripts were Python/bash | Packaging for non-Python users needs `pipx`/`uv`; weaker static typing than TS/Go unless pyright is strict |
| B. TypeScript (Node >=22) | Same language as many agent harnesses; strong typing | Node process/fsync semantics less direct; larger dependency surface; more build tooling |
| C. Go | Single static binary, great process control | Slower iteration on prompt/schema-heavy code; fewer agent-ecosystem libraries |

Toolchain sub-decisions (if A): package/venv manager (`uv` vs `pip`+`venv`), test runner (`pytest`), lint/format (`ruff`), typing (`pyright` strict vs `mypy`), JSON Schema validator (`jsonschema` dependency vs vendored minimal validator), and **config/workflow file format**: the standard library has **no YAML parser** (`tomllib` for TOML is stdlib in 3.11). Options: YAML via `PyYAML` `safe_load` only (second runtime dependency), or TOML (zero extra dependencies, but nested workflow definitions read worse), or JSON (no comments). CI gates: lint, type-check, unit+contract+workflow tests on Linux and macOS.

## Recommendation
**A**, with `uv`, `pytest`, `ruff`, `pyright` (strict on `core` and `contracts`), and exactly **two** runtime dependencies: `jsonschema` and `PyYAML` (`safe_load` only; never `load`). This corrects the earlier analysis, which said "single dependency" while also specifying YAML. Rationale: the contracts are JSON Schema, so the language is reversible; Python's stdlib covers every durability primitive the store needs.

## Default if unanswered
Option A with the toolchain above and YAML via PyYAML. **Safe to proceed with default: yes** (reversible because contracts are language-neutral; cost of reversal = rewriting `core`, not the design).

## Blocks
T-01 (repo bootstrap), and transitively everything. Questions for you: (1) Do you or your team already prefer a language? (2) Will target repos be mostly JS/TS, Python, or mixed (affects the demo fixtures, not the engine)? (3) Is a single static binary a requirement? (4) Is a second runtime dependency (PyYAML) acceptable, or do you prefer TOML/JSON with zero extra dependencies?

## Resolution
_Pending. Post: chosen option, toolchain list, minimum versions. Update SPEC-01 "Language and storage" in the same PR._
