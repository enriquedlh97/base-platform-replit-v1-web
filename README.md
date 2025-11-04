# Platform - AI Scheduling Assistant

A scheduling-first platform where freelancers and consulting businesses can spin up AI agents that answer questions and book meetings via Calendly.

## 🚀 Project Status

**Current Phase**: ✅ MVP Foundation - Complete! 🎉
**Architecture**: ✅ Established
**Backend**: ✅ Ready (FastAPI + SQLModel + Supabase)
**Frontend**: ✅ MVP Complete (Next.js 16 + TypeScript + shadcn/ui)
**Database**: ✅ Ready (PostgreSQL via Supabase)
**Authentication**: ✅ Complete (Supabase Auth + SSR)

### ✅ Phase 1: Backend Foundation (Jan 2025)
- **5 New Database Models**: Workspace, WorkspaceService, SchedulingConnector, Conversation, ConversationMessage
- **Extended User Model**: Business profile fields (name, tagline, bio, contact info)
- **5 API Route Modules**: Complete CRUD operations for all new entities
- **Database Migration**: Successfully applied with proper constraints and relationships
- **Test Suite**: 18 new tests added, all 79 tests passing
- **Code Quality**: Clean linting and comprehensive documentation

### ✅ Phase 2: Frontend MVP (Oct 2025)
- **Authentication System**: Login/signup pages with Supabase SSR integration
- **Knowledge Base**: Default landing page with unlimited text editor for business information (now includes a minimal Calendly link input saved as a SchedulingConnector)
- **Dashboard**: Responsive layout with shadcn/ui sidebar component
- **Public Chat (Phase 1 shell)**: Public page at `/u/{workspace_handle}/chat` with polling-based chat UI. Sidebar includes a "Public Chat" item for quick access (opens in a new tab).
- **Workspace Management**: Auto-created on first access, settings page with full CRUD
- **API Integration**: Type-safe client with automatic auth token injection
- **Landing Page**: Marketing content with auto-redirect to knowledge base for authenticated users
- **Development Tools**: ESLint, Prettier, pre-commit hooks, npm migration

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI with SQLModel for database models
- **Database**: PostgreSQL via Supabase (schema managed through Alembic migrations)
- **Authentication**: Supabase Auth with JWT validation (password, Google, Apple OAuth)
- **API**: RESTful endpoints with automatic OpenAPI schema generation
- **Development**: Hot reload, comprehensive testing, linting

### Frontend
- **Framework**: Next.js 16 with App Router and TypeScript
- **UI**: shadcn/ui components with Tailwind CSS 4
- **State Management**: TanStack Query (React Query) for server state
- **Forms**: React Hook Form with Zod validation
- **Authentication**: Supabase SSR with cookie-based sessions
- **API Client**: Auto-generated TypeScript client with automatic auth injection
- **Type Safety**: End-to-end type safety from backend to frontend

### Infrastructure
- **Supabase**: Authentication, Database, Storage services
- **Docker**: Containerized development environment
- **Development Tools**: VS Code debugging, test coverage, pre-commit hooks

## 🚦 Quick Start

### Prerequisites
- Node.js 20.19.2+ (use nvm: `nvm use`)
- npm (comes with Node.js)
- Python 3.12+ and uv (for backend)
- Docker and Docker Compose (for Supabase)
- pre-commit (for code quality hooks): `pip install pre-commit` or `brew install pre-commit`

### Development Setup

**First-time setup:**

1. **Install pre-commit hooks** (required):
   ```bash
   # Install root-level hooks
   pre-commit install

   # Install frontend hooks (run after npm install)
   cd frontend
   npm install  # Automatically sets up Husky via "prepare" script
   ```

2. **Start Supabase** (database, auth, storage)
   ```bash
   cd supabase
   nvm use && npm start
   ```

3. **Start Backend** (in another terminal)
   ```bash
   cd backend
   uv sync                    # Install dependencies
   source .venv/bin/activate  # Activate virtual environment
   bash scripts/prestart.sh   # Run migrations and initial setup (first time or after DB reset)
   fastapi run app/main.py --reload
   ```

