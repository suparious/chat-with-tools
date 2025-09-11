"""Test suite for Chat with Tools framework."""

import unittest
import tempfile
import os
import json
import yaml
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.base_tool import BaseTool
from tools import discover_tools
from agent_enhanced import OpenRouterAgent, ConnectionPool
from utils import (
    validate_url, 
    get_env_or_config, 
    format_time_duration,
    RateLimiter,
    MetricsCollector
)


class TestUtils(unittest.TestCase):
    """Test utility functions."""
    
    def test_validate_url(self):
        """Test URL validation."""
        # Valid URLs
        self.assertTrue(validate_url("https://example.com"))
        self.assertTrue(validate_url("http://example.com/path"))
        self.assertTrue(validate_url("https://api.example.com:8080/v1"))
        
        # Invalid URLs
        self.assertFalse(validate_url("not-a-url"))
        self.assertFalse(validate_url("http://"))
        self.assertFalse(validate_url(""))
        self.assertFalse(validate_url("javascript:alert('xss')"))
        self.assertFalse(validate_url("http://localhost/admin"))
        self.assertFalse(validate_url("http://127.0.0.1:8080"))
        self.assertFalse(validate_url("file:///etc/passwd"))
    
    def test_get_env_or_config(self):
        """Test environment variable and config retrieval."""
        config = {
            'openrouter': {
                'api_key': 'config_key',
                'model': 'config_model'
            }
        }
        
        # Test config retrieval
        self.assertEqual(
            get_env_or_config('openrouter.api_key', config),
            'config_key'
        )
        
        # Test with environment variable
        os.environ['OPENROUTER_API_KEY'] = 'env_key'
        self.assertEqual(
            get_env_or_config('openrouter_api_key', config),
            'env_key'
        )
        del os.environ['OPENROUTER_API_KEY']
        
        # Test default value
        self.assertEqual(
            get_env_or_config('non.existent', config, 'default'),
            'default'
        )
    
    def test_format_time_duration(self):
        """Test time duration formatting."""
        self.assertEqual(format_time_duration(30.5), "30.5s")
        self.assertEqual(format_time_duration(90), "1m 30s")
        self.assertEqual(format_time_duration(3665), "1h 1m 5s")
        self.assertEqual(format_time_duration(86400), "1d 0h 0m")
    
    def test_rate_limiter(self):
        """Test rate limiter functionality."""
        limiter = RateLimiter(rate=2, per=1.0)
        
        # First two requests should be allowed
        self.assertTrue(limiter.allow_request())
        self.assertTrue(limiter.allow_request())
        
        # Third request should be denied
        self.assertFalse(limiter.allow_request())
    
    def test_metrics_collector(self):
        """Test metrics collection."""
        metrics = MetricsCollector()
        
        metrics.record_api_call(100)
        metrics.record_tool_call("search_web")
        metrics.record_tool_call("search_web")
        metrics.record_response_time(1.5)
        metrics.record_error()
        
        summary = metrics.get_summary()
        
        self.assertEqual(summary['api_calls'], 1)
        self.assertEqual(summary['total_tokens'], 100)
        self.assertEqual(summary['tool_calls']['search_web'], 2)
        self.assertEqual(summary['errors'], 1)
        self.assertEqual(summary['avg_response_time'], 1.5)


class TestBaseTool(unittest.TestCase):
    """Test base tool functionality."""
    
    def test_tool_schema_generation(self):
        """Test OpenRouter schema generation."""
        
        class TestTool(BaseTool):
            @property
            def name(self):
                return "test_tool"
            
            @property
            def description(self):
                return "A test tool"
            
            @property
            def parameters(self):
                return {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string"}
                    },
                    "required": ["param1"]
                }
            
            def execute(self, **kwargs):
                return {"result": "success"}
        
        tool = TestTool({})
        schema = tool.to_openrouter_schema()
        
        self.assertEqual(schema['type'], 'function')
        self.assertEqual(schema['function']['name'], 'test_tool')
        self.assertEqual(schema['function']['description'], 'A test tool')
        self.assertIn('properties', schema['function']['parameters'])


class TestToolDiscovery(unittest.TestCase):
    """Test automatic tool discovery."""
    
    @patch('tools.importlib.import_module')
    @patch('tools.os.listdir')
    def test_discover_tools(self, mock_listdir, mock_import):
        """Test tool discovery mechanism."""
        # Mock file listing
        mock_listdir.return_value = ['test_tool.py', '__init__.py', 'base_tool.py']
        
        # Create mock tool class
        class MockTool(BaseTool):
            @property
            def name(self):
                return "mock_tool"
            
            @property
            def description(self):
                return "Mock tool"
            
            @property
            def parameters(self):
                return {"type": "object", "properties": {}}
            
            def execute(self, **kwargs):
                return {"status": "ok"}
        
        # Mock module with tool
        mock_module = MagicMock()
        mock_module.MockTool = MockTool
        mock_import.return_value = mock_module
        
        # Discover tools
        tools = discover_tools({}, silent=True)
        
        # Verify discovery
        self.assertIn('mock_tool', tools)
        self.assertIsInstance(tools['mock_tool'], MockTool)


