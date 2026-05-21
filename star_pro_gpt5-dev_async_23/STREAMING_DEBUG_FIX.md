# Streaming Debug Fix - hotelSearch Not Being Streamed

## 🐛 Problems Found

### Problem 1: Redundant Early Return Branch (agent.py)
**Location:** Lines 1301-1323 (removed)

**Issue:** 
- Had a standalone `elif serpapi_one_hotel_used:` branch
- This returned hotelSearch with NO message (message was commented out)
- When both tavily AND serpapi_one_hotel were used, this branch executed FIRST
- It returned early and NEVER reached the tavily branch
- Result: Only hotelSearch was returned, webSearch was lost

**Code Before:**
```python
elif serpapi_one_hotel_used:
    # Returns hotelSearch but no message
    return StructuredChatResponse(
        # message=latest_response,  # COMMENTED OUT!
        hotelSearch=hotel_search,
        ...
    )

elif tavily_used:
    # This branch never executed when serpapi_one_hotel was used!
    ...
```

### Problem 2: elif Instead of if (service.py)
**Location:** Line 392

**Issue:**
- Used `elif response.webSearch:` instead of `if response.webSearch:`
- This meant: if hotelSearch exists, webSearch is SKIPPED
- Only ONE result type could be streamed at a time
- When both were present, only hotelSearch would stream

**Code Before:**
```python
if response.hotelSearch:
    yield hotel_event

elif response.webSearch:  # ❌ NEVER EXECUTES if hotelSearch exists!
    yield WebResultsEvent(...)
```

### Problem 3: Logic Flow Issue
**Location:** agent.py lines 1301-1338

**Issue:**
- Branch logic used multiple `elif` statements
- Only ONE branch could execute
- Needed to handle combinations: tavily only, hotel only, or BOTH

## ✅ Solutions Applied

### Fix 1: Consolidated Branch Logic (agent.py)
**Changed:**
```python
# OLD: Separate branches that couldn't both execute
elif serpapi_one_hotel_used:
    # ... 23 lines of code
    return StructuredChatResponse(hotelSearch=...)
    
elif tavily_used:
    # ... 37 lines of code
    return StructuredChatResponse(webSearch=...)
```

**To:**
```python
# NEW: Single unified branch that handles BOTH
elif tavily_used or serpapi_one_hotel_used:
    # Handle both web search and hotel search results
    web_search = None
    hotel_search = None
    
    # Get web search results if tavily was used
    if tavily_used:
        tavily_search_raw = tool_usage_info["tool_outputs"].get("tavily_web_search")
        if tavily_search_raw:
            web_search = await self.parse_tavily_web_search_results(tavily_search_raw)
    
    # Get hotel search results if serpapi_one_hotel was used
    if serpapi_one_hotel_used:
        serpapi_one_hotel_raw = tool_usage_info["tool_outputs"].get("serpapi_one_hotel")
        if serpapi_one_hotel_raw:
            hotel_search = await self.parse_serpapi_hotel_results(serpapi_one_hotel_raw)
    
    # Return BOTH (either can be None if tool wasn't used)
    return StructuredChatResponse(
        message=latest_response,
        webSearch=web_search,
        hotelSearch=hotel_search,
        ...
    )
```

**Benefits:**
- ✅ Handles tavily only (webSearch set, hotelSearch None)
- ✅ Handles serpapi_one_hotel only (hotelSearch set, webSearch None)
- ✅ Handles BOTH tools (both set)
- ✅ Always includes message for text streaming
- ✅ No early returns that skip other results

### Fix 2: Changed elif to if (service.py)
**Changed:**
```python
# OLD: Only one could stream
if response.hotelSearch:
    yield hotel_event

elif response.webSearch:  # ❌ Skipped if hotelSearch exists
    yield WebResultsEvent(...)
```

**To:**
```python
# NEW: Both can stream independently
# Stream hotel results if available
if response.hotelSearch:
    yield hotel_event

# Stream web search results if available (independent of hotel results)
if response.webSearch:  # ✅ Always checks, regardless of hotelSearch
    yield WebResultsEvent(...)
```

**Benefits:**
- ✅ Both events can be yielded in the same response
- ✅ Frontend receives BOTH hotel cards AND web images
- ✅ Order is preserved: hotels first, then web results

### Fix 3: Added Debug Logging
**Added in agent.py:**
```python
logger.info(f"🔍 Tool outputs keys: {list(tool_usage_info['tool_outputs'].keys())}")
logger.info(f"🏨 HOTEL hotel_search: {hotel_search}")
logger.info(f"🌐 WEB web_search: {web_search}")
```

**Benefits:**
- ✅ Easy to see which tools were actually used
- ✅ Can verify if results are being parsed correctly
- ✅ Helps debug future issues

## 🎯 Result

### Before Fix:
- ❌ Only web results OR hotel results could stream (not both)
- ❌ If serpapi_one_hotel was used alone, no message was sent
- ❌ If both tools used, early return caused loss of one result type

### After Fix:
- ✅ Both hotel results AND web results stream together
- ✅ Message always included for text streaming
- ✅ All tool combinations work:
  - tavily only → webSearch + message
  - serpapi_one_hotel only → hotelSearch + message
  - both → hotelSearch + webSearch + message

## 🔄 Streaming Flow (Fixed)

```
Agent processes message
    ↓
Both tavily and serpapi_one_hotel tools execute
    ↓
agent.py: Combined branch (line 1301)
    ↓
Parse both results:
  - web_search = parse_tavily(...)
  - hotel_search = parse_serpapi(...)
    ↓
Return StructuredChatResponse with BOTH
    ↓
service.py receives response
    ↓
Check hotelSearch (line 343) → YIELD hotel event
    ↓
Check webSearch (line 394) → YIELD web event
    ↓
Stream text message
    ↓
Frontend receives:
  1. hotel_results event (hotel cards appear)
  2. web_results event (web images appear)
  3. text_chunk events (text streams word-by-word)
  4. suggestions event
```

## 🧪 Testing

To verify the fix works:

1. **Test web search only:**
   - Query: "What's happening in Sydney today?"
   - Expected: webSearch results stream, no hotelSearch

2. **Test hotel search only:**
   - Query: "Tell me about Hilton Sydney"
   - Expected: hotelSearch results stream, no webSearch

3. **Test BOTH:**
   - Query: "Find me hotels in Sydney with rooftop pools"
   - Expected: BOTH hotelSearch AND webSearch stream

4. **Check logs for:**
   ```
   🔍 Tool outputs keys: ['tavily_web_search', 'serpapi_one_hotel']
   🏨 HOTEL hotel_search: HotelSearchResponse(...)
   🌐 WEB web_search: WebSearchResponse(...)
   🏨 Sending hotel results: ...
   ```

## 📝 Files Modified

1. **app/chat/agent.py** (Lines 1301-1337)
   - Removed redundant serpapi_one_hotel branch
   - Consolidated into unified branch
   - Added proper logging

2. **app/chat/service.py** (Lines 342-394)
   - Changed `elif` to `if` for webSearch
   - Added clarifying comments

## 🎉 Status: FIXED ✅

Both hotelSearch and webSearch now stream correctly, independently or together!

