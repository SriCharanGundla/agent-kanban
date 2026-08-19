---
name: agent-kanban
description: Manage tasks, projects, and subtasks on the Agent Kanban Board using API Key authentication. Create projects, add tasks with priorities, track progress with subtasks, and move items through backlog/todo/in_progress/done workflow.
---

# Agent Kanban Board API Skill

This skill enables AI agents to autonomously manage tasks, projects, and subtasks on the Agent Kanban Board using API Key authentication.

## Configuration

Before using this skill, configure your API credentials:

```bash
API_KEY="<api-key>"          # Set your API key here after deployment
BASE_URL="<ip-address>"      # Production API server
API_PATH="/api/v1"
```

**How to get your API Key:**
1. Register: `POST <ip-address>/api/v1/auth/register`
2. Login: `POST <ip-address>/api/v1/auth/login`
3. Generate key: `POST <ip-address>/api/v1/api-keys` (with JWT token)
4. Save the API key (shown only once!)

## Authentication

All API requests require the `X-API-Key` header:

```bash
curl -H "X-API-Key: <api-key>" \
     <ip-address>/api/v1/projects
```

**API Key Format:**
- Prefix: `ak_` (e.g., `ak_7f3d8a9b2c1e4...`)
- Keys are hashed before storage
- Last used timestamp is tracked automatically

## Data Model

The Kanban Board follows this hierarchy:

```
User (many)
  └─> Project (many - as owner or member)
        ├─> ProjectMember (many - collaboration)
        └─> Task (many)
              ├─> Assignee (User)
              └─> Subtask (many)
```

**Collaboration:** 
- Projects can have multiple members with `owner` or `member` roles
- Tasks can be assigned to any project member
- Project owners can invite new members via email
- Members receive invitations they can accept or decline

## Task Status Values

| Status | Value | Description |
|--------|-------|-------------|
| Backlog | `backlog` | Tasks not yet scheduled |
| To Do | `todo` | Tasks ready to start |
| In Progress | `in_progress` | Currently working on |
| Done | `done` | Completed tasks |

## Task Priority Values

| Priority | Value | Description |
|----------|-------|-------------|
| Low | `low` | Low priority |
| Medium | `medium` | Normal priority (default) |
| High | `high` | Important tasks |
| Urgent | `urgent` | Critical/immediate attention |

---

## Projects API

### List All Projects

```bash
GET <ip-address>/api/v1/projects?limit=20&offset=0
```

**Query Parameters:**
- `limit` (int, default: 20) - Max results per page
- `offset` (int, default: 0) - Skip first N results

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "owner_id": "uuid",
    "name": "My Project",
    "description": "Project description",
    "created_at": "2026-01-27T10:00:00Z",
    "updated_at": "2026-01-27T10:00:00Z",
    "task_count": 5,
    "done_count": 2
  }
]
```

### Create Project

```bash
POST <ip-address>/api/v1/projects
Content-Type: application/json
X-API-Key: <api-key>

{
  "name": "New Project",
  "description": "Optional description"
}
```

**Response:** `201 Created` - Returns `ProjectResponse`

### Get Project Details

```bash
GET <ip-address>/api/v1/projects/{project_id}
```

**Response:** `200 OK` - Returns project with stats (task_count, done_count)

### Update Project

```bash
PUT <ip-address>/api/v1/projects/{project_id}
Content-Type: application/json
X-API-Key: <api-key>

{
  "name": "Updated Project Name",
  "description": "Updated description"
}
```

**Note:** All fields are optional. Omit fields you don't want to change.

**Response:** `200 OK`

### Delete Project

```bash
DELETE <ip-address>/api/v1/projects/{project_id}
```

**Response:** `204 No Content` (soft delete - recoverable)

---

## Tasks API

### List Tasks in Project

```bash
GET <ip-address>/api/v1/projects/{project_id}/tasks?limit=100&offset=0
```

**Query Parameters:**
- `limit` (int, default: 100)
- `offset` (int, default: 0)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "project_id": "uuid",
    "title": "Task title",
    "description": "Task description",
    "status": "todo",
    "priority": "high",
    "position": 0,
    "assignee_id": "uuid",
    "assignee_name": "John Doe",
    "created_at": "2026-01-27T10:00:00Z",
    "updated_at": "2026-01-27T10:00:00Z"
  }
]
```

### Create Task

```bash
POST <ip-address>/api/v1/projects/{project_id}/tasks
Content-Type: application/json
X-API-Key: <api-key>

{
  "title": "New task",
  "description": "Optional description",
  "status": "todo",
  "priority": "medium",
  "assignee_id": "uuid"
}
```

