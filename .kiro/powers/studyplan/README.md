# StudyPlan — Kiro Power

Reusable guidance for working with StudyPilot's study-plan generation feature.

This power is packaged in the [Agent Plugins v1.0.0](https://agent-plugins.org) format so it works with any compliant client. Inside Kiro, it activates on mentions of study plans, `build_plan`, `HOURS_PER_TOPIC`, or the `/study-plan` endpoint.

## What it provides

Two skills, both scoped tightly to this feature:

- **`study-plan-workflow`** — orient in the domain, know which files to touch, follow the standard workflow, preserve the pure/adapter split, and avoid out-of-scope changes.
- **`verify-plan-invariants`** — run the pytest + Hypothesis suite, inspect live plans against the five invariants, and confirm error paths return HTTP 422 with useful messages.

Each skill ships references under `skills/<name>/references/`:

- `invariants.md` — the five invariants stated formally.
- `api-contract.md` — the wire contract for `POST /study-plan` and its TypeScript mirror.

## What it does not do

- Does not include an MCP server. No `mcp.json`.
- Does not rewrite the application. Skills are read-only guidance until Kiro applies them to an edit.
- Does not add features outside the study-plan generator's spec.

## Layout

```
studyplan/
├── plugin.json                                  # Agent Plugins manifest
├── README.md
└── skills/
    ├── study-plan-workflow/
    │   ├── SKILL.md
    │   └── references/
    │       ├── invariants.md
    │       └── api-contract.md
    └── verify-plan-invariants/
        └── SKILL.md
```

## Related project files

- `.kiro/specs/study-plan-generator/` — requirements, design, tasks
- `.kiro/steering/product.md`, `architecture.md`, `coding-standards.md` — always-included project rules
- `backend/app/study_plan.py` — the pure planning module
- `backend/tests/test_study_plan_properties.py` — the property-based tests this power expects to stay green
