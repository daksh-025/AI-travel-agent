#!/usr/bin/env python3
"""
Debug script to test streaming and see what's happening with hotel results
"""
import asyncio
import aiohttp
import json
import sys


async def debug_streaming():
    """Debug the streaming to see what's happening"""
    url = "http://localhost:8000/chat/message/stream"
    
    # Simple hotel search request
    payload = {
        "message": "Find hotels in Sydney",
        "session_id": "debug-session",
        "enable_progress": True,
        "streaming_speed": "fast"
    }
    
    print("🔍 Debug: Hotel Search Streaming")
    print(f"Request: {payload['message']}")
    print("=" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    print(f"❌ HTTP Error: {response.status}")
                    text = await response.text()
                    print(f"Response: {text}")
                    return
                
                print("✅ Connected to streaming endpoint")
                print("📡 Events:")
                print("-" * 30)
                
                event_count = 0
                hotel_results_found = False
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        event_data = line[6:]
                        if event_data.strip():
                            try:
                                event = json.loads(event_data)
                                event_count += 1
                                event_type = event.get('event_type', 'unknown')
                                
                                print(f"[{event_count:2d}] {event_type.upper()}")
                                
                                if event_type == 'progress':
                                    progress = event.get('progress', {})
                                    message = progress.get('message', '')
                                    percentage = progress.get('percentage', 0)
                                    print(f"    {message} ({percentage}%)")
                                
                                elif event_type == 'hotel_results':
                                    hotel_results_found = True
                                    hotel_search = event.get('hotel_search', {})
                                    title = hotel_search.get('resultsTitle', 'No title')
                                    results = hotel_search.get('results', [])
                                    print(f"    🏨 HOTEL RESULTS FOUND!")
                                    print(f"    Title: {title}")
                                    print(f"    Count: {len(results)} hotels")
                                    
                                    if results:
                                        for i, hotel in enumerate(results[:2], 1):
                                            name = hotel.get('name', 'Unknown')
                                            price = hotel.get('price', 'No price')
                                            print(f"      {i}. {name} - {price}")
                                
                                elif event_type == 'text_chunk':
                                    chunk = event.get('chunk', {})
                                    content = chunk.get('content', '')
                                    if content.strip():
                                        print(f"    Text: '{content}'")
                                
                                elif event_type == 'suggestions':
                                    suggestions = event.get('suggestions', [])
                                    print(f"    Suggestions: {len(suggestions)} items")
                                
                                elif event_type == 'complete':
                                    print(f"    ✅ Complete")
                                    break
                                
                                elif event_type == 'error':
                                    error_msg = event.get('error_message', 'Unknown error')
                                    print(f"    ❌ Error: {error_msg}")
                                
                            except json.JSONDecodeError as e:
                                print(f"    ⚠️  JSON Error: {e}")
                                print(f"    Raw: {event_data[:100]}...")
                
                print("-" * 30)
                print(f"Total events: {event_count}")
                print(f"Hotel results found: {'✅ YES' if hotel_results_found else '❌ NO'}")
                
                if not hotel_results_found:
                    print("\n🔍 Debugging steps:")
                    print("1. Check server logs for tool usage info")
                    print("2. Verify SerpAPI tool is working")
                    print("3. Check if agent is calling the tool")
                    print("4. Verify tool output parsing")
                
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🧪 Debug Streaming Test")
    print("This will help identify why hotel results aren't appearing")
    print()
    
    asyncio.run(debug_streaming())
