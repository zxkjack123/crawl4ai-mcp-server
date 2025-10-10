#!/usr/bin/env python
"""
Test script to search for the best LLM for programming using the Crawl4AI MCP server
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from search import SearchManager

async def test_search():
    """Test searching for best LLM for programming"""
    
    print("=" * 80)
    print("Testing Crawl4AI MCP Server - Search for Best LLM for Programming")
    print("=" * 80)
    print()
    
    # Initialize search manager
    search_manager = SearchManager()
    print(f"✓ Search manager initialized with engines: {[type(e).__name__ for e in search_manager.engines]}")
    print()
    
    # Test query
    query = "best LLM for programming 2025"
    num_results = 5
    
    print(f"🔍 Searching for: '{query}'")
    print(f"📊 Requesting {num_results} results")
    print()
    
    try:
        # Perform search
        results = await search_manager.search(query, num_results=num_results, engine="duckduckgo")
        
        if not results:
            print("❌ No results found")
            return
        
        print(f"✅ Found {len(results)} results")
        print()
        print("=" * 80)
        print("SEARCH RESULTS")
        print("=" * 80)
        print()
        
        # Display results
        for i, result in enumerate(results, 1):
            print(f"Result #{i}")
            print(f"Title: {result['title']}")
            print(f"URL: {result['link']}")
            print(f"Snippet: {result['snippet'][:200]}..." if len(result['snippet']) > 200 else f"Snippet: {result['snippet']}")
            print(f"Source: {result['source']}")
            print("-" * 80)
            print()
        
        # Save results to JSON file
        output_file = "/home/gw/opt/crawl4ai-mcp-server/test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Results saved to: {output_file}")
        print()
        print("=" * 80)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error during search: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())
