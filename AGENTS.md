# WCVA project / workspace rules (Codex)

Apply these in all conversations, plans, debugging sessions, and related workflows.

## Language and style

- Use **UK/British English** for all responses, plans, docs, comments, and user-facing text unless the user explicitly requests otherwise.

## Environment and local tooling

- Use the project virtual environment at **`.venv`** in the project root before running any Python commands, scripts, tests, linters, formatters, documentation tooling, or related project commands.
- Prefer project-local tools and dependencies over globally installed ones.

## Review context first

- Before recommending, changing, or planning: review the relevant code, tests, docs, ADRs, references, configuration, and existing patterns needed to complete the task correctly.
- For large, architectural, cross-cutting, or high-impact work: widen review to the broader repository structure and adjacent subsystems.

## Review project memory and planning context

- Before making substantial changes: review relevant prior conversations, plans, notes, and any files in Cursor plan directories or equivalent project memory; reuse and respect prior decisions unless the user asks to revisit them.

## Follow project conventions

- Follow the project’s documented conventions, styles, and workflows, especially **CONTRIBUTING.md**, plus ADRs, architecture notes, developer docs, docstrings, tests, and established code patterns. Prefer consistency with the existing codebase unless the user explicitly requests a redesign or the current pattern is clearly unsound.

## Human-in-the-loop decisions

- Ask for confirmation before: architectural decisions, broad refactors, destructive actions, dependency or schema changes, public API changes, security-sensitive changes, changes affecting multiple subsystems, or other high-impact or hard-to-reverse decisions.
- Do not ask unnecessary questions for small, low-risk, localised tasks. If the user’s preferred level of involvement is unclear, ask at the start of the session.

## Plan mode for substantial work

- For multi-step, cross-file, architectural, exploratory, or high-impact work: use plan mode first so the approach is transparent, reviewable, and easy to track. Keep plans concise and updated as work progresses.

## Focused changes

- Avoid unrelated refactors, opportunistic rewrites, unnecessary renames, or broad formatting churn unless required or approved. Keep diffs focused and minimal. For broader clean-up, explain why and seek approval if impact is non-trivial.

## Keep code, tests, docs, and references aligned

- When making significant changes: update implementation, tests, documentation, examples, comments, docstrings, architecture notes, ADR references, configuration, and developer guidance as appropriate. Do not leave obviously stale material without flagging it.

## Surface deferred work

- If follow-up work is intentionally deferred: record it clearly (in the response, plan, TODOs, or agreed tracking location). Distinguish work completed now, work intentionally postponed, and work blocked pending user input.

## Prefer automation

- Where practical: favour tests, linting, formatting, type checking, documentation builds, link checks, generated artefact refreshes, and pre-commit or CI checks to keep the codebase aligned. Suggest or implement automation where it reduces drift.

## Validate before concluding

- After making changes: run the most relevant checks (unit/integration tests, lint, format, type check, docs build, import checks) using the local project environment where practical. If validation cannot be completed, say so and explain what remains unverified.

## Destructive or irreversible actions

- Before deleting files, removing features, rewriting large sections, altering persistent data structures, or changing generated outputs relied on elsewhere: seek confirmation unless the user has already authorised that category of change.

## Respect architecture and boundaries

- Preserve intended architectural boundaries, layering, module responsibilities, and separation of concerns. Do not introduce shortcuts, hidden coupling, circular dependencies, or inconsistent patterns without strong justification and user approval where appropriate.

## Root-cause fixes

- When debugging or refactoring: prefer solutions that address the underlying cause rather than masking symptoms. Check for related tests, nearby assumptions, edge cases, and knock-on effects before finalising changes.

## Clear communication

- Summarise what was reviewed, what changed, what was validated, assumptions, open questions, risks, trade-offs, and recommended next steps. Keep communication clear and proportionate to the scale of the task.

## Respect existing user decisions

- Do not repeatedly reopen decisions already made by the user unless new evidence, constraints, or direct instructions justify reconsideration.

## Be explicit about uncertainty

- If context is incomplete, requirements are ambiguous, or confidence is limited: say so. Make grounded recommendations and seek clarification only where the decision affects correctness, safety, maintainability, or architecture.

## Repository usability

- When making broad improvements: consider end users, contributors, and maintainers. Prefer changes that improve discoverability, readability, onboarding, documentation quality, and maintainability without unnecessary complexity.

## Documentation as part of the product

- Treat documentation, examples, architecture notes, and contributor guidance as first-class assets. When code changes alter behaviour, structure, setup, workflows, or expectations: update the relevant docs as part of the same body of work where practical.

## Sensible, reversible defaults

- When several acceptable options exist and the user has not specified a preference: prefer the option that is simpler, clearer, more maintainable, and easier to reverse later.

## Performance and security

- For changes affecting performance, secrets, authentication, data handling, permissions, external services, or deployment: review the relevant code paths and call out material risks, trade-offs, or assumptions before or alongside implementation.

## Avoid overstating completion

- Do not imply that the whole codebase has been fully reviewed, aligned, or validated unless that is true. Be precise about scope: what was checked, what was changed, what remains outside the reviewed area.

## Coherent plans and outputs

- Ensure plans, implemented changes, documentation updates, and final summaries align. Avoid situations where code, plan, and explanation describe different outcomes.

## Tests first where appropriate

- When fixing bugs or changing behaviour in established areas: prefer adding or updating tests that demonstrate the intended behaviour before or alongside implementation.

## Do not bypass checks casually

- Do not disable tests, lint rules, type checks, or safety checks without a clear reason and explicit explanation.

## Session-start involvement

- At the start of a new substantial session, if not already clear: ask how involved the user wants to be (e.g. highly collaborative, approval-based for major choices only, or mostly autonomous within these rules).

## Architecture and documentation hygiene

- For large changes: check whether architecture diagrams, flow charts, README sections, setup guides, developer docs, and ADR references should be updated.

## Generated artefacts

- Where the repository contains generated documentation, diagrams, stubs, or other derived artefacts: refresh them when source changes require it, or clearly note that regeneration is still needed.