**Required:**
- `title` (string, 1-500 chars)

**Optional:**
- `description` (string)
- `status` (default: `backlog`)
- `priority` (default: `medium`)
- `assignee_id` (UUID) - User ID to assign task to

**Response:** `201 Created`

### Get Task with Subtasks

```bash
GET <ip-address>/api/v1/tasks/{task_id}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "title": "Task title",
  "description": "Description",
  "status": "in_progress",
  "priority": "high",
  "position": 0,
  "assignee_id": "uuid",
  "assignee_name": "John Doe",
  "created_at": "2026-01-27T10:00:00Z",
  "updated_at": "2026-01-27T10:00:00Z",
  "subtasks": [
    {
      "id": "uuid",
      "task_id": "uuid",
      "title": "Subtask 1",
      "is_completed": false,
      "position": 0,
      "created_at": "2026-01-27T10:00:00Z",
      "updated_at": "2026-01-27T10:00:00Z"
    }
  ],
  "completed_subtasks": 0,
  "total_subtasks": 1
}
```

### Update Task (Multiple Fields)

```bash
PUT <ip-address>/api/v1/tasks/{task_id}
Content-Type: application/json
X-API-Key: <api-key>

{
  "title": "Updated title",
  "description": "Updated description",
  "status": "in_progress",
  "priority": "urgent",
  "position": 0,
  "assignee_id": "uuid"
}
```

**Note:** All fields are optional. Use this for multi-field updates. Set `assignee_id` to `null` to unassign.

**Response:** `200 OK`

### Update Task Status (Atomic)

```bash
PATCH <ip-address>/api/v1/tasks/{task_id}/status
Content-Type: application/json
X-API-Key: <api-key>

{
  "status": "in_progress"
}
```

**Important:** This endpoint automatically moves the task to the end of the new status column. **Prefer this over PUT when only changing status.**

**Response:** `200 OK`

### Reorder Task

```bash
PATCH <ip-address>/api/v1/tasks/{task_id}/reorder
Content-Type: application/json
X-API-Key: <api-key>

{
  "position": 2,
  "status": "todo"
}
```

**Parameters:**
- `position` (int, required) - New position in column (0-indexed)
- `status` (string, optional) - Move to different status column

**Response:** `200 OK`

### Delete Task

```bash
DELETE <ip-address>/api/v1/tasks/{task_id}
```

**Response:** `204 No Content` (soft delete - recoverable)

---

## Subtasks API

### List Subtasks

```bash
GET <ip-address>/api/v1/tasks/{task_id}/subtasks?limit=100&offset=0
```

**Response:** `200 OK` - Returns array of subtasks

### Create Subtask

```bash
POST <ip-address>/api/v1/tasks/{task_id}/subtasks
Content-Type: application/json
X-API-Key: <api-key>

{
  "title": "Subtask title"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "task_id": "uuid",
  "title": "Subtask title",
  "is_completed": false,
  "position": 0,
  "created_at": "2026-01-27T10:00:00Z",
  "updated_at": "2026-01-27T10:00:00Z"
}
```

### Update Subtask

```bash
PATCH <ip-address>/api/v1/subtasks/{subtask_id}
Content-Type: application/json
X-API-Key: <api-key>

{
  "title": "Updated title",
  "is_completed": true,
  "position": 1
}
```

**Note:** All fields are optional.

**Response:** `200 OK`

### Delete Subtask

```bash
DELETE <ip-address>/api/v1/subtasks/{subtask_id}
```

**Response:** `204 No Content` (hard delete - permanent!)

---

## Project Members API

### List Project Members

```bash
GET <ip-address>/api/v1/projects/{project_id}/members
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "project_id": "uuid",
    "user_id": "uuid",
    "email": "member@example.com",
    "role": "member",
    "status": "accepted",
    "invited_by": {
      "id": "uuid",
      "full_name": "AI Agent",
      "email": "agent@example.com"
    },
    "user": {
      "id": "uuid",
      "full_name": "Team Member",
      "email": "member@example.com"
    },
    "created_at": "2026-01-28T10:00:00Z",
    "expires_at": "2026-02-04T10:00:00Z",
    "accepted_at": "2026-01-28T10:30:00Z"
  }
]
```

### List Project Assignees

Get all users who can be assigned to tasks (project owner + accepted members).

