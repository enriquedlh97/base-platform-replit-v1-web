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
   NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
   NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

### Development

Start the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

#### Using the app

1. Log in or sign up
2. Navigate to Knowledge Base
3. Paste your Calendly URL at the top and click Save
4. Reload the page to confirm the link persists

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

Note: The public chat client normalizes the base URL to include `/api/v1` if omitted. You can set `NEXT_PUBLIC_API_URL` to either `http://127.0.0.1:8000` or `http://127.0.0.1:8000/api/v1`.

### Streaming Chat

- Public page at `/u/{workspace_handle}/chat` streams assistant replies over SSE.
- Optimistic UI: user message appears immediately; assistant final text is appended on `message_end`.
- Idle sync: a lightweight polling loop (every ~2.5s) runs only while idle to pick up messages created by other clients; it pauses during active streams.
- SSE endpoint: `GET /api/v1/public/conversations/{conversation_id}/stream`.

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
├── proxy.ts              # Route protection (Next.js 16)
├── scripts/               # Development scripts
└── .cursor/                # Cursor IDE configuration
```

## Current State (MVP Complete ✅)

### ✅ Completed Features

**Authentication System:**

- Supabase SSR integration with `@supabase/ssr`
- Browser and server Supabase clients with cookie-based sessions
- Login page with email/password authentication
- Signup page with React Hook Form + Zod validation
- Disabled Google/Apple social auth buttons (future feature)
- Proxy middleware for route protection (Next.js 16)
- Server actions: `signIn()`, `signUp()`, `signOut()`
- Auth hooks: `useUser()`, `useAuthStatus()`

**Dashboard & Layout:**

- Responsive dashboard layout with shadcn/ui sidebar
- Automatic mobile/desktop handling (no custom responsive logic)
- Navigation: Dashboard, Services, Connectors, Settings, Public Chat (opens in a new tab)
- User menu with avatar and sign out

**Knowledge Base:**

- Knowledge base editor as default landing page for authenticated users
- Unlimited text input for business information
- Auto-save functionality with change indicators
- Character count display
- Workspace auto-creation on first access
- Calendly link input at the top of the page (stored as a SchedulingConnector with type "calendly"; persists across sessions)

**Workspace Management:**

- Workspaces auto-created when needed (no setup wizard required)
- Dashboard home with workspace overview
- Settings page with edit and delete functionality
- Workspace CRUD hooks using TanStack Query
- Form validation with Zod schemas
- API integration with automatic auth token injection

**Landing Page:**

- Marketing content for unauthenticated users
- Auto-redirect authenticated users to knowledge base
- Hero section, feature cards, and footer

**Code Quality & Development Tools:**

- ESLint + Prettier with TypeScript strict mode
- Pre-commit hooks via Python pre-commit tool
- Package manager migration from Yarn 4 to npm
- React Compiler compatibility (React 19 experimental)
- Generated API client from OpenAPI schema

**State Management:**

- TanStack Query for server state with caching
- React Query Devtools in development mode
- Workspace context for global state

**UI Components (shadcn/ui):**

- Button, Card, Input, Label, Dialog
- Dropdown Menu, Avatar, Badge, Skeleton
- Select, Separator, Sheet, Sidebar
- Form, Sonner (toast notifications)
- Tooltip

### 📋 Next Phase (Phase 3)

**Services Management:**

- CRUD UI for workspace services
- Service configuration forms

**Scheduling Connectors:**

- Calendly integration UI
- Connector configuration and testing

**Public Chat Interface:**

- Public page at `/u/{workspace_handle}/chat`
- SSE streaming replies; conversation created automatically on first load

**Testing:**

- Jest + React Testing Library setup
- Component and hook tests
- Integration tests

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
