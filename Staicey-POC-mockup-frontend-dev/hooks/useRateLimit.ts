// hooks/useRateLimit.ts
import { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface RateLimitInfo {
  type: 'guest' | 'authenticated';
  usage: number | null;
  limit: number | null;
  remaining: number | string;
  reset_at: string | null;
  reset_in_seconds: number | null;
}

export interface RateLimitError {
  error: string;
  message: string;
  usage: number;
  limit: number;
  reset_at: string;
  reset_in_seconds: number;
}

/**
 * Hook to manage rate limiting for guest users
 * Returns rate limit info and utilities
 */
export function useRateLimit(isAuthenticated: boolean) {
  const [rateLimitInfo, setRateLimitInfo] = useState<RateLimitInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Get or create a guest identifier
   * This is stored in localStorage to track guest users across sessions
   */
  const getGuestId = useCallback((): string => {
    if (typeof window === 'undefined') return '';
    
    let guestId = localStorage.getItem('guest_id');
    if (!guestId) {
      // Use crypto.randomUUID() for built-in UUID generation
      guestId = crypto.randomUUID();
      localStorage.setItem('guest_id', guestId);
    }
    return guestId;
  }, []);

  /**
   * Get authorization headers for API calls
   * Uses token for authenticated users, guest_id for guests
   */
  const getHeaders = useCallback((): HeadersInit => {
    if (isAuthenticated) {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };
    } else {
      const guestId = getGuestId();
      return {
        'X-Guest-ID': guestId,
        'Content-Type': 'application/json',
      };
    }
  }, [isAuthenticated, getGuestId]);

  /**
   * Fetch current rate limit status from the API
   */
  const fetchRateLimit = useCallback(async (): Promise<RateLimitInfo | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/chat/rate-limit`, {
        method: 'GET',
        headers: getHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch rate limit: ${response.status}`);
      }

      const data: RateLimitInfo = await response.json();
      setRateLimitInfo(data);
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch rate limit';
      setError(errorMessage);
      console.error('Rate limit fetch error:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [getHeaders]);

  /**
   * Check if the user can send a message
   * Returns true if allowed, false if rate limited
   */
  const canSendMessage = useCallback((): boolean => {
    if (isAuthenticated) return true;
    if (!rateLimitInfo) return true; // Allow if we haven't fetched yet
    if (rateLimitInfo.type === 'authenticated') return true;
    
    const remaining = rateLimitInfo.remaining;
    return typeof remaining === 'number' && remaining > 0;
  }, [isAuthenticated, rateLimitInfo]);

  /**
   * Increment usage count locally (optimistic update)
   * This will be synced with the server on next fetch
   */
  const incrementUsage = useCallback(() => {
    if (rateLimitInfo && rateLimitInfo.type === 'guest') {
      setRateLimitInfo(prev => {
        if (!prev || prev.type !== 'guest') return prev;
        return {
          ...prev,
          usage: (prev.usage || 0) + 1,
          remaining: Math.max(0, (prev.remaining as number) - 1),
        };
      });
    }
  }, [rateLimitInfo]);

  /**
   * Format time remaining until reset
   */
  const getResetTimeFormatted = useCallback((): string => {
    if (!rateLimitInfo || !rateLimitInfo.reset_in_seconds) return '';
    
    const seconds = rateLimitInfo.reset_in_seconds;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  }, [rateLimitInfo]);

  // Fetch rate limit on mount and when authentication status changes
  useEffect(() => {
    fetchRateLimit();
  }, [fetchRateLimit]);

  return {
    rateLimitInfo,
    isLoading,
    error,
    fetchRateLimit,
    canSendMessage,
    incrementUsage,
    getResetTimeFormatted,
    getGuestId,
    getHeaders,
  };
}

