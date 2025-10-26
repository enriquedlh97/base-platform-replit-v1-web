# Frontend - Scheduling Platform

This is a [Next.js 16](https://nextjs.org) frontend for an AI-powered scheduling and meeting booking platform. Built with TypeScript, Tailwind CSS, shadcn/ui, and TanStack Query.

## Architecture

- **Framework**: Next.js 16 with App Router
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS 4 with mobile-first responsive design
- **UI Components**: shadcn/ui with MCP integration
- **State Management**: TanStack Query for server state, React Context for UI state
- **Authentication**: Supabase Auth with cookie-based session management
- **API Client**: Auto-generated from OpenAPI spec with automatic auth token injection
- **Forms**: React Hook Form with Zod validation
- **Package Manager**: npm

## Prerequisites

- Node.js 20.19.2+ (use `nvm use` to switch)
- npm (comes with Node.js)
- Backend API running on `http://127.0.0.1:8000`
- Supabase local instance running on `http://127.0.0.1:54321`

## Getting Started

### Environment Setup

1. Copy environment variables:

   ```bash
   cp .env.example .env.local
   ```

2. Update `.env.local` with your configuration:
   ```env
   NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
   NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

### Development

Start the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

### Code Quality

```bash
# Format all files
npm run format

# Check formatting
npm run format:check

# Lint and auto-fix
npm run lint:fix

# Check linting
npm run lint:check

# Type check
npm run type-check
```

### API Client Generation

Regenerate the API client after backend schema changes:

```bash
npm run generate:api
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with providers
│   └── page.tsx           # Home page
├── components/
│   ├── providers/         # React providers (Query, Theme)
│   └── ui/               # shadcn/ui components
├── lib/
│   ├── api/              # Generated API client
│   ├── auth/             # Authentication hooks and actions
│   ├── forms/            # Form schemas and utilities
│   ├── supabase/         # Supabase client configuration
│   ├── workspace/        # Workspace hooks and utilities
│   ├── env.ts            # Environment validation
│   └── react-query.ts    # TanStack Query configuration
├── middleware.ts          # Route protection middleware
├── scripts/               # Development scripts
└── .cursor/                # Cursor IDE configuration
```

## Current State (Phase 2-3 Complete)

### ✅ Completed

**Code Quality & Development Tools:**

- ESLint + Prettier configured with TypeScript strict rules
- Pre-commit hooks via Python pre-commit tool
- Lint/format scripts for CI/CD

**State Management:**

- TanStack Query installed with caching defaults
- QueryProvider and ThemeProvider setup
- React Query Devtools in development mode

**Authentication System:**

- Auth hooks: `useAuth()`, `useUser()`, `useAuthStatus()`
- Server actions: `signIn()`, `signUp()`, `signOut()`
- Middleware for route protection
- Cookie-based session management

**API Integration:**

- Generated client with automatic auth token injection
- Type-safe API calls with backend models

### 🚧 In Progress

**Authentication Pages:**

- Login page with email/password
- Signup page with form validation

**Responsive Layout:**

- Dashboard layout with responsive sidebar
- Loading and error states

**Workspace Management:**

- Workspace hooks and CRUD operations
- Setup flow for new users
- Settings page

**Testing:**

- Jest + React Testing Library setup
- Example tests for components and hooks

### 📋 Planned

- Form patterns with React Hook Form + Zod
- Documentation updates
- Additional UI pages and components

## Shadcn UI Components (MCP Integration)

This project uses [shadcn/ui](https://ui.shadcn.com) components through the Model Context Protocol (MCP) server integration with Cursor.

### Setup

The MCP server is configured in `.cursor/mcp.json` and uses a custom wrapper script (`.cursor/shadcn-mcp.sh`) that:

1. Ensures Node.js 20 is used (required by the shadcn MCP server)
2. Runs the shadcn MCP server from the frontend directory

### MCP Server Configuration

```json
{
  "mcpServers": {
    "shadcn": {
      "command": "sh",
      "args": [".cursor/shadcn-mcp.sh"]
    }
  }
}
```

### Available Components

The project has access to 449+ shadcn/ui components via the MCP server, including:

- **UI Components**: accordion, alert, button, card, dialog, form, input, and more
- **Blocks**: Dashboard layouts, sidebars, login/signup forms, calendar variants
- **Charts**: Area, bar, line, pie/radar charts with various configurations
- **Examples**: Demo implementations and best practices
- **Hooks & Utils**: Custom React hooks and utility functions
- **Themes**: Multiple color theme variants

### Adding Components

Use the shadcn MCP tools through Cursor to:

- Browse available components
- View component implementations
- Get usage examples
- Add components to your project

### Node Version Requirement

The shadcn MCP server requires Node.js 20+. The wrapper script automatically switches to Node 20 using nvm.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
