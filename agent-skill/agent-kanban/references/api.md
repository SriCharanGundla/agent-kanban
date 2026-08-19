# Agent Kanban API reference

All resource endpoints use the `/api/v1` prefix. Authenticate agent requests with `X-API-Key: $AGENT_KANBAN_API_KEY`. The interactive OpenAPI specification is available at `/docs` on a running backend and is the source of truth for complete schemas.

## Projects

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/projects` | List accessible projects with task statistics |
| `POST` | `/projects` | Create a project |
| `GET` | `/projects/{project_id}` | Read a project |
| `PUT` | `/projects/{project_id}` | Update a project |
| `DELETE` | `/projects/{project_id}` | Soft-delete a project |

Create a project:

```bash
curl --fail-with-body -X POST \
  -H "X-API-Key: $AGENT_KANBAN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"Release planning","description":"Prepare the next release"}' \
  "$AGENT_KANBAN_BASE_URL/api/v1/projects"
```

## Tasks

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/projects/{project_id}/tasks` | List project tasks and subtasks |
| `POST` | `/projects/{project_id}/tasks` | Create a task |
| `GET` | `/tasks/{task_id}` | Read a task |
| `PUT` | `/tasks/{task_id}` | Update a task |
| `PATCH` | `/tasks/{task_id}/status` | Move a task to another status |
| `PATCH` | `/tasks/{task_id}/reorder` | Reorder a task within or across columns |
| `DELETE` | `/tasks/{task_id}` | Soft-delete a task |

Valid statuses are `backlog`, `todo`, `in_progress`, and `done`. Valid priorities are `low`, `medium`, `high`, and `urgent`.

Create a task:

```bash
curl --fail-with-body -X POST \
  -H "X-API-Key: $AGENT_KANBAN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"Add release notes","status":"todo","priority":"medium"}' \
  "$AGENT_KANBAN_BASE_URL/api/v1/projects/$PROJECT_ID/tasks"
```

Change status:

```bash
curl --fail-with-body -X PATCH \
  -H "X-API-Key: $AGENT_KANBAN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}' \
  "$AGENT_KANBAN_BASE_URL/api/v1/tasks/$TASK_ID/status"
```

## Subtasks

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/tasks/{task_id}/subtasks` | List subtasks |
| `POST` | `/tasks/{task_id}/subtasks` | Create a subtask |
| `PATCH` | `/subtasks/{subtask_id}` | Update title, completion, or position |
| `DELETE` | `/subtasks/{subtask_id}` | Soft-delete a subtask |

## Collaboration

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/projects/{project_id}/members` | List project members |
| `GET` | `/projects/{project_id}/assignees` | List assignable users |
| `POST` | `/projects/{project_id}/members` | Invite a member |
| `PATCH` | `/projects/{project_id}/members/{member_id}` | Change a member role |
| `DELETE` | `/projects/{project_id}/members/{member_id}` | Remove a member |
| `GET` | `/invitations` | List pending invitations |
| `POST` | `/invitations/{token}/accept` | Accept an invitation |
| `DELETE` | `/invitations/{token}` | Decline an invitation |

Member and invitation operations affect other people. Perform them only when the user explicitly asks.

## API-key management

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api-keys` | Generate an API key; JWT login required |
| `GET` | `/api-keys` | List the current user's keys; JWT required |
| `DELETE` | `/api-keys/{api_key_id}` | Revoke a key; JWT required |

Agents normally receive an existing API key. They should not attempt to create or revoke keys using other credentials.

## Error handling

- `400` or `422`: correct the payload only when the intended value is unambiguous.
- `401`: the API key is missing, malformed, invalid, or expired.
- `403`: the authenticated identity lacks access to the resource or operation.
- `404`: refresh the parent collection; the resource may have been removed.
- `409`: refresh state before retrying because a membership or invitation conflict exists.
- `5xx`: do not repeat writes blindly. Re-read state first and report persistent failures.
