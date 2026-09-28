# Study Plan Generator — Requirements

## Overview
Add a Study Plan Generator to StudyPilot. A user supplies a subject, a list of topics, a number of study days, and available study hours per day. The system returns a day-by-day plan that covers every topic within the requested window and respects the daily hour budget.

The feature is additive. It does not change existing `Topic` / `Question` models or endpoints.

## User Stories

### US-1: Generate a study plan
As a student, I want to generate a study plan from a subject, topics, day count, and daily hour budget, so I have a concrete day-by-day schedule.

**Acceptance criteria**
1. WHEN the user submits a valid subject, non-empty topics list, day count ≥ 1, and hours-per-day > 0, THEN the system SHALL return a plan with exactly `days` daily entries indexed `1..days`.
2. The plan SHALL include every submitted topic at least once across its daily tasks.
3. No daily entry SHALL reference a day number outside `1..days`.
4. The estimated hours assigned to any single day SHALL be ≤ `hours_per_day`.
5. Each daily entry SHALL list the topics scheduled for that day and the estimated hours for that day.

### US-2: Validation
As a user, I want clear validation errors when my input is invalid, so I can correct it before submitting.

**Acceptance criteria**
1. WHEN `topics` is empty or contains only blank strings, THEN the API SHALL return HTTP 422 with an error indicating topics are required.
2. WHEN `days` is less than 1 or not an integer, THEN the API SHALL return HTTP 422.
3. WHEN `hours_per_day` is less than or equal to 0, THEN the API SHALL return HTTP 422.
4. WHEN `subject` is blank, THEN the API SHALL return HTTP 422.
5. WHEN the total workload cannot fit within `days * hours_per_day` (given the per-topic estimate defined in Design), THEN the API SHALL return HTTP 422 with a message stating the plan does not fit.

### US-3: View plan in the UI
As a user, I want to submit the form from the frontend and see the generated plan, so I can review my schedule.

**Acceptance criteria**
1. The frontend SHALL provide a form with fields: subject, topics (repeatable / comma-separated), days, hours per day.
2. On submit, the frontend SHALL call the plan generation endpoint and render each day with its topics and estimated hours.
3. WHEN the backend returns a validation error, the frontend SHALL display the error message.

## Out of scope
- Persisting plans to the database.
- Authentication / users.
- Per-topic difficulty or custom duration input (fixed estimate defined in Design).
- Editing / regenerating an existing plan.
