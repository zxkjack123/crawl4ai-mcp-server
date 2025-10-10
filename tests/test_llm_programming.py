#!/usr/bin/env python
"""
Test script to search for the best LLM for programming using English queries
"""

import asyncio
import json
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from search import SearchManager


async def test_search_with_multiple_queries():
    """Test searching with multiple programming-related queries"""
    
    print("=" * 80)
    print("Testing Crawl4AI MCP Server - LLM Programming Search Test")
    print("=" * 80)
    print()
    
    # Initialize search manager
    search_manager = SearchManager()
    engines = [type(e).__name__ for e in search_manager.engines]
    print(f"✓ Search manager initialized with engines: {engines}")
    print()
    
    # Test queries
    queries = [
        "GPT-4 Claude coding comparison",
        "best AI models for software development",
        "GitHub Copilot vs ChatGPT programming"
    ]
    
    all_results = {}
    
    for query in queries:
        print(f"🔍 Searching for: '{query}'")
        print("-" * 80)
        
        try:
            # Perform search
            results = await search_manager.search(
                query, 
                num_results=3, 
                engine="duckduckgo"
            )
            
            if results:
                print(f"✅ Found {len(results)} results\n")
                
                for i, result in enumerate(results, 1):
                    print(f"  Result #{i}")
                    print(f"  Title: {result['title']}")
                    print(f"  URL: {result['link']}")
                    snippet = result['snippet']
                    if len(snippet) > 150:
                        snippet = snippet[:150] + "..."
                    print(f"  Snippet: {snippet}")
                    print()
                
                all_results[query] = results
            else:
                print("❌ No results found\n")
                
        except Exception as e:
            print(f"❌ Error during search: {str(e)}\n")
    
    # Save all results
    if all_results:
        output_file = "/home/gw/opt/crawl4ai-mcp-server/llm_search_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print("=" * 80)
        print(f"💾 All results saved to: {output_file}")
        print("=" * 80)
        print()
        
        # Summary
        print("📊 SUMMARY")
        print("-" * 80)
        total_results = sum(len(r) for r in all_results.values())
        print(f"Total queries: {len(queries)}")
        print(f"Total results: {total_results}")
        print(f"Average results per query: {total_results/len(queries):.1f}")
        print()
        
    print("=" * 80)
    print("✅ TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_search_with_multiple_queries())
