#!/usr/bin/env python3
"""
Example data analysis script for UnityAI Python Worker.
"""

import json
import sys
from typing import Dict, Any, List
import pandas as pd
import numpy as np


def analyze_data(data: List[Dict[str, Any]], operation: str = "summary") -> Dict[str, Any]:
    """Analyze data using pandas and numpy."""
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        if operation == "summary":
            return {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.to_dict(),
                "null_counts": df.isnull().sum().to_dict(),
                "numeric_summary": df.describe().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else None
            }
        
        elif operation == "statistics":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                return {"error": "No numeric columns found"}
            
            stats = {}
            for col in numeric_cols:
                stats[col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "quartiles": df[col].quantile([0.25, 0.5, 0.75]).to_dict()
                }
            return stats
        
        elif operation == "correlation":
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) < 2:
                return {"error": "Need at least 2 numeric columns for correlation"}
            
            return numeric_df.corr().to_dict()
        
        elif operation == "groupby":
            # Simple groupby operation - group by first categorical column
            categorical_cols = df.select_dtypes(include=['object']).columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            if len(categorical_cols) == 0 or len(numeric_cols) == 0:
                return {"error": "Need both categorical and numeric columns for groupby"}
            
            group_col = categorical_cols[0]
            result = {}
            
            for num_col in numeric_cols:
                grouped = df.groupby(group_col)[num_col].agg(['mean', 'sum', 'count'])
                result[num_col] = grouped.to_dict()
            
            return result
        
        else:
            return {"error": f"Unknown operation: {operation}"}
    
    except Exception as e:
        return {"error": str(e)}


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python data_analysis.py <json_data> [operation]"}))
        sys.exit(1)
    
    try:
        data = json.loads(sys.argv[1])
        operation = sys.argv[2] if len(sys.argv) > 2 else "summary"
        
        result = analyze_data(data, operation)
        print(json.dumps(result, indent=2))
    
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON data"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()