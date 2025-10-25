import { Session } from '@supabase/supabase-js'
import { useQuery } from '@tanstack/react-query'

import { UsersService } from './api-client/sdk.gen'
import { UserPublic } from './api-client/types.gen'
import { useSessionContext } from './supabase/useSessionContext'

/**
 * Interface defining the return type of the useUser hook
 */
interface UseUserResult {
  /** Current Supabase session or null if not authenticated */
  session: Session | null
  /** User data from backend API */
  user: UserPublic | null
  /** Alias for user data (for compatibility) */
  profile: UserPublic | null
  /** URL for the user's avatar */
  avatarUrl: string
  /** Function to trigger a refresh of the user profile */
  updateProfile: () => Promise<unknown>
  /** Whether the session is currently loading */
  isLoadingSession: boolean
  /** Whether the profile data is currently loading */
  isLoadingProfile: boolean
  /** Whether any data is currently loading */
  isLoading: boolean
}

/**
 * Hook to access and manage the current user's data
 * @returns Object containing user data, loading states, and management functions
 */
export const useUser = (): UseUserResult => {
  const { session, isLoading: isLoadingSession } = useSessionContext()

  /**
   * Fetch the current user's profile using the generated SDK.
   * We request `responseStyle: "data"` so the promise resolves with the
   * deserialised User object (or throws ApiError via the global interceptor).
   */
  const fetchCurrentUserProfile = async (): Promise<UserPublic> => {
    const result = await UsersService.readUserMe()
    if (!result.data) {
      throw new Error('No user data returned from API')
    }
    return result.data
  }

  const {
    data: user,
    refetch,
    isLoading: isLoadingProfile,
  } = useQuery({
    queryKey: ['user', 'me'] as const,
    queryFn: fetchCurrentUserProfile,
    // Only execute the query when:
    // 1. Session is loaded (not loading)
    // 2. User is authenticated (has session)
    enabled: !isLoadingSession && !!session?.user?.id,
  })

  const avatarUrl: string = (() => {
    // Use backend avatar_url if available, otherwise fall back to generated avatar
    if (user?.avatar_url) {
      return user.avatar_url
    }

    // Fallback to generated avatar from name/email
    const params: URLSearchParams = new URLSearchParams()
    const name: string = user?.name || user?.full_name || user?.email || ''
    params.append('name', name)
    params.append('size', '256') // will be resized again by NextImage/SolitoImage
    return `https://ui-avatars.com/api.jpg?${params.toString()}`
  })()

  return {
    session,
    user: user || null,
    // The "profile" is now the same as the user object from our API.
    profile: user || null,
    avatarUrl,
    updateProfile: () => refetch(),
    isLoadingSession,
    isLoadingProfile,
    isLoading: isLoadingSession || isLoadingProfile,
  }
}
