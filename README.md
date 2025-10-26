# Platform - AI Scheduling Assistant

A scheduling-first platform where freelancers and consulting businesses can spin up AI agents that answer questions and book meetings via Calendly.

## 🚀 Project Status

**Current Phase**: Foundation (Phase 1) - Core Data Models & Authentication
**Architecture**: ✅ Established
**Backend**: ✅ Ready (FastAPI + SQLModel + Supabase)
**Frontend**: ✅ Ready (TypeScript + Generated API Client)
**Database**: ✅ Ready (PostgreSQL via Supabase)

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI with SQLModel for database models
- **Database**: PostgreSQL via Supabase (schema managed through Alembic migrations)
- **Authentication**: Supabase Auth with JWT validation (password, Google, Apple OAuth)
- **API**: RESTful endpoints with automatic OpenAPI schema generation
- **Development**: Hot reload, comprehensive testing, linting

### Frontend
- **Client**: Auto-generated TypeScript API client from OpenAPI schemas
- **Authentication**: Supabase client integration
- **Type Safety**: End-to-end type safety from backend to frontend

### Infrastructure
- **Supabase**: Authentication, Database, Storage services
- **Docker**: Containerized development environment
- **Development Tools**: VS Code debugging, test coverage, pre-commit hooks

## 🚦 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js and npm (for Supabase)
- Python 3.12+ and uv (for backend)

### Development Setup

1. **Start Services**
   ```bash
   # Start Supabase (database, auth, storage)
   cd supabase && nvm use && yarn start

   # In another terminal, start backend and database
   docker compose watch
   ```

2. **Backend Development**
   ```bash
   cd backend
   uv sync                    # Install dependencies
   source .venv/bin/activate  # Activate virtual environment
   ```

3. **Generate API Client** (when backend changes)
   ```bash
   ./scripts/generate-api-client.sh
   ```

4. **Run Tests**
   ```bash
   # Backend tests
   cd backend && bash scripts/test.sh

   # Frontend setup (when ready)
   cd frontend && npm install
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
├── frontend/            # TypeScript frontend (in development)
│   └── sample_client/   # Generated API client example
├── supabase/           # Database and auth services
└── scripts/            # Project utilities
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

### 🚧 In Progress (Phase 1)
- Workspace model and relationships
- Scheduling services model
- Scheduling connector model
- Conversation tracking models
- Extended user profiles

### 🔄 Upcoming Phases
- Setup wizard (onboarding flow)
- Dashboard (workspace management)
- Public chat interface
- Scheduling integration (Calendly)
- Agent/conversation system

## 🛠️ Key Commands

```bash
# Start full development stack
docker compose watch

# Backend only
cd backend && source .venv/bin/activate && fastapi run app/main.py --reload

# Run all tests with coverage
cd backend && bash scripts/test.sh

# Generate API client
./scripts/generate-api-client.sh

# Supabase services
cd supabase && yarn start
```

## 📚 Resources

- [Backend README](backend/README.md) - Detailed backend documentation
- [Supabase README](supabase/README.md) - Database and auth setup
- [API Documentation](http://localhost:8000/api/v1/docs) - Auto-generated when running

## 🤝 Contributing

1. Follow existing patterns in the codebase
2. Write tests for new functionality
3. Update documentation as needed
4. Use conventional commits
5. Ensure all tests pass before submitting

---

**Next**: Phase 1 implementation - Core data models for workspaces, services, and scheduling connectors.
