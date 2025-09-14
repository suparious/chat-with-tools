---
title: Tools Reference
tags: [tools, reference, api, documentation]
created: 2025-09-14
updated: 2025-09-14
status: active
---

# Tools Reference

## Complete Tool Inventory

This reference provides comprehensive documentation for all available tools in the Chat with Tools framework.

## Core Tools (12 Available)

### 🧮 calculate
Mathematical calculations and evaluations.

**Usage:**
```python
"Calculate the compound interest on $1000 at 5% for 3 years"
"What is sin(π/2) + cos(0)?"
```

**Parameters:**
- `expression` (string, required): Mathematical expression to evaluate

**Returns:** Calculation result or error message

---

### 🔍 search_web
Web search using DuckDuckGo for current information.

**Usage:**
```python
"Search for the latest AI news"
"Find current Bitcoin price"
```

**Parameters:**
- `query` (string, required): Search query
- `max_results` (integer, optional): Maximum results (1-10, default: 5)
- `fetch_content` (boolean, optional): Fetch page content (default: true)

**Returns:** Search results with titles, URLs, and snippets

---

### 🐍 python_executor
Execute Python code in a sandboxed environment.

**Usage:**
```python
"Generate the first 20 Fibonacci numbers"
"Create a prime number checker function"
```

**Parameters:**
- `code` (string, required): Python code to execute
- `description` (string, optional): Code description

**Available Libraries:**
- Standard: `math`, `random`, `statistics`, `collections`, `itertools`, `json`, `datetime`, `time`, `re`
- Data Science: `pandas` (as pd), `numpy` (as np)

**Security:** Sandboxed execution, no file/network access

---

### 🧠 memory
Persistent information storage across conversations.

**Usage:**
```python
"Remember that my project uses PostgreSQL"
"What did I tell you about the API design?"
```

**Parameters:**
- `action` (string, required): store, retrieve, search, forget, stats
- `content` (string, conditional): Content to store (required for store)
- `memory_type` (string, optional): fact, experience, preference, instruction, context
- `tags` (array, optional): Categorization tags
- `query` (string, conditional): Search query (required for search)

**Returns:** Memory ID, retrieved content, or search results

---

### 🤔 sequential_thinking
Step-by-step problem analysis with revision capabilities.

**Usage:**
```python
"Think through database optimization strategies"
"Analyze sorting algorithm trade-offs"
```

**Parameters:**
- `action` (string, required): start, think, revise, branch, conclude, get_summary, export
- `problem` (string, conditional): Problem statement (required for start)
- `thought` (string, conditional): Thought content (required for think/revise)
- `confidence` (float, optional): Confidence level (0-1)

**Features:** Branching thoughts, revision tracking, confidence scoring

---

### 📖 read_file
Read text file contents.

**Usage:**
```python
"Read config.yaml"
"Load data from output.csv"
```

**Parameters:**
- `path` (string, required): File path to read

**Supported Formats:** Text files (txt, md, yaml, json, csv, etc.)

---

### 💾 write_file
Write content to files.

**Usage:**
```python
"Save this data to results.json"
"Create a new Python script"
```

**Parameters:**
- `path` (string, required): File path to write
- `content` (string, required): Content to write

**Features:** Creates directories if needed, overwrites existing files

---

### 📝 summarizer
Text summarization and analysis.

**Usage:**
```python
"Summarize this article: [long text]"
"Extract key points from this document"
```

**Parameters:**
- `action` (string, required): summarize, key_points, statistics
- `text` (string, required): Text to analyze
- `ratio` (float, optional): Summary ratio (0.1-0.9)
- `num_points` (integer, optional): Number of key points

**Returns:** Summary, key points, or text statistics

---

### ✅ mark_task_complete
Signal task completion.

**Usage:** Automatically called by agent when task completes

**Parameters:**
- `summary` (string, required): Task completion summary

**Returns:** Completion confirmation

---

### 📊 data_analysis
Comprehensive data analysis with statistics and visualization.

**Usage:**
```python
"Create correlation matrix from CSV data"
"Find outliers in temperature data"
"Generate sales chart by region"
```

**Parameters:**
- `action` (string, required): load_csv, load_json, describe, analyze, transform, visualize, query
- `data` (string, conditional): Data string (CSV or JSON)
- `analysis_type` (string, optional): correlation, distribution, outliers, trends, summary
- `transform_type` (string, optional): normalize, standardize, log
- `chart_type` (string, optional): line, bar, scatter, histogram, box, heatmap, pie

**Features:**
- Statistical analysis
- Data transformations
- Visualizations (base64 PNG)
- Outlier detection
- Trend analysis

---

### 🌐 api_request
HTTP requests to external APIs with authentication.

