# Backend - FastAPI Application

This is the **unified backend** for the Base Platform scheduling assistant platform. It provides a single API layer that serves both web and mobile frontends, with a unified database architecture using Supabase for services and Alembic for schema management.

## Current Status

**Phase 1: Core Models & Authentication Foundation** ✅ **COMPLETE**

**Phase 2 (MVP): Public Chat Agent Streaming** ✅ **COMPLETE**

- Added SSE endpoint to stream assistant replies:
  - `GET /api/v1/public/conversations/{conversation_id}/stream` (text/event-stream)
- Minimal in-process agent using Groq via `ChatGroq` (aligned with ava best practices):
  - Requires `GROQ_API_KEY` in backend environment
  - Defaults: `TEXT_MODEL_NAME=llama-3.3-70b-versatile`, `MODEL_TEMPERATURE=0.7`
- On `message_end`, the assistant’s full reply is persisted to `conversation_messages`.
- Event shapes: `message_start`, `delta`, `message_end`, `tool_call`, `tool_result`, `error`.

All Phase 1 features are implemented and tested:
- ✅ Workspace models and CRUD operations
- ✅ Workspace services management
- ✅ Scheduling connectors with activation/deactivation
- ✅ Conversation and message tracking
- ✅ Extended user profile fields
- ✅ Database migrations applied
- ✅ Comprehensive test suite (79 tests passing)
- ✅ Code linting and formatting

## Architecture Overview

The backend follows a clean architecture pattern with clear separation of concerns:

### Models (`app/models.py`)
- **User**: Base user model with extended business profile fields (business_name, tagline, bio, phone, website, social_links, setup_completed)
- **Workspace**: One workspace per user, globally unique handle, tone and timezone configuration
  - **knowledge_base**: Unlimited text field for storing business information used by AI agent
- **WorkspaceService**: Services offered by the workspace (consultation, audit, workshop, etc.)
- **SchedulingConnector**: External scheduling integration configs (Calendly, Square, etc.)
- **Conversation**: Visitor conversations with the AI agent
- **ConversationMessage**: Individual messages within conversations

### API Routes
- `/api/v1/workspaces/*` - Workspace management (includes knowledge_base field)
  - `GET /workspaces/me` - Auto-creates workspace if missing
  - `PATCH /workspaces/{id}` - Updates workspace including knowledge_base
- `/api/v1/workspace-services/*` - Service management
- `/api/v1/connectors/*` - Connector management
  - `GET /connectors/workspaces/{workspace_id}` - List connectors for workspace
  - `POST /connectors/workspaces/{workspace_id}` - Create connector
  - `PATCH /connectors/{connector_id}` - Update connector
  - `DELETE /connectors/{connector_id}` - Delete connector
- `/api/v1/conversations/*` - Conversation tracking
- `/api/v1/messages/*` - Message management
- `/api/v1/public/*` - Public, anonymous chat endpoints
  - `POST /public/conversations` → Create conversation by `workspace_handle`
  - `POST /public/conversations/{conversation_id}/messages` → Post user message
  - `GET /public/conversations/{conversation_id}/messages?since&limit` → List messages (polling/sync)
  - `GET /public/conversations/{conversation_id}/stream` → Stream assistant reply (SSE)

## Key Design Decisions

### One Workspace Per User
- Enforced via unique database constraint on `workspace.owner_id`
- Simplifies MVP architecture
- **Auto-creation**: Workspaces are automatically created when accessing `/api/v1/workspaces/me` if none exists
  - Generates unique handle from user email
  - Sets sensible defaults (type: individual, tone: professional, timezone: UTC)
  - Eliminates need for setup wizard
- Future: Helper users can be added via separate table

### Globally Unique Handles
- Each workspace has a URL-friendly `handle` (e.g., "acme-consulting")
- Validated with regex: `^[a-z0-9]+(?:-[a-z0-9]+)*$`
- Used for public-facing workspace URLs

### Flexible Connector Configuration
- Connector configs stored as JSON for extensibility
- Only one active connector per workspace at a time
- Supports multiple connector types (Calendly, Square, AgendaPro)
  - For Calendly MVP, the frontend Knowledge Base page saves a connector with `type: "calendly"` and `config: { "link": "https://calendly.com/<username>" }`.

### Conversation Tracking
- Messages support multiple channels (web, instagram, whatsapp, sms, messenger, chatgpt, phone)
- Tags system for organization and filtering
- Tracks time saved for analytics

## Requirements

