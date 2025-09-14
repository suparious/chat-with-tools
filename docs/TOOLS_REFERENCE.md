# Chat with Tools - Available Tools

## 📚 Complete Tool Reference

This document provides a comprehensive reference for all available tools in the Chat with Tools framework.

## Core Tools (12 Available)

### 1. 🧮 **calculate**
Perform mathematical calculations and evaluations.

**Example Usage:**
```
"Calculate the compound interest on $1000 at 5% for 3 years"
"What is the square root of 144?"
"Calculate sin(π/2) + cos(0)"
```

**Parameters:**
- `expression`: Mathematical expression to evaluate

---

### 2. 🔍 **search_web**
Search the web using DuckDuckGo for current information.

**Example Usage:**
```
"Search for the latest news about AI"
"Find information about quantum computing"
"Look up the current Bitcoin price"
```

**Parameters:**
- `query`: Search query
- `max_results`: Maximum results (1-10, default: 5)
- `fetch_content`: Whether to fetch page content (default: true)

---

### 3. 🐍 **python_executor**
Execute Python code safely in a sandboxed environment.

**Example Usage:**
```
"Write a Python script to generate the first 20 Fibonacci numbers"
"Create a function to check if a number is prime"
"Use pandas to analyze this data: [...]"
```

**Parameters:**
- `code`: Python code to execute
- `description`: Optional description of the code

**Available Libraries:**
- Standard library: math, random, statistics, collections, itertools, json, datetime, time, re
- Data science: pandas (as pd), numpy (as np)

---

### 4. 🧠 **memory**
Store and retrieve information persistently across conversations.

**Example Usage:**
```
"Remember that my favorite programming language is Python"
"What did I tell you about my project requirements?"
"Search your memory for information about databases"
```

**Parameters:**
- `action`: store, retrieve, search, forget, stats
- `content`: Content to store
- `memory_type`: fact, experience, preference, instruction, context
- `tags`: Tags for categorization
- `query`: Search query

---

### 5. 🤔 **sequential_thinking**
Think through problems step-by-step with revision capabilities.

**Example Usage:**
```
"Think step by step about how to optimize a database query"
"Analyze the pros and cons of different sorting algorithms"
"Break down the problem of building a web scraper"
```

**Parameters:**
- `action`: start, think, revise, branch, conclude, get_summary, export
- `problem`: Problem statement
- `thought`: Thought content
- `confidence`: Confidence level (0-1)

---

### 6. 📖 **read_file**
Read contents of text files.

**Example Usage:**
```
"Read the contents of config.yaml"
"What's in the README.md file?"
"Load data from output.csv"
```

**Parameters:**
- `path`: File path to read

---

### 7. 💾 **write_file**
Write content to files.

**Example Usage:**
```
"Save this data to results.json"
"Create a new Python script with this code"
"Write the analysis to report.md"
```

**Parameters:**
- `path`: File path to write
- `content`: Content to write

---

### 8. 📝 **summarizer**
Summarize and analyze text using various strategies.

**Example Usage:**
```
"Summarize this article: [long text]"
"Extract the key points from this document"
"Analyze the readability of this text"
```

**Parameters:**
- `action`: summarize, key_points, statistics
- `text`: Text to analyze
- `ratio`: Ratio to keep (0.1-0.9)
- `num_points`: Number of key points

---

### 9. ✅ **mark_task_complete**
Signal that a task has been completed.

**Example Usage:**
Automatically called when the agent completes a task.

**Parameters:**
- `summary`: Summary of what was accomplished

---

### 10. 📊 **data_analysis** (NEW)
Comprehensive data analysis with statistics and visualization.

**Example Usage:**
```
"Load this CSV data and create a correlation matrix"
"Analyze the distribution of values in this dataset"
"Create a bar chart of sales by region"
"Find outliers in the temperature data"
```

**Parameters:**
- `action`: load_csv, load_json, describe, analyze, transform, visualize, query
- `data`: Data string (CSV or JSON)
- `analysis_type`: correlation, distribution, outliers, trends, summary
- `transform_type`: normalize, standardize, log
- `chart_type`: line, bar, scatter, histogram, box, heatmap, pie

**Features:**
- Statistical analysis (mean, median, mode, std dev, correlations)
- Data transformations (normalization, standardization)
- Visualizations (exports as base64 PNG)
- Outlier detection
- Trend analysis

---

### 11. 🌐 **api_request** (NEW)
Make HTTP requests to external APIs with authentication.

