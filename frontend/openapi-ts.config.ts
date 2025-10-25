import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  input: './openapi.json',
  output: {
    path: './packages/app/utils/api-client',
    clean: false,
  },
  plugins: [
    {
      name: '@hey-api/sdk',
      // NOTE: this doesn't allow tree-shaking
      asClass: true,
      classNameBuilder: (tag) => `${tag.charAt(0).toUpperCase() + tag.slice(1)}Service`,
      operationId: true,
      methodNameBuilder: (operation) => {
        // @ts-ignore
        const tag = operation.tags?.[0]
        // @ts-ignore
        let name = operation.operationId

        if (tag && name.startsWith(tag)) {
          // Removes tag from operationId
          name = name.slice(tag.length)
        }

        // Removes leading `-` or `_`
        if (name.startsWith('-') || name.startsWith('_')) {
          name = name.slice(1)
        }

        // Converts to camelCase
        return name.replace(/_([a-z])/g, (g) => g[1].toUpperCase())
      },
    },
  ],
})
