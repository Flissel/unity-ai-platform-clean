#!/usr/bin/env python3
"""
Example script demonstrating how to execute n8n workflows through the API.

This script shows how to:
1. Connect to the n8n API
2. List available workflows
3. Execute a specific workflow
4. Monitor execution status
5. Retrieve execution results

Usage:
    python execute_workflow_example.py [workflow_id]

Environment Variables Required:
    N8N_API_KEY: Your n8n API key
    N8N_BASE_URL: Your n8n instance URL (default: https://n8n.unit-y-ai.io)
"""

import os
import sys
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
project_root = Path(__file__).parent
load_dotenv(project_root / ".env")


class N8nWorkflowExecutor:
    """Class to handle n8n workflow execution through the API."""
    
    def __init__(self, api_key: str, base_url: str = "https://n8n.unit-y-ai.io"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "X-N8N-API-KEY": api_key,
            "Content-Type": "application/json"
        }
    
    async def list_workflows(self) -> Dict[str, Any]:
        """List all available workflows."""
        async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=30.0) as client:
            response = await client.get("/api/v1/workflows")
            response.raise_for_status()
            return response.json()
    
    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get details of a specific workflow."""
        async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=30.0) as client:
            response = await client.get(f"/api/v1/workflows/{workflow_id}")
            response.raise_for_status()
            return response.json()
    
    async def execute_workflow(self, workflow_id: str, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a workflow with optional input data."""
        payload = {}
        if input_data:
            payload["data"] = input_data
        
        async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=60.0) as client:
            response = await client.post(f"/api/v1/workflows/{workflow_id}/execute", json=payload)
            response.raise_for_status()
            return response.json()
    
    async def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """Get details of a specific execution."""
        async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=30.0) as client:
            response = await client.get(f"/api/v1/executions/{execution_id}")
            response.raise_for_status()
            return response.json()
    
    async def wait_for_execution(self, execution_id: str, timeout: int = 300, poll_interval: int = 2) -> Dict[str, Any]:
        """Wait for an execution to complete and return the result."""
        start_time = datetime.now()
        
        while True:
            execution = await self.get_execution(execution_id)
            status = execution.get('status', 'unknown')
            
            print(f"⏳ Execution status: {status}")
            
            if status in ['success', 'error', 'canceled']:
                return execution
            
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                print(f"⏰ Execution timed out after {timeout} seconds")
                return execution
            
            await asyncio.sleep(poll_interval)


async def demonstrate_workflow_execution():
    """Demonstrate workflow execution capabilities."""
    
    # Get configuration
    api_key = os.getenv("N8N_API_KEY")
    base_url = os.getenv("N8N_BASE_URL", "https://n8n.unit-y-ai.io")
    
    if not api_key:
        print("❌ Error: N8N_API_KEY environment variable not set")
        print("Please set your API key in the .env file")
        sys.exit(1)
    
    # Initialize executor
    executor = N8nWorkflowExecutor(api_key, base_url)
    
    try:
        print("🚀 n8n Workflow Executor Demo")
        print("=" * 50)
        print(f"🔗 Connected to: {base_url}")
        
        # List workflows
        print("\n📋 Fetching available workflows...")
        workflows_data = await executor.list_workflows()
        
        # Handle both direct list and dict with 'data' key
        if isinstance(workflows_data, dict) and 'data' in workflows_data:
            workflows = workflows_data['data']
        else:
            workflows = workflows_data if isinstance(workflows_data, list) else []
        
        if not workflows:
            print("🔍 No workflows found in your n8n instance.")
            return
        
        print(f"\n✅ Found {len(workflows)} workflow(s):")
        print("-" * 80)
        for i, workflow in enumerate(workflows[:10], 1):  # Show first 10
            status = "🟢 Active" if workflow.get('active', False) else "🔴 Inactive"
            print(f"{i:2d}. {workflow.get('name', 'Unnamed'):<30} | ID: {workflow.get('id'):<20} | {status}")
        
        if len(workflows) > 10:
            print(f"    ... and {len(workflows) - 10} more workflows")
        
        # Get workflow ID from command line or user input
        workflow_id = None
        if len(sys.argv) > 1:
            workflow_id = sys.argv[1]
        else:
            print("\n🎯 Enter a workflow ID to execute (or press Enter to exit):")
            workflow_id = input("> ").strip()
        
        if not workflow_id:
            print("👋 Goodbye!")
            return
        
        # Validate workflow exists
        workflow_exists = any(w.get('id') == workflow_id for w in workflows)
        if not workflow_exists:
            print(f"❌ Workflow with ID '{workflow_id}' not found.")
            return
        
        # Get workflow details
        print(f"\n🔍 Getting details for workflow: {workflow_id}")
        workflow_details = await executor.get_workflow(workflow_id)
        print(f"📝 Workflow Name: {workflow_details.get('name', 'Unnamed')}")
        print(f"📊 Status: {'🟢 Active' if workflow_details.get('active', False) else '🔴 Inactive'}")
        
        # Ask for input data
        print("\n💾 Enter input data for the workflow (JSON format, or press Enter for no input):")
        input_data_str = input("> ").strip()
        input_data = None
        
        if input_data_str:
            try:
                input_data = json.loads(input_data_str)
                print(f"✅ Input data parsed: {input_data}")
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON format: {e}")
                print("Proceeding without input data...")
        
        # Execute workflow
        print(f"\n🚀 Executing workflow: {workflow_id}")
        execution_result = await executor.execute_workflow(workflow_id, input_data)
        
        execution_id = execution_result.get('data', {}).get('executionId')
        if not execution_id:
            print(f"❌ Failed to get execution ID from response: {execution_result}")
            return
        
        print(f"✅ Workflow execution started!")
        print(f"🆔 Execution ID: {execution_id}")
        
        # Wait for completion
        print("\n⏳ Waiting for execution to complete...")
        final_execution = await executor.wait_for_execution(execution_id)
        
        # Display results
        status = final_execution.get('status', 'unknown')
        print(f"\n🏁 Execution completed with status: {status}")
        
        if status == 'success':
            print("🎉 Workflow executed successfully!")
            
            # Show execution data if available
            execution_data = final_execution.get('data', {})
            if execution_data:
                print("\n📊 Execution Results:")
                print(json.dumps(execution_data, indent=2, default=str))
        
        elif status == 'error':
            print("❌ Workflow execution failed!")
            error_message = final_execution.get('data', {}).get('resultData', {}).get('error', {}).get('message', 'Unknown error')
            print(f"💥 Error: {error_message}")
        
        else:
            print(f"⚠️ Workflow execution ended with status: {status}")
        
        # Show execution summary
        started_at = final_execution.get('startedAt')
        finished_at = final_execution.get('stoppedAt')
        if started_at and finished_at:
            from datetime import datetime
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(finished_at.replace('Z', '+00:00'))
            duration = (end_time - start_time).total_seconds()
            print(f"⏱️ Execution time: {duration:.2f} seconds")
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print("❌ Authentication failed - check your N8N_API_KEY")
        elif e.response.status_code == 403:
            print("❌ Insufficient permissions to access workflows")
        elif e.response.status_code == 404:
            print("❌ Workflow not found")
        else:
            print(f"❌ API request failed with status {e.response.status_code}")
            print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def main():
    """Main function."""
    await demonstrate_workflow_execution()


if __name__ == "__main__":
    asyncio.run(main())