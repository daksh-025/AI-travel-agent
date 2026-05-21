# Guest Chat Flow - Implementation Guide

## Overview

Non-logged-in users can now ask Staicey questions from the HeroSection and be taken to a simplified chat page with rate limiting (3 free searches per day).

## What Changed

### 1. HeroSection Updates (`components/sections/HeroSection.tsx`)

**Before:** Guest users clicking "Ask Staicey" would see the login popup and stay on home page.

**Now:** Guest users are redirected to a dedicated guest chat page at `/chat/guest` with their query automatically sent.

#### Key Changes:
- Query is stored in `sessionStorage` as `guest_query`
- Redirects to `/chat/guest` instead of showing login popup
- Authenticated users still work as before (sent to `/chat/{tab_id}`)

### 2. New Guest Chat Page (`app/chat/guest/page.tsx`)

A simplified chat interface specifically for guest users:

**Features:**
- ✅ No sidebar (clean, focused interface)
- ✅ No tabs needed
- ✅ Rate limiting applied (3 searches/day)
- ✅ Rate limit banner at top
- ✅ Auto-sends query from HeroSection
- ✅ Simple header with Home and Login buttons
- ✅ Full streaming support
- ✅ Hotel results and suggestions work
- ✅ Redirects to regular chat if user logs in

**Special Guest Features:**
- Uses `tab_id: "guest"` for API calls
- Sends `X-Guest-ID` header instead of auth token
- Shows remaining free searches count
- Encourages sign-up when limit approaches

## User Flow

### Guest User Journey

1. **User visits home page** (not logged in)
2. **Types query** in HeroSection textarea
   - Example: "Cheapest hotel in Brisbane next weekend"
3. **Clicks "Ask Staicey"** or presses Enter
4. **Redirected to `/chat/guest`**
5. **Query auto-sends** immediately
6. **Staicey responds** with streaming (just like regular chat)
7. **User can continue chatting** until rate limit reached
8. **Banner shows**: "2 of 3 free searches remaining" (updates in real-time)

### Rate Limit Reached

9. **User tries to send 4th message**
10. **Modal appears**: "Daily Limit Reached"
11. **Shows benefits** of signing up
12. **User clicks "Sign Up Now"**
13. **Login popup opens**
14. **After signup**: Redirected to regular chat with unlimited access

### Sign Up During Chat

- User can click "Sign Up / Login" button in header anytime
- After successful login, automatically redirected to regular chat (`/chat`)
- Chat history is managed by backend (if backend supports guest-to-user migration)

## Technical Details

### Session Storage
```javascript
// HeroSection sets this before redirect
sessionStorage.setItem('guest_query', searchQuery.trim());

// Guest chat page reads and auto-sends on mount
const guestQuery = sessionStorage.getItem('guest_query');
```

### API Integration

Guest chat uses special identifiers:

**Headers sent:**
```javascript
{
  'X-Guest-ID': '<unique-uuid>',  // Generated and stored in localStorage
  'Content-Type': 'application/json'
}
```

**Request body:**
```json
{
  "message": "User's query",
  "tab_id": "guest"
}
```

### Rate Limiting

Same system as regular chat:
- Fetches from `/chat/rate-limit` endpoint
- Shows banner with remaining count
- Blocks sending when limit reached
- Shows modal with conversion CTA

## UI Components

### Guest Chat Header
- **Left**: Staicey logo + tagline
- **Right**: Home button + Sign Up/Login button
- Clean, minimal design

### Rate Limit Banner
- Only shows for guest users
- Color-coded based on remaining searches
- Prominent "Sign Up for Unlimited" button

### Chat Area
- Same components as regular chat:
  - `ChatMessage` - message bubbles
  - `DateSeparator` - date dividers
  - `HotelResults` - hotel cards (if applicable)
  - Streaming progress indicators
  - Suggestions buttons

### Input Area
- Same textarea as regular chat
- Auto-resize
- Enter to send (Shift+Enter for new line)
- Disabled when rate limit reached

## Backend Requirements

Your backend should:

1. **Accept `tab_id: "guest"`** for guest users
2. **Track by `X-Guest-ID` header** instead of user auth
3. **Return proper rate limit info** for guest requests
4. **Return 429** when limit exceeded
5. **Optional**: Migrate guest chat history to user account on signup

### Guest Tab Handling

