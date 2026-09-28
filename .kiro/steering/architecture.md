# StudyPilot — Architecture

## Shape
Two-tier local application:

```
┌─────────────────────────────┐        HTTP/JSON        ┌────────────────────────────┐
│  Frontend                   │  ───────────────────▶   │  Backend                   │
│  React + TypeScript + Vite  │                         │  FastAPI (Python)          │
│  http://localhost:5173      │  ◀───────────────────   │  http://localhost:8000     │
└─────────────────────────────┘                         │        │                   │
                                                        │        ▼                   │
                                                        │  SQLAlchemy ORM            │
                                                        │        │                   │
                                                        │        ▼                   │
                                                        │  SQLite (studypilot.db)    │
                                                        └────────────────────────────┘
```

Everything runs on the user's machine. There are no external services in the request path.

## Frontend — `frontend/`
- **Stack:** React 18+ with TypeScript, bundled by Vite.
- **Role:** Renders the UI, holds transient UI state, calls the backend over `fetch`.
- **State:** Local component state via `useState` / `useReducer`. No Redux, no global store — the app is small enough that prop-passing and colocated state are sufficient.
- **API access:** Direct `fetch` to `http://localhost:8000/...`. No generated client; response shapes are declared inline (or in a small shared types file) alongside the component that consumes them.
- **Styling:** Plain CSS files (`App.css`, `index.css`). No CSS-in-JS framework.

## Backend — `backend/app/`
- **Stack:** FastAPI + Pydantic v2 + SQLAlchemy 2.0 (typed `Mapped` API) + SQLite.
- **Layout:**
  - `main.py` — FastAPI app, route handlers. Thin: parse input, delegate, return.
  - `models.py` — SQLAlchemy ORM models (`Topic`, `Question`).
  - `database.py` — engine, session factory, `Base`, `get_db` dependency.
  - `study_plan.py` — pure planning module (see below).
- **DB session:** Injected per request via the `get_db` FastAPI dependency.
- **Schema management:** `Base.metadata.create_all()` on startup. No migration tool for now — the schema is small and evolves rarely. If migrations become necessary, introduce Alembic then, not preemptively.

## Study Plan Generator — pure module
`backend/app/study_plan.py` is intentionally **pure**:
- No database access, no FastAPI imports beyond Pydantic models.
- `build_plan(subject, topics, days, hours_per_day) -> list[DailyTask]` is a plain function.
- The FastAPI route in `main.py` is a thin adapter around it.

This makes the planning logic trivially unit-testable (see `tests/test_study_plan_properties.py`) and keeps the persistence layer decoupled from the algorithm. Any future planning features should follow the same pattern: pure module + thin route adapter.

## Frontend / backend contract
- Communication is HTTP + JSON. No websockets, no server-sent events.
- Pydantic response models on the backend define the wire shape; the frontend mirrors them with hand-written TypeScript types.
- CORS is enabled for `http://localhost:5173` (Vite dev server). Production packaging is not a current concern.

## Data flow examples
- **Create topic:** UI form → `POST /topics` → SQLAlchemy insert → return row → UI list refreshes.
- **Generate plan:** UI form → `POST /study-plan` → `build_plan()` (in-memory) → JSON response → UI renders days.
- **Complete topic:** UI click → `PATCH /topics/{id}/complete` → SQLAlchemy update → return row.

## Simplicity constraints
The project is intended to remain **simple and local-first**. Before adopting any of the following, there must be a concrete need already visible in the codebase:
- background workers / task queues,
- caching layers,
- separate services or microservices,
- ORMs or query builders other than SQLAlchemy,
- authentication / authorization frameworks,
- containerization for local dev.

When in doubt, prefer the smaller change that keeps the two-tier shape intact.
