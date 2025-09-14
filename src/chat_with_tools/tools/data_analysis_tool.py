"""
Data Analysis Tool for Chat with Tools Framework

This tool provides comprehensive data analysis capabilities including
loading various data formats, statistical analysis, and visualization.
"""

import json
import csv
import io
import base64
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import statistics
import math
from .base_tool import BaseTool

# Try to import optional data science libraries
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False


class DataAnalysisTool(BaseTool):
    """
    Comprehensive data analysis tool for statistical analysis,
    data manipulation, and visualization.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.current_dataframe = None
        self.dataframe_name = None
    
    @property
    def name(self) -> str:
        return "data_analysis"
    
    @property
    def description(self) -> str:
        return """Analyze data from CSV, JSON, or direct input. Perform statistical analysis, transformations, and create visualizations.
        
        Actions:
        - load_csv: Load data from CSV string
        - load_json: Load data from JSON string
        - describe: Get statistical summary
        - analyze: Perform specific analysis
        - transform: Apply transformations
        - visualize: Create charts and plots
        - query: Filter and query data
        """
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["load_csv", "load_json", "describe", "analyze", "transform", "visualize", "query"],
                    "description": "Action to perform"
                },
                "data": {
                    "type": "string",
                    "description": "Data string (CSV or JSON format)"
                },
                "analysis_type": {
                    "type": "string",
                    "enum": ["correlation", "distribution", "outliers", "trends", "summary"],
                    "description": "Type of analysis to perform"
                },
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to analyze"
                },
                "transform_type": {
                    "type": "string",
                    "enum": ["normalize", "standardize", "log", "difference", "pivot", "melt"],
                    "description": "Type of transformation"
                },
                "chart_type": {
                    "type": "string",
                    "enum": ["line", "bar", "scatter", "histogram", "box", "heatmap", "pie"],
                    "description": "Type of visualization"
                },
                "query_string": {
                    "type": "string",
                    "description": "Query string for filtering data (e.g., 'column > 5')"
                },
                "x_column": {
                    "type": "string",
                    "description": "Column for x-axis"
                },
                "y_column": {
                    "type": "string",
                    "description": "Column for y-axis"
                }
            },
            "required": ["action"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute data analysis operations."""
        action = kwargs.get("action")
        
        try:
            if action == "load_csv":
                return self._load_csv(kwargs.get("data", ""))
            
            elif action == "load_json":
                return self._load_json(kwargs.get("data", ""))
            
            elif action == "describe":
                return self._describe(kwargs.get("columns"))
            
            elif action == "analyze":
                return self._analyze(
                    kwargs.get("analysis_type", "summary"),
                    kwargs.get("columns")
                )
            
            elif action == "transform":
                return self._transform(
                    kwargs.get("transform_type", "normalize"),
                    kwargs.get("columns")
                )
            
            elif action == "visualize":
                return self._visualize(
                    kwargs.get("chart_type", "bar"),
                    kwargs.get("x_column"),
                    kwargs.get("y_column")
                )
            
            elif action == "query":
                return self._query(kwargs.get("query_string", ""))
            
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": f"Data analysis failed: {str(e)}"}
    
    def _load_csv(self, csv_string: str) -> Dict[str, Any]:
        """Load CSV data."""
        if not csv_string:
            return {"error": "No CSV data provided"}
        
        try:
            if PANDAS_AVAILABLE:
                # Use pandas for better CSV handling
                self.current_dataframe = pd.read_csv(io.StringIO(csv_string))
                
                return {
                    "status": "loaded",
                    "shape": self.current_dataframe.shape,
                    "columns": list(self.current_dataframe.columns),
                    "dtypes": {col: str(dtype) for col, dtype in self.current_dataframe.dtypes.items()},
                    "preview": self.current_dataframe.head().to_dict('records')
                }
            else:
                # Fallback to basic CSV parsing
                reader = csv.DictReader(io.StringIO(csv_string))
                data = list(reader)
                
                if not data:
                    return {"error": "No data found in CSV"}
                
                return {
                    "status": "loaded",
                    "rows": len(data),
                    "columns": list(data[0].keys()) if data else [],
                    "preview": data[:5]
                }
                
        except Exception as e:
            return {"error": f"Failed to load CSV: {str(e)}"}
    
    def _load_json(self, json_string: str) -> Dict[str, Any]:
        """Load JSON data."""
        if not json_string:
            return {"error": "No JSON data provided"}
        
        try:
            data = json.loads(json_string)
            
            if PANDAS_AVAILABLE:
                # Convert to DataFrame
                if isinstance(data, list):
                    self.current_dataframe = pd.DataFrame(data)
                elif isinstance(data, dict):
                    self.current_dataframe = pd.DataFrame([data])
                else:
                    return {"error": "Unsupported JSON structure"}
                
                return {
                    "status": "loaded",
                    "shape": self.current_dataframe.shape,
                    "columns": list(self.current_dataframe.columns),
                    "dtypes": {col: str(dtype) for col, dtype in self.current_dataframe.dtypes.items()},
                    "preview": self.current_dataframe.head().to_dict('records')
                }
            else:
                return {
                    "status": "loaded",
                    "data_type": type(data).__name__,
                    "preview": data[:5] if isinstance(data, list) else data
                }
                
        except Exception as e:
            return {"error": f"Failed to load JSON: {str(e)}"}
    
    def _describe(self, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get statistical description of data."""
        if not PANDAS_AVAILABLE or self.current_dataframe is None:
            return {"error": "No data loaded or pandas not available"}
        
        try:
            df = self.current_dataframe
            
            if columns:
                df = df[columns]
            
            # Get numeric columns only
            numeric_df = df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                return {"error": "No numeric columns to describe"}
            
            description = numeric_df.describe().to_dict()
            
            # Add additional statistics
            for col in numeric_df.columns:
                description[col]['median'] = numeric_df[col].median()
                description[col]['mode'] = numeric_df[col].mode().values[0] if not numeric_df[col].mode().empty else None
                description[col]['skewness'] = numeric_df[col].skew()
                description[col]['kurtosis'] = numeric_df[col].kurtosis()
                description[col]['null_count'] = numeric_df[col].isnull().sum()
            
            return {
                "status": "described",
                "statistics": description,
                "shape": df.shape,
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
        except Exception as e:
            return {"error": f"Description failed: {str(e)}"}
    
    def _analyze(self, analysis_type: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform specific analysis."""
        if not PANDAS_AVAILABLE or self.current_dataframe is None:
            return {"error": "No data loaded or pandas not available"}
        
        try:
            df = self.current_dataframe
            
            if columns:
                df = df[columns]
            
            if analysis_type == "correlation":
                # Correlation matrix
                numeric_df = df.select_dtypes(include=[np.number])
                correlation = numeric_df.corr().to_dict()
                
                return {
                    "status": "analyzed",
                    "analysis_type": "correlation",
                    "correlation_matrix": correlation,
                    "highly_correlated": self._find_high_correlations(numeric_df.corr())
                }
            
            elif analysis_type == "distribution":
                # Distribution analysis
                distributions = {}
                numeric_df = df.select_dtypes(include=[np.number])
                
                for col in numeric_df.columns:
                    distributions[col] = {
                        "mean": numeric_df[col].mean(),
                        "std": numeric_df[col].std(),
                        "skewness": numeric_df[col].skew(),
                        "kurtosis": numeric_df[col].kurtosis(),
                        "quartiles": {
                            "Q1": numeric_df[col].quantile(0.25),
                            "Q2": numeric_df[col].quantile(0.50),
                            "Q3": numeric_df[col].quantile(0.75)
                        }
                    }
                
                return {
                    "status": "analyzed",
                    "analysis_type": "distribution",
                    "distributions": distributions
                }
            
            elif analysis_type == "outliers":
                # Outlier detection using IQR method
                outliers = {}
                numeric_df = df.select_dtypes(include=[np.number])
                
                for col in numeric_df.columns:
                    Q1 = numeric_df[col].quantile(0.25)
                    Q3 = numeric_df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outlier_mask = (numeric_df[col] < lower_bound) | (numeric_df[col] > upper_bound)
                    outlier_values = numeric_df[col][outlier_mask].tolist()
                    
                    outliers[col] = {
                        "count": len(outlier_values),
                        "percentage": len(outlier_values) / len(numeric_df[col]) * 100,
                        "lower_bound": lower_bound,
                        "upper_bound": upper_bound,
                        "values": outlier_values[:10]  # First 10 outliers
                    }
                
                return {
                    "status": "analyzed",
                    "analysis_type": "outliers",
                    "outliers": outliers
                }
            
            elif analysis_type == "trends":
                # Trend analysis (for time series or sequential data)
                trends = {}
                numeric_df = df.select_dtypes(include=[np.number])
                
                for col in numeric_df.columns:
                    values = numeric_df[col].dropna()
                    if len(values) > 1:
                        # Simple linear trend
                        x = np.arange(len(values))
                        z = np.polyfit(x, values, 1)
                        
                        trends[col] = {
                            "slope": z[0],
                            "intercept": z[1],
                            "direction": "increasing" if z[0] > 0 else "decreasing",
                            "strength": abs(z[0])
                        }
                
                return {
                    "status": "analyzed",
                    "analysis_type": "trends",
                    "trends": trends
                }
            
            else:  # summary
                return self._describe(columns)
                
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _transform(self, transform_type: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Apply transformations to data."""
        if not PANDAS_AVAILABLE or self.current_dataframe is None:
            return {"error": "No data loaded or pandas not available"}
        
        try:
            df = self.current_dataframe.copy()
            
            if transform_type == "normalize":
                # Min-max normalization
                if columns:
                    for col in columns:
                        if col in df.columns and np.issubdtype(df[col].dtype, np.number):
                            df[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
                else:
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    for col in numeric_cols:
                        df[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
                
                self.current_dataframe = df
                
                return {
                    "status": "transformed",
                    "transform_type": "normalize",
                    "preview": df.head().to_dict('records')
                }
            
            elif transform_type == "standardize":
                # Z-score standardization
                if columns:
                    for col in columns:
                        if col in df.columns and np.issubdtype(df[col].dtype, np.number):
                            df[col] = (df[col] - df[col].mean()) / df[col].std()
                else:
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    for col in numeric_cols:
                        df[col] = (df[col] - df[col].mean()) / df[col].std()
                
                self.current_dataframe = df
                
                return {
                    "status": "transformed",
                    "transform_type": "standardize",
                    "preview": df.head().to_dict('records')
                }
            
            elif transform_type == "log":
                # Log transformation
                if columns:
                    for col in columns:
                        if col in df.columns and np.issubdtype(df[col].dtype, np.number):
                            df[col] = np.log1p(df[col])  # log1p to handle zeros
                else:
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    for col in numeric_cols:
                        df[col] = np.log1p(df[col])
                
                self.current_dataframe = df
                
                return {
                    "status": "transformed",
                    "transform_type": "log",
                    "preview": df.head().to_dict('records')
                }
            
            else:
                return {"error": f"Transform type '{transform_type}' not implemented"}
                
        except Exception as e:
            return {"error": f"Transformation failed: {str(e)}"}
    
    def _visualize(self, chart_type: str, x_column: Optional[str] = None, y_column: Optional[str] = None) -> Dict[str, Any]:
        """Create visualizations."""
        if not PLOTTING_AVAILABLE:
            return {"error": "Matplotlib not available for plotting"}
        
        if not PANDAS_AVAILABLE or self.current_dataframe is None:
            return {"error": "No data loaded"}
        
        try:
            plt.figure(figsize=(10, 6))
            
            if chart_type == "line":
                if x_column and y_column:
                    plt.plot(self.current_dataframe[x_column], self.current_dataframe[y_column])
                    plt.xlabel(x_column)
                    plt.ylabel(y_column)
                else:
                    self.current_dataframe.plot(kind='line')
                plt.title("Line Chart")
            
            elif chart_type == "bar":
                if x_column and y_column:
                    plt.bar(self.current_dataframe[x_column], self.current_dataframe[y_column])
                    plt.xlabel(x_column)
                    plt.ylabel(y_column)
                else:
                    self.current_dataframe.plot(kind='bar')
                plt.title("Bar Chart")
            
            elif chart_type == "scatter":
                if x_column and y_column:
                    plt.scatter(self.current_dataframe[x_column], self.current_dataframe[y_column])
                    plt.xlabel(x_column)
                    plt.ylabel(y_column)
                else:
                    return {"error": "Scatter plot requires x_column and y_column"}
                plt.title("Scatter Plot")
            
            elif chart_type == "histogram":
                if y_column:
                    plt.hist(self.current_dataframe[y_column], bins=30)
                    plt.xlabel(y_column)
                else:
                    numeric_cols = self.current_dataframe.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        plt.hist(self.current_dataframe[numeric_cols[0]], bins=30)
                        plt.xlabel(numeric_cols[0])
                plt.ylabel("Frequency")
                plt.title("Histogram")
            
            elif chart_type == "box":
                numeric_df = self.current_dataframe.select_dtypes(include=[np.number])
                numeric_df.boxplot()
                plt.title("Box Plot")
            
            elif chart_type == "heatmap":
                numeric_df = self.current_dataframe.select_dtypes(include=[np.number])
                correlation = numeric_df.corr()
                
                plt.imshow(correlation, cmap='coolwarm', aspect='auto')
                plt.colorbar()
                plt.xticks(range(len(correlation.columns)), correlation.columns, rotation=45)
                plt.yticks(range(len(correlation.columns)), correlation.columns)
                plt.title("Correlation Heatmap")
            
            else:
                return {"error": f"Chart type '{chart_type}' not implemented"}
            
            # Save to base64
            buffer = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            return {
                "status": "visualized",
                "chart_type": chart_type,
                "image_base64": image_base64,
                "image_format": "png",
                "note": "Image is base64 encoded. Decode to view."
            }
            
        except Exception as e:
            plt.close()
            return {"error": f"Visualization failed: {str(e)}"}
    
    def _query(self, query_string: str) -> Dict[str, Any]:
        """Query and filter data."""
        if not PANDAS_AVAILABLE or self.current_dataframe is None:
            return {"error": "No data loaded or pandas not available"}
        
        try:
            # Use pandas query method
            result_df = self.current_dataframe.query(query_string)
            
            return {
                "status": "queried",
                "query": query_string,
                "result_shape": result_df.shape,
                "result_preview": result_df.head(20).to_dict('records'),
                "total_matches": len(result_df)
            }
            
        except Exception as e:
            return {"error": f"Query failed: {str(e)}"}
    
    def _find_high_correlations(self, corr_matrix, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find highly correlated pairs."""
        high_corr = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i, j]) > threshold:
                    high_corr.append({
                        "column1": corr_matrix.columns[i],
                        "column2": corr_matrix.columns[j],
                        "correlation": round(corr_matrix.iloc[i, j], 3)
                    })
        
        return high_corr