class TestOpenRouterAgent(unittest.TestCase):
    """Test OpenRouter agent functionality."""
    
    def setUp(self):
        """Set up test configuration."""
        self.config = {
            'openrouter': {
                'api_key': 'test_key',
                'base_url': 'https://test.api.com',
                'model': 'test-model'
            },
            'system_prompt': 'Test system prompt',
            'agent': {
                'max_iterations': 5,
                'temperature': 0.7
            }
        }
        
        # Create temporary config file
        self.config_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.yaml', 
            delete=False
        )
        yaml.dump(self.config, self.config_file)
        self.config_file.close()
    
    def tearDown(self):
        """Clean up temporary files."""
        os.unlink(self.config_file.name)
    
    @patch('agent_enhanced.ConnectionPool.get_client')
    @patch('agent_enhanced.discover_tools')
    def test_agent_initialization(self, mock_discover, mock_get_client):
        """Test agent initialization."""
        # Mock tools discovery
        mock_discover.return_value = {}
        
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Initialize agent
        agent = OpenRouterAgent(self.config_file.name, silent=True)
        
        # Verify initialization
        self.assertEqual(agent.model, 'test-model')
        self.assertEqual(agent.max_iterations, 5)
        self.assertEqual(agent.temperature, 0.7)
        self.assertIsNotNone(agent.metrics)
        self.assertIsNotNone(agent.rate_limiter)
    
    @patch('agent_enhanced.ConnectionPool.get_client')
    @patch('agent_enhanced.discover_tools')
    def test_tool_argument_validation(self, mock_discover, mock_get_client):
        """Test tool argument validation."""
        # Create mock tool
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.parameters = {
            "type": "object",
            "properties": {
                "required_param": {"type": "string"},
                "optional_param": {"type": "integer"}
            },
            "required": ["required_param"]
        }
        
        mock_discover.return_value = {"test_tool": mock_tool}
        mock_get_client.return_value = MagicMock()
        
        # Initialize agent
        agent = OpenRouterAgent(self.config_file.name, silent=True)
        
        # Test valid arguments
        valid_args = agent.validate_tool_arguments(
            "test_tool",
            {"required_param": "value", "optional_param": "123"}
        )
        self.assertEqual(valid_args["required_param"], "value")
        self.assertEqual(valid_args["optional_param"], 123)  # Converted to int
        
        # Test missing required parameter
        with self.assertRaises(ValueError):
            agent.validate_tool_arguments("test_tool", {"optional_param": 5})


class TestConnectionPool(unittest.TestCase):
    """Test connection pooling."""
    
    @patch('agent_enhanced.OpenAI')
    def test_connection_reuse(self, mock_openai):
        """Test that connections are reused."""
        # Clear pool
        ConnectionPool._instances.clear()
        
        # Get client twice with same config
        client1 = ConnectionPool.get_client("https://api.test.com", "key123")
        client2 = ConnectionPool.get_client("https://api.test.com", "key123")
        
        # Should be same instance
        self.assertIs(client1, client2)
        
        # OpenAI should only be instantiated once
        self.assertEqual(mock_openai.call_count, 1)
        
        # Different config should create new client
        client3 = ConnectionPool.get_client("https://api2.test.com", "key456")
        self.assertIsNot(client1, client3)
        self.assertEqual(mock_openai.call_count, 2)


class TestEndToEnd(unittest.TestCase):
    """End-to-end integration tests."""
    
    @patch('agent_enhanced.OpenAI')
    @patch('agent_enhanced.discover_tools')
    def test_simple_query_flow(self, mock_discover, mock_openai_class):
        """Test a simple query through the agent."""
        # Set up mocks
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.tool_calls = None
        mock_response.usage.total_tokens = 50
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock tools
        mock_discover.return_value = {}
        
        # Create config
        config = {
            'openrouter': {
                'api_key': 'test_key',
                'base_url': 'https://test.api.com',
                'model': 'test-model'
            },
            'system_prompt': 'Test prompt',
            'agent': {'max_iterations': 1}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_file = f.name
        
        try:
            # Initialize and run agent
            agent = OpenRouterAgent(config_file, silent=True)
            response = agent.run("Test query")
            
            # Verify response
            self.assertEqual(response, "Test response")
            
            # Verify metrics
            metrics = agent.get_metrics()
            self.assertEqual(metrics['api_calls'], 1)
            self.assertEqual(metrics['total_tokens'], 50)
            
        finally:
            os.unlink(config_file)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestBaseTool))
    suite.addTests(loader.loadTestsFromTestCase(TestToolDiscovery))
    suite.addTests(loader.loadTestsFromTestCase(TestOpenRouterAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestConnectionPool))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEnd))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
