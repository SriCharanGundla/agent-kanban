# Agent Kanban Backend

FastAPI backend for Agent Kanban, designed so AI agents can autonomously view, edit, and manage tasks while users retain visibility and control through authenticated project, collaboration, and invitation workflows.

## Features

- Authentication:
  - JWT auth for web flows
  - API key auth for agent workflows (`X-API-Key`)
  - Flexible auth dependency supporting either JWT or API key on project/task APIs
- User management:
  - Register/login/current-user/profile update
  - Pending invitation auto-accept on registration when email matches
- Projects:
  - Create/list/get/update/delete (soft delete)
  - Per-project stats (`task_count`, `done_count`)
  - Role and member count metadata
- Tasks:
  - CRUD operations
  - Status updates and stable reorder logic within/across columns
  - Assignee validation against accepted project members
  - Soft delete
- Subtasks:
  - CRUD operations with ordered positions
  - Completion tracking
- Collaboration:
  - Project member invite/list/update role/remove
  - Invitation link generation with expiry
  - Owner/member role controls and safeguards (e.g., last-owner protection)
  - Assignee listing endpoint
- API keys:
  - Generate/list/revoke keys
  - Secure key hashing, prefix/suffix storage, last-used timestamp tracking
- Operational:
  - Alembic migrations
  - Structured exception handling
  - Health endpoint
  - Integration and unit test coverage for auth, collaboration, projects, tasks, subtasks, edge cases

## Prerequisites

- Python `3.12`
- [`uv`](https://docs.astral.sh/uv/) package manager
- PostgreSQL (separate DBs for app and tests recommended)

## Setup

1. Install dependencies:

```bash
uv sync
```

2. Configure environment:

```bash
cp .env.example .env
```

After copying, open `.env` and configure all values for your environment (database URLs, JWT settings, CORS/frontend URL, and environment mode).

3. Run database migrations:

```bash
uv run alembic upgrade head
```

4. Start API server:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 7655 --reload
```

5. Open:

- API root: `http://localhost:7655/`
- Health: `http://localhost:7655/health`
- Swagger: `http://localhost:7655/docs`

## Initialization Flow

1. Register user: `POST /api/v1/auth/register`
2. Login: `POST /api/v1/auth/login` (form-urlencoded OAuth2 password flow)
3. Generate API key (JWT required): `POST /api/v1/api-keys`
4. Use API key in agent calls:

```http
X-API-Key: ak_...
```

5. Create project, then create tasks/subtasks and manage collaborators.

## Agent Self-Use Requirement

For agents to use the system autonomously, you must do all of the following first:

1. Run/deploy the app so the API is reachable from the agent.
2. Generate an API key after logging in.
3. Update `SKILL.md` configuration with your real deployed API URL and key:

```bash
API_KEY="<generated-api-key>"
BASE_URL="https://your-deployed-api-url"
API_PATH="/api/v1"
```

Without these values, agents cannot authenticate and execute project/task operations on their own.

## Production / Docker

For Docker deployment, `backend/deploy.sh` reads environment variables from `../be-env/.env` (not `backend/.env`).  
Place the file there before running deploy:

```bash
mkdir -p ../be-env
cp .env.example ../be-env/.env
# then edit ../be-env/.env with your deployment values
```

From `backend/`:

```bash
./deploy.sh
```

This script:

- Reads `../be-env/.env`
- Builds and runs backend container on port `7655` (or `$BACKEND_PORT`)
- Container startup runs `alembic upgrade head` before launching `uvicorn`

Teardown:

```bash
./teardown.sh
```

Teardown stops and removes the `agent-kanban-backend` container only.
It does not remove Docker images or your PostgreSQL data.

## Testing

```bash
uv run pytest
```

Note: tests require `TEST_DATABASE_URL` in `.env`.

## Skill File

`SKILL.md` uses the Agent Skills open format: a portable package of instructions, scripts, and resources that compatible agents can load on demand for repeatable workflows and domain-specific capability. In our case, it provides the necessary configuration and instructions for AI agents to interact with the Agent Kanban API autonomously.

### Skill Installation Paths

- Claude Code:
  - Global: `~/.claude/skills/agent-kanban/SKILL.md`
  - Local: `./.claude/skills/agent-kanban/SKILL.md`

- OpenAI Codex:
  - Global: `~/.agents/skills/agent-kanban/SKILL.md`
  - Local: `./.agents/skills/agent-kanban/SKILL.md`
  
- OpenCode:
  - Global: `~/.config/opencode/skills/agent-kanban/SKILL.md`
  - Local: `.opencode/skills/agent-kanban/SKILL.md`
