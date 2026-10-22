# Domain docs (single context)

- **Glossary:** `GLOSSARY.md` at the repo root. Shared language; use these nouns in code, tests, docs, issues and PRs.
- **Decisions:** `docs/adr/NNNN-slug.md`, numbered from `0001`. Template: `docs/adr/0000-template.md`.
- **Spec:** `docs/spec/SPEC.md` (committed copy of SPEC-01; the issue may truncate).

## When to update the glossary
When you introduce a noun that will appear in code, tests or docs; when two words mean the same thing (pick one, list the other under "Not to be confused with"); when a ticket's review finds drift. Do it in the same PR as the code. For a contested term run `/domain-modeling` and ask the maintainer.

## ADR bar (all three must hold)
1. **Hard to reverse** (on-disk formats, public CLI, lock formats, contract majors, choosing a dependency).
2. **Surprising without context** (a future reader would wonder why).
3. **A real trade-off** (credible alternatives existed and were weighed).
If any is false, put the rationale in the PR or code comment instead. One ADR per decision; supersede, never edit history.

## Who writes what
Decision tickets (DEC-xx) end with an ADR when they clear the bar. Build tickets add an ADR only when they uncover a new decision that clears the bar (and should have stopped for a decision first if it was not already settled).
