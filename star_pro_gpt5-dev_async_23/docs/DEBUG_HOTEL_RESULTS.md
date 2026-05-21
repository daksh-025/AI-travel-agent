# 🔍 Debug: Hotel Results Not Appearing in Streaming

## 🎯 **Problem**
Hotel search tool is being called, but hotel search results are not appearing in the streaming response.

## 🔧 **Debugging Steps Added**

### 1. **Agent Debug Logging**
Added logging to track:
- Tool usage information
- SerpAPI tool execution
- Tool outputs and parsing
- Response structure

### 2. **Streaming Service Debug Logging**
Added logging to track:
- Response hotelSearch field
- Response webSearch field  
- Response message content

### 3. **Tool Callback Debug Logging**
Added logging to track:
- When tools start
- Tool inputs
- When tools end
- Tool outputs and their types

## 🧪 **Debug Scripts**

### Quick Debug:
```bash
python debug_streaming.py
```

### Comprehensive Test:
```bash
python test_hotel_streaming.py
```

## 🔍 **What to Check**

### 1. **Server Logs**
When you run the streaming test, check the server logs for:

```
🔧 Tool started: serpapi_hotels
🔧 Tool input: {"location": "Sydney", "check_in": "2024-01-01"...}
🔧 Tool ended: serpapi_hotels
🔧 Tool output type: <class 'str'>
🔧 Tool output length: 1234
🔧 Tool output preview: {"search_parameters": {"q": "hotels in Sydney"...
```

### 2. **Tool Usage Info**
Look for:
```
Tool usage info: {'tools_used': ['serpapi_hotels'], 'serpapi_hotels_used': True, ...}
SerpAPI used: True
Hotel search raw output: {"search_parameters": {...}, "properties": [...]}
```

### 3. **Response Structure**
Look for:
```
Response hotelSearch: HotelSearchResponse(resultsTitle='Hotels in Sydney', results=[...])
Response webSearch: None
Response message: "Here are some great hotels in Sydney..."
```

## 🚨 **Common Issues**

### Issue 1: Tool Not Being Called
**Symptoms:** No "Tool started" logs
**Causes:**
- API keys not configured
- Tool not enabled
- Agent not recognizing hotel search request

**Fix:**
- Check SerpAPI key in environment
- Verify tool is enabled in agent
- Use more explicit hotel search language

### Issue 2: Tool Called But No Output
**Symptoms:** "Tool started" but no "Tool ended" or empty output
**Causes:**
- SerpAPI API error
- Network issues
- Invalid search parameters

**Fix:**
- Check SerpAPI quota/credits
- Verify network connectivity
- Test with simpler search terms

### Issue 3: Tool Output Not Parsed
**Symptoms:** Tool output exists but hotelSearch is None
**Causes:**
- JSON parsing error
- Invalid response format
- Parsing logic bug

**Fix:**
- Check parse_serpapi_hotel_results method
- Verify JSON structure
- Add error handling

### Issue 4: Streaming Service Issue
**Symptoms:** hotelSearch exists but not sent in stream
**Causes:**
- Event not being yielded
- Frontend not handling event
- Event ordering issue

**Fix:**
- Check streaming service logic
- Verify event types
- Test frontend event handling

## 🎯 **Expected Flow**

### Successful Hotel Search:
```
1. User: "Find hotels in Sydney"
2. 🔧 Tool started: serpapi_hotels
3. 🔧 Tool ended: serpapi_hotels (with JSON output)
4. SerpAPI used: True
5. Hotel search raw output: {...}
6. Parsed hotel search results: HotelSearchResponse(...)
7. Response hotelSearch: HotelSearchResponse(...)
8. 🏨 HOTEL RESULTS EVENT sent
9. Text streaming starts
```

## 🚀 **Quick Fixes to Try**

### 1. **Check API Keys**
```bash
echo $SERPAPI_API_KEY
```

### 2. **Test Regular Endpoint**
```bash
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Find hotels in Sydney"}'
```

### 3. **Check Tool Configuration**
Look in server logs for tool initialization:
```
SerpAPI Hotels tool initialized
Tools available: ['serpapi_hotels', 'tavily_web_search']
```

### 4. **Verify Request Format**
Use explicit hotel search language:
- "Find hotels in Sydney"
- "Search for accommodation in Sydney"
- "Show me hotels in Sydney CBD"

## 📋 **Debug Checklist**

- [ ] Server is running with debug logging
- [ ] SerpAPI key is configured
- [ ] Tool is being called (check logs)
- [ ] Tool is returning output (check logs)
- [ ] Output is being parsed (check logs)
- [ ] Response has hotelSearch field (check logs)
- [ ] Streaming service sends hotel_results event (check logs)
- [ ] Frontend receives and displays hotel results (check browser console)

## 🎉 **Success Indicators**

When working correctly, you should see:
1. **Server logs:** Tool execution and parsing
2. **Stream events:** `hotel_results` event
3. **Frontend:** Hotel results displayed with green indicator
4. **Console:** "🏨 Hotel results received" message

The debugging will help identify exactly where the issue is occurring in the pipeline!