**Example Usage:**
```
"Make a GET request to the GitHub API for user information"
"POST this data to the webhook URL"
"Fetch weather data from the OpenWeather API"
```

**Parameters:**
- `url`: API endpoint URL
- `method`: GET, POST, PUT, DELETE, PATCH
- `headers`: Custom headers
- `body`: Request body
- `auth_type`: none, bearer, api_key, basic
- `auth_value`: Authentication credentials

**Features:**
- Multiple authentication methods
- Automatic retry with backoff
- JSON/form/multipart body formats
- Response parsing
- SSL verification
- Rate limiting

---

### 12. 🗄️ **database** (NEW)
SQLite database operations for local data management.

**Example Usage:**
```
"Create a database table for storing user information"
"Query all records where status is 'active'"
"Import this CSV data into a database table"
"Show me the schema of the products table"
```

**Parameters:**
- `action`: connect, execute, create_table, list_tables, describe_table, import_csv, export_table, backup
- `database`: Database file path
- `query`: SQL query
- `table_name`: Table name
- `columns`: Column definitions
- `data`: Data to import

**Features:**
- Full SQL support (SELECT, INSERT, UPDATE, DELETE)
- Table creation and schema management
- CSV import/export
- Database backup
- Query result formatting (dict, list, CSV, JSON)
- Basic SQL injection prevention

---

## Tool Categories

### 🔢 **Computation & Analysis**
- `calculate` - Mathematical calculations
- `python_executor` - Code execution
- `data_analysis` - Data analysis and visualization

### 🔍 **Information Retrieval**
- `search_web` - Web search
- `api_request` - API interactions
- `read_file` - File reading

### 💾 **Data Storage**
- `memory` - Persistent memory
- `database` - SQLite operations
- `write_file` - File writing

### 🤖 **AI Enhancement**
- `sequential_thinking` - Structured reasoning
- `summarizer` - Text summarization

### ⚙️ **System**
- `mark_task_complete` - Task completion signal

---

## Usage Tips

### Combining Tools
Many tasks benefit from using multiple tools together:

```python
# Example: Data pipeline
1. api_request - Fetch data from API
2. data_analysis - Analyze the data
3. database - Store results
4. write_file - Export report
```

### Tool Selection Guide

**For calculations:**
- Simple math → `calculate`
- Complex algorithms → `python_executor`
- Statistical analysis → `data_analysis`

**For data:**
- Web data → `search_web` or `api_request`
- Local files → `read_file`
- Structured storage → `database`
- Quick storage → `memory`

**For analysis:**
- Text → `summarizer`
- Data → `data_analysis`
- Problems → `sequential_thinking`

---

## Performance Considerations

### Fast Tools (< 1 second)
- `calculate`
- `memory` (retrieve)
- `read_file` (small files)

### Medium Tools (1-5 seconds)
- `search_web`
- `database` (queries)
- `summarizer`
- `data_analysis` (small datasets)

### Potentially Slow Tools (> 5 seconds)
- `api_request` (depends on endpoint)
- `python_executor` (complex code)
- `data_analysis` (large datasets, visualizations)
- `sequential_thinking` (deep analysis)

---

## Error Handling

All tools return structured responses with error information:

```json
{
  "status": "success|error",
  "data": "...",
  "error": "Error message if failed",
  "error_type": "validation|execution|timeout"
}
```

---

## Security Notes

- **python_executor**: Sandboxed, no file/network access
- **api_request**: URL validation, SSL verification
- **database**: SQL injection prevention
- **file operations**: Sandboxed to workspace directory

---

## Examples

### Complex Query Using Multiple Tools

```
"Fetch the latest cryptocurrency prices from the CoinGecko API, 
analyze the price changes over the last 24 hours, 
store the top 10 gainers in a database, 
and create a visualization of the results."
```

This would use:
1. `api_request` - Fetch data
2. `data_analysis` - Analyze and visualize
3. `database` - Store results
4. `mark_task_complete` - Signal completion

---

## Adding Custom Tools

To add a new tool, create a Python file in `src/chat_with_tools/tools/` that:

1. Imports `BaseTool`
2. Implements required properties: `name`, `description`, `parameters`
3. Implements `execute(**kwargs)` method

Example:
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
        return "Description of what my tool does"
    
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
        # Tool logic here
        return {"status": "success", "result": "..."}
```

The tool will be automatically discovered and loaded!
