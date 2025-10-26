This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

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
