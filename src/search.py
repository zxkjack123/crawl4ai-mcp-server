from typing import List, Dict, Optional
import httpx
import json
import os
import logging
from abc import ABC, abstractmethod
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class SearchResult:
    def __init__(self, title: str, link: str, snippet: str, source: str):
        self.title = title
        self.link = link
        self.snippet = snippet
        self.source = source

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "link": self.link,
            "snippet": self.snippet,
            "source": self.source
        }

class SearchEngine(ABC):
    @abstractmethod
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        pass

class DuckDuckGoSearch(SearchEngine):
    def __init__(self):
        self.ddgs = DDGS()
        
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        try:
            # 使用duckduckgo_search库进行搜索
            # 设置region为wt-wt(全球),safesearch为moderate(适中)
            raw_results = self.ddgs.text(
                keywords=query,
                region="wt-wt",
                safesearch="moderate",
                max_results=num_results
            )
            
            logger.info(f"DuckDuckGo search successful for query: {query}")
            
            results = []
            for item in raw_results:
                results.append(SearchResult(
                    title=item.get('title', ''),
                    link=item.get('href', ''),  # duckduckgo_search使用'href'作为链接字段
                    snippet=item.get('body', ''),  # duckduckgo_search使用'body'作为摘要字段
                    source='duckduckgo'
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {str(e)}")
            return []

class GoogleSearch(SearchEngine):
    def __init__(self, api_key: str, cse_id: str):
        self.api_key = api_key
        self.cse_id = cse_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        if not self.api_key or not self.cse_id:
            logger.warning("Google search credentials not configured")
            return []
            
        # Use HTTP proxy if available, ignore socks5 proxy
        import os
        proxies = None
        http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
        
        if http_proxy and http_proxy.startswith('http'):
            proxies = {
                "http://": http_proxy,
                "https://": https_proxy or http_proxy
            }
        
        async with httpx.AsyncClient(timeout=30.0, proxies=proxies) as client:
            try:
                params = {
                    'key': self.api_key,
                    'cx': self.cse_id,
                    'q': query,
                    'num': min(num_results, 10)
                }
                
                logger.info(f"Sending request to Google: {query}")
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                logger.info("Google search request successful")
            except Exception as e:
                logger.error(f"Google search failed: {str(e)}")
                return []
            
            results = []
            for item in data.get('items', []):
                results.append(SearchResult(
                    title=item.get('title', ''),
                    link=item.get('link', ''),
                    snippet=item.get('snippet', ''),
                    source='google'
                ))
                
            return results

class BraveSearch(SearchEngine):
    def __init__(self, api_key: str):
        """
        初始化 Brave Search 搜索引擎
        
        Args:
            api_key: Brave Search API 密钥
        """
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """
        使用 Brave Search API 进行搜索
        
        Args:
            query: 搜索查询字符串
            num_results: 需要返回的结果数量
            
        Returns:
            搜索结果列表
        """
        if not self.api_key:
            logger.warning("Brave Search API key not configured")
            return []
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    'Accept': 'application/json',
                    'X-Subscription-Token': self.api_key
                }
                
                params = {
                    'q': query,
                    'count': min(num_results, 20)  # Brave API 最多支持 20 个结果
                }
                
                logger.info(f"Sending request to Brave Search with query: {query}")
                
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                web_results = data.get('web', {}).get('results', [])
                logger.info(f"Brave Search successful, got {len(web_results)} results")
                
                for item in web_results[:num_results]:
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        link=item.get('url', ''),
                        snippet=item.get('description', ''),
                        source='brave'
                    ))
                
                return results
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Brave Search API key is invalid or expired")
            elif e.response.status_code == 429:
                logger.error("Brave Search API rate limit exceeded")
            else:
                logger.error(f"Brave Search HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Brave Search failed: {str(e)}")
            return []

