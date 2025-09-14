"""
API Request Tool for Chat with Tools Framework

This tool enables making HTTP requests to external APIs with
proper authentication, error handling, and response parsing.
"""

import json
import time
import base64
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlencode, urlparse, parse_qs
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from .base_tool import BaseTool
from ..utils import validate_url, setup_logging


class APIRequestTool(BaseTool):
    """
    HTTP API request tool for interacting with external services.
    
    Supports various authentication methods, request types,
    and automatic response parsing.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging(f"{__name__}", level="INFO")
        
        # Create session with retry strategy
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Default headers
        self.default_headers = {
            'User-Agent': 'Chat-with-Tools/1.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        
        # Timeout settings
        self.timeout = config.get('api_request', {}).get('timeout', 30)
        
        # Rate limiting
        self.rate_limit_delay = config.get('api_request', {}).get('rate_limit_delay', 0)
        self.last_request_time = 0
    
    @property
    def name(self) -> str:
        return "api_request"
    
    @property
    def description(self) -> str:
        return """Make HTTP requests to external APIs with authentication support.
        
        Supports:
        - GET, POST, PUT, DELETE, PATCH methods
        - JSON, form-data, and raw body formats
        - Bearer token, API key, and basic authentication
        - Automatic JSON parsing
        - Custom headers and query parameters
        - Rate limiting and retry logic
        
        Use this for:
        - Fetching data from REST APIs
        - Submitting data to webhooks
        - Interacting with third-party services
        - Testing API endpoints
        """
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Full URL of the API endpoint"
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
                    "default": "GET",
                    "description": "HTTP method"
                },
                "headers": {
                    "type": "object",
                    "description": "Custom headers as key-value pairs"
                },
                "params": {
                    "type": "object",
                    "description": "Query parameters as key-value pairs"
                },
                "body": {
                    "type": ["object", "string", "null"],
                    "description": "Request body (JSON object or string)"
                },
                "body_type": {
                    "type": "string",
                    "enum": ["json", "form", "raw", "multipart"],
                    "default": "json",
                    "description": "Format of the request body"
                },
                "auth_type": {
                    "type": "string",
                    "enum": ["none", "bearer", "api_key", "basic", "custom"],
                    "default": "none",
                    "description": "Authentication type"
                },
                "auth_value": {
                    "type": "string",
                    "description": "Authentication value (token, key, or username:password for basic)"
                },
                "auth_header": {
                    "type": "string",
                    "default": "Authorization",
                    "description": "Header name for API key authentication"
                },
                "timeout": {
                    "type": "integer",
                    "default": 30,
                    "description": "Request timeout in seconds"
                },
                "follow_redirects": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to follow HTTP redirects"
                },
                "verify_ssl": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to verify SSL certificates"
                }
            },
            "required": ["url"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute HTTP request."""
        url = kwargs.get("url")
        
        if not url:
            return {"error": "URL is required"}
        
        # Validate URL
        if not validate_url(url):
            return {"error": f"Invalid or unsafe URL: {url}"}
        
        # Apply rate limiting
        self._apply_rate_limit()
        
        method = kwargs.get("method", "GET").upper()
        headers = kwargs.get("headers", {})
        params = kwargs.get("params", {})
        body = kwargs.get("body")
        body_type = kwargs.get("body_type", "json")
        auth_type = kwargs.get("auth_type", "none")
        auth_value = kwargs.get("auth_value")
        auth_header = kwargs.get("auth_header", "Authorization")
        timeout = kwargs.get("timeout", self.timeout)
        follow_redirects = kwargs.get("follow_redirects", True)
        verify_ssl = kwargs.get("verify_ssl", True)
        
        try:
            # Prepare headers
            request_headers = self.default_headers.copy()
            request_headers.update(headers)
            
            # Add authentication
            auth_headers = self._prepare_authentication(auth_type, auth_value, auth_header)
            request_headers.update(auth_headers)
            
            # Prepare body
            data, files, json_data = self._prepare_body(body, body_type)
            
            # Log request details
            self.logger.debug(f"Making {method} request to {url}")
            
            # Make request
            response = self.session.request(
                method=method,
                url=url,
                headers=request_headers,
                params=params,
                data=data,
                json=json_data,
                files=files,
                timeout=timeout,
                allow_redirects=follow_redirects,
                verify=verify_ssl
            )
            
            # Parse response
            result = self._parse_response(response)
            
            # Add request metadata
            result["request"] = {
                "method": method,
                "url": url,
                "headers_sent": list(request_headers.keys()),
                "params": params,
                "body_type": body_type if body else None
            }
            
            self.logger.info(f"API request completed: {method} {url} -> {response.status_code}")
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                "error": f"Request timed out after {timeout} seconds",
                "error_type": "timeout",
                "url": url,
                "method": method
            }
        except requests.exceptions.ConnectionError as e:
            return {
                "error": f"Connection error: {str(e)}",
                "error_type": "connection",
                "url": url,
                "method": method
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Request failed: {str(e)}",
                "error_type": "request",
                "url": url,
                "method": method
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unknown",
                "url": url,
                "method": method
            }
    
    def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        if self.rate_limit_delay > 0:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
    
    def _prepare_authentication(self, auth_type: str, auth_value: Optional[str], auth_header: str) -> Dict[str, str]:
        """Prepare authentication headers."""
        headers = {}
        
        if auth_type == "none" or not auth_value:
            return headers
        
        if auth_type == "bearer":
            headers["Authorization"] = f"Bearer {auth_value}"
        
        elif auth_type == "api_key":
            headers[auth_header] = auth_value
        
        elif auth_type == "basic":
            # Expect username:password format
            if ":" in auth_value:
                username, password = auth_value.split(":", 1)
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
            else:
                self.logger.warning("Basic auth value should be in username:password format")
        
        elif auth_type == "custom":
            # Custom auth - auth_value should be the full header value
            headers[auth_header] = auth_value
        
        return headers
    
    def _prepare_body(self, body: Any, body_type: str) -> tuple:
        """Prepare request body based on type."""
        data = None
        files = None
        json_data = None
        
        if body is None:
            return data, files, json_data
        
        if body_type == "json":
            if isinstance(body, str):
                try:
                    json_data = json.loads(body)
                except json.JSONDecodeError:
                    json_data = {"data": body}
            else:
                json_data = body
        
        elif body_type == "form":
            if isinstance(body, str):
                data = body
            elif isinstance(body, dict):
                data = urlencode(body)
            else:
                data = str(body)
        
        elif body_type == "raw":
            if isinstance(body, dict):
                data = json.dumps(body)
            else:
                data = str(body)
        
        elif body_type == "multipart":
            # For multipart, body should be a dict with file paths
            if isinstance(body, dict):
                files = {}
                for key, value in body.items():
                    if isinstance(value, str) and value.startswith("@"):
                        # File path indicator
                        file_path = value[1:]
                        try:
                            files[key] = open(file_path, 'rb')
                        except IOError:
                            self.logger.warning(f"Could not open file: {file_path}")
                    else:
                        if data is None:
                            data = {}
                        data[key] = value
        
        return data, files, json_data
    
    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse HTTP response."""
        result = {
            "status_code": response.status_code,
            "success": 200 <= response.status_code < 300,
            "headers": dict(response.headers),
            "url": response.url,
            "elapsed_time": response.elapsed.total_seconds()
        }
        
        # Try to parse JSON response
        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'application/json' in content_type:
            try:
                result["data"] = response.json()
                result["data_type"] = "json"
            except json.JSONDecodeError:
                result["data"] = response.text
                result["data_type"] = "text"
                result["parse_error"] = "Failed to parse JSON response"
        elif 'text' in content_type or 'html' in content_type:
            result["data"] = response.text
            result["data_type"] = "text"
        elif 'xml' in content_type:
            result["data"] = response.text
            result["data_type"] = "xml"
        else:
            # For binary content, return base64 encoded
            if len(response.content) < 1024 * 1024:  # Less than 1MB
                result["data"] = base64.b64encode(response.content).decode('utf-8')
                result["data_type"] = "base64"
                result["content_type"] = content_type
            else:
                result["data"] = f"Binary content too large ({len(response.content)} bytes)"
                result["data_type"] = "binary"
                result["content_size"] = len(response.content)
        
        # Add cookies if present
        if response.cookies:
            result["cookies"] = dict(response.cookies)
        
        # Add redirect history if any
        if response.history:
            result["redirects"] = [
                {"url": r.url, "status_code": r.status_code}
                for r in response.history
            ]
        
        return result
    
    def close(self):
        """Close the session."""
        self.session.close()
