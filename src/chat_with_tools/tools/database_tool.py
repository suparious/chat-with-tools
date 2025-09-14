"""
Database Tool for Chat with Tools Framework

This tool provides SQLite database operations including
querying, schema inspection, and data manipulation.
"""

import sqlite3
import json
import csv
import io
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
from .base_tool import BaseTool


class DatabaseTool(BaseTool):
    """
    SQLite database tool for local data operations.
    
    Provides safe database operations with query validation
    and result formatting.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.db_path = config.get('database', {}).get('default_path', './data/local.db')
        self.connections = {}
        self.current_db = None
        
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    @property
    def name(self) -> str:
        return "database"
    
    @property
    def description(self) -> str:
        return """Perform SQLite database operations for local data storage and querying.
        
        Actions:
        - connect: Connect to a database
        - execute: Execute SQL query (SELECT, INSERT, UPDATE, DELETE)
        - create_table: Create a new table
        - list_tables: List all tables
        - describe_table: Get table schema
        - import_csv: Import CSV data into a table
        - export_table: Export table to CSV/JSON
        - backup: Create database backup
        
        Use this for:
        - Storing structured data locally
        - Complex SQL queries and joins
        - Data persistence across sessions
        - Building local data warehouses
        """
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["connect", "execute", "create_table", "list_tables", 
                            "describe_table", "import_csv", "export_table", "backup"],
                    "description": "Database action to perform"
                },
                "database": {
                    "type": "string",
                    "description": "Database file path (defaults to ./data/local.db)"
                },
                "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                },
                "table_name": {
                    "type": "string",
                    "description": "Name of the table"
                },
                "columns": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string", "enum": ["TEXT", "INTEGER", "REAL", "BLOB", "NULL"]},
                            "primary_key": {"type": "boolean"},
                            "not_null": {"type": "boolean"},
                            "unique": {"type": "boolean"},
                            "default": {"type": ["string", "number", "null"]}
                        }
                    },
                    "description": "Column definitions for table creation"
                },
                "data": {
                    "type": ["array", "string"],
                    "description": "Data to insert (array of records or CSV string)"
                },
                "params": {
                    "type": "array",
                    "description": "Query parameters for parameterized queries"
                },
                "format": {
                    "type": "string",
                    "enum": ["dict", "list", "csv", "json"],
                    "default": "dict",
                    "description": "Output format for query results"
                },
                "limit": {
                    "type": "integer",
                    "default": 100,
                    "description": "Maximum number of rows to return"
                }
            },
            "required": ["action"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute database operations."""
        action = kwargs.get("action")
        
        try:
            if action == "connect":
                return self._connect(kwargs.get("database", self.db_path))
            
            elif action == "execute":
                return self._execute_query(
                    kwargs.get("query"),
                    kwargs.get("params"),
                    kwargs.get("format", "dict"),
                    kwargs.get("limit", 100)
                )
            
            elif action == "create_table":
                return self._create_table(
                    kwargs.get("table_name"),
                    kwargs.get("columns")
                )
            
            elif action == "list_tables":
                return self._list_tables()
            
            elif action == "describe_table":
                return self._describe_table(kwargs.get("table_name"))
            
            elif action == "import_csv":
                return self._import_csv(
                    kwargs.get("table_name"),
                    kwargs.get("data")
                )
            
            elif action == "export_table":
                return self._export_table(
                    kwargs.get("table_name"),
                    kwargs.get("format", "csv")
                )
            
            elif action == "backup":
                return self._backup_database()
            
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": f"Database operation failed: {str(e)}"}
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get current database connection."""
        if self.current_db and self.current_db in self.connections:
            return self.connections[self.current_db]
        
        # Auto-connect to default database
        self._connect(self.db_path)
        return self.connections[self.current_db]
    
    def _connect(self, database: str) -> Dict[str, Any]:
        """Connect to a database."""
        try:
            # Close existing connection if any
            if database in self.connections:
                self.connections[database].close()
            
            # Create new connection
            conn = sqlite3.connect(database)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            self.connections[database] = conn
            self.current_db = database
            
            # Get database info
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            return {
                "status": "connected",
                "database": database,
                "table_count": table_count,
                "message": f"Connected to database: {database}"
            }
            
        except Exception as e:
            return {"error": f"Failed to connect: {str(e)}"}
    
    def _execute_query(self, query: str, params: Optional[List] = None, 
                      format: str = "dict", limit: int = 100) -> Dict[str, Any]:
        """Execute SQL query."""
        if not query:
            return {"error": "Query is required"}
        
        # Validate query (basic SQL injection prevention)
        if not self._validate_query(query):
            return {"error": "Query validation failed - potential SQL injection detected"}
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Determine query type
            query_type = query.strip().upper().split()[0]
            
            # Execute query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Handle different query types
            if query_type == "SELECT":
                # Fetch results with limit
                if limit and "LIMIT" not in query.upper():
                    query += f" LIMIT {limit}"
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description] if cursor.description else []
                
                # Format results
                if format == "dict":
                    results = [dict(zip(columns, row)) for row in rows]
                elif format == "list":
                    results = [list(row) for row in rows]
                elif format == "csv":
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow(columns)
                    writer.writerows(rows)
                    results = output.getvalue()
                elif format == "json":
                    results = json.dumps([dict(zip(columns, row)) for row in rows], indent=2)
                else:
                    results = [dict(zip(columns, row)) for row in rows]
                
                return {
                    "status": "success",
                    "query_type": "SELECT",
                    "columns": columns,
                    "row_count": len(rows),
                    "data": results
                }
            
            elif query_type in ["INSERT", "UPDATE", "DELETE"]:
                conn.commit()
                return {
                    "status": "success",
                    "query_type": query_type,
                    "rows_affected": cursor.rowcount,
                    "last_row_id": cursor.lastrowid if query_type == "INSERT" else None
                }
            
            elif query_type in ["CREATE", "DROP", "ALTER"]:
                conn.commit()
                return {
                    "status": "success",
                    "query_type": query_type,
                    "message": f"{query_type} operation completed"
                }
            
            else:
                conn.commit()
                return {
                    "status": "success",
                    "query_type": query_type,
                    "message": "Query executed successfully"
                }
                
        except Exception as e:
            return {"error": f"Query execution failed: {str(e)}", "query": query}
    
    def _create_table(self, table_name: str, columns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a new table."""
        if not table_name:
            return {"error": "Table name is required"}
        
        if not columns:
            return {"error": "Column definitions are required"}
        
        try:
            # Build CREATE TABLE statement
            column_defs = []
            for col in columns:
                col_def = f"{col['name']} {col.get('type', 'TEXT')}"
                
                if col.get('primary_key'):
                    col_def += " PRIMARY KEY"
                if col.get('not_null'):
                    col_def += " NOT NULL"
                if col.get('unique'):
                    col_def += " UNIQUE"
                if 'default' in col:
                    default_val = col['default']
                    if isinstance(default_val, str):
                        col_def += f" DEFAULT '{default_val}'"
                    else:
                        col_def += f" DEFAULT {default_val}"
                
                column_defs.append(col_def)
            
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
            
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            
            return {
                "status": "created",
                "table_name": table_name,
                "columns": columns,
                "message": f"Table '{table_name}' created successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to create table: {str(e)}"}
    
    def _list_tables(self) -> Dict[str, Any]:
        """List all tables in the database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name, sql 
                FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            
            tables = []
            for row in cursor.fetchall():
                # Get row count for each table
                cursor.execute(f"SELECT COUNT(*) FROM {row[0]}")
                row_count = cursor.fetchone()[0]
                
                tables.append({
                    "name": row[0],
                    "row_count": row_count,
                    "sql": row[1]
                })
            
            return {
                "status": "success",
                "database": self.current_db,
                "table_count": len(tables),
                "tables": tables
            }
            
        except Exception as e:
            return {"error": f"Failed to list tables: {str(e)}"}
    
    def _describe_table(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information."""
        if not table_name:
            return {"error": "Table name is required"}
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "cid": row[0],
                    "name": row[1],
                    "type": row[2],
                    "not_null": bool(row[3]),
                    "default": row[4],
                    "primary_key": bool(row[5])
                })
            
            if not columns:
                return {"error": f"Table '{table_name}' not found"}
            
            # Get indexes
            cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = []
            for row in cursor.fetchall():
                indexes.append({
                    "name": row[1],
                    "unique": bool(row[2])
                })
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            sample_rows = cursor.fetchall()
            sample_data = [dict(zip([col[1] for col in columns], row)) for row in sample_rows]
            
            return {
                "status": "success",
                "table_name": table_name,
                "columns": columns,
                "indexes": indexes,
                "row_count": row_count,
                "sample_data": sample_data
            }
            
        except Exception as e:
            return {"error": f"Failed to describe table: {str(e)}"}
    
    def _import_csv(self, table_name: str, data: Union[str, List[Dict]]) -> Dict[str, Any]:
        """Import CSV data into a table."""
        if not table_name:
            return {"error": "Table name is required"}
        
        if not data:
            return {"error": "Data is required"}
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Parse data
            if isinstance(data, str):
                # CSV string
                reader = csv.DictReader(io.StringIO(data))
                records = list(reader)
            elif isinstance(data, list):
                # List of dictionaries
                records = data
            else:
                return {"error": "Data must be CSV string or list of dictionaries"}
            
            if not records:
                return {"error": "No data to import"}
            
            # Get column names from first record
            columns = list(records[0].keys())
            
            # Check if table exists, create if not
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                # Create table with all TEXT columns (simple approach)
                column_defs = [f"{col} TEXT" for col in columns]
                create_query = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
                cursor.execute(create_query)
            
            # Insert data
            placeholders = ', '.join(['?' for _ in columns])
            insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            inserted = 0
            failed = 0
            for record in records:
                try:
                    values = [record.get(col) for col in columns]
                    cursor.execute(insert_query, values)
                    inserted += 1
                except Exception as e:
                    failed += 1
            
            conn.commit()
            
            return {
                "status": "imported",
                "table_name": table_name,
                "total_records": len(records),
                "inserted": inserted,
                "failed": failed,
                "columns": columns
            }
            
        except Exception as e:
            return {"error": f"Import failed: {str(e)}"}
    
    def _export_table(self, table_name: str, format: str = "csv") -> Dict[str, Any]:
        """Export table data."""
        if not table_name:
            return {"error": "Table name is required"}
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all data from table
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            if format == "csv":
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(columns)
                writer.writerows(rows)
                data = output.getvalue()
            elif format == "json":
                data = json.dumps([dict(zip(columns, row)) for row in rows], indent=2)
            else:
                data = [dict(zip(columns, row)) for row in rows]
            
            return {
                "status": "exported",
                "table_name": table_name,
                "format": format,
                "row_count": len(rows),
                "columns": columns,
                "data": data
            }
            
        except Exception as e:
            return {"error": f"Export failed: {str(e)}"}
    
    def _backup_database(self) -> Dict[str, Any]:
        """Create database backup."""
        try:
            conn = self._get_connection()
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.current_db}.backup_{timestamp}"
            
            # Create backup
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
            
            # Get backup file size
            backup_size = Path(backup_path).stat().st_size
            
            return {
                "status": "backed_up",
                "backup_path": backup_path,
                "backup_size": backup_size,
                "timestamp": timestamp,
                "message": f"Database backed up to {backup_path}"
            }
            
        except Exception as e:
            return {"error": f"Backup failed: {str(e)}"}
    
    def _validate_query(self, query: str) -> bool:
        """Basic SQL injection prevention."""
        # This is a simple validation - in production, use proper parameterized queries
        dangerous_patterns = [
            '--', '/*', '*/', 'xp_', 'sp_', 'exec', 'execute',
            'drop database', 'drop table', 'truncate'
        ]
        
        query_lower = query.lower()
        for pattern in dangerous_patterns:
            if pattern in query_lower:
                return False
        
        return True
    
    def __del__(self):
        """Clean up database connections."""
        for conn in self.connections.values():
            try:
                conn.close()
            except:
                pass
