# Study Plan Generator — Tasks

- [ ] 1. Create `backend/app/study_plan.py`
  - Define `HOURS_PER_TOPIC = 1.0`.
  - Define `PlanValidationError(Exception)`.
  - Define Pydantic models: `StudyPlanRequest`, `DailyTask`, `StudyPlanResponse` with the validators described in design.md.
  - Implement `build_plan(subject, topics, days, hours_per_day) -> list[DailyTask]` using the round-robin, capacity-aware algorithm from design.md.
  - _Requirements: US-1 (AC 1–5), US-2 (AC 1, 5)_

- [ ] 2. Wire the endpoint in `backend/app/main.py`
  - Import `StudyPlanRequest`, `StudyPlanResponse`, `build_plan`, `PlanValidationError`.
  - Add `POST /study-plan` that validates input, calls `build_plan`, and maps `PlanValidationError` to `HTTPException(status_code=422)`.
  - Do not touch existing routes or model imports.
  - _Requirements: US-1, US-2_

- [ ] 3. Enable CORS for the frontend dev server
  - Add `fastapi.middleware.cors.CORSMiddleware` allowing `http://localhost:5173` for `POST` and `GET`.
  - Only if CORS is not already configured; leave existing config alone if present.
  - _Requirements: US-3_

- [ ] 4. Create `frontend/src/StudyPlanGenerator.tsx`
  - Controlled form: subject (text), topics (comma-separated text), days (number), hours per day (number).
  - Submit handler POSTs to `http://localhost:8000/study-plan` with parsed topics.
  - Render loading state, error string, and the returned plan grouped by day with topics and `estimated_hours`.
  - Inline `DailyTask` / `StudyPlanResponse` types.
  - _Requirements: US-3 (AC 1–3)_

- [ ] 5. Mount the generator in `frontend/src/App.tsx`
  - Import `StudyPlanGenerator` and render it as a new `<section>` below the existing hero section.
  - Leave the existing hero, docs, and social sections untouched.
  - _Requirements: US-3_

- [ ] 6. Manual verification
  - Start backend (`uvicorn app.main:app --reload` from `backend/`) and frontend (`npm run dev` from `frontend/`).
  - Submit: subject "Math", topics "Algebra, Geometry, Calculus", days 3, hours per day 2 → expect 3 days, one topic each, 1.0 hrs per day.
  - Submit: empty topics → expect inline validation error.
  - Submit: days 1, hours per day 1, topics "A, B, C" → expect 422 "plan does not fit".
  - _Requirements: US-1, US-2, US-3_
