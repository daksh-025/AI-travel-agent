# Configuration Guide

## Rate Limiting Configuration

### Quick Setup

Add this to your `.env` file to configure the guest rate limit:

```env
GUEST_RATE_LIMIT_PER_DAY=3
```

### Examples

**Allow 5 requests per day:**
```env
GUEST_RATE_LIMIT_PER_DAY=5
```

**Allow 10 requests per day:**
```env
GUEST_RATE_LIMIT_PER_DAY=10
```

**Allow unlimited (for testing - not recommended):**
```env
GUEST_RATE_LIMIT_PER_DAY=999999
```

**Very strict (1 request per day):**
```env
GUEST_RATE_LIMIT_PER_DAY=1
```

### How It Works

1. The value is loaded from the environment variable `GUEST_RATE_LIMIT_PER_DAY`
2. If not set, it defaults to `3` (defined in `app/core/config.py`)
3. The limit applies to non-authenticated users only
4. Authenticated users have unlimited access
5. Limits reset daily at midnight UTC

### Testing Different Limits

To test different rate limits without modifying files:

```bash
# Start server with custom rate limit
GUEST_RATE_LIMIT_PER_DAY=5 uvicorn main:app --reload

# Or export for the session
export GUEST_RATE_LIMIT_PER_DAY=5
uvicorn main:app --reload
```

### Checking Current Configuration

You can check the current rate limit by:

1. **Via API:**
```bash
curl http://localhost:8000/chat/rate-limit
```

Response will show:
```json
{
  "type": "guest",
  "usage": 0,
  "limit": 3,  // <-- Current rate limit
  "remaining": 3,
  "reset_at": "2025-10-02T00:00:00Z"
}
```

2. **Via Python:**
```python
from app.core.config import settings
print(f"Current rate limit: {settings.guest_rate_limit_per_day}")
```

### Production Recommendations

**For Production:**
- Set `GUEST_RATE_LIMIT_PER_DAY=3` (default, good for most use cases)
- Monitor usage and adjust based on:
  - Conversion rates (guest → signed up user)
  - API costs
  - Server load

**For Development:**
- Set `GUEST_RATE_LIMIT_PER_DAY=10` or higher for easier testing
- Or disable rate limiting entirely during development

**For Testing:**
- Set `GUEST_RATE_LIMIT_PER_DAY=1` to test rate limit behavior quickly

### Related Configuration

Other rate limit related settings in `.env`:

```env
# Redis (required for rate limiting)
REDIS_URL=redis://localhost:6379

# JWT (for authenticated users)
ACCESS_TOKEN_EXPIRE_MINUTES=120
```

## Other Configuration Options

See individual configuration files for more options:
- `app/core/config.py` - All application settings
- `.env` - Environment-specific values
- `docker-compose.yml` - Docker configuration

## Troubleshooting

**Rate limit not working?**
1. Check Redis is running: `redis-cli ping` (should return `PONG`)
2. Verify `.env` file is loaded: `echo $GUEST_RATE_LIMIT_PER_DAY`
3. Restart the application after changing `.env`

**Need to change limit dynamically?**
Currently, you need to restart the application. For dynamic limits, you would need to implement a settings reload mechanism or use a database-backed configuration.

**Want different limits for different IPs?**
This would require modifying `RateLimitService` to support custom limits per identifier. Current implementation uses a single global limit.

