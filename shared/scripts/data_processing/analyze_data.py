#!/usr/bin/env python3
"""
Data Analysis Script for n8n Integration

This script performs various data analysis operations and can be executed
directly from n8n workflows using the Execute Command node.

Usage:
  python3 analyze_data.py --input '{"data": [...], "operation": "summary"}'
  python3 analyze_data.py --input-file input.json --operation statistics
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

# Add shared libs to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'libs'))
from common import (
    handle_errors, setup_logging, validate_input, safe_json_loads,
    create_success_response, create_error_response, measure_execution_time
)
from config import get_config

# Setup logging
logger = setup_logging()
config = get_config()


@measure_execution_time
@handle_errors
def analyze_data(data: List[Dict[str, Any]], operation: str = "summary") -> Dict[str, Any]:
    """Analyze data using pandas and numpy."""
    
    try:
        import pandas as pd
        import numpy as np
    except ImportError as e:
        return create_error_response(
            f"Required packages not installed: {e}",
            "ImportError",
            {"required_packages": ["pandas", "numpy"]}
        )
    
    logger.info(f"Starting data analysis with operation: {operation}")
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        logger.info(f"Created DataFrame with shape: {df.shape}")
        
        if operation == "summary":
            result = {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "null_counts": df.isnull().sum().to_dict(),
                "memory_usage": df.memory_usage(deep=True).to_dict()
            }
            
            # Add numeric summary if numeric columns exist
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                result["numeric_summary"] = df[numeric_cols].describe().to_dict()
            
            return create_success_response(result, {
                "operation": operation,
                "rows_processed": len(df),
                "columns_processed": len(df.columns)
            })
        
        elif operation == "statistics":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                return create_error_response(
                    "No numeric columns found for statistics",
                    "ValueError",
                    {"available_columns": df.columns.tolist()}
                )
            
            stats = {}
            for col in numeric_cols:
                col_data = df[col].dropna()
                stats[col] = {
                    "count": int(len(col_data)),
                    "mean": float(col_data.mean()),
                    "median": float(col_data.median()),
                    "std": float(col_data.std()),
                    "min": float(col_data.min()),
                    "max": float(col_data.max()),
                    "quartiles": {
                        "q1": float(col_data.quantile(0.25)),
                        "q2": float(col_data.quantile(0.5)),
                        "q3": float(col_data.quantile(0.75))
                    },
                    "skewness": float(col_data.skew()),
                    "kurtosis": float(col_data.kurtosis())
                }
            
            return create_success_response(stats, {
                "operation": operation,
                "numeric_columns_analyzed": len(numeric_cols)
            })
        
        elif operation == "correlation":
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) < 2:
                return create_error_response(
                    "Need at least 2 numeric columns for correlation analysis",
                    "ValueError",
                    {"numeric_columns_found": len(numeric_df.columns)}
                )
            
            correlation_matrix = numeric_df.corr().to_dict()
            
            return create_success_response({
                "correlation_matrix": correlation_matrix,
                "strong_correlations": find_strong_correlations(correlation_matrix)
            }, {
                "operation": operation,
                "columns_analyzed": list(numeric_df.columns)
            })
        
        elif operation == "groupby":
            # Group by first categorical column and aggregate numeric columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            if len(categorical_cols) == 0:
                return create_error_response(
                    "No categorical columns found for groupby operation",
                    "ValueError",
                    {"available_columns": df.columns.tolist()}
                )
            
            if len(numeric_cols) == 0:
                return create_error_response(
                    "No numeric columns found for aggregation",
                    "ValueError",
                    {"categorical_columns": categorical_cols.tolist()}
                )
            
            group_col = categorical_cols[0]
            result = {"grouped_by": group_col, "aggregations": {}}
            
            for num_col in numeric_cols:
                grouped = df.groupby(group_col)[num_col].agg([
                    'count', 'mean', 'median', 'std', 'min', 'max', 'sum'
                ])
                result["aggregations"][num_col] = grouped.to_dict()
            
            return create_success_response(result, {
                "operation": operation,
                "group_column": group_col,
                "numeric_columns": numeric_cols.tolist(),
                "unique_groups": int(df[group_col].nunique())
            })
        
        elif operation == "outliers":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                return create_error_response(
                    "No numeric columns found for outlier detection",
                    "ValueError"
                )
            
            outliers = {}
            for col in numeric_cols:
                col_data = df[col].dropna()
                q1 = col_data.quantile(0.25)
                q3 = col_data.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outlier_mask = (col_data < lower_bound) | (col_data > upper_bound)
                outlier_values = col_data[outlier_mask].tolist()
                
                outliers[col] = {
                    "count": len(outlier_values),
                    "percentage": (len(outlier_values) / len(col_data)) * 100,
                    "values": outlier_values[:50],  # Limit to first 50 outliers
                    "bounds": {
                        "lower": float(lower_bound),
                        "upper": float(upper_bound)
                    }
                }
            
            return create_success_response(outliers, {
                "operation": operation,
                "columns_analyzed": numeric_cols.tolist()
            })
        
        else:
            return create_error_response(
                f"Unknown operation: {operation}",
                "ValueError",
                {"available_operations": ["summary", "statistics", "correlation", "groupby", "outliers"]}
            )
    
    except Exception as e:
        logger.error(f"Error in data analysis: {e}")
        return create_error_response(
            f"Data analysis failed: {str(e)}",
            type(e).__name__
        )


def find_strong_correlations(correlation_matrix: Dict[str, Dict[str, float]], threshold: float = 0.7) -> List[Dict[str, Any]]:
    """Find strong correlations in correlation matrix."""
    
    strong_correlations = []
    
    for col1, correlations in correlation_matrix.items():
        for col2, corr_value in correlations.items():
            if col1 != col2 and abs(corr_value) >= threshold:
                # Avoid duplicates by ensuring col1 < col2 alphabetically
                if col1 < col2:
                    strong_correlations.append({
                        "column1": col1,
                        "column2": col2,
                        "correlation": round(corr_value, 4),
                        "strength": "strong" if abs(corr_value) >= 0.8 else "moderate"
                    })
    
    return sorted(strong_correlations, key=lambda x: abs(x["correlation"]), reverse=True)


def main():
    """Main function for command-line usage."""
    
    parser = argparse.ArgumentParser(
        description="Analyze data using pandas and numpy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze data from JSON string
  python3 analyze_data.py --input '{"data": [{"x": 1, "y": 2}, {"x": 3, "y": 4}], "operation": "summary"}'
  
  # Analyze data from file
  python3 analyze_data.py --input-file data.json --operation statistics
  
  # Find correlations
  python3 analyze_data.py --input '{"data": [...]}' --operation correlation
"""
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', help='JSON input data as string')
    input_group.add_argument('--input-file', help='Path to JSON input file')
    
    # Operation options
    parser.add_argument(
        '--operation', 
        default='summary',
        choices=['summary', 'statistics', 'correlation', 'groupby', 'outliers'],
        help='Analysis operation to perform (default: summary)'
    )
    
    # Output options
    parser.add_argument('--output-file', help='Path to save output JSON file')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    
    args = parser.parse_args()
    
    try:
        # Parse input data
        if args.input:
            input_data = safe_json_loads(args.input)
        else:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                input_data = json.load(f)
        
        # Validate input structure
        schema = {
            "data": {"type": "array", "required": True},
            "operation": {"type": "string", "required": False}
        }
        
        validate_input(input_data, schema)
        
        # Extract data and operation
        data = input_data["data"]
        operation = input_data.get("operation", args.operation)
        
        # Perform analysis
        result = analyze_data(data, operation)
        
        # Output result
        output_json = json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False)
        
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(output_json)
            logger.info(f"Results saved to {args.output_file}")
        else:
            print(output_json)
    
    except Exception as e:
        error_result = create_error_response(str(e), type(e).__name__)
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()