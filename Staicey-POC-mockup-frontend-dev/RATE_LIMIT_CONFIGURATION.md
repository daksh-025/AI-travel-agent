# Rate Limit Configuration Guide

## Overview

The rate limiting system for guest users is now fully configurable through a centralized constants file. You can easily adjust the daily limit, messages, and other settings in one place.

## Configuration File

**Location:** `lib/constants/rateLimit.ts`

### Main Configuration

```typescript
// Change this value to adjust the daily limit
export const GUEST_RATE_LIMIT = 3;

export const RATE_LIMIT_CONFIG = {
  // Daily limit for guest users
  guestDailyLimit: GUEST_RATE_LIMIT,
  
  // Reset period in hours (24 hours = daily reset)
  resetPeriodHours: 24,
  
  // Display messages
  messages: {
    dailyLimitReached: "Daily limit reached",
    signUpPrompt: "Sign up for unlimited access",
    freeSearchesRemaining: (remaining: number, limit: number) => 
      `${remaining} of ${limit} free searches remaining`,
    limitExceededMessage: (limit: number) => 
      `You have reached your daily limit of ${limit} free chat requests...`,
  },
};
```

## How to Change the Rate Limit

### Option 1: Change the Limit Value (Recommended)

Simply update the `GUEST_RATE_LIMIT` constant:

```typescript
// lib/constants/rateLimit.ts

// Change from 3 to any number you want
export const GUEST_RATE_LIMIT = 5; // Now guests get 5 searches per day
```

All UI components will automatically update to show the new limit!

### Option 2: Use Environment Variable

For deployment flexibility, you can use an environment variable:

1. **Update the constants file:**
```typescript
// lib/constants/rateLimit.ts
export const GUEST_RATE_LIMIT = parseInt(
  process.env.NEXT_PUBLIC_GUEST_RATE_LIMIT || '3'
);
```

2. **Set in your `.env.local`:**
```bash
NEXT_PUBLIC_GUEST_RATE_LIMIT=5
```

3. **Restart your dev server** to apply changes

## Where the Limit is Used

The rate limit configuration is automatically applied in:

### 1. **Rate Limit Banner** (`RateLimitBanner.tsx`)
- Shows "X of Y free searches remaining"
- Auto-updates with your configured limit

### 2. **Rate Limit Modal** (`RateLimitModal.tsx`)
- Shows "You have reached your daily limit of X..."
- Uses your configured messages

### 3. **Guest Chat Page** (`app/chat/guest/page.tsx`)
- Empty state shows "You have X free searches today"
- Uses `getDefaultRateLimit()` helper

### 4. **Backend Integration**
- Your backend should also use the same limit value
- Frontend displays what backend enforces

## Customizing Messages

You can customize all user-facing messages in the config:

```typescript
messages: {
  // Modal title
  dailyLimitReached: "Daily limit reached",
  
  // Button text
  signUpPrompt: "Sign up for unlimited access",
  
  // Banner text (function for dynamic values)
  freeSearchesRemaining: (remaining: number, limit: number) => 
    `${remaining} of ${limit} free searches remaining`,
  
  // Modal description (function for dynamic limit)
  limitExceededMessage: (limit: number) => 
    `You have reached your daily limit of ${limit} free chat requests. 
     Please sign up or log in for unlimited access.`,
}
```

### Example: Custom Messages

```typescript
messages: {
  dailyLimitReached: "Oops! Out of free searches",
  signUpPrompt: "Get Unlimited Access",
  freeSearchesRemaining: (remaining: number, limit: number) => 
    `🎁 ${remaining} free ${remaining === 1 ? 'search' : 'searches'} left today!`,
  limitExceededMessage: (limit: number) => 
    `You've used all ${limit} free searches today! 
     Create a free account for unlimited searches 🚀`,
}
```

## Helper Functions

### `getDefaultRateLimit()`

Use this when rate limit info is not yet loaded from the API:

```typescript
import { getDefaultRateLimit } from '@/lib/constants/rateLimit';

// Shows configured limit as fallback
const limit = rateLimitInfo?.remaining || getDefaultRateLimit();
```

### `RATE_LIMIT_CONFIG`

Access the full configuration object:

```typescript
import { RATE_LIMIT_CONFIG } from '@/lib/constants/rateLimit';

// Get the limit
const limit = RATE_LIMIT_CONFIG.guestDailyLimit;

// Get a message
const message = RATE_LIMIT_CONFIG.messages.dailyLimitReached;
```

## Examples

### Example 1: Increase to 5 Searches

```typescript
// lib/constants/rateLimit.ts
export const GUEST_RATE_LIMIT = 5;
```

**Result:**
- Banner: "5 of 5 free searches remaining"
- Modal: "You have reached your daily limit of 5..."
- Empty state: "You have 5 free searches today"

### Example 2: Promotional Period (10 Searches)

```typescript
// lib/constants/rateLimit.ts
export const GUEST_RATE_LIMIT = 10;

export const RATE_LIMIT_CONFIG = {
  guestDailyLimit: GUEST_RATE_LIMIT,
  resetPeriodHours: 24,
  messages: {
    dailyLimitReached: "Promotional limit reached",
    signUpPrompt: "Sign up to never lose access",
    freeSearchesRemaining: (remaining: number, limit: number) => 
      `🎉 ${remaining} of ${limit} promotional searches remaining`,
    limitExceededMessage: (limit: number) => 
      `You've used all ${limit} promotional searches today! 
       Sign up now to continue with unlimited access.`,
  },
};
```

### Example 3: Weekend Boost (Different Limit)

For dynamic limits based on day of week, update the constant based on logic:

```typescript
// lib/constants/rateLimit.ts
const isWeekend = () => {
  const day = new Date().getDay();
  return day === 0 || day === 6; // Sunday or Saturday
};

export const GUEST_RATE_LIMIT = isWeekend() ? 5 : 3;
```

## Testing

After changing the rate limit:

1. **Clear localStorage**: `localStorage.clear()`
2. **Refresh the page**
3. **Check the banner**: Should show new limit
4. **Send messages**: Counter should decrement correctly
5. **Check modal**: Should show new limit when reached

## Deployment Checklist

- [ ] Update `GUEST_RATE_LIMIT` in `lib/constants/rateLimit.ts`
- [ ] Or set `NEXT_PUBLIC_GUEST_RATE_LIMIT` environment variable
- [ ] Update backend rate limit to match
- [ ] Test in development
- [ ] Deploy frontend and backend together
- [ ] Verify in production

## Backend Sync

**Important:** Your backend must return the same limit in the API response!

```json
// Backend response should match
{
  "type": "guest",
  "usage": 2,
  "limit": 3,  // ← Must match GUEST_RATE_LIMIT
  "remaining": 1,
  "reset_at": "2025-10-02T00:00:00Z"
}
```

If they don't match:
- Frontend will display your configured limit
- Backend will enforce its own limit
- May cause confusion if limits differ!

## Summary

✅ **Single source of truth**: `lib/constants/rateLimit.ts`
✅ **Easy to change**: Just update one number
✅ **Auto-updates**: All UI components use the same value
✅ **Customizable messages**: Change wording without touching components
✅ **Type-safe**: TypeScript ensures correct usage
✅ **Environment variable support**: Can use `.env` for deployment flexibility

Change the limit once, and it updates everywhere! 🎉