4. **Start Frontend** (in another terminal)
   ```bash
   cd frontend
   nvm use                    # Ensure Node 20
   npm install                # First time only (also sets up Husky)
   npm run dev
   ```

5. **Access the Application**
   - Frontend: http://localhost:3000 (redirects to /knowledge-base after login)
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/api/v1/docs
   - Supabase Studio: http://localhost:54323

   After login, navigate to Knowledge Base and add your Calendly link at the top, then click Save.

**Note**: After signing up, you'll be redirected to the Knowledge Base page where you can immediately start adding business information. Workspaces are automatically created on first access.

6. **Generate API Client** (when backend schema changes)
   ```bash
   ./scripts/generate-api-client.sh
   ```

## 📁 Project Structure

```
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # API routes and dependencies
│   │   ├── core/        # Configuration and services
│   │   ├── models.py    # SQLModel database models
│   │   └── tests/       # Comprehensive test suite
│   └── scripts/         # Development utilities
├── frontend/            # Next.js 16 application
│   ├── app/            # App Router pages and layouts
│   │   ├── (auth)/     # Authentication pages (login, signup)
│   │   └── (dashboard)/ # Protected dashboard pages
│   ├── components/     # UI components (shadcn/ui)
│   ├── lib/           # Utilities and integrations
│   │   ├── api/       # Generated API client
│   │   ├── auth/      # Authentication hooks and actions
│   │   └── supabase/  # Supabase clients (browser & server)
│   └── scripts/       # Development utilities
├── supabase/          # Database and auth services
└── scripts/           # Project utilities
```

## 🔄 Development Workflow

### Initial Setup

**1. Install Pre-commit Hooks** (required before first commit)

This ensures all code quality checks run automatically on each commit:

```bash
# Install root-level pre-commit hooks (runs checks for both frontend and backend)
pre-commit install

# Install frontend Husky hooks (runs frontend-specific checks)
cd frontend
npm install  # This automatically runs the "prepare" script which sets up Husky
```

### Daily Development Workflow

**Before committing code, always run these checks:**

**1. Run Backend Scripts** (from `backend/` directory):
```bash
cd backend
source .venv/bin/activate  # If not already activated

# Format code
bash scripts/format.sh

# Lint code
bash scripts/lint.sh

# Run tests
bash scripts/test.sh
```

**2. Run Frontend Scripts** (from `frontend/` directory):
```bash
cd frontend
nvm use  # Ensure correct Node version

# Format code
bash scripts/format.sh

# Lint and type-check
bash scripts/lint.sh

# Run tests (if available)
bash scripts/test.sh
```

**3. Verify Frontend Build** (critical before committing):
```bash
cd frontend
nvm use
npm run build
```

**Fix any build errors before committing.** The build must complete successfully without errors.

**4. Commit Your Changes**:
```bash
git add .
git commit -m "your commit message"
```

The pre-commit hooks will automatically run:
- Backend: Ruff linting and formatting
- Frontend: ESLint, Prettier, and TypeScript type checking
- Root: YAML/TOML validation, trailing whitespace checks

If any checks fail, fix the issues and commit again.

### Database Changes Workflow

1. **Make Changes**: Modify models in `backend/app/models.py`
2. **Create Migration**: `alembic revision --autogenerate -m "description"`
3. **Apply Migration**: Run `bash scripts/prestart.sh` (which runs `alembic upgrade head`) or manually: `alembic upgrade head`
4. **Generate API Client**: `./scripts/generate-api-client.sh`
5. **Run All Scripts** (as described above)
6. **Verify Frontend Build**: `cd frontend && npm run build`
7. **Commit**: Pre-commit hooks will run automatically

**Note**: After resetting the database (e.g., `npm run reset` in supabase), always run `bash scripts/prestart.sh` to recreate tables and apply migrations.

## 📋 Current Implementation Plan