* [Docker](https://www.docker.com/).
* [uv](https://docs.astral.sh/uv/) for Python package and environment management.
* [Supabase](https://supabase.com) - Local development requires Supabase services running
* Groq API key in backend environment: `GROQ_API_KEY`

## Quick Start

### 1. Start Supabase Services
```bash
cd supabase
nvm use && yarn start
```

### 2. Start Backend (in separate terminal)
```bash
cd backend
source .venv/bin/activate
bash scripts/prestart.sh  # Run migrations and initial setup (required after DB reset)
export GROQ_API_KEY=sk_...            # required for the agent
export TEXT_MODEL_NAME=llama-3.3-70b-versatile   # optional (default)
export MODEL_TEMPERATURE=0.7                    # optional (default)
fastapi run app/main.py --reload
```

**Note**: The `prestart.sh` script:
- Waits for database to be ready
- Runs Alembic migrations (`alembic upgrade head`)
- Creates initial data (superuser, etc.)

Always run this after resetting the Supabase database.

### 3. Verify
- API available at: http://localhost:8000
- API docs at: http://localhost:8000/api/v1/docs
- Stream test (replace with a real `conversation_id`):
  ```bash
  curl -N -H 'Accept: text/event-stream' \
    http://127.0.0.1:8000/api/v1/public/conversations/<conversation_id>/stream
  ```
- Supabase dashboard at: http://localhost:54323

## Development Workflow

### Adding New Models
1. Add SQLModel classes to `app/models.py`
2. Create migration: `alembic revision --autogenerate -m "description"`
3. Apply migration: `alembic upgrade head`
4. Add routes in `app/api/routes/`
5. Write tests in `app/tests/`
6. Run tests: `bash scripts/test.sh`
7. Run linting: `bash scripts/lint.sh`

### Common Database Operations

**Check database tables:**
```python
from app.core.db import engine
from sqlalchemy import inspect
inspector = inspect(engine)
print(sorted(inspector.get_table_names()))
```

**Common Tables:**
- `user` - Base user accounts
- `workspaces` - User workspaces (Phase 1)
- `workspace_services` - Services offered (Phase 1)
- `scheduling_connectors` - External integrations (Phase 1)
- `conversations` - Visitor conversations (Phase 1)
- `conversation_messages` - Chat messages (Phase 1)
- Plus legacy tables: `item`, `client`, `appointment`, `service`, `provider`, `event`, `post`, `project`, etc.

## Docker Compose

Start the local development environment with Docker Compose following the guide in [../development.md](../development.md).

**Note**: The backend is part of a unified stack that includes the frontend and Supabase services. Use `docker compose watch` from the root directory to start everything together.

## General Workflow

By default, the dependencies are managed with [uv](https://docs.astral.sh/uv/), go there and install it.

From `./backend/` you can install all the dependencies with:

```console
$ uv sync
```

Then you can activate the virtual environment with:

```console
$ source .venv/bin/activate
```

Make sure your editor is using the correct Python virtual environment, with the interpreter at `backend/.venv/bin/python`.

Modify or add SQLModel models for data and SQL tables in `./backend/app/models.py`, API endpoints in `./backend/app/api/`, CRUD (Create, Read, Update, Delete) utils in `./backend/app/crud.py`.

## VS Code

There are already configurations in place to run the backend through the VS Code debugger, so that you can use breakpoints, pause and explore variables, etc.

The setup is also already configured so you can run the tests through the VS Code Python tests tab.

## Docker Compose Override

During development, you can change Docker Compose settings that will only affect the local development environment in the file `docker-compose.override.yml`.

The changes to that file only affect the local development environment, not the production environment. So, you can add "temporary" changes that help the development workflow.

For example, the directory with the backend code is synchronized in the Docker container, copying the code you change live to the directory inside the container. That allows you to test your changes right away, without having to build the Docker image again. It should only be done during development, for production, you should build the Docker image with a recent version of the backend code. But during development, it allows you to iterate very fast.

There is also a command override that runs `fastapi run --reload` instead of the default `fastapi run`. It starts a single server process (instead of multiple, as would be for production) and reloads the process whenever the code changes. Have in mind that if you have a syntax error and save the Python file, it will break and exit, and the container will stop. After that, you can restart the container by fixing the error and running again:

```console
$ docker compose watch
```

There is also a commented out `command` override, you can uncomment it and comment the default one. It makes the backend container run a process that does "nothing", but keeps the container alive. That allows you to get inside your running container and execute commands inside, for example a Python interpreter to test installed dependencies, or start the development server that reloads when it detects changes.

To get inside the container with a `bash` session you can start the stack with:

```console
$ docker compose watch
```

and then in another terminal, `exec` inside the running container:

```console
$ docker compose exec backend bash
```

You should see an output like:

```console
root@7f2607af31c3:/app#
```

that means that you are in a `bash` session inside your container, as a `root` user, under the `/app` directory, this directory has another directory called "app" inside, that's where your code lives inside the container: `/app/app`.

There you can use the `fastapi run --reload` command to run the debug live reloading server.

```console
$ fastapi run --reload app/main.py
```

...it will look like:

```console
root@7f2607af31c3:/app# fastapi run --reload app/main.py
```

and then hit enter. That runs the live reloading server that auto reloads when it detects code changes.

Nevertheless, if it doesn't detect a change but a syntax error, it will just stop with an error. But as the container is still alive and you are in a Bash session, you can quickly restart it after fixing the error, running the same command ("up arrow" and "Enter").

...this previous detail is what makes it useful to have the container alive doing nothing and then, in a Bash session, make it run the live reload server.

## Backend tests

### Running All Tests
```bash
bash ./scripts/test.sh
```

This runs:
- All unit tests with pytest
- Coverage reporting
- Generates `htmlcov/index.html` for coverage analysis

**Current Test Status:** 82 tests passing, including:
- 10 workspace tests
- 5 workspace service tests
- 7 scheduling connector tests
- 8 conversation tests
- Plus all legacy tests
 - 3 public chat streaming tests (SSE: happy path, error, 404)

### Test Structure
Tests are organized in `app/tests/`:
- `app/tests/api/routes/` - API endpoint tests
- `app/tests/crud/` - Database operation tests
- `app/tests/utils/` - Test utilities and fixtures

**Fixtures Available:**
- `client: TestClient` - FastAPI test client
- `db: Session` - Database session with auto-rollback
- `superuser_token_headers` - Auth headers for superuser
- `normal_user_token_headers` - Auth headers for normal user

### Running Specific Tests

**Start Supabase first:**
```bash
cd supabase && nvm use && npm start
```

**Then in another terminal:**
```bash
cd backend
source .venv/bin/activate
pytest app/tests/api/routes/test_workspaces.py -v
```

### Docker-based Testing
```bash
# Start stack
docker compose watch

# Run specific test
docker compose exec backend pytest app/tests/api/routes/test_workspaces.py::test_create_workspace -v

# Run with logs
docker compose exec backend pytest app/tests/api/routes/test_workspaces.py::test_create_workspace -s
```

### Test running stack

If your stack is already up and you just want to run the tests, you can use:

```bash
docker compose exec backend bash scripts/tests-start.sh
```

That `/app/scripts/tests-start.sh` script just calls `pytest` after making sure that the rest of the stack is running. If you need to pass extra arguments to `pytest`, you can pass them to that command and they will be forwarded.

For example, to stop on first error:

```bash
docker compose exec backend bash scripts/tests-start.sh -x
```

### Test Coverage

When the tests are run, a file `htmlcov/index.html` is generated, you can open it in your browser to see the coverage of the tests.

## Migrations

**Important**: This project uses a **unified database architecture**:
### Recent Additive Changes

- `conversation_messages.idempotency_key` (nullable, indexed) added to support safe client retries.
- `GET /public/conversations/{conversation_id}/stream` SSE endpoint
- Minimal Groq-backed agent (reads `GROQ_API_KEY` from settings)

- **Supabase** handles authentication, storage, and database hosting
- **Alembic** manages all database schema migrations and schema changes
- **No local PostgreSQL service** - all database operations go through Supabase

As during local development your app directory is mounted as a volume inside the container, you can also run the migrations with `alembic` commands inside the container and the migration code will be in your app directory (instead of being only inside the container). So you can add it to your git repository.

Make sure you create a "revision" of your models and that you "upgrade" your database with that revision every time you change them. As this is what will update the tables in your database. Otherwise, your application will have errors.

* Start an interactive session in the backend container:

```console
$ docker compose exec backend bash
```

* Alembic is already configured to import your SQLModel models from `./backend/app/models.py`.

* After changing a model (for example, adding a column), inside the container, create a revision, e.g.:

```console
$ alembic revision --autogenerate -m "Add column last_name to User model"
```

* Commit to the git repository the files generated in the alembic directory.

* After creating the revision, run the migration in the database (this is what will actually change the database):

```console
$ alembic upgrade head
```

**Note**: The database connection is configured to use Supabase. Make sure your Supabase services are running (`cd supabase && nvm use && npm start`) before running migrations.

## Executing Commands Inside Docker

Since the backend runs in a Docker container, you can execute commands directly inside it. This is useful for running scripts, testing, and development tasks.

### Accessing the Container

```bash
# Start the unified stack
docker compose watch

# In another terminal, access the backend container
docker compose exec backend bash
```

You'll see a prompt like:
```bash
root@container-id:/app#
```

### Common Commands Inside the Container

Once inside the container, you can run various backend operations:

#### **Database Seeding**
```bash
# Inside the container
python scripts/seed_db.py
```

#### **Running Tests**
```bash
# Run all tests with coverage
bash scripts/test.sh

# Run tests with custom title
bash scripts/test.sh "Custom Coverage Title"

# Run specific test file
pytest app/tests/test_deps.py

# Run with verbose output
pytest -v
```

#### **Linting and Code Quality**
```bash
# Run linting checks
bash scripts/lint.sh

# Format code
bash scripts/format.sh
```

#### **Database Operations**
```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Check migration status
alembic current
```

#### **Development Server**
```bash
# Start development server with reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or using FastAPI CLI
fastapi run app/main.py --reload
```

### **Alternative: Direct Command Execution**

You can also run commands directly without entering the container:

```bash
# Run seeding
docker compose exec backend python scripts/seed_db.py

# Run tests
docker compose exec backend bash scripts/test.sh

# Run linting
docker compose exec backend bash scripts/lint.sh

# Run formatting
docker compose exec backend bash scripts/format.sh

# Run migrations
docker compose exec backend alembic upgrade head
```

This approach is useful for one-off commands or CI/CD scripts.

If you don't want to use migrations at all, uncomment the lines in the file at `./backend/app/core/db.py` that end in:

```python
SQLModel.metadata.create_all(engine)
```

and comment the line in the file `scripts/prestart.sh` that contains:

```console
$ alembic upgrade head
```

If you don't want to start with the default models and want to remove them / modify them, from the beginning, without having any previous revision, you can remove the revision files (`.py` Python files) under `./backend/app/alembic/versions/`. And then create a first migration as described above.

## Email Templates

The email templates are in `./backend/app/email-templates/`. Here, there are two directories: `build` and `src`. The `src` directory contains the source files that are used to build the final email templates. The `build` directory contains the final email templates that are used by the application.

Before continuing, ensure you have the [MJML extension](https://marketplace.visualstudio.com/items?itemName=attilabuti.vscode-mjml) installed in your VS Code.

Once you have the MJML extension installed, you can create a new email template in the `src` directory. After creating the new email template and with the `.mjml` file open in your editor, open the command palette with `Ctrl+Shift+P` and search for `MJML: Export to HTML`. This will convert the `.mjml` file to a `.html` file and now you can save it in the build directory.

## Seeding the Database

After running migrations, you can seed the database with initial data:

```bash
uv run python scripts/seed_db.py
```

- The script will insert sample data into your Supabase database
- It is safe to run multiple times; it will not create duplicates
- **Note**: Make sure your Supabase services are running (`cd supabase && nvm use && npm start`) before seeding

## Troubleshooting

### Database Connection Issues
**Error:** `connection is bad: connection to server at "127.0.0.1", port 54322 failed`

**Solution:** Make sure Supabase is running:
```bash
cd supabase
nvm use
yarn start
```

Check the output shows:
```
DB URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
```

### Migration Conflicts
**Error:** `Multiple head revisions are present`

**Solution:** Check migration heads:
```bash
alembic heads
```

Update the `down_revision` in your migration file to resolve conflicts.

### Type Errors
**Error:** `list[WorkspaceService](...)` - This syntax is incorrect

**Solution:** Use Python's `list()` constructor, not type annotation:
```python
# Wrong
services = list[WorkspaceService](session.exec(statement).all())

# Correct
services = list(session.exec(statement).all())
```

### Port Already in Use
**Error:** `Port 8000 is already in use`

**Solution:** Either stop the running process or change the port:
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8001 --reload
```

### Import Errors
**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:** Make sure you're in the right directory and environment:
```bash
cd backend
source .venv/bin/activate
python -m pytest  # Note: use python -m, not pytest directly
```

### Linting Issues
**Auto-fix:** Most linting issues can be auto-fixed:
```bash
ruff check --fix app
ruff format app
```

### Test Failures
**Common causes:**
1. Supabase not running - start it first
2. Database migrations not applied - run `alembic upgrade head`
3. Test database state - tests use auto-rollback, should be isolated

**Debug tests:**
```bash
# Run single test with output
pytest app/tests/api/routes/test_workspaces.py::test_create_workspace -v -s

# Run with debugging
pytest app/tests/api/routes/test_workspaces.py::test_create_workspace -v --pdb
```
