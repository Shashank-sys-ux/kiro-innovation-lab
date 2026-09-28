# StudyPilot — Product

## Purpose
StudyPilot is a **local-first study planning and interview-preparation tracker**. It runs on the user's own machine against a local SQLite database, with no cloud services, no accounts, and no telemetry. The goal is to help a single learner organize what they're studying, plan how to cover it, and see progress as they go.

Local-first means:
- All data lives in `backend/studypilot.db` on the user's disk.
- The app works offline.
- No authentication layer — the app assumes a single trusted user.

## Core user workflows

### 1. Manage topics
The user records what they need to study as `Topic` entries, each with a name and a subject (e.g. "Binary Search" / "Algorithms"). Topics are the atomic unit the rest of the product is built around.

### 2. Generate a study plan
Given a subject, a list of topics, a number of study days, and available study hours per day, StudyPilot produces a day-by-day plan that:
- covers every topic within the requested window,
- respects the daily hour budget,
- returns clear validation errors when the workload doesn't fit.

The plan is computed on demand and displayed in the UI. It is not persisted (see the study-plan-generator spec).

### 3. Complete topics
As the user finishes a topic, they mark it complete. Completion is a simple boolean on the `Topic` record — no timestamps, no history, no partial-progress states.

### 4. View progress
The user can see which topics are done and which are outstanding, giving a quick sense of how much of a subject remains.

### Adjacent: interview-prep questions
Alongside topics, StudyPilot stores `Question` records (question, answer, difficulty) tied to a topic. These support the interview-preparation side of the product: reviewing questions per topic. Kept simple — no spaced-repetition scheduling.

## Scope guardrails
The product intentionally stays small. Before adding a feature, prefer:
- extending an existing model over introducing a new one,
- computing on request over persisting new state,
- a single clear workflow over configurable options.

Out of scope for now: multi-user accounts, cloud sync, sharing, mobile apps, AI-generated content, spaced-repetition scheduling, and analytics dashboards beyond simple progress views.