### ✅ Completed
- Core authentication system (Supabase)
- Basic user management
- Database schema and migrations
- API client generation pipeline
- Development environment setup
- **Phase 1: Core Data Models & Authentication** 🎉
  - Workspace management with unique handles
  - Business service catalog system
  - Scheduling connector configuration
  - Conversation and message tracking
  - Extended user business profiles
- **Phase 2: Knowledge Base Feature** 🎉
  - Knowledge base editor as default landing page
  - Unlimited text input for business information
  - Auto-creation of workspaces on first access
  - Streamlined onboarding (no setup wizard required)

### 🔄 Upcoming Phases (Phase 3+)
- **Services Management**: CRUD for workspace services
- **Scheduling Connectors**: Full connectors management UI and provider-specific flows (Calendly MVP link input already available in Knowledge Base)
- **Public Chat Streaming + Agent**: Upgrade to streaming (SSE) and LLM-powered agent responses
- **Agent System**: AI-powered conversation handling
- **Conversation History**: View and manage past interactions
- **Testing**: Jest + React Testing Library setup

## 🛠️ Key Commands

### Development Servers

```bash
# Supabase (database, auth, storage)
cd supabase && nvm use && npm start

# Backend API server (run prestart.sh first after DB reset)
cd backend && source .venv/bin/activate && bash scripts/prestart.sh && fastapi run app/main.py --reload

# Frontend dev server
cd frontend && nvm use && npm run dev
```

### Code Quality Checks

```bash
# Backend scripts (run all before committing)
cd backend && source .venv/bin/activate
bash scripts/format.sh    # Format Python code
bash scripts/lint.sh      # Lint and type-check
bash scripts/test.sh      # Run tests with coverage

# Frontend scripts (run all before committing)
cd frontend && nvm use
bash scripts/format.sh    # Format code
bash scripts/lint.sh      # Lint and type-check
bash scripts/test.sh      # Run tests

# Frontend build verification (critical before committing)
cd frontend && nvm use && npm run build
```

### Utilities

```bash
# Generate API client (after backend schema changes)
./scripts/generate-api-client.sh

# Install pre-commit hooks (first time setup)
pre-commit install
cd frontend && npm install  # Sets up Husky automatically
```

## 📚 Resources

- [Frontend README](frontend/README.md) - Frontend architecture and development guide
- [Backend README](backend/README.md) - Backend API documentation
- Public chat URL shape: `/u/{workspace_handle}/chat`
- [Supabase README](supabase/README.md) - Database and auth setup
- [API Documentation](http://localhost:8000/api/v1/docs) - Auto-generated OpenAPI docs
- [Frontend App](http://localhost:3000) - Next.js application
- [Supabase Studio](http://localhost:54323) - Database management UI

## 🤝 Contributing

1. **Follow existing patterns** in the codebase
2. **Run all scripts before committing**:
   - Backend: `bash scripts/format.sh`, `bash scripts/lint.sh`, `bash scripts/test.sh`
   - Frontend: `bash scripts/format.sh`, `bash scripts/lint.sh`, `bash scripts/test.sh`
   - **Frontend build must succeed**: `npm run build`
3. **Install pre-commit hooks** (first time only):
   - `pre-commit install` (root level)
   - `cd frontend && npm install` (sets up Husky)
4. **Write tests** for new functionality
5. **Update documentation** as needed
6. **Use conventional commits**
7. **Ensure all pre-commit checks pass** before submitting

## 📊 Current Statistics

- **Database Models**: 10 total (including knowledge_base field)
- **API Endpoints**: 15+ CRUD routes
- **Backend Tests**: 79 tests passing
- **Frontend Pages**: 6 pages (landing, login, signup, dashboard, knowledge-base, settings)
- **UI Components**: 15+ shadcn/ui components integrated
- **Code Quality**: ESLint + Prettier + pre-commit hooks
- **Type Safety**: Full end-to-end TypeScript coverage

## 🎯 Test Credentials

For local development:
```
Email: seeduser@example.com
Password: 123456
```

Run backend seed script if user doesn't exist:
```bash
cd backend && python scripts/seed_db.py
```

---

**Next Steps**: Phase 3 - Services management, connectors UI, and public chat interface.
