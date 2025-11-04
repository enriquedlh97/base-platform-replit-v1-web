import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "./openapi.json",
  output: {
    path: "./lib/api/generated",
    clean: true,
  },
  plugins: [
    {
      name: "@hey-api/sdk",
      // NOTE: this doesn't allow tree-shaking
      asClass: true,
      classNameBuilder: (tag) =>
        `${tag.charAt(0).toUpperCase() + tag.slice(1)}Service`,
      operationId: true,
      methodNameBuilder: (operation) => {
        // @ts-expect-error operation.tags exists at runtime
        const tag = operation.tags?.[0];
        // @ts-expect-error operation.operationId exists at runtime
        let name = operation.operationId;

        if (tag && name.startsWith(tag)) {
          // Removes tag from operationId
          name = name.slice(tag.length);
        }

        // Removes leading `-` or `_`
        if (name.startsWith("-") || name.startsWith("_")) {
          name = name.slice(1);
        }

        // Converts to camelCase
        return name.replace(/_([a-z])/g, (g: string) => g[1].toUpperCase());
      },
    },
  ],
});
