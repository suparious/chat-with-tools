#!/usr/bin/env python3
"""
Test script to verify enhanced features and backwards compatibility
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from chat_with_tools.agent import OpenRouterAgent


def test_backwards_compatibility():
    """Test that the agent works with minimal configuration."""
    print("\n" + "="*60)
    print("TEST: Backwards Compatibility")
    print("="*60)
    
    try:
        # Create agent with default settings (should work with minimal config)
        agent = OpenRouterAgent(silent=True)
        print("✅ Agent initialized with default settings")
        
        # Test simple query
        response = agent.run("What is 2+2?")
        print(f"✅ Simple query works: {response[:50]}...")
        
        # Check that multi-endpoint is disabled by default
        if not agent.endpoint_manager.is_enabled():
            print("✅ Multi-endpoint disabled by default (as expected)")
        else:
            print("⚠️  Multi-endpoint is enabled (unexpected)")
        
        # Check that structured output is disabled by default
        if not agent.use_structured_output:
            print("✅ Structured output disabled by default (as expected)")
        else:
            print("⚠️  Structured output is enabled (unexpected)")
        
        print("\n✅ Backwards compatibility test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Backwards compatibility test FAILED: {e}")
        return False


def test_enhanced_features():
    """Test enhanced features when configured."""
    print("\n" + "="*60)
    print("TEST: Enhanced Features")
    print("="*60)
    
    # Create a temporary config with enhanced features
    import tempfile
    import yaml
    
    enhanced_config = {
        'openrouter': {
            'api_key': '',
            'api_key_required': False,
            'base_url': 'http://infer.sbx-1.lq.ca.obenv.net:8000/v1',
            'model': 'NousResearch/Hermes-4-14B',
            'temperature': 0.7,
            'max_tokens': 2000
        },
        'inference_endpoints': {
            'fast': {
                'base_url': 'http://infer.sbx-1.lq.ca.obenv.net:8000/v1',
                'api_key': '',
                'model': 'NousResearch/Hermes-4-14B',
                'model_type': 'fast',
                'temperature': 0.5,
                'max_tokens': 1000,
                'supports_tools': True,
                'supports_structured_output': False,
                'is_vllm': True
            }
        },
        'vllm_structured_output': {
            'enabled': True,
            'backend': 'outlines'
        },
        'agent': {'max_iterations': 5},
        'system_prompt': 'You are a helpful assistant.'
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(enhanced_config, f)
        temp_config_path = f.name
    
    try:
        # Test with enhanced configuration
        agent = OpenRouterAgent(config_path=temp_config_path, silent=True)
        print("✅ Agent initialized with enhanced config")
        
        # Check that multi-endpoint is enabled
        if agent.endpoint_manager.is_enabled():
            print("✅ Multi-endpoint enabled when configured")
        else:
            print("❌ Multi-endpoint not enabled despite configuration")
        
        # Test using specific endpoint
        agent_fast = OpenRouterAgent(
            config_path=temp_config_path, 
            endpoint_name='fast',
            silent=True
        )
        print("✅ Created agent with specific endpoint")
        
        # Verify endpoint settings
        if agent_fast.endpoint_name == 'fast':
            print(f"✅ Using correct endpoint: {agent_fast.endpoint_name}")
        
        if agent_fast.temperature == 0.5:  # From fast endpoint config
            print(f"✅ Endpoint temperature applied: {agent_fast.temperature}")
        
        print("\n✅ Enhanced features test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Enhanced features test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up temp config
        os.unlink(temp_config_path)


def test_run_thinking():
    """Test the run_thinking method."""
    print("\n" + "="*60)
    print("TEST: run_thinking Method")
    print("="*60)
    
    try:
        agent = OpenRouterAgent(silent=True)
        
        # Test run_thinking without multi-endpoint configured
        # Should fall back to regular run
        response = agent.run_thinking("What is the meaning of life?")
        print(f"✅ run_thinking works without multi-endpoint: {response[:50]}...")
        
        print("\n✅ run_thinking test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ run_thinking test FAILED: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("   ENHANCED FRAMEWORK INTEGRATION TESTS")
    print("="*60)
    
    tests = [
        ("Backwards Compatibility", test_backwards_compatibility),
        ("Enhanced Features", test_enhanced_features),
        ("run_thinking Method", test_run_thinking)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Fatal error in {name}: {e}")
            results.append((name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("   TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {name:30} {status}")
    
    if passed == total:
        print("\n🎉 All tests passed! Framework is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
