# Project Manager

REST API for personal task management and team projects with role-based access control.

---

## Features
### Core Functionality
- **Personal Tasks** - Manage your individual tasks with full CRUD operations
- **Team Projects** - Collaborate with role-based access control (Owner/Admin/Member)
- **Advanced Filtering** - Filter and sort by status, priority, deadline, assignee, and more
### Open Tasks System
- **Self-Assignment** - Any project member can pick up open tasks
- **Flexible Workflow** - Members can unassign themselves from open tasks anytime
- **Task Unassignment** - Admin+ can unassign any open task
- **Two Task Types** - Default (assigned) and Open (self-service) tasks
### Role-Based Access Control
- **Hierarchical Permissions** - Owner > Admin > Member with granular access control
- **Role Management** - Users can only assign roles below their own level
- **Project Autonomy** - Members can leave projects voluntarily (except owners)
### Technical Excellence
- **JWT Authentication** - Secure access and refresh token system
- **97% Test Coverage** - 430 comprehensive tests (unit + integration)
- **Clean Architecture** - Repository and Service Layer patterns
- **Docker Ready** - One command deployment with docker-compose

---
## Tech Stack

- **Backend**: FastAPI 0.120 + SQLAlchemy 2.0 (async) + Pydantic
- **Database**: PostgreSQL 18.1 + AsyncPG
- **Auth**: JWT + bcrypt
- **Testing**: Pytest + coverage (430 tests, 97%)
- **Tools**: Docker, Alembic, UV

---

## Architecture

```
modules/
├── auth/           # Registration, login
├── users/          # User profile
├── personal_tasks/ # Personal tasks
├── projects/       # Projects
├── project_members/# Project members
└── project_tasks/  # Project tasks
    ├── model.py       # SQLAlchemy models
    ├── repository.py  # Database operations
    ├── service.py     # Business logic
    └── schemas.py     # Pydantic validation
```

Patterns: Repository, Service Layer, Dependency Injection

---

## Prerequisites

- Docker & Docker Compose
- (Optional) Python 3.13+ for local development

---

## Quick Start

### 1. Clone repository
```bash
git clone https://github.com/ziparh/Project-Manager.git
cd Project-Manager
```

### 2. Create .env file
```bash
cp .env.example .env
```

`.env.example` content:
```env
# DATABASE
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=project_manager
POSTGRES_TEST_DB=project_manager_test

APP_CONFIG__DB__URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}"
APP_CONFIG__DB__TEST_DB_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@test_db:5432/${POSTGRES_TEST_DB}"

# JWT
APP_CONFIG__JWT__SECRET_KEY=your-secret-key
```

### 3. Start with Docker
```bash
docker compose up --build -d
```

API available at: **http://localhost:8000**
Documentation: **http://localhost:8000/docs**

### 4. Run tests
```bash
docker compose exec app uv run pytest --cov=src
```

### 5. Stop project
```bash
docker compose down -v
```

---

## API Endpoints

### Authentication
```
POST   /api/v1/auth/register  - Register new user
POST   /api/v1/auth/login     - Login (get tokens)
POST   /api/v1/auth/refresh   - Refresh access token
```

### Users
```
GET    /api/v1/users/me       - Get current user
PATCH  /api/v1/users/me       - Update current user
DELETE /api/v1/users/me       - Delete current user
```

### Personal Tasks
```
GET    /api/v1/personal_tasks           - Get task list (with filters)
POST   /api/v1/personal_tasks           - Create task
GET    /api/v1/personal_tasks/{id}      - Get task by id
PATCH  /api/v1/personal_tasks/{id}      - Update task
DELETE /api/v1/personal_tasks/{id}      - Delete task
```

**Query parameters for GET:**
- `status` - filter by status (todo, in_progress, done, cancelled)
- `priority` - filter by priority (low, medium, high, critical)
- `overdue` - filter overdue tasks (true/false)
- `search` - search in title or description
- `sort_by` - sort field (deadline, status, priority, created_at, updated_at)
- `order` - sort order (asc, desc)
- `page` - page number
- `size` - items per page

### Projects
```
GET    /api/v1/projects           - Get user's projects (with filters)
POST   /api/v1/projects           - Create project
GET    /api/v1/projects/{id}      - Get project by id (member+)
PATCH  /api/v1/projects/{id}      - Update project (admin+)
DELETE /api/v1/projects/{id}      - Delete project (owner only)
```

**Query parameters for GET:**
- `creator_id` - filter by project creator id
- `status` - filter by status (planning, active, on_hold, completed, cancelled)
- `role` - filter by your role in project (owner, admin, member)
- `overdue` - filter overdue tasks (true/false)
- `search` - search in title, description or creator name
- `sort_by` - sort field (deadline, status, created_at, updated_at)
- `order` - sort order (asc, desc)
- `page` - page number
- `size` - items per page

### Project Members
```
GET    /api/v1/projects/{project_id}/members           - Get all members (member+)
POST   /api/v1/projects/{project_id}/members           - Add member (admin+)
PATCH  /api/v1/projects/{project_id}/members/{user_id} - Update member role (admin+)
DELETE /api/v1/projects/{project_id}/members/{user_id} - Remove member
```

**Query parameters for GET:**
- `role` - filter by role (owner, admin, member)
- `sort_by` - sort field (role, joined_at)
- `order` - sort order (asc, desc)
- `page` - page number
- `size` - items per page

### Project Tasks
```
GET    /api/v1/projects/{project_id}/tasks                - Get all project tasks (member+)
POST   /api/v1/projects/{project_id}/tasks                - Create task (admin+)
GET    /api/v1/projects/{project_id}/tasks/{task_id}      - Get task by id (member+)
PATCH  /api/v1/projects/{project_id}/tasks/{task_id}      - Update task (admin+)
DELETE /api/v1/projects/{project_id}/tasks/{task_id}      - Delete task (admin+)

POST   /api/v1/projects/{project_id}/tasks/{task_id}/assign   - Assign open task to yourself (member+)
DELETE /api/v1/projects/{project_id}/tasks/{task_id}/assign   - Unassign open task (member+)
```

**Query parameters for GET:**
- `type` - filter by type (default, open)
- `assignee_id` - filter by assignee id
- `created_by_id` - filter by creator id
- `status` - filter by status
- `priority` - filter by priority
- `overdue` - filter overdue tasks (true/false)
- `search` - search in title, description, assignee name or creator name
- `sort_by` - sort field (deadline, status, priority, assigned_at, created_at, updated_at)
- `order` - sort order (asc, desc)
- `page` - page number
- `size` - items per page

**Extra:**
- admin+ can unassign open tasks to other users
- member can only unassign own open task

Full interactive documentation: `/docs`

---

## Testing

**97% coverage | 430 tests**

```bash
# All tests
docker compose exec app uv run pytest

# With coverage report
docker compose exec app uv run pytest --cov=src --cov-report=html

# Unit tests only (no database)
docker compose exec app uv run pytest -m "unit"

# Integration tests only
docker compose exec app uv run pytest -m "integration"
```

**Structure:**
- `tests/unit/` - unit tests (no database)
- `tests/integrations/api/` - endpoint tests
- `tests/integrations/repositories/` - database tests
- `tests/fixtures/` - fixtures
- `tests/factories/` - factories

---

## Database Migrations

```bash
# Create migration
docker compose exec app uv run alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec app uv run alembic upgrade head

# Rollback
docker compose exec app uv run alembic downgrade -1
```

---

## Author

**GitHub**: [@ziparh](https://github.com/ziparh)
