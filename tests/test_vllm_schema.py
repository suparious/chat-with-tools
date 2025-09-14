#!/usr/bin/env python3
"""Test script to determine correct vLLM schema format."""

import json
import requests
from openai import OpenAI

# Configuration
BASE_URL = "http://infer.sbx-1.lq.ca.obenv.net:8000/v1"
MODEL = "NousResearch/Hermes-4-14B"

# Create client
client = OpenAI(base_url=BASE_URL, api_key="dummy")

# Test 1: Simple JSON schema format (OpenAI style)
def test_openai_style():
    """Test with OpenAI-style response_format."""
    print("\n=== Test 1: OpenAI-style response_format ===")
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "What is 2+2? Answer in JSON with a field 'answer'."}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "math_response",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "answer": {"type": "number"},
                            "explanation": {"type": "string"}
                        },
                        "required": ["answer"]
                    }
                }
            }
        )
        print(f"✅ Success! Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Failed: {e}")

# Test 2: vLLM outlines format with guided_json
def test_vllm_guided_json():
    """Test with vLLM guided_json in extra_body."""
    print("\n=== Test 2: vLLM guided_json (schema object) ===")
    try:
        schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "number"},
                "explanation": {"type": "string"}
            },
            "required": ["answer"]
        }
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "What is 2+2? Answer in JSON with a field 'answer'."}
            ],
            extra_body={
                "guided_json": schema,
                "guided_decoding_backend": "outlines"
            }
        )
        print(f"✅ Success! Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Failed: {e}")

# Test 3: vLLM with guided_json=True (no schema)
def test_vllm_guided_json_true():
    """Test with guided_json=True."""
    print("\n=== Test 3: vLLM guided_json=True ===")
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "What is 2+2? Answer in JSON with a field 'answer'."}
            ],
            extra_body={
                "guided_json": True,
                "guided_decoding_backend": "outlines"
            }
        )
        print(f"✅ Success! Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Failed: {e}")

# Test 4: Simple JSON mode without schema
def test_json_mode():
    """Test with simple JSON mode."""
    print("\n=== Test 4: Simple JSON mode ===")
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "What is 2+2? Answer in JSON with a field 'answer'."}
            ],
            response_format={"type": "json_object"}
        )
        print(f"✅ Success! Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Failed: {e}")

# Test 5: Guided grammar
def test_guided_grammar():
    """Test with guided grammar."""
    print("\n=== Test 5: Guided grammar ===")
    try:
        grammar = '''
        root ::= object
        object ::= "{" ws "\"answer\":" ws number ws "}"
        number ::= [0-9]+
        ws ::= [ \\t\\n\\r]*
        '''
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "What is 2+2?"}
            ],
            extra_body={
                "guided_grammar": grammar.strip(),
                "guided_decoding_backend": "outlines"
            }
        )
        print(f"✅ Success! Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Failed: {e}")

# Test 6: Tool calling with structured output
def test_tool_calling():
    """Test tool calling with structured output."""
    print("\n=== Test 6: Tool calling with schema ===")
    
    tools = [{
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform a calculation",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression"}
                },
                "required": ["expression"]
            }
        }
    }]
    
    try:
        # First try without any schema constraint
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "Calculate 2+2 using the calculate tool"}
            ],
            tools=tools
        )
        print(f"✅ Success! Tool calls: {response.choices[0].message.tool_calls}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    print("Testing vLLM Schema Formats")
    print("=" * 50)
    print(f"Server: {BASE_URL}")
    print(f"Model: {MODEL}")
    
    # Run tests
    test_openai_style()
    test_vllm_guided_json()
    test_vllm_guided_json_true()
    test_json_mode()
    test_guided_grammar()
    test_tool_calling()
    
    print("\n" + "=" * 50)
    print("Testing complete!")
