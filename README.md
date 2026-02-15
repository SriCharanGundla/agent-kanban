# Agent Kanban Frontend

Vite + React + TypeScript + ShadCN based Web UI for Agent Kanban, where AI agents can view, edit, and manage project tasks across sessions while users get clear visibility into progress, activity, and collaboration.

## Features

- Auth flows: register, login, protected routes, token persistence
- Dashboard with project stats and pending invitation banner
- Project creation and project cards with progress summaries
- Kanban board with columns: `backlog`, `todo`, `in_progress`, `done`
- Drag-and-drop task movement with persisted ordering/status
- Task CRUD with priority and assignee support
- Subtask create/update/delete and completion progress tracking
- Project settings sheet with:
  - General project settings
  - Team member management (invite/update role/remove)
- Invitation acceptance flow (`/invitations/:token`)
- API key management UI (create/list/revoke)
- Error handling + toast notifications + route guards

## Prerequisites

- Node.js 22+ (Node 22.12.0 is used in Docker)
- `pnpm`
- Running backend API (default: `http://localhost:7655`)

## Setup

1. Install dependencies:

```bash
pnpm install
```

2. Configure environment:

```bash
cp .env.example .env
```

After copying, open `.env` and configure the values for your environment (API URL, version, ports, etc.).

3. Start development server:

```bash
pnpm dev --host 0.0.0.0 --port 7654
```

4. Open:

- App: `http://localhost:7654`

## Initialization Flow

1. Register a new user from `/register`.
2. Log in and land on `/dashboard`.
3. Create your first project.
4. Open the project board and add tasks/subtasks.
5. Go to `Settings -> API Keys` and generate an API key for AI agents.
6. (Optional) Invite members from project settings.

## Agent Self-Use Requirement

For agents to use the system autonomously, you must do all of the following first:

1. Run/deploy the frontend and backend so the API is reachable.
2. Generate an API key from the app (`Settings -> API Keys`).
3. Update `SKILL.md` configuration with your real deployed API URL and key:

```bash
API_KEY="<generated-api-key>"
BASE_URL="https://your-deployed-api-url"
API_PATH="/api/v1"
```

Without these values, agents cannot authenticate and execute project/task operations on their own.

## Production / Docker

For Docker deployment, `frontend/deploy.sh` reads environment variables from `../fe-env/.env` (not `frontend/.env`).  
Place the file there before running deploy:

```bash
mkdir -p ../fe-env
cp .env.example ../fe-env/.env
# then edit ../fe-env/.env with your deployment values
```

From `frontend/`:

```bash
./deploy.sh
```

This script:

- Reads `../fe-env/.env`
- Builds Docker image with `VITE_API_BASE_URL`
- Runs nginx container on port `7654` (or `$FRONTEND_PORT`)

Teardown:

```bash
./teardown.sh
```

Teardown stops and removes the `agent-kanban-frontend` container only.
It does not remove Docker images or any other containers.

## Quality Commands

```bash
pnpm lint
pnpm build
pnpm preview
```

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