**Usage:**
```python
"GET user data from GitHub API"
"POST webhook with this data"
```

**Parameters:**
- `url` (string, required): API endpoint URL
- `method` (string, required): GET, POST, PUT, DELETE, PATCH
- `headers` (object, optional): Custom headers
- `body` (any, optional): Request body
- `auth_type` (string, optional): none, bearer, api_key, basic
- `auth_value` (string, conditional): Authentication credentials

**Features:**
- Multiple auth methods
- Automatic retry with backoff
- Response parsing
- SSL verification

---

### 🗄️ database
SQLite database operations for local data management.

**Usage:**
```python
"Create user information table"
"Query active status records"
"Import CSV into database"
```

**Parameters:**
- `action` (string, required): connect, execute, create_table, list_tables, describe_table, import_csv, export_table, backup
- `database` (string, required): Database file path
- `query` (string, conditional): SQL query
- `table_name` (string, conditional): Table name
- `columns` (object, conditional): Column definitions
- `data` (string, conditional): Data to import

**Features:**
- Full SQL support
- Schema management
- CSV import/export
- Database backup
- SQL injection prevention

## Tool Categories

### Computation & Analysis
- [[#calculate|calculate]] - Mathematical operations
- [[#python_executor|python_executor]] - Code execution
- [[#data_analysis|data_analysis]] - Data analysis

### Information Retrieval
- [[#search_web|search_web]] - Web search
- [[#api_request|api_request]] - API interactions
- [[#read_file|read_file]] - File reading

### Data Storage
- [[#memory|memory]] - Persistent memory
- [[#database|database]] - SQLite operations
- [[#write_file|write_file]] - File writing

### AI Enhancement
- [[#sequential_thinking|sequential_thinking]] - Structured reasoning
- [[#summarizer|summarizer]] - Text summarization

### System
- [[#mark_task_complete|mark_task_complete]] - Task completion

## Usage Patterns

### Tool Combinations
Effective workflows using multiple tools:

```python
# Data Pipeline Example
1. api_request    # Fetch external data
2. data_analysis  # Analyze and visualize
3. database       # Store results
4. write_file     # Export report
```

### Tool Selection Guide

**Calculations:**
- Simple math → `calculate`
- Complex algorithms → `python_executor`
- Statistical analysis → `data_analysis`

**Data Operations:**
- Web data → `search_web` or `api_request`
- Local files → `read_file`
- Structured storage → `database`
- Quick storage → `memory`

**Analysis Tasks:**
- Text → `summarizer`
- Data → `data_analysis`
- Problems → `sequential_thinking`

## Performance Characteristics

### Response Times

| Category | Tools | Time |
|----------|-------|------|
| **Fast** (< 1s) | calculate, memory (retrieve), read_file (small) | Instant |
| **Medium** (1-5s) | search_web, database, summarizer, data_analysis (small) | Quick |
| **Slow** (> 5s) | api_request, python_executor (complex), sequential_thinking | Variable |

## Error Handling

All tools return structured responses:

```json
{
  "status": "success|error",
  "data": "...",
  "error": "Error message if failed",
  "error_type": "validation|execution|timeout"
}
```

## Security Considerations

- **python_executor**: Sandboxed, no file/network access
- **api_request**: URL validation, SSL verification
- **database**: SQL injection prevention
- **file operations**: Sandboxed to workspace directory

## Adding Custom Tools

Create a Python file in `src/chat_with_tools/tools/`:

```python
from .base_tool import BaseTool

class MyTool(BaseTool):
    def __init__(self, config: dict):
        self.config = config
    
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "Tool description"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string"}
            },
            "required": ["param1"]
        }
    
    def execute(self, **kwargs):
        # Implementation
        return {"status": "success", "result": "..."}
```

Tools are automatically discovered and loaded!

## Complex Query Example

```
"Fetch cryptocurrency prices from CoinGecko API,
analyze 24-hour price changes,
store top 10 gainers in database,
and create a visualization."
```

**Tools Used:**
1. `api_request` - Fetch data
2. `data_analysis` - Analyze and visualize
3. `database` - Store results
4. `mark_task_complete` - Signal completion

## Best Practices

1. **Validate Inputs**: Always validate tool parameters
2. **Handle Errors**: Provide helpful error messages
3. **Cache Results**: Cache expensive operations
4. **Document Usage**: Include clear examples
5. **Test Thoroughly**: Write comprehensive tests

## Related Documentation

- [[../../guides/development/tool-enhancement|Tool Enhancement Guide]]
- [[../../components/vllm/index|vLLM Integration]]
- [[../../architecture/adrs/index|Architecture Decisions]]

---

*Source: [[../../archive/2025-09-14/tools-reference-original|Original Tools Reference]]*