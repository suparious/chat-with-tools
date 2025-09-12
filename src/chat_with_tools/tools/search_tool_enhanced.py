"""Enhanced search tool with improved security and caching."""

import hashlib
import json
import time
from typing import Dict, List, Any, Optional
from .base_tool import BaseTool
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests
from ..utils import validate_url, setup_logging


class SearchCache:
    """Simple in-memory cache for search results."""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl: Time to live in seconds (default: 1 hour)
        """
        self.cache = {}
        self.ttl = ttl
    
    def _get_key(self, query: str, max_results: int) -> str:
        """Generate cache key from query parameters."""
        key_string = f"{query}:{max_results}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query: str, max_results: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached results if available and not expired."""
        key = self._get_key(query, max_results)
        
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['results']
            else:
                # Expired, remove from cache
                del self.cache[key]
        
        return None
    
    def set(self, query: str, max_results: int, results: List[Dict[str, Any]]) -> None:
        """Cache search results."""
        key = self._get_key(query, max_results)
        self.cache[key] = {
            'results': results,
            'timestamp': time.time()
        }
    
    def clear(self) -> None:
        """Clear all cached results."""
        self.cache.clear()


class EnhancedSearchTool(BaseTool):
    """Enhanced web search tool with security, caching, and better error handling."""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging(f"{__name__}", level="INFO")
        
        # Initialize cache
        cache_ttl = config.get('search', {}).get('cache_ttl', 3600)
        self.cache = SearchCache(ttl=cache_ttl)
        
        # Security settings
        self.max_content_length = config.get('search', {}).get('max_content_length', 5000)
        self.request_timeout = config.get('search', {}).get('request_timeout', 10)
        self.user_agent = config.get('search', {}).get('user_agent', 
                                                       'Mozilla/5.0 (compatible; Chat-with-Tools/1.0)')
        
        # Blocked domains for security
        self.blocked_domains = config.get('search', {}).get('blocked_domains', [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            '192.168.',
            '10.',
            '172.16.',
            'internal',
            '.local'
        ])
    
    @property
    def name(self) -> str:
        return "search_web"
    
    @property
    def description(self) -> str:
        return "Search the web using DuckDuckGo for current information. Returns titles, URLs, snippets, and page content."
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find information on the web"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results to return (1-10)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                },
                "fetch_content": {
                    "type": "boolean",
                    "description": "Whether to fetch and parse page content (slower but more comprehensive)",
                    "default": True
                }
            },
            "required": ["query"]
        }
    
    def _is_url_safe(self, url: str) -> bool:
        """
        Check if a URL is safe to fetch.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is safe, False otherwise
        """
        # Use utility function for basic validation
        if not validate_url(url):
            return False
        
        # Additional domain blocking
        url_lower = url.lower()
        for blocked in self.blocked_domains:
            if blocked in url_lower:
                self.logger.warning(f"Blocked URL with forbidden domain: {url}")
                return False
        
        return True
    
    def _fetch_page_content(self, url: str) -> str:
        """
        Safely fetch and parse page content.
        
        Args:
            url: URL to fetch
            
        Returns:
            Parsed text content or error message
        """
        if not self._is_url_safe(url):
            return "URL blocked for security reasons"
        
        try:
            # Set up headers
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Fetch with timeout and size limit
            response = requests.get(
                url, 
                headers=headers,
                timeout=self.request_timeout,
                allow_redirects=True,
                stream=True
            )
            
            # Check content length
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_content_length * 10:
                return "Page too large to fetch"
            
            # Read content with size limit
            content = b''
            for chunk in response.iter_content(chunk_size=1024):
                content += chunk
                if len(content) > self.max_content_length * 10:
                    return "Page too large to fetch"
            
            # Parse HTML
            response.encoding = response.apparent_encoding
            text = content.decode(response.encoding or 'utf-8', errors='ignore')
            
            soup = BeautifulSoup(text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'meta', 'link', 'noscript']):
                element.decompose()
            
            # Extract text
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Clean and truncate
            text_content = ' '.join(text_content.split())
            
            if len(text_content) > self.max_content_length:
                text_content = text_content[:self.max_content_length] + "..."
            
            return text_content
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return f"Failed to fetch content: {str(e)}"
        except Exception as e:
            self.logger.error(f"Error processing {url}: {e}")
            return f"Error processing page: {str(e)}"
    
    def execute(self, query: str, max_results: int = 5, fetch_content: bool = True) -> List[Dict[str, Any]]:
        """
        Execute web search with caching and enhanced security.
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-10)
            fetch_content: Whether to fetch page content
            
        Returns:
            List of search results with content
        """
        # Validate parameters
        max_results = min(max(max_results, 1), 10)  # Clamp between 1 and 10
        
        # Check cache first
        cached_results = self.cache.get(query, max_results)
        if cached_results and not fetch_content:
            self.logger.info(f"Returning cached results for query: {query}")
            return cached_results
        
        try:
            self.logger.info(f"Searching for: {query} (max_results={max_results})")
            
            # Perform search
            ddgs = DDGS()
            search_results = ddgs.text(query, max_results=max_results)
            
            simplified_results = []
            
            for idx, result in enumerate(search_results):
                # Build base result
                result_entry = {
                    "title": result.get('title', 'No title'),
                    "url": result.get('href', ''),
                    "snippet": result.get('body', 'No description available')
                }
                
                # Fetch content if requested and URL is valid
                if fetch_content and result_entry['url']:
                    self.logger.debug(f"Fetching content for result {idx + 1}: {result_entry['url']}")
                    result_entry['content'] = self._fetch_page_content(result_entry['url'])
                else:
                    result_entry['content'] = result_entry['snippet']
                
                simplified_results.append(result_entry)
            
            # Cache results
            self.cache.set(query, max_results, simplified_results)
            
            self.logger.info(f"Search completed: {len(simplified_results)} results")
            return simplified_results
            
        except Exception as e:
            self.logger.error(f"Search failed for query '{query}': {e}")
            return [{
                "error": f"Search failed: {str(e)}",
                "query": query
            }]
    
    def clear_cache(self) -> Dict[str, str]:
        """Clear the search cache."""
        self.cache.clear()
        return {"status": "Cache cleared successfully"}
