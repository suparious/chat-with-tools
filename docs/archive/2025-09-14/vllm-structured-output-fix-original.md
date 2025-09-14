# vLLM Structured Output - Fixed Implementation

## Issue Resolved (Sept 14, 2025)

### The Problem
The vLLM server crashed with this error when using simple `json_object` format:
```
ValueError: Invalid request type for Outlines backend (StructuredOutputOptions.JSON_OBJECT)
```

The server's Outlines backend doesn't support the simple `json_object` type, only full JSON schemas.

### The Solution
Modified the implementation to:
1. **Never use** `response_format: {"type": "json_object"}` with Outlines backend
2. **Always provide** a complete JSON schema when using structured output
3. **Use** `guided_json` with schema object for Outlines backend
4. **Skip** structured output for non-tool requests to avoid crashes

## Implementation Details

### Schema Format for Tool Calling
```python
schema = {
    "type": "object",
    "properties": {
        "thought": {
            "type": "string",
            "description": "Brief reasoning about the task"
        },
        "action": {
            "type": "string",
            "enum": ["tool_call", "direct_answer"],
            "description": "Whether to call a tool or answer directly"
        },
        "tool_name": {
            "type": "string",
            "enum": [list_of_tool_names],
            "description": "Name of the tool to call"
        },
        "tool_args": {
            "type": "object",
            "description": "Arguments for the tool"
        },
        "answer": {
            "type": "string",
            "description": "Direct answer to user"
        }
    },
    "required": ["thought", "action"]
}
```

### Request Format
```python
# For Outlines backend (vLLM)
request_params["extra_body"] = {
    "guided_json": schema,
    "guided_decoding_backend": "outlines"
}
```

## Configuration

```yaml
# config.yaml
vllm_structured_output:
  enabled: true           # Enable structured output
  backend: "outlines"     # Use Outlines backend
  enforcement_level: "strict"
  validate_with_pydantic: true
  retry_on_failure: true
  max_retries: 3
```

## Testing

### Quick Test
```bash
cd /home/shaun/repos/chat-with-tools
uv run python test_fixed_structured.py
```

### Expected Behavior
- When tools are available: Uses structured schema for better tool calling
- When no tools needed: Skips structured output to avoid crashes
- Tool selection constrained to valid options only
- Arguments properly structured as JSON

## Benefits of This Implementation

1. **No Server Crashes**: Avoids unsupported `json_object` type
2. **Better Tool Selection**: Schema constrains to valid tool names
3. **Structured Arguments**: Ensures proper JSON formatting
4. **Fallback Support**: Works without structured output if needed
5. **Clear Reasoning**: Includes "thought" field for transparency

## Known Limitations

1. **Outlines-Specific**: Current implementation is tailored for Outlines backend
2. **Tool-Only**: Structured output only works with tool calling currently
3. **Schema Complexity**: Complex tools may need more sophisticated schemas

## Future Improvements

1. **General Response Schema**: Create schema for non-tool responses
2. **Dynamic Schema Generation**: Build schemas based on tool parameters
3. **Multiple Backend Support**: Add schemas for other vLLM backends
4. **Response Validation**: Add Pydantic validation for structured responses

## Troubleshooting

### If Server Crashes
- Check that `json_object` is NOT being used
- Verify schema is a proper JSON Schema object
- Ensure `guided_json` contains the schema, not `True`

### If Tool Calling Fails
- Check tool names in schema match actual tool names
- Verify structured output is enabled in config
- Look for parsing errors in logs

### Performance Issues
- Consider disabling structured output for simple queries
- Use `enforcement_level: "lenient"` for faster generation
- Cache schemas to reduce overhead

## Example Output

With structured output enabled, the model generates responses like:
```json
{
    "thought": "The user wants to calculate 25% of 80. I'll use the calculate tool.",
    "action": "tool_call",
    "tool_name": "calculate",
    "tool_args": {
        "expression": "80 * 0.25"
    }
}
```

This structured format ensures consistent, parseable tool calls that improve reliability.

---

*Implementation completed Sept 14, 2025 - Fixed to avoid vLLM server crashes with Outlines backend*