```bash
GET <ip-address>/api/v1/projects/{project_id}/assignees
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "full_name": "AI Agent",
    "email": "agent@example.com"
  },
  {
    "id": "uuid",
    "full_name": "Team Member",
    "email": "member@example.com"
  }
]
```

### Invite Project Member

```bash
POST <ip-address>/api/v1/projects/{project_id}/members
Content-Type: application/json
X-API-Key: <api-key>

{
  "email": "newmember@example.com",
  "role": "member"
}
```

**Required:**
- `email` (string) - Email address to invite

**Optional:**
- `role` (string, default: `member`) - Either `owner` or `member`

**Response:** `201 Created`
```json
{
  "member": {
    "id": "uuid",
    "project_id": "uuid",
    "user_id": null,
    "email": "newmember@example.com",
    "role": "member",
    "status": "pending",
    "invited_by": {
      "id": "uuid",
      "full_name": "AI Agent",
      "email": "agent@example.com"
    },
    "user": null,
    "created_at": "2026-01-28T14:00:00Z",
    "expires_at": "2026-02-04T14:00:00Z",
    "accepted_at": null
  },
  "invitation_link": "http://localhost:7654/invitations/AbCdEf123456..."
}
```

**Note:** Only project owners can invite members. Invitations expire after 7 days.

### Update Member Role

```bash
PATCH <ip-address>/api/v1/projects/{project_id}/members/{member_id}
Content-Type: application/json
X-API-Key: <api-key>

{
  "role": "owner"
}
```

**Response:** `200 OK` - Returns updated `ProjectMemberResponse`

**Note:** Only project owners can update roles. Cannot demote the last owner.

### Remove Project Member

```bash
DELETE <ip-address>/api/v1/projects/{project_id}/members/{member_id}
```

**Response:** `204 No Content`

**Note:** 
- Owners can remove any member (except project creator)
- Members can remove themselves
- Cannot remove the original project creator

---

## Invitations API

### List My Invitations

Get all pending invitations for the current user.

```bash
GET <ip-address>/api/v1/invitations
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "token": "AbCdEf123456789...",
    "project": {
      "id": "uuid",
      "name": "Website Redesign",
      "description": "Complete overhaul of company website"
    },
    "inviter": {
      "id": "uuid",
      "full_name": "AI Agent",
      "email": "agent@example.com"
    },
    "role": "member",
    "created_at": "2026-01-28T14:00:00Z",
    "expires_at": "2026-02-04T14:00:00Z"
  }
]
```

### Accept Invitation

```bash
POST <ip-address>/api/v1/invitations/{token}/accept
Content-Type: application/json
X-API-Key: <api-key>
```

**Response:** `200 OK`
```json
{
  "project_id": "uuid",
  "message": "Invitation accepted successfully"
}
```

**Note:** 
- Invitation must match your email address
- Invitation must not be expired
- You can only accept invitations once

### Decline Invitation

```bash
DELETE <ip-address>/api/v1/invitations/{token}
X-API-Key: <api-key>
```

**Response:** `204 No Content`

---

## Error Handling

All errors return JSON with this format:

```json
{
  "detail": "Error message",
  "code": 400
}
```

**Common HTTP Status Codes:**
- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid API key
- `403 Forbidden` - No access to resource
- `404 Not Found` - Resource doesn't exist
- `422 Unprocessable Entity` - Validation error

---

## Best Practices for AI Agents

### Workflow Recommendations

1. **Status Changes:**
   - Use `PATCH /tasks/{id}/status` for atomic status updates
   - Only use `PUT /tasks/{id}` when updating multiple fields
   - Status changes auto-position tasks at end of column

2. **Check Before Creating:**
   - List existing projects before creating duplicates
   - Search tasks by title to avoid duplicates

3. **Pagination:**
   - Use `limit` and `offset` for large datasets
   - Default limits: 20 for projects, 100 for tasks/subtasks

4. **Task Organization:**
   - Start tasks in `backlog` status
   - Move to `todo` when ready to work
   - Move to `in_progress` when starting
   - Move to `done` when completed

5. **Subtask Management:**
   - Break complex tasks into subtasks
   - Mark subtasks as completed individually
   - Track progress with `completed_subtasks` / `total_subtasks`

6. **Delete Operations:**
   - Projects and tasks: Soft deleted (recoverable)
   - Subtasks: Hard deleted (permanent)

7. **Team Collaboration:**
   - Invite members by email (owners only)
   - Assign tasks to specific team members
   - List assignees before assigning tasks
   - Accept invitations before accessing shared projects

### Example AI Agent Workflow

