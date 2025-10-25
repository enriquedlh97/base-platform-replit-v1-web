import { createPagesBrowserClient } from '@supabase/auth-helpers-nextjs'

import { getBackendBaseUrl } from './getBackendBaseUrl'

// NOTE: This is the web-only Supabase client
const supabase = createPagesBrowserClient()

const API_BASE_URL = getBackendBaseUrl()

type ApiClientOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  body?: any
  headers?: Record<string, string>
}

export const apiClient = async <T>(
  endpoint: string,
  options: ApiClientOptions = {}
): Promise<T> => {
  const { method = 'GET', body, headers = {} } = options

  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`
  }

  if (body) {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(
      `API request failed with status ${response.status}: ${errorBody.detail || 'No error detail'}`
    )
  }

  if (response.status === 204) {
    // No Content
    return null as T
  }

  return response.json()
}
