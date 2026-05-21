# Guest User Rate Limiting Implementation

This document describes the implementation of rate limiting for non-logged-in (guest) users, allowing them to use the chat service 3 times per day.

## Overview

Guest users can now use the chat service up to 3 times per day. When they reach this limit, they are encouraged to sign up for unlimited access. The implementation includes:

- **Rate limit tracking** using a unique guest identifier
- **Visual feedback** showing remaining requests
- **Graceful error handling** with user-friendly modals
- **Seamless integration** with the existing authentication system

## Architecture

### 1. Rate Limit Hook (`hooks/useRateLimit.ts`)

The core of the rate limiting system. This hook:

- **Tracks guest users** using a UUID stored in localStorage
- **Fetches rate limit info** from the backend API (`/chat/rate-limit`)
- **Manages state** for current usage, limit, and remaining requests
- **Provides utilities** for checking if a message can be sent
- **Handles headers** differently for authenticated vs guest users

#### Key Features:

```typescript
// For authenticated users: uses Bearer token
Authorization: Bearer <token>

// For guest users: uses guest ID
X-Guest-ID: <guest-uuid>
```

The guest ID is automatically generated on first visit and persisted across sessions.

### 2. UI Components

#### Rate Limit Banner (`components/custom-components/RateLimitBanner.tsx`)

- Displays at the top of the chat interface for guest users
- Shows remaining requests in real-time
- Color-coded warnings:
  - **Blue**: 2-3 requests remaining
  - **Orange**: 1 request remaining
  - **Red**: 0 requests remaining (with reset time)
- Prominent "Sign Up for Unlimited" CTA button

#### Rate Limit Modal (`components/custom-components/RateLimitModal.tsx`)

- Appears when guest users try to exceed their limit
- Shows benefits of signing up:
  - Unlimited searches
  - Save chat history
  - Personalized recommendations
  - Priority support
- Easy sign-up flow with one-click CTA
- Displays time until rate limit resets

### 3. Integration with Chat System

#### Modified `StreamingHandler.ts`

Updated to support guest users:

```typescript
async startStreaming(
  apiUrl: string,
  requestBody: {...},
  token: string | null,  // Now nullable for guest users
  additionalHeaders?: HeadersInit  // Guest headers
)
```

- Handles 429 (rate limit exceeded) responses
- Passes guest headers when token is null
- Throws structured errors for rate limit violations

#### Updated Chat Page (`app/chat/[id]/page.tsx`)

Integrates rate limiting throughout:

1. **Pre-send validation**: Checks if user can send message before creating UI elements
2. **Dynamic headers**: Passes appropriate headers based on authentication status
3. **Usage tracking**: Increments local count after successful sends
4. **Error handling**: Detects rate limit errors and shows appropriate UI
5. **Banner display**: Shows rate limit info for guest users
6. **Modal handling**: Opens modal when limit is reached

## User Flow

### Guest User Journey

1. **First Visit**
   - System generates unique guest ID (UUID)
   - Stored in localStorage
   - Fetches rate limit info from backend
   - Banner shows "3 of 3 free searches remaining"

2. **Sending Messages**
   - Each message decrements the counter
   - Banner updates to show remaining requests
   - Local counter is optimistic (updates immediately)
   - Backend enforces actual limit

3. **Approaching Limit**
   - Banner turns orange when 1 request remains
   - Clear warning encourages sign-up

4. **Limit Reached**
   - Banner turns red
   - Shows time until reset
   - Modal appears if user tries to send another message
   - Modal highlights benefits of signing up

5. **After Sign-Up**
   - Banner disappears
   - Unlimited access granted
   - Chat history saved and accessible

### Authenticated User Journey

- No rate limiting applied
- No banner shown
- Unlimited chat access
- Full feature access

## Backend Integration

The implementation expects the following backend endpoints:

### GET `/chat/rate-limit`

Returns current rate limit status.

**Headers:**
- Authenticated: `Authorization: Bearer <token>`
- Guest: `X-Guest-ID: <uuid>`

**Response (Guest):**
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

**Response (Authenticated):**
```json
{
  "type": "authenticated",
  "usage": null,
  "limit": null,
  "remaining": "unlimited",
  "reset_at": null
}
```

### POST `/chat/message/stream`

Streaming endpoint for chat messages.

**Headers:**
- Authenticated: `Authorization: Bearer <token>`
- Guest: `X-Guest-ID: <uuid>`

**Response on Rate Limit:**
- Status: `429 Too Many Requests`
- Body:
```json
{
  "detail": {
    "error": "Rate limit exceeded",
    "message": "You have reached your daily limit of 3 free chat requests...",
    "usage": 3,
    "limit": 3,
    "reset_at": "2025-10-02T00:00:00Z",
    "reset_in_seconds": 43200
  }
}
```

## Technical Details

### Guest ID Management

- **Generation**: Uses `crypto.randomUUID()` (built-in browser API)
- **Storage**: localStorage key `guest_id`
- **Persistence**: Survives page refreshes and browser restarts
- **Uniqueness**: Each browser/device gets a unique ID

