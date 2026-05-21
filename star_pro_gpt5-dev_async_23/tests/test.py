import tavily


search_params = {
    "query": "What is the weather in Tokyo?",
    "search_depth": "basic",
    "topic": "general",
    "max_results": 5,
    "include_images": True,
    "include_image_descriptions": True
}
client = tavily.TavilyClient(api_key="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")

response = client.search(**search_params)

print(response)