import requests
import json
import time

BASE_URL = "http://localhost:18080"

def test_health():
    print("Testing /health...")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        resp.raise_for_status()
        data = resp.json()
        print("✅ Health check passed")
        print(json.dumps(data, indent=2))
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_read_url():
    print("\nTesting /read_url...")
    url = "https://example.com"
    payload = {
        "url": url,
        "format": "markdown_with_citations"
    }
    try:
        start = time.time()
        resp = requests.post(f"{BASE_URL}/read_url", json=payload)
        resp.raise_for_status()
        data = resp.json()
        duration = time.time() - start
        
        if "content" in data and "Example Domain" in data["content"]:
            print(f"✅ Read URL passed ({duration:.2f}s)")
            print(f"Content length: {len(data['content'])}")
        else:
            print("❌ Read URL failed: Content mismatch or missing")
            print(data)
    except Exception as e:
        print(f"❌ Read URL failed: {e}")

def test_search():
    print("\nTesting /search...")
    query = "test query"
    payload = {
        "query": query,
        "num_results": 3,
        "engine": "duckduckgo"
    }
    try:
        start = time.time()
        resp = requests.post(f"{BASE_URL}/search", json=payload)
        resp.raise_for_status()
        data = resp.json()
        duration = time.time() - start
        
        results = data.get("results", [])
        if results and len(results) > 0:
            print(f"✅ Search passed ({duration:.2f}s)")
            print(f"Found {len(results)} results")
            print(f"First result: {results[0].get('title')}")
        else:
            print("⚠️ Search returned no results (but request succeeded)")
            print(data)
    except Exception as e:
        print(f"❌ Search failed: {e}")

if __name__ == "__main__":
    print(f"Target: {BASE_URL}")
    if test_health():
        test_read_url()
        test_search()
