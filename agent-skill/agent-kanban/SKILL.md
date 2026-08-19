---
name: agent-kanban
description: Manage Agent Kanban projects, tasks, subtasks, assignments, and status through its REST API. Use when an agent needs to inspect or update a user's Agent Kanban board using an API key.
---

# Agent Kanban

Operate a user's Agent Kanban workspace through the REST API. Read [references/api.md](references/api.md) before making calls that change project state.

## Required configuration

Obtain these values from the user or the runtime's secret manager:

- `AGENT_KANBAN_BASE_URL`: deployed backend origin, such as `https://agent-kanban-backend.onrender.com`
- `AGENT_KANBAN_API_KEY`: key generated in **Settings → API Keys**; it begins with `ak_`

Do not write an API key into this skill, source control, logs, or chat output. Send it only in the `X-API-Key` request header.

## Operating workflow

1. Verify connectivity with `GET $AGENT_KANBAN_BASE_URL/health`.
2. List projects and resolve names to IDs before working with tasks.
3. Read the current project, task, or subtask immediately before modifying it.
4. Make the smallest requested mutation.
5. Fetch the affected resource again and report the confirmed result.

Use `/api/v1` as the API prefix. Prefer exact IDs returned by the API; never invent or guess IDs.

## Safety rules

- Treat delete operations as destructive even though application records are soft-deleted. Ask for confirmation unless deletion is explicit in the current request.
- Do not invite users, alter roles, remove members, revoke keys, or delete projects without explicit authorization.
- Preserve task descriptions and metadata when changing only status or position.
- When moving several tasks, refresh the board after each reorder because positions can change.
- If the server returns `401` or `403`, stop and report the authentication or permission issue; do not retry with guessed credentials.
- If a write returns an error, do not claim success. Re-read state before deciding whether to retry.

## Request pattern

```bash
curl --fail-with-body \
  -H "X-API-Key: $AGENT_KANBAN_API_KEY" \
  -H "Content-Type: application/json" \
  "$AGENT_KANBAN_BASE_URL/api/v1/projects"
```

See [references/api.md](references/api.md) for endpoints, payloads, status values, and examples.
