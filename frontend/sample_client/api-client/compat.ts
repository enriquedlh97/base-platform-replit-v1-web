export type ReactNativeFile = { uri: string; name: string; type: string }

// Centralized helper to satisfy the OpenAPI client's File | Blob typing
// while allowing React Native's file-like object at call sites.
//
// Note:
// The OpenAPI generator maps schema type "binary" to `File | Blob` (browser types).
// On React Native, we also need to support the RN file shape `{ uri, name, type }`.
// If you want zero casts in application code, you can customize the generator
// to widen the generated types to `Blob | File | { uri: string; name: string; type: string }`.
// Until then, we keep this small boundary cast so components can pass the RN file
// object while the runtime serializer handles it correctly on native.
export function asFormDataFile(
  value: File | Blob | ReactNativeFile
): File | Blob | any /* RN file */ {
  return value as any
}
