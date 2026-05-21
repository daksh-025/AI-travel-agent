// lib/constants/rateLimit.ts
// Rate limiting configuration for guest users

/**
 * Number of free chat requests allowed per day for non-logged-in users
 * Change this value to adjust the daily limit for guest users
 */
export const GUEST_RATE_LIMIT = 10;

/**
 * Rate limit configuration
 */
export const RATE_LIMIT_CONFIG = {
  /**
   * Daily limit for guest users
   */
  guestDailyLimit: GUEST_RATE_LIMIT,
  
  /**
   * Reset period in hours (24 hours = daily reset)
   */
  resetPeriodHours: 24,
  
  /**
   * Display messages
   */
  messages: {
    dailyLimitReached: "Daily limit reached",
    signUpPrompt: "Sign up for unlimited access",
    freeSearchesRemaining: (remaining: number, limit: number) => 
      `${remaining} of ${limit} free searches remaining`,
    limitExceededMessage: (limit: number) => 
      `You have reached your daily limit of ${limit} free chat requests. Please sign up or log in for unlimited access.`,
  },
};

/**
 * Get the default rate limit for display purposes
 * Used when rate limit info is not yet loaded
 */
export const getDefaultRateLimit = () => GUEST_RATE_LIMIT;

