import { client } from 'app/utils/api-client/client.gen'
import { debug } from 'app/utils/debug'
import { getBackendBaseUrl } from 'app/utils/getBackendBaseUrl'
import { supabase } from 'app/utils/supabase/client'

/**
 * Custom error class for API errors with additional context
 */
export class ApiError extends Error {
  constructor(message: string, public statusCode?: number, public responseData?: unknown) {
    super(message)
    this.name = 'ApiError'
  }
}

let isConfigured: boolean = false

export function configureApiClient(): void {
  if (isConfigured) {
    return // avoid double-registration in hot reload
  }
  isConfigured = true

  const baseUrl: string = getBackendBaseUrl()

  client.setConfig({
    baseUrl,
    throwOnError: true,
    auth: async (security) => {
      const {
        data: { session },
      } = await supabase.auth.getSession()
      const token = session?.access_token
      if (security.scheme === 'bearer' && token) {
        return token // Bearer prefix added by openapi-ts client
      }
      return undefined
    },
  })

  // Centralised error interceptor for all requests
  client.interceptors.error.use(async (error, response) => {
    debug.error('API Error:', error)

    if (!response) {
      return new ApiError('Network error - Failed to reach the server')
    }

    let responseData: unknown
    try {
      responseData = await response.clone().json()
    } catch {
      // ignore if not JSON
    }

    const status = response.status

    switch (status) {
      case 401:
        return new ApiError('Authentication required', status, responseData)
      case 403:
        return new ApiError('Not authorized to perform this action', status, responseData)
      case 422:
        return new ApiError('Invalid request data', status, responseData)
      case 404:
        return new ApiError('Resource not found', status, responseData)
      case 500:
        return new ApiError('Internal server error', status, responseData)
      default:
        return new ApiError(`Request failed with status ${status}`, status, responseData)
    }
  })

  debug.log('API client configured')
}