### Rate Limit State Management

The hook maintains state for:
- `rateLimitInfo`: Current rate limit data from backend
- `isLoading`: Loading state for API calls
- `error`: Error messages if fetching fails

### Optimistic Updates

When a guest user sends a message:
1. Local counter decrements immediately (optimistic)
2. Message is sent to backend
3. Backend validates and enforces actual limit
4. If backend rejects (429), modal appears and state is synced

This provides instant feedback while maintaining backend authority.

### Error Handling

Rate limit errors are identified by checking the error message:

```typescript
try {
  const errorData = JSON.parse(error.message);
  if (errorData.type === 'rate_limit') {
    // Handle rate limit error
    setRateLimitModalOpen(true);
    fetchRateLimit(); // Sync with backend
  }
} catch (e) {
  // Normal error handling
}
```

## Best Practices

### For Frontend Developers

1. **Always fetch rate limit on mount**: The hook automatically fetches on mount
2. **Check before sending**: Use `canSendMessage()` before allowing user to send
3. **Increment after success**: Only increment local counter after successful API response
4. **Sync on errors**: Refresh rate limit info from backend when errors occur
5. **Handle edge cases**: Consider network failures, stale data, etc.

### For Backend Developers

1. **Validate on every request**: Don't trust client-side checks
2. **Use consistent identifiers**: Track by guest_id for guests, user_id for authenticated
3. **Return detailed errors**: Include reset time and remaining count in 429 responses
4. **Handle race conditions**: Multiple concurrent requests should be handled gracefully
5. **Clear limits on sign-up**: When guest signs up, associate their history with new account

## Configuration

You can adjust the following:

### Rate Limit Display Colors

In `RateLimitBanner.tsx`:
```typescript
const getBannerColor = () => {
  if (remaining === 0) return 'bg-red-50 border-red-200 text-red-800';
  if (remaining === 1) return 'bg-orange-50 border-orange-200 text-orange-800';
  return 'bg-blue-50 border-blue-200 text-blue-800';
};
```

### Modal Benefits List

In `RateLimitModal.tsx`, update the benefits list to match your product features.

### API Endpoints

In `hooks/useRateLimit.ts` and `StreamingHandler.ts`:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

## Testing Recommendations

### Manual Testing

1. **Fresh guest user**:
   - Clear localStorage
   - Send 3 messages
   - Verify counter decrements correctly
   - Try to send 4th message, verify modal appears

2. **Sign-up flow**:
   - As guest with 2 messages sent
   - Click sign-up from banner
   - Complete registration
   - Verify banner disappears
   - Verify unlimited access

3. **Reset behavior**:
   - Wait for reset time (or manipulate backend time)
   - Verify counter resets to 3
   - Verify can send messages again

4. **Multiple devices**:
   - Use different browsers/devices
   - Verify each gets unique guest ID
   - Verify each has independent rate limits

### Edge Cases to Test

- Network failures during rate limit check
- Concurrent message sends
- Page refresh mid-conversation
- Browser back/forward navigation
- localStorage disabled/blocked
- API returning unexpected formats

## Troubleshooting

### Banner not showing

- Check if user is authenticated (`isAuthenticated` should be false)
- Verify `rateLimitInfo` is being fetched successfully
- Check browser console for errors

### Counter not updating

- Verify `incrementUsage()` is called after successful message send
- Check if `fetchRateLimit()` is working
- Look for API errors in network tab

### Modal not appearing

- Verify 429 error is being thrown by backend
- Check error parsing logic in `onError` callback
- Ensure `rateLimitModalOpen` state is managed correctly

### Guest ID not persisting

- Check if localStorage is enabled in browser
- Verify `guest_id` key is being set
- Check for conflicting localStorage operations

## Future Enhancements

Potential improvements:

1. **Tiered Limits**: Different limits for different user types
2. **Time-based Windows**: Rolling 24-hour window instead of daily reset
3. **Progressive Warnings**: Subtle reminders at 2 remaining, 1 remaining
4. **Analytics**: Track conversion rate from rate limit modal
5. **Soft Limits**: Warning at limit but allow 1-2 more with strong CTA
6. **Local Caching**: Cache rate limit info to reduce API calls
7. **Retry Logic**: Automatic retry with exponential backoff on failures

## Security Considerations

1. **Guest ID Spoofing**: Backend should validate and track by IP/fingerprint if needed
2. **LocalStorage Access**: Guest IDs in localStorage can be manipulated
3. **API Rate Limiting**: Backend should have its own rate limiting independent of client
4. **CORS Headers**: Ensure proper CORS configuration for guest users
5. **Token Validation**: Always validate tokens on backend for authenticated users

## Conclusion

This implementation provides a seamless experience for guest users while encouraging sign-ups through smart rate limiting. The system is built to be:

- **User-friendly**: Clear communication about limits
- **Developer-friendly**: Easy to integrate and maintain
- **Scalable**: Can handle high traffic
- **Secure**: Backend-enforced limits
- **Flexible**: Easy to adjust limits and UI

For questions or issues, please refer to the codebase or contact the development team.

