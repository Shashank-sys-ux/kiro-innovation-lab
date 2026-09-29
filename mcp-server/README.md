# StudyPilot MCP Server

A local MCP server that exposes StudyPilot's data and study-plan generator to any MCP-compatible client (Kiro, Claude Desktop, etc.). Runs on your machine, reads the local SQLite database, makes no network calls, and never writes.

## Tools

| Tool | Description |
|---|---|
| `list_topics` | Every topic with `id`, `name`, `subject`, `completed`. |
| `get_progress` | `total_topics`, `completed_topics`, `percent_complete`. |
| `list_questions` | Every practice question with `topic_id`, `question`, `answer`, `difficulty`. |
| `generate_study_plan` | Given `subject`, `topics`, `days`, `hours_per_day`, returns a plan built by the exact same `build_plan` function the `/study-plan` API uses. |

## Design

- **Reuses `backend/app/study_plan.py` directly** by adding `backend/` to `sys.path`. No duplicated planning logic → every invariant (full topic coverage, day range, per-day hour cap, total-hours equality, rejection of invalid inputs) is preserved by construction.
- **Reads the DB directly** with `sqlite3` in read-only URI mode (`file:...?mode=ro`). The backend owns writes.
- **Isolated under `mcp-server/`.** No changes to `backend/` or `frontend/`.
- **stdio transport** — the format Kiro's `mcp.json` and Claude Desktop expect.

## Setup

From `mcp-server/`:

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

Sanity check the server can start (Ctrl+C to exit — it's waiting for a stdio client):

```powershell
.\.venv\Scripts\python.exe server.py
```

## Wire it up in Kiro

Add to `.kiro/settings/mcp.json` (workspace) or `~/.kiro/settings/mcp.json` (user-level):

```json
{
  "mcpServers": {
    "studypilot": {
      "command": "C:\\Users\\Shashank\\Desktop\\kiro-innovation-lab\\mcp-server\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\Shashank\\Desktop\\kiro-innovation-lab\\mcp-server\\server.py"],
      "disabled": false
    }
  }
}
```

Adjust the paths if your workspace lives somewhere else. Kiro will pick up config changes without a restart.

## Requirements

- Python 3.10+
- The StudyPilot backend has been started at least once so `backend/studypilot.db` exists.

## What this server intentionally does not do

- No write tools (create/complete/delete). Writes stay in the FastAPI backend so there's one source of truth for validation and state changes.
- No auth. Local-first, single-user, per the project's steering docs.
- No caching. The database is small; queries are cheap.
- No new dependencies beyond `mcp` and `pydantic`.
