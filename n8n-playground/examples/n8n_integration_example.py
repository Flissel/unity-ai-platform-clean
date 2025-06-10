#!/usr/bin/env python3
"""
n8n Integration Example

This script demonstrates how to use the n8n API integration to:
1. List available workflows
2. Execute workflows with custom data
3. Monitor execution status
4. Retrieve results
5. Manage workflow executions

Author: UnityAI Team
Version: 1.0.0
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List

import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.json import JSON

# Initialize rich console for beautiful output
console = Console()


class N8nApiClient:
    """Client for interacting with the n8n API integration."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/workflow-automation/n8n"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check n8n API health."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base}/health")
            response.raise_for_status()
            return response.json()
    
    async def list_workflows(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List all available workflows."""
        params = {"active_only": active_only}
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base}/workflows", params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed workflow information."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base}/workflows/{workflow_id}")
            response.raise_for_status()
            return response.json()
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any] = None,
        wait_for_completion: bool = True,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """Execute a workflow."""
        payload = {
            "workflow_id": workflow_id,
            "input_data": input_data or {},
            "wait_for_completion": wait_for_completion,
            "timeout": timeout,
            "metadata": {
                "source": "n8n_integration_example",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        async with httpx.AsyncClient(timeout=timeout + 30) as client:
            response = await client.post(
                f"{self.api_base}/workflows/{workflow_id}/execute",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status and results."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base}/executions/{execution_id}")
            response.raise_for_status()
            return response.json()
    
    async def list_executions(self, workflow_id: str = None) -> List[Dict[str, Any]]:
        """List workflow executions."""
        params = {}
        if workflow_id:
            params["workflow_id"] = workflow_id
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base}/executions", params=params)
            response.raise_for_status()
            return response.json()
    
    async def cancel_execution(self, execution_id: str) -> Dict[str, Any]:
        """Cancel a running execution."""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.api_base}/executions/{execution_id}/cancel")
            response.raise_for_status()
            return response.json()
    
    async def get_workflow_stats(self, workflow_id: str, days: int = 30) -> Dict[str, Any]:
        """Get workflow execution statistics."""
        params = {"days": days}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/workflows/{workflow_id}/stats",
                params=params
            )
            response.raise_for_status()
            return response.json()


def display_workflows(workflows: List[Dict[str, Any]]):
    """Display workflows in a formatted table."""
    table = Table(title="Available n8n Workflows")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Created", style="blue")
    table.add_column("Updated", style="blue")
    table.add_column("Tags", style="yellow")
    
    for workflow in workflows:
        status = "🟢 Active" if workflow.get("active") else "🔴 Inactive"
        created = workflow.get("created_at", "N/A")
        updated = workflow.get("updated_at", "N/A")
        tags = ", ".join(workflow.get("tags", []))
        
        # Format dates
        if created != "N/A":
            try:
                created = datetime.fromisoformat(created.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        if updated != "N/A":
            try:
                updated = datetime.fromisoformat(updated.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        table.add_row(
            workflow["id"],
            workflow["name"],
            status,
            created,
            updated,
            tags or "None"
        )
    
    console.print(table)


def display_execution_result(execution: Dict[str, Any]):
    """Display execution result in a formatted panel."""
    status_color = {
        "success": "green",
        "error": "red",
        "running": "yellow",
        "canceled": "orange"
    }.get(execution.get("status", "unknown"), "white")
    
    status_emoji = {
        "success": "✅",
        "error": "❌",
        "running": "🔄",
        "canceled": "⏹️"
    }.get(execution.get("status", "unknown"), "❓")
    
    title = f"{status_emoji} Execution Result - {execution.get('status', 'Unknown').upper()}"
    
    content = f"""
[bold]Execution ID:[/bold] {execution.get('execution_id', 'N/A')}
[bold]Workflow ID:[/bold] {execution.get('workflow_id', 'N/A')}
[bold]Status:[/bold] [{status_color}]{execution.get('status', 'Unknown')}[/{status_color}]
[bold]Started:[/bold] {execution.get('started_at', 'N/A')}
[bold]Finished:[/bold] {execution.get('finished_at', 'N/A')}
[bold]Duration:[/bold] {execution.get('duration', 'N/A')} seconds
"""
    
    if execution.get('error_message'):
        content += f"\n[bold red]Error:[/bold red] {execution['error_message']}"
    
    panel = Panel(content, title=title, border_style=status_color)
    console.print(panel)
    
    # Display result data if available
    if execution.get('result_data'):
        console.print("\n[bold]Result Data:[/bold]")
        console.print(JSON(json.dumps(execution['result_data'], indent=2)))


def display_workflow_stats(stats: Dict[str, Any]):
    """Display workflow statistics."""
    success_rate = stats.get('success_rate_percent', 0)
    success_color = "green" if success_rate >= 90 else "yellow" if success_rate >= 70 else "red"
    
    content = f"""
[bold]Workflow ID:[/bold] {stats.get('workflow_id', 'N/A')}
[bold]Analysis Period:[/bold] {stats.get('period_days', 'N/A')} days
[bold]Total Executions:[/bold] {stats.get('total_executions', 0)}
[bold]Successful:[/bold] [green]{stats.get('successful_executions', 0)}[/green]
[bold]Failed:[/bold] [red]{stats.get('failed_executions', 0)}[/red]
[bold]Success Rate:[/bold] [{success_color}]{success_rate}%[/{success_color}]
[bold]Average Duration:[/bold] {stats.get('average_duration_seconds', 0):.2f} seconds
[bold]Generated:[/bold] {stats.get('analysis_timestamp', 'N/A')}
"""
    
    panel = Panel(content, title="📊 Workflow Statistics", border_style="blue")
    console.print(panel)


async def demo_health_check(client: N8nApiClient):
    """Demonstrate health check functionality."""
    console.print("\n[bold blue]🔍 Checking n8n API Health...[/bold blue]")
    
    try:
        health = await client.health_check()
        
        if health.get('status') == 'healthy':
            console.print("[green]✅ n8n API is healthy and accessible![/green]")
        else:
            console.print("[red]❌ n8n API is not healthy[/red]")
        
        console.print(f"Base URL: {health.get('base_url')}")
        console.print(f"Timestamp: {health.get('timestamp')}")
        
    except Exception as e:
        console.print(f"[red]❌ Health check failed: {e}[/red]")


async def demo_list_workflows(client: N8nApiClient):
    """Demonstrate workflow listing functionality."""
    console.print("\n[bold blue]📋 Listing Available Workflows...[/bold blue]")
    
    try:
        workflows = await client.list_workflows()
        
        if workflows:
            display_workflows(workflows)
            console.print(f"\n[green]Found {len(workflows)} workflows[/green]")
            return workflows
        else:
            console.print("[yellow]No workflows found[/yellow]")
            return []
            
    except Exception as e:
        console.print(f"[red]❌ Failed to list workflows: {e}[/red]")
        return []


async def demo_execute_workflow(client: N8nApiClient, workflow_id: str):
    """Demonstrate workflow execution."""
    console.print(f"\n[bold blue]🚀 Executing Workflow {workflow_id}...[/bold blue]")
    
    # Example input data - customize based on your workflow needs
    input_data = {
        "message": "Hello from n8n API integration!",
        "timestamp": datetime.utcnow().isoformat(),
        "source": "unity_ai_example"
    }
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Executing workflow...", total=None)
            
            execution = await client.execute_workflow(
                workflow_id=workflow_id,
                input_data=input_data,
                wait_for_completion=True,
                timeout=300
            )
            
            progress.update(task, description="Execution completed!")
        
        display_execution_result(execution)
        return execution
        
    except Exception as e:
        console.print(f"[red]❌ Failed to execute workflow: {e}[/red]")
        return None


async def demo_workflow_stats(client: N8nApiClient, workflow_id: str):
    """Demonstrate workflow statistics."""
    console.print(f"\n[bold blue]📊 Getting Workflow Statistics for {workflow_id}...[/bold blue]")
    
    try:
        stats = await client.get_workflow_stats(workflow_id, days=30)
        display_workflow_stats(stats)
        
    except Exception as e:
        console.print(f"[red]❌ Failed to get workflow stats: {e}[/red]")


async def demo_list_executions(client: N8nApiClient, workflow_id: str = None):
    """Demonstrate execution listing."""
    console.print("\n[bold blue]📜 Listing Recent Executions...[/bold blue]")
    
    try:
        executions = await client.list_executions(workflow_id)
        
        if executions:
            table = Table(title="Recent Executions")
            table.add_column("Execution ID", style="cyan", no_wrap=True)
            table.add_column("Workflow ID", style="magenta", no_wrap=True)
            table.add_column("Status", style="green")
            table.add_column("Started", style="blue")
            table.add_column("Duration", style="yellow")
            
            for execution in executions[:10]:  # Show only first 10
                status_emoji = {
                    "success": "✅",
                    "error": "❌",
                    "running": "🔄",
                    "canceled": "⏹️"
                }.get(execution.get("status", "unknown"), "❓")
                
                started = execution.get('started_at', 'N/A')
                if started != 'N/A':
                    try:
                        started = datetime.fromisoformat(started.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                
                duration = execution.get('duration')
                duration_str = f"{duration:.2f}s" if duration else "N/A"
                
                table.add_row(
                    execution.get('execution_id', 'N/A')[:8] + "...",
                    execution.get('workflow_id', 'N/A')[:8] + "...",
                    f"{status_emoji} {execution.get('status', 'Unknown')}",
                    started,
                    duration_str
                )
            
            console.print(table)
            console.print(f"\n[green]Found {len(executions)} executions[/green]")
        else:
            console.print("[yellow]No executions found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]❌ Failed to list executions: {e}[/red]")


async def main():
    """Main demonstration function."""
    console.print(Panel.fit(
        "[bold blue]n8n API Integration Demo[/bold blue]\n"
        "This demo shows how to integrate with n8n workflows through the UnityAI API.",
        title="🚀 UnityAI n8n Integration"
    ))
    
    # Initialize client
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    client = N8nApiClient(api_base_url)
    
    # Run demonstrations
    await demo_health_check(client)
    
    workflows = await demo_list_workflows(client)
    
    if workflows:
        # Use the first active workflow for demonstration
        active_workflows = [w for w in workflows if w.get('active', False)]
        
        if active_workflows:
            demo_workflow = active_workflows[0]
            workflow_id = demo_workflow['id']
            
            console.print(f"\n[bold green]Using workflow '{demo_workflow['name']}' for demonstration[/bold green]")
            
            # Execute the workflow
            execution = await demo_execute_workflow(client, workflow_id)
            
            # Show workflow statistics
            await demo_workflow_stats(client, workflow_id)
            
            # List recent executions
            await demo_list_executions(client, workflow_id)
            
        else:
            console.print("\n[yellow]No active workflows found for demonstration[/yellow]")
            await demo_list_executions(client)
    
    console.print("\n[bold green]✅ Demo completed![/bold green]")
    console.print("\n[dim]To use this integration in your own code:")
    console.print("1. Set up your n8n API credentials in .env")
    console.print("2. Start the FastAPI server")
    console.print("3. Use the N8nApiClient class to interact with workflows[/dim]")


if __name__ == "__main__":
    # Install required packages if not available
    try:
        import rich
    except ImportError:
        console.print("[red]Please install required packages: pip install rich httpx[/red]")
        exit(1)
    
    asyncio.run(main())