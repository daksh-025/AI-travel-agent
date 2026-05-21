# Rate Limiting for Non-Authenticated Users

## Overview

This implementation provides rate limiting for non-authenticated (guest) users accessing the chat service. Guest users are limited to **3 chat requests per day**, with limits resetting at midnight UTC. Authenticated users have unlimited access.

## Architecture

### Components

1. **Rate Limit Service** (`app/services/rate_limit_service.py`)
   - Core logic for tracking and checking rate limits
   - Uses Redis for fast, distributed rate limiting
   - Automatic daily resets at midnight UTC

2. **Rate Limit Middleware** (`app/middleware/rate_limit.py`)
   - FastAPI dependencies for enforcing rate limits
   - IP-based user identification
   - Handles X-Forwarded-For and X-Real-IP headers for proxy/load balancer support

3. **Redis Client** (`app/core/redis_client.py`)
   - Connection pool management for Redis
   - Async Redis client with proper cleanup

### How It Works

1. **User Identification**: Non-authenticated users are identified by their IP address
2. **Redis Keys**: Format: `rate_limit:guest:{ip_address}:{date}`
3. **Counters**: Each request increments a counter in Redis
4. **TTL**: Keys automatically expire at midnight UTC
5. **Check & Increment**: Rate limit is checked before processing, then incremented

## API Endpoints

### Protected Endpoints

The following endpoints are rate-limited for guest users:

- `POST /chat/message` - Send a chat message
- `POST /chat/message/stream` - Send a chat message with streaming response

### Rate Limit Info Endpoint

```http
GET /chat/rate-limit
```

Returns current usage information:

**Response for Guest Users:**
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

**Response for Authenticated Users:**
```json
{
  "type": "authenticated",
  "usage": null,
  "limit": null,
  "remaining": "unlimited",
  "reset_at": null
}
```

### Rate Limit Exceeded Response

When a guest user exceeds their limit, they receive a `429 Too Many Requests` response:

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

## Configuration

### Environment Variables

The rate limiting uses existing Redis configuration from `.env`:

```env
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=5
REDIS_SOCKET_TIMEOUT=5
REDIS_CONNECTION_TIMEOUT=5
REDIS_RETRY_ON_TIMEOUT=true
```

### Adjusting the Daily Limit

To change the daily limit, modify the `daily_limit` value in `app/services/rate_limit_service.py`:

```python
class RateLimitService:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.daily_limit = 3  # Change this value
```

## Testing

### Test Rate Limiting

1. **As a Guest User:**

```bash
# First request (should succeed)
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test-session"}'

# Check remaining requests
curl http://localhost:8000/chat/rate-limit

# Make 2 more requests (should succeed)
# ... repeat the POST request 2 more times ...

# Fourth request (should fail with 429)
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello again", "session_id": "test-session"}'
```

2. **As an Authenticated User:**

```bash
# Login first
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use the token for unlimited requests
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"message": "Hello", "session_id": "test-session"}'
```

### Manual Reset (Admin/Testing)

You can manually reset a user's rate limit using Redis CLI:

```bash
# Connect to Redis
redis-cli

# Find rate limit keys for today
KEYS rate_limit:guest:*:2025-10-01

# Delete a specific user's rate limit
DEL rate_limit:guest:192.168.1.100:2025-10-01

# Or clear all rate limits
KEYS rate_limit:guest:* | xargs redis-cli DEL
```

## Frontend Integration

### Displaying Rate Limit Information

```javascript
// Check rate limit status before sending message
async function checkRateLimit() {
  const response = await fetch('/chat/rate-limit');
  const data = await response.json();
  
  if (data.type === 'guest') {
    console.log(`Remaining requests: ${data.remaining}`);
    console.log(`Resets at: ${data.reset_at}`);
    
    // Show warning when close to limit
    if (data.remaining === 1) {
      alert('You have 1 free request remaining today!');
    }
  }
}

// Handle rate limit exceeded error
async function sendMessage(message) {
  try {
    const response = await fetch('/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    
    if (response.status === 429) {
      const error = await response.json();
      // Show error message with signup prompt
      showRateLimitModal(error.detail);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

function showRateLimitModal(details) {
  // Display a modal encouraging user to sign up
  alert(`${details.message}\n\nLimit resets in ${formatTime(details.reset_in_seconds)}`);
}
```

### UI Recommendations

1. **Show remaining requests** in the chat interface
2. **Warning at 1 remaining** - encourage signup
3. **Rate limit modal** - when limit is reached, show signup/login options
4. **Reset countdown** - display time until next reset
5. **Authenticated badge** - show "Unlimited" for logged-in users

## IP Address Considerations

### Proxy/Load Balancer Support

The implementation checks headers in this order:
1. `X-Forwarded-For` (takes first IP if multiple)
2. `X-Real-IP`
3. Direct client IP

### Limitations of IP-Based Rate Limiting

- **VPNs**: Users can change IP to bypass limits
- **Shared IPs**: Multiple users behind same NAT may share limits
- **Dynamic IPs**: User's IP may change between sessions

### Enhancements (Future)

For more robust user identification:
1. **Browser Fingerprinting**: Combine IP with browser characteristics
2. **Cookies**: Set a unique identifier cookie
3. **Device ID**: Use localStorage to track device
4. **Combination Approach**: Use multiple factors for identification

## Monitoring

### Redis Keys to Monitor

```bash
# Count active rate limits today
redis-cli KEYS "rate_limit:guest:*:$(date +%Y-%m-%d)" | wc -l

# See all IPs that hit the limit today
redis-cli KEYS "rate_limit:guest:*:$(date +%Y-%m-%d)" | while read key; do
  count=$(redis-cli GET "$key")
  if [ "$count" -ge 3 ]; then
    echo "$key: $count"
  fi
done
```

### Metrics to Track

1. Number of rate-limited requests per day
2. IPs hitting the rate limit
3. Conversion rate (guest → signup after hitting limit)
4. Average requests per guest user

## Benefits of This Implementation

✅ **Fast**: Redis-based, sub-millisecond lookups  
✅ **Scalable**: Works across multiple server instances  
✅ **Automatic**: Daily resets without cron jobs  
✅ **Informative**: Provides detailed feedback to users  
✅ **Non-intrusive**: Authenticated users unaffected  
✅ **Flexible**: Easy to adjust limits and timeframes  

## Troubleshooting

### Rate Limiting Not Working

1. **Check Redis Connection:**
```bash
redis-cli ping
# Should return: PONG
```

2. **Verify Redis URL in .env:**
```bash
cat .env | grep REDIS_URL
```

3. **Check Application Logs:**
```bash
# Look for Redis connection errors
tail -f logs/app.log | grep -i redis
```

### False Positives

If legitimate users are being rate-limited unexpectedly:

1. Check if they're behind a proxy/NAT
2. Verify X-Forwarded-For header is being passed correctly
3. Consider increasing the daily limit for your use case

### Reset Not Working

If limits don't reset at midnight:

1. Verify Redis TTL is set correctly:
```bash
redis-cli TTL rate_limit:guest:YOUR_IP:$(date +%Y-%m-%d)
```

2. Check server timezone vs UTC
3. Verify Redis persistence is enabled if needed

## Security Considerations

1. **DDoS Protection**: Rate limiting helps prevent abuse
2. **No PII Storage**: Only IP addresses are stored temporarily
3. **Automatic Cleanup**: Keys expire daily, no manual cleanup needed
4. **Bypass for Auth**: Authenticated users not rate-limited
5. **Informative Errors**: Users know why they're limited and when it resets

## Alternative Approaches Considered

| Approach | Pros | Cons | Chosen? |
|----------|------|------|---------|
| Redis + IP | Fast, distributed, automatic TTL | Can be bypassed with VPN | ✅ Yes |
| MongoDB | Persistent, query-able | Slower, requires cleanup jobs | ❌ No |
| In-Memory | Fastest | Lost on restart, not distributed | ❌ No |
| Cookies | Survives IP changes | Easy to clear/bypass | ❌ No (could enhance) |
| Browser Fingerprint | More robust | Complex, privacy concerns | ❌ No (future) |

## License & Credits

This implementation is part of the Staiz API project.

