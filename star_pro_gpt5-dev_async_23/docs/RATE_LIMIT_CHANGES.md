# Rate Limit Configuration Changes

## Summary

The rate limit is now **configurable via environment variable** instead of being hardcoded!

## What Changed

### 1. Added Configuration Setting

**File:** `app/core/config.py`

Added new setting:
```python
# Rate Limiting Configuration
guest_rate_limit_per_day: int = 3  # Number of chat requests allowed per day for non-authenticated users
```

### 2. Updated Rate Limit Service

**File:** `app/services/rate_limit_service.py`

Changed from:
```python
self.daily_limit = 3  # Hardcoded ❌
```

To:
```python
self.daily_limit = settings.guest_rate_limit_per_day  # From config ✅
```

### 3. Updated Error Message

**File:** `app/middleware/rate_limit.py`

The error message now dynamically shows the configured limit:
```python
"message": f"You have reached your daily limit of {settings.guest_rate_limit_per_day} free chat requests..."
```

## How to Use

### Method 1: Environment Variable (Recommended)

Add to your `.env` file:
```env
GUEST_RATE_LIMIT_PER_DAY=5
```

Then restart the application:
```bash
uvicorn main:app --reload
```

### Method 2: Command Line

Set when starting the server:
```bash
GUEST_RATE_LIMIT_PER_DAY=10 uvicorn main:app --reload
```

### Method 3: Modify Default in Code

Edit `app/core/config.py`:
```python
guest_rate_limit_per_day: int = 5  # Change default
```

## Quick Examples

**Allow 5 requests per day:**
```bash
echo "GUEST_RATE_LIMIT_PER_DAY=5" >> .env
```

**Allow 10 requests per day:**
```bash
echo "GUEST_RATE_LIMIT_PER_DAY=10" >> .env
```

**Testing (1 request to test quickly):**
```bash
GUEST_RATE_LIMIT_PER_DAY=1 uvicorn main:app --reload
```

**Generous (for development):**
```bash
GUEST_RATE_LIMIT_PER_DAY=100 >> .env
```

## Check Current Configuration

Run the helper script:
```bash
python show_rate_limit_config.py
```

Or via API:
```bash
curl http://localhost:8000/chat/rate-limit
```

## Files Modified

1. ✅ `app/core/config.py` - Added `guest_rate_limit_per_day` setting
2. ✅ `app/services/rate_limit_service.py` - Uses config instead of hardcoded value
3. ✅ `app/middleware/rate_limit.py` - Dynamic error message
4. ✅ `RATE_LIMITING.md` - Updated documentation
5. ✅ `CONFIGURATION.md` - Created configuration guide
6. ✅ `show_rate_limit_config.py` - Created helper script

## Benefits

✅ **Easy to change** - Just edit .env file  
✅ **No code changes needed** - Configure without touching code  
✅ **Environment-specific** - Different limits for dev/staging/prod  
✅ **Dynamic** - Can be set at runtime via environment variable  
✅ **Well-documented** - Clear configuration options  

## Next Steps

1. Add `GUEST_RATE_LIMIT_PER_DAY=3` to your `.env` file (or use your preferred limit)
2. Restart your application
3. Test the new configuration with: `python show_rate_limit_config.py`
4. Verify with: `curl http://localhost:8000/chat/rate-limit`

## Notes

- **Default value:** 3 requests per day (if not configured)
- **Restart required:** Application must be restarted after changing .env
- **Applies to:** Non-authenticated users only
- **Authenticated users:** Always have unlimited access
- **Reset time:** Midnight UTC daily

Enjoy your configurable rate limiting! 🎉

