"""StudyPilot MCP server.

Exposes read-only views of the StudyPilot SQLite database plus the pure
`build_plan` function to any MCP-compatible client (Kiro, Claude Desktop, etc.).

Runs entirely on the user's machine. No network calls, no writes.

Tools:
    list_topics       — topics with completion status
    get_progress      — total / completed / percent complete
    list_questions    — practice questions with topic_id, question, answer, difficulty
    generate_study_plan — reuses backend.app.study_plan.build_plan (same invariants)
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Locate the existing StudyPilot backend so we can reuse study_plan.py.
# We add backend/ to sys.path rather than duplicating the algorithm; this
# guarantees the MCP server enforces the exact same invariants as the API.
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
DB_PATH = BACKEND_DIR / "studypilot.db"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Imported after sys.path is set. The module is pure — no FastAPI, no DB.
from app.study_plan import (  # noqa: E402
    HOURS_PER_TOPIC,
    PlanValidationError,
    build_plan,
)

from mcp.server.fastmcp import FastMCP  # noqa: E402

mcp = FastMCP("studypilot")


# ---------------------------------------------------------------------------
# DB helpers — plain sqlite3, read-only. The backend owns writes.
# ---------------------------------------------------------------------------


def _connect() -> sqlite3.Connection:
    """Open a read-only connection to the StudyPilot SQLite database."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"StudyPilot database not found at {DB_PATH}. "
            "Start the backend once to create it."
        )
    # `mode=ro` prevents accidental writes; `uri=True` enables the URI form.
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_topics() -> list[dict[str, Any]]:
    """Return every StudyPilot topic with its name, subject, and completion flag."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name, subject, completed FROM topics ORDER BY id"
        ).fetchall()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "subject": row["subject"],
            "completed": bool(row["completed"]),
        }
        for row in rows
    ]


@mcp.tool()
def get_progress() -> dict[str, Any]:
    """Return total topics, completed topics, and completion percentage.

    `percent_complete` is 0.0 when there are no topics (rather than raising).
    """
    with _connect() as conn:
        row = conn.execute(
            "SELECT "
            "  COUNT(*) AS total, "
            "  COALESCE(SUM(CASE WHEN completed THEN 1 ELSE 0 END), 0) AS done "
            "FROM topics"
        ).fetchone()

    total = int(row["total"])
    completed = int(row["done"])
    percent = round((completed / total) * 100, 2) if total else 0.0

    return {
        "total_topics": total,
        "completed_topics": completed,
        "percent_complete": percent,
    }


@mcp.tool()
def list_questions() -> list[dict[str, Any]]:
    """Return practice questions with topic_id, question, answer, and difficulty."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, topic_id, question, answer, difficulty "
            "FROM questions ORDER BY id"
        ).fetchall()
    return [
        {
            "id": row["id"],
            "topic_id": row["topic_id"],
            "question": row["question"],
            "answer": row["answer"],
            "difficulty": row["difficulty"],
        }
        for row in rows
    ]


@mcp.tool()
def generate_study_plan(
    subject: str,
    topics: list[str],
    days: int,
    hours_per_day: float,
) -> dict[str, Any]:
    """Generate a study plan using the same rules as the /study-plan endpoint.

    Delegates to `backend.app.study_plan.build_plan`, so every invariant
    (full topic coverage, day range, per-day hour budget, total-hours
    equality, rejection of invalid inputs) is preserved by construction.

    Raises a ValueError with a human-readable message when inputs are invalid;
    MCP clients will surface this as a tool error.
    """
    try:
        daily_tasks = build_plan(
            subject=subject,
            topics=topics,
            days=days,
            hours_per_day=hours_per_day,
        )
    except PlanValidationError as exc:
        # FastMCP surfaces exceptions as tool errors. Re-raise as ValueError
        # so the error type is standard rather than a project-internal class.
        raise ValueError(str(exc)) from exc

    return {
        "subject": subject,
        "hours_per_topic": HOURS_PER_TOPIC,
        "days": [task.model_dump() for task in daily_tasks],
    }


# ---------------------------------------------------------------------------
# Entry point — stdio transport, which is what Kiro's mcp.json expects.
# ---------------------------------------------------------------------------


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