```
1. List projects → Find or create target project
2. Create task in project with status="backlog"
3. Add subtasks for task breakdown
4. Update task status to "todo" when ready
5. Update task status to "in_progress" when starting
6. Mark subtasks as completed incrementally
7. Update task status to "done" when all subtasks done
8. Track project progress via task_count / done_count
```

### Common Patterns

**Create a complete task with subtasks:**
```bash
# 1. Create task
POST /api/v1/projects/{project_id}/tasks
{"title": "Implement feature X", "status": "todo", "priority": "high"}

# 2. Add subtasks
POST /api/v1/tasks/{task_id}/subtasks
{"title": "Write tests"}

POST /api/v1/tasks/{task_id}/subtasks
{"title": "Implement logic"}

POST /api/v1/tasks/{task_id}/subtasks
{"title": "Update docs"}
```

**Track and update progress:**
```bash
# 1. Get task with subtasks
GET /api/v1/tasks/{task_id}

# 2. Mark subtask complete
PATCH /api/v1/subtasks/{subtask_id}
{"is_completed": true}

# 3. Move task to next status when done
PATCH /api/v1/tasks/{task_id}/status
{"status": "done"}
```

**Invite and assign team members:**
```bash
# 1. Invite a team member
POST /api/v1/projects/{project_id}/members
{"email": "teammate@example.com", "role": "member"}

# 2. Get list of assignable users
GET /api/v1/projects/{project_id}/assignees

# 3. Create task and assign to member
POST /api/v1/projects/{project_id}/tasks
{"title": "Review code", "assignee_id": "{user_id}", "priority": "high"}

# 4. Reassign task to different member
PUT /api/v1/tasks/{task_id}
{"assignee_id": "{other_user_id}"}
```

---

## When to Use This Skill

Use this skill when you need to:
- Manage your own tasks across multiple projects
- Collaborate with team members on shared projects
- Assign tasks to specific project members
- Break down complex work into organized subtasks
- Track progress through a backlog → todo → in_progress → done workflow
- Prioritize work with low/medium/high/urgent levels
- Query project statistics (task counts, completion rates)
- Integrate task management into automated workflows

**Do not use this skill for:**
- Real-time notifications (polling-based)
- Time tracking or scheduling (no time fields)
- File attachments (text-only tasks)
- Complex permission hierarchies (only owner/member roles)

---

## Quick Reference: cURL Examples

**List all projects:**
```bash
curl -H "X-API-Key: <api-key>" <ip-address>/api/v1/projects
```

**Create project:**
```bash
curl -X POST -H "X-API-Key: <api-key>" \
     -H "Content-Type: application/json" \
     -d '{"name": "My Project"}' \
     <ip-address>/api/v1/projects
```

**Create task:**
```bash
curl -X POST -H "X-API-Key: <api-key>" \
     -H "Content-Type: application/json" \
     -d '{"title": "My Task", "status": "todo", "priority": "high"}' \
     <ip-address>/api/v1/projects/{project_id}/tasks
```

**Update task status:**
```bash
curl -X PATCH -H "X-API-Key: <api-key>" \
     -H "Content-Type: application/json" \
     -d '{"status": "in_progress"}' \
     <ip-address>/api/v1/tasks/{task_id}/status
```

**Create subtask:**
```bash
curl -X POST -H "X-API-Key: <api-key>" \
     -H "Content-Type: application/json" \
     -d '{"title": "Subtask"}' \
     <ip-address>/api/v1/tasks/{task_id}/subtasks
```

**Mark subtask complete:**
```bash
curl -X PATCH -H "X-API-Key: <api-key>" \
     -H "Content-Type: application/json" \
     -d '{"is_completed": true}' \
     <ip-address>/api/v1/subtasks/{subtask_id}
```

**Invite team member:**
```bash
curl -X POST -H "X-API-Key: <api-key>" \
     -H "Content-Type: application/json" \
     -d '{"email": "teammate@example.com", "role": "member"}' \
     <ip-address>/api/v1/projects/{project_id}/members
```

**List my invitations:**
```bash
curl -H "X-API-Key: <api-key>" \
     <ip-address>/api/v1/invitations
```

**Accept invitation:**
```bash
curl -X POST -H "X-API-Key: <api-key>" \
     <ip-address>/api/v1/invitations/{token}/accept
```

---

## Additional Resources

- **API Documentation:** `<ip-address>/docs` (Swagger UI)
- **OpenAPI Spec:** `<ip-address>/openapi.json`
- **Health Check:** `<ip-address>/health`

---