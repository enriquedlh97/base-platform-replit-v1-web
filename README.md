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
- **Dashboard**: Responsive layout with shadcn/ui sidebar component
- **Workspace Management**: Setup wizard and settings page with full CRUD
- **API Integration**: Type-safe client with automatic auth token injection
- **Landing Page**: Marketing content with auto-redirect for authenticated users
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

### Development Setup

1. **Start Supabase** (database, auth, storage)
   ```bash
   cd supabase
   nvm use && yarn start
   ```

2. **Start Backend** (in another terminal)
   ```bash
   cd backend
   uv sync                    # Install dependencies
   source .venv/bin/activate  # Activate virtual environment
   fastapi run app/main.py --reload
   ```

3. **Start Frontend** (in another terminal)
   ```bash
   cd frontend
   nvm use                    # Ensure Node 20
   npm install                # First time only
   npm run dev
   ```

4. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/api/v1/docs
   - Supabase Studio: http://localhost:54323

5. **Generate API Client** (when backend schema changes)
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

1. **Make Changes**: Modify models in `backend/app/models.py`
2. **Create Migration**: `alembic revision --autogenerate -m "description"`
3. **Apply Migration**: `alembic upgrade head`
4. **Run Tests**: `bash scripts/test.sh`
5. **Generate API Client**: `./scripts/generate-api-client.sh`
6. **Commit**: Changes are automatically reflected in development containers

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

### 🔄 Upcoming Phases (Phase 3+)
- **Services Management**: CRUD for workspace services
- **Scheduling Connectors**: Calendly integration UI
- **Public Chat Interface**: Customer-facing conversation widget
- **Agent System**: AI-powered conversation handling
- **Conversation History**: View and manage past interactions
- **Testing**: Jest + React Testing Library setup

## 🛠️ Key Commands

```bash
# Supabase (database, auth, storage)
cd supabase && nvm use && yarn start

# Backend API server
cd backend && source .venv/bin/activate && fastapi run app/main.py --reload

# Frontend dev server
cd frontend && nvm use && npm run dev

# Frontend linting and formatting
cd frontend && npm run lint
cd frontend && npm run format

# Backend tests with coverage
cd backend && bash scripts/test.sh

# Generate API client (after backend schema changes)
./scripts/generate-api-client.sh
```

## 📚 Resources

- [Frontend README](frontend/README.md) - Frontend architecture and development guide
- [Backend README](backend/README.md) - Backend API documentation
- [Supabase README](supabase/README.md) - Database and auth setup
- [API Documentation](http://localhost:8000/api/v1/docs) - Auto-generated OpenAPI docs
- [Frontend App](http://localhost:3000) - Next.js application
- [Supabase Studio](http://localhost:54323) - Database management UI

## 🤝 Contributing

1. Follow existing patterns in the codebase
2. Write tests for new functionality
3. Update documentation as needed
4. Use conventional commits
5. Ensure all tests pass before submitting

## 📊 Current Statistics

- **Database Models**: 10 total
- **API Endpoints**: 15+ CRUD routes
- **Backend Tests**: 79 tests passing
- **Frontend Pages**: 6 pages (landing, login, signup, dashboard, setup, settings)
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
