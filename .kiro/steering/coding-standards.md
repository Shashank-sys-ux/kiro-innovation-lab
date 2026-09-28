# StudyPilot — Coding Standards

Practical rules for this repository. Short list, applied consistently.

## Universal
- **Small, focused functions.** One responsibility per function. If a function needs a paragraph to explain, split it.
- **Clear names over clever names.** `build_plan`, not `bp`. `topicsInput`, not `x`. Names should read like what the code does.
- **No unnecessary dependencies.** Prefer the standard library / already-installed packages. New dependencies need a real reason and should be pinned.
- **Tests for core business logic.** Anything that computes a result (planning, validation, transformations) gets tests. Wiring code (route handlers, JSX rendering) doesn't need dedicated tests unless it has real logic.
- **Handle errors close to where they occur.** Raise domain-specific exceptions (`PlanValidationError`) and translate them at the boundary (route handler → HTTP status).
- **No dead code.** Delete unused imports, functions, and branches rather than commenting them out. Git remembers.

## Python / FastAPI (`backend/`)
- **Type hints on every function signature.** Return types included. Use `list[str]`, `dict[str, int]` (PEP 585) — the project targets a modern Python.
- **Pydantic v2 for I/O.** Request/response bodies are Pydantic models. Do not accept loose `dict` payloads in routes.
- **Route handlers stay thin.** Parse input → call a pure function or a small DB helper → return. If a handler grows past ~15 lines of logic, extract it.
- **Pure modules for logic.** Anything that isn't inherently tied to HTTP or the DB (e.g. `study_plan.py`) belongs in its own module with no framework imports beyond Pydantic.
- **SQLAlchemy 2.0 typed style.** Use `Mapped[...]` and `mapped_column(...)` as `models.py` already does; don't mix in the legacy 1.x `Column` style.
- **DB sessions via `Depends(get_db)`.** Don't open sessions ad hoc inside handlers.
- **Explicit imports.** No `from module import *`.
- **Formatting.** Follow standard `black`-style formatting: 88-char lines, double quotes, trailing commas in multiline literals. If a formatter is added later, it should not churn existing files.

## TypeScript / React (`frontend/`)
- **`strict: true` in tsconfig; keep it strict.** No `any` without a comment justifying it.
- **Function components + hooks only.** No class components.
- **Types near their consumer.** Small response types live inline with the component that uses them. Only promote a type to a shared file when a second consumer appears.
- **Controlled inputs for forms.** Component state is the source of truth for form fields.
- **`fetch` directly.** No axios / react-query for now — the app has too few endpoints to justify them.
- **CSS in plain `.css` files.** Class names in kebab-case (`.study-plan-form`). No inline style objects except for truly dynamic values (e.g. computed widths).
- **Component files are PascalCase** (`StudyPlanGenerator.tsx`); non-component modules are camelCase.
- **Keep components under ~150 lines.** If a component grows past that, extract subcomponents or a hook.
- **No default exports for shared components.** Named exports make refactors and search easier. `App.tsx` may keep its default export for Vite's convention.

## Testing
- **Backend:** `pytest`. Property-based tests via Hypothesis for anything with invariants (see `tests/test_study_plan_properties.py`). Prefer strategies over hard-coded examples when generating inputs is straightforward.
- **Frontend:** Add a test runner (Vitest) only when non-trivial client logic exists. Rendering a form and posting JSON does not warrant it.
- **Test names describe the behavior, not the function.** `test_every_topic_appears_exactly_once`, not `test_build_plan_1`.

## Comments and documentation
- **Comments explain _why_, not _what_.** The code shows what it does; comments justify non-obvious choices.
- **Module docstrings** on non-trivial modules (like `study_plan.py`) — one short paragraph on purpose and any invariants.
- **No boilerplate function docstrings** that just restate the signature.

## Commit hygiene
- Small, self-contained commits. A feature spec, its implementation, and its tests can be separate commits.
- Commit messages state the change and its intent in the first line; details go in the body if needed.
