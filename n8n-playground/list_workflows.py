#!/usr/bin/env python3
"""
Script to fetch and display all workflows from n8n API in the terminal.
"""

import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# Load environment variables
project_root = Path(__file__).parent
load_dotenv(project_root / ".env")

async def fetch_workflows():
    """Fetch all workflows from n8n API."""
    api_key = os.getenv("N8N_API_KEY")
    base_url = os.getenv("N8N_BASE_URL", "https://n8n.unit-y-ai.io")
    
    if not api_key:
        print("❌ Error: N8N_API_KEY environment variable not set")
        print("Please set your API key in the .env file")
        sys.exit(1)
    
    headers = {
        "X-N8N-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0) as client:
            print(f"🔗 Connecting to n8n API at {base_url}...")
            response = await client.get("/api/v1/workflows")
            
            if response.status_code == 401:
                print("❌ Authentication failed - check your N8N_API_KEY")
                sys.exit(1)
            elif response.status_code == 403:
                print("❌ Insufficient permissions to access workflows")
                sys.exit(1)
            elif response.status_code != 200:
                print(f"❌ API request failed with status {response.status_code}")
                print(f"Response: {response.text}")
                sys.exit(1)
            
            data = response.json()
            return data
            
    except httpx.RequestError as e:
        print(f"❌ Network error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def format_workflow_status(active):
    """Format workflow status with emoji."""
    return "🟢 Active" if active else "🔴 Inactive"

def format_datetime(date_str):
    """Format datetime string for display."""
    if not date_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return date_str

def display_workflows(workflows_data):
    """Display workflows in a formatted table."""
    # Handle both direct list and dict with 'data' key
    if isinstance(workflows_data, dict) and 'data' in workflows_data:
        workflows = workflows_data['data']
        total_count = len(workflows)
        has_more = workflows_data.get('nextCursor') is not None
    else:
        workflows = workflows_data if isinstance(workflows_data, list) else []
        total_count = len(workflows)
        has_more = False
    
    print(f"\n📋 Found {total_count} workflow(s)")
    if has_more:
        print("📄 Note: There may be more workflows (pagination detected)")
    
    if not workflows:
        print("\n🔍 No workflows found in your n8n instance.")
        return
    
    print("\n" + "="*100)
    print(f"{'ID':<20} {'Name':<30} {'Status':<15} {'Created':<20} {'Updated':<20}")
    print("="*100)
    
    for workflow in workflows:
        workflow_id = str(workflow.get('id', 'N/A'))[:18]
        name = str(workflow.get('name', 'Unnamed'))[:28]
        status = format_workflow_status(workflow.get('active', False))
        created = format_datetime(workflow.get('createdAt', ''))
        updated = format_datetime(workflow.get('updatedAt', ''))
        
        print(f"{workflow_id:<20} {name:<30} {status:<15} {created:<20} {updated:<20}")
    
    print("="*100)
    
    # Display summary statistics
    active_count = sum(1 for w in workflows if w.get('active', False))
    inactive_count = total_count - active_count
    
    print(f"\n📊 Summary:")
    print(f"   🟢 Active workflows: {active_count}")
    print(f"   🔴 Inactive workflows: {inactive_count}")
    print(f"   📈 Total workflows: {total_count}")

async def main():
    """Main function."""
    print("🚀 n8n Workflow Lister")
    print("=" * 50)
    
    workflows_data = await fetch_workflows()
    display_workflows(workflows_data)
    
    print("\n✅ Done!")

if __name__ == "__main__":
    asyncio.run(main())