# Rate Limiting Quick Start Guide

## What Was Implemented

I've implemented a complete guest user rate limiting system that allows non-logged-in users to use your chat service 3 times per day. Here's what was added:

## Files Created

1. **`hooks/useRateLimit.ts`** - Core rate limiting logic and API integration
2. **`components/custom-components/RateLimitBanner.tsx`** - Banner showing remaining requests
3. **`components/custom-components/RateLimitModal.tsx`** - Modal when limit is exceeded
4. **`RATE_LIMITING_IMPLEMENTATION.md`** - Comprehensive documentation

## Files Modified

1. **`app/chat/[id]/page.tsx`** - Integrated rate limiting into chat page
2. **`app/chat/components/StreamingHandler.ts`** - Added support for guest users and 429 error handling

## How It Works

### For Guest Users:

1. **First visit**: System generates a unique ID (stored in browser)
2. **Visible banner**: Shows "3 of 3 free searches remaining"
3. **As they chat**: Counter decrements with each message
4. **At limit**: Modal appears encouraging sign-up
5. **After sign-up**: Banner disappears, unlimited access granted

### For Logged-in Users:

- No rate limiting
- No banner displayed
- Unlimited chat access

## Visual Elements

### Rate Limit Banner
- **Location**: Top of chat interface (below header)
- **For**: Guest users only
- **Shows**:
  - Remaining requests (e.g., "2 of 3 free searches remaining")
  - Reset time when limit reached
  - "Sign Up for Unlimited" button
- **Colors**:
  - Blue: 2-3 requests left
  - Orange: 1 request left
  - Red: 0 requests (limit reached)

### Rate Limit Modal
- **Triggers**: When guest tries to send message after limit reached
- **Shows**:
  - Friendly "Daily Limit Reached" message
  - Time until reset
  - Benefits of signing up
  - "Sign Up Now" button
  - "Maybe Later" option

## Backend Requirements

Your backend needs to support:

### 1. Rate Limit Check Endpoint

```http
GET /chat/rate-limit
```

**Request Headers:**
- Guest users: `X-Guest-ID: <uuid>`
- Authenticated users: `Authorization: Bearer <token>`

**Response for Guests:**
```json
{
  "type": "guest",
  "usage": 2,
  "limit": 3,
  "remaining": 1,
  "reset_at": "2025-10-02T00:00:00Z",
  "reset_in_seconds": 43200
}
```

**Response for Authenticated:**
```json
{
  "type": "authenticated",
  "usage": null,
  "limit": null,
  "remaining": "unlimited",
  "reset_at": null
}
```

### 2. Chat Endpoint Updates

```http
POST /chat/message/stream
```

**Must Accept:**
- `X-Guest-ID` header for guest users
- Return `429 Too Many Requests` when limit exceeded

**429 Response Format:**
```json
{
  "detail": {
    "error": "Rate limit exceeded",
    "message": "You have reached your daily limit of 3 free chat requests. Please sign up or log in for unlimited access.",
    "usage": 3,
    "limit": 3,
    "reset_at": "2025-10-02T00:00:00Z",
    "reset_in_seconds": 43200
  }
}
```

## Testing

### Quick Test (Guest User):

1. **Open incognito window** (fresh guest session)
2. **Navigate to chat page**
3. **See banner**: "3 of 3 free searches remaining"
4. **Send a message**: Counter becomes "2 of 3"
5. **Send 2 more messages**: Counter becomes "0 of 3"
6. **Try to send another**: Modal appears
7. **Click "Sign Up Now"**: Login popup opens

### Test with Backend:

If your backend is ready, test:

1. Open Network tab in DevTools
2. Look for calls to `/chat/rate-limit`
3. Verify `X-Guest-ID` header is sent
4. Send messages and verify backend counts correctly
5. On 4th message, verify backend returns 429

## Configuration

### Change Daily Limit

In your **backend**, adjust the limit (currently 3).

### Change UI Colors

In `components/custom-components/RateLimitBanner.tsx`:

```typescript
const getBannerColor = () => {
  if (remaining === 0) return 'bg-red-50 border-red-200 text-red-800';
  if (remaining === 1) return 'bg-orange-50 border-orange-200 text-orange-800';
  return 'bg-blue-50 border-blue-200 text-blue-800';
};
```

### Change Modal Benefits

In `components/custom-components/RateLimitModal.tsx`, update the benefits list.

## Important Notes

### Guest ID Storage

- Stored as: `localStorage.getItem('guest_id')`
- Generated using: `crypto.randomUUID()`
- **Persists**: Across page refreshes and browser restarts
- **Unique**: Per browser/device

### Rate Limit Enforcement

- **Client-side**: Optimistic updates for UX
- **Backend**: Actual enforcement (cannot be bypassed)
- **Sync**: Frontend regularly syncs with backend

### Sign-Up Flow

When guest clicks "Sign Up":
1. Opens your existing login/signup popup
2. Uses `SignInUpContext.openPopup()`
3. After signup, banner automatically disappears
4. User gets unlimited access

## Common Issues

### "Banner not showing"

- Check: User is not logged in (`isAuthenticated === false`)
- Check: Backend is returning rate limit info
- Check: Console for errors

### "Counter not decreasing"

- Verify: Backend is returning correct rate limit info
- Check: `incrementUsage()` is being called
- Check: Network tab for API responses

### "Modal not appearing at limit"

- Verify: Backend returns 429 status
- Check: Error handling in `onError` callback
- Check: Modal state in React DevTools

## Next Steps

1. **Deploy backend changes** (rate limit endpoint)
2. **Test with real backend** (not just localhost)
3. **Monitor conversion rate** (how many guests sign up)
4. **Adjust limit if needed** (based on data)
5. **Consider A/B testing** (different limits/messaging)

## Code Integration Points

The rate limiting is integrated at these key points:

1. **Chat page mount**: Fetches rate limit info
2. **Before message send**: Checks if user can send
3. **After message send**: Updates local counter
4. **On API error**: Detects rate limit errors
5. **UI rendering**: Shows banner and modal

## Support

For detailed implementation info, see `RATE_LIMITING_IMPLEMENTATION.md`.

For questions or issues:
1. Check browser console for errors
2. Check network tab for API calls
3. Verify backend is configured correctly
4. Review the implementation guide

---

## Summary

✅ Guest users get 3 free chat requests per day
✅ Clear visual feedback with banner
✅ Friendly modal when limit reached
✅ Seamless sign-up conversion flow
✅ Backend-enforced security
✅ Works with existing authentication system

The implementation is ready to use once your backend supports the `/chat/rate-limit` endpoint and returns 429 errors when limits are exceeded!