The backend can:
- Create temporary sessions for `tab_id: "guest"`
- Store messages temporarily (or not at all)
- Clean up old guest sessions periodically
- Or treat each guest request independently

## Testing

### Test as Guest User:

1. **Clear cookies/localStorage** or use incognito mode
2. **Go to home page** (`/`)
3. **Type a query** in the textarea
4. **Click "Ask Staicey"**
5. **Verify**: Redirected to `/chat/guest`
6. **Verify**: Query auto-sends immediately
7. **Verify**: Banner shows "3 of 3 free searches remaining"
8. **Send 2 more messages**
9. **Verify**: Counter decrements to "0 of 3"
10. **Try to send 4th message**
11. **Verify**: Modal appears, message blocked

### Test Sign-Up Flow:

1. **As guest user** at `/chat/guest`
2. **Click "Sign Up / Login"** in header
3. **Complete registration**
4. **Verify**: Automatically redirected to `/chat`
5. **Verify**: Banner disappears
6. **Verify**: Can send unlimited messages

### Test Authenticated User:

1. **Login first**
2. **Go to home page**
3. **Type query and submit**
4. **Verify**: Redirected to `/chat/{tab_id}` (regular chat)
5. **Verify**: NOT redirected to guest chat

## Styling

The guest chat page uses the same styling as regular chat:
- Tailwind CSS classes
- Same color scheme
- Responsive design
- Mobile-friendly

## Differences from Regular Chat

| Feature | Regular Chat | Guest Chat |
|---------|-------------|------------|
| Sidebar | ✅ Yes | ❌ No |
| Chat tabs | ✅ Multiple | ❌ Single session |
| Rate limiting | ❌ Unlimited | ✅ 3 per day |
| Rate limit banner | ❌ Hidden | ✅ Shown |
| Authentication | ✅ Required | ❌ Not required |
| History saved | ✅ Permanent | ❌ Temporary |
| Tab ID | User's tabs | `"guest"` |
| Headers | Bearer token | X-Guest-ID |

## Conversion Optimization

The guest chat flow is designed to encourage sign-ups:

1. **Immediate value**: Let them try before asking to sign up
2. **Clear limits**: Show remaining searches prominently
3. **Timely prompts**: Modal appears at perfect moment
4. **Clear benefits**: List advantages of signing up
5. **Easy action**: One-click to open signup form
6. **No friction**: Can start chatting without account

## Future Enhancements

Potential improvements:

1. **Chat persistence**: Save guest chats and migrate to account on signup
2. **Smart reminders**: Show subtle prompts at strategic moments
3. **Extended trial**: Offer 1-2 extra searches for email signup
4. **Social proof**: Show "X users signed up today"
5. **Progressive disclosure**: Unlock features after signup
6. **Email capture**: Optional email before hitting limit

## Troubleshooting

### Guest chat not loading
- Check: `/chat/guest` route exists
- Check: No errors in console
- Check: Backend accepts `tab_id: "guest"`

### Query not auto-sending
- Check: `sessionStorage` has `guest_query`
- Check: `hasAutoSentRef` is working
- Check: Network tab for API call

### Rate limit not working
- Check: `X-Guest-ID` header being sent
- Check: Backend rate limit endpoint working
- Check: localStorage has `guest_id`

### Redirect issues
- Check: Router navigation in HeroSection
- Check: useEffect in guest chat page
- Check: isAuthenticated state

## Files Modified/Created

### Created:
- `app/chat/guest/page.tsx` - Guest chat page

### Modified:
- `components/sections/HeroSection.tsx` - Guest user handling

### Existing (Used):
- `hooks/useRateLimit.ts` - Rate limiting logic
- `components/custom-components/RateLimitBanner.tsx` - Banner component
- `components/custom-components/RateLimitModal.tsx` - Modal component
- `app/chat/components/StreamingHandler.ts` - Streaming support
- `app/chat/components/ChatMessage.tsx` - Message display

## Summary

✅ **Guest users** can now ask questions from home page
✅ **No login required** to try the service
✅ **Rate limiting applied** (3 searches/day)
✅ **Clean interface** without sidebar/tabs
✅ **Auto-send query** from HeroSection
✅ **Smooth conversion** to signup when limit reached
✅ **Production ready** with proper error handling

The implementation provides a frictionless experience for new users while encouraging conversion through smart rate limiting!