class SearXNGSearch(SearchEngine):
    def __init__(self, base_url: str = "http://localhost:8080", language: str = "zh-CN"):
        """
        初始化 SearXNG 搜索引擎
        
        Args:
            base_url: SearXNG 实例的基础 URL (例如: http://localhost:8080 或 https://searx.example.com)
            language: 搜索语言，默认为 zh-CN (中文)
        """
        self.base_url = base_url.rstrip('/')
        self.language = language
        
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """
        使用 SearXNG 进行搜索
        
        Args:
            query: 搜索查询字符串
            num_results: 需要返回的结果数量
            
        Returns:
            搜索结果列表
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    'q': query,
                    'format': 'json',
                    'language': self.language,
                    'pageno': 1
                }
                
                search_url = f"{self.base_url}/search"
                logger.info(f"Sending request to SearXNG: {search_url} with query: {query}")
                
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"SearXNG search successful, got {len(data.get('results', []))} results")
                
                results = []
                for item in data.get('results', [])[:num_results]:
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        link=item.get('url', ''),
                        snippet=item.get('content', ''),
                        source='searxng'
                    ))
                
                return results
                
        except httpx.HTTPError as e:
            logger.error(f"SearXNG HTTP error: {str(e)}")
            logger.warning("如果 SearXNG 未运行，请使用 'docker run -d -p 8080:8080 searxng/searxng' 启动")
            return []
        except Exception as e:
            logger.error(f"SearXNG search failed: {str(e)}")
            return []

class SearchManager:
    def __init__(self):
        self.engines: List[SearchEngine] = []
        self.fallback_engines: List[SearchEngine] = []  # 回退引擎列表
        self._initialize_engines()
        
    def _initialize_engines(self):
        # 总是添加DuckDuckGo作为默认回退引擎
        duckduckgo = DuckDuckGoSearch()
        self.fallback_engines.append(duckduckgo)
        
        # 如果配置文件存在,尝试添加其他搜索引擎
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'config.json'
        )
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                # 添加 Brave Search 搜索（优先级最高）
                if 'brave' in config:
                    brave_config = config['brave']
                    if brave_config.get('api_key'):
                        brave_engine = BraveSearch(
                            api_key=brave_config['api_key']
                        )
                        self.engines.append(brave_engine)
                        logger.info("Brave Search engine initialized")
                    
                # 添加 Google 搜索
                if 'google' in config:
                    google_config = config['google']
                    if (google_config.get('api_key') and
                            google_config.get('cse_id')):
                        google_engine = GoogleSearch(
                            api_key=google_config['api_key'],
                            cse_id=google_config['cse_id']
                        )
                        self.engines.append(google_engine)
                        self.fallback_engines.append(google_engine)
                        logger.info("Google search engine initialized")
                
                # 添加 SearXNG 搜索
                if 'searxng' in config:
                    searxng_config = config['searxng']
                    base_url = searxng_config.get(
                        'base_url', 'http://localhost:8080'
                    )
                    language = searxng_config.get('language', 'zh-CN')
                    searxng_engine = SearXNGSearch(
                        base_url=base_url,
                        language=language
                    )
                    self.engines.append(searxng_engine)
                    self.fallback_engines.append(searxng_engine)
                    logger.info(
                        f"SearXNG search engine initialized: {base_url}"
                    )
                    
            except Exception as e:
                logger.error(
                    f"Failed to load search configuration: {e}"
                )
        
        # 如果没有配置任何引擎，确保至少有 DuckDuckGo
        if not self.engines:
            self.engines.append(duckduckgo)
            logger.info("No engines configured, using DuckDuckGo as default")
                
    async def search(
            self,
            query: str,
            num_results: int = 10,
            engine: str = "auto"
    ) -> List[Dict]:
        """
        执行搜索，支持自动回退机制
        
        Args:
            query: 搜索查询字符串
            num_results: 返回结果数量
            engine: 搜索引擎选择 (auto/brave/google/duckduckgo/searxng/all)
                   - auto: 自动选择，优先使用配置的引擎，失败时自动回退
                   - brave/google/duckduckgo/searxng: 使用指定引擎
                   - all: 使用所有可用引擎
        
        Returns:
            搜索结果列表
        """
        all_results = []
        
        if not self.engines and not self.fallback_engines:
            logger.warning("No search engines available")
            return []

        logger.info(
            f"Starting search with query: {query}, "
            f"engine: {engine}, num_results: {num_results}"
        )
        
        # 确定要使用的引擎列表
        engines_to_try = []
        
        if engine.lower() == "all":
            # 使用所有可用的引擎
            engines_to_try = self.engines + [e for e in self.fallback_engines if e not in self.engines]
        elif engine.lower() == "auto":
            # 自动模式：优先使用配置的引擎，失败时回退
            engines_to_try = self.engines if self.engines else self.fallback_engines
        else:
            # 指定引擎模式
            for search_engine in self.engines + self.fallback_engines:
                engine_name = search_engine.__class__.__name__.lower()
                if engine_name.startswith('brave'):
                    engine_type = 'brave'
                elif engine_name.startswith('duckduckgo'):
                    engine_type = 'duckduckgo'
                elif engine_name.startswith('google'):
                    engine_type = 'google'
                elif engine_name.startswith('searxng'):
                    engine_type = 'searxng'
                else:
                    engine_type = engine_name
                    
                if engine_type == engine.lower():
                    engines_to_try = [search_engine]
                    break
        
        # 如果没有找到指定的引擎，使用回退引擎
        if not engines_to_try and engine.lower() not in ["all", "auto"]:
            logger.warning(f"Requested engine '{engine}' not available, using fallback engines")
            engines_to_try = self.fallback_engines
        
        # 尝试每个引擎进行搜索
        for search_engine in engines_to_try:
            engine_name = search_engine.__class__.__name__
            
            try:
                results = await search_engine.search(query, num_results)
                logger.info(
                    f"Got {len(results)} results from {engine_name}"
                )
                
                if results:
                    logger.info(f"First result type: {type(results[0])}")
                    converted_results = [r.to_dict() for r in results]
                    logger.info(f"Converted results: {converted_results}")
                    all_results.extend(converted_results)
                    
                    # 如果是 auto 模式且已获得足够结果，则停止尝试其他引擎
                    if engine.lower() == "auto" and len(all_results) >= num_results:
                        logger.info(f"Got enough results from {engine_name}, stopping")
                        break
                else:
                    logger.warning(f"No results from {engine_name}, trying next engine")
                    
            except Exception as e:
                logger.error(
                    f"Search failed for {engine_name}: {str(e)}",
                    exc_info=True
                )
                # 继续尝试下一个引擎
                if engine.lower() == "auto":
                    logger.info(f"Trying fallback engines due to {engine_name} failure")
                
        final_results = all_results[:num_results]
        logger.info(f"Returning {len(final_results)} total results")
        
        if not final_results:
            logger.warning("All search engines failed to return results")
            
        return final_results