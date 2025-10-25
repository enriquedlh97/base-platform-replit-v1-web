# Backend - FastAPI Application

This is the **unified backend** for the Base Platform cross-platform monorepo. It provides a single API layer that serves both the web (Next.js) and mobile (Expo) frontends, with a unified database architecture using Supabase for services and Alembic for schema management.

## Requirements

* [Docker](https://www.docker.com/).
* [uv](https://docs.astral.sh/uv/) for Python package and environment management.

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

To test the backend run:

```console
$ bash ./scripts/test.sh
```

The tests run with Pytest, modify and add tests to `./backend/app/tests/`.

If you use GitHub Actions the tests will run automatically.

To test manually a specific test, start the unified stack from the root directory:
```bash
docker compose watch
```
or with
```
docker compose up db adminer prestart backend --watch
```

Then execute the specific test, (-s shows all logs and print statements):
```bash
docker compose exec backend \
  pytest app/tests/test_deps.py::test_jit_user_creation -s
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

**Note**: The database connection is configured to use Supabase. Make sure your Supabase services are running (`cd supabase && nvm use && yarn supa start`) before running migrations.

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
- **Note**: Make sure your Supabase services are running (`cd supabase && yarn supa start`) before seeding
