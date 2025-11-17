"""FastMCP HTTP Server for TickTick Integration"""

import os
import json
import traceback
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from fastmcp import FastMCP
from ticktick_client import TickTickClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP
mcp = FastMCP("TickTick MCP Remote")

# Get configuration from environment
TICKTICK_ACCESS_TOKEN = os.getenv("TICKTICK_ACCESS_TOKEN")
MCP_API_KEY = os.getenv("MCP_API_KEY")

if not TICKTICK_ACCESS_TOKEN:
    raise ValueError("TICKTICK_ACCESS_TOKEN environment variable is required")

if not MCP_API_KEY:
    logger.warning("MCP_API_KEY not set - server will run without authentication")

# Initialize TickTick client (will be created per request or cached)
ticktick_client: Optional[TickTickClient] = None


def format_json_response(data: Dict[str, Any]) -> str:
    """
    Format response data as JSON string.
    
    Args:
        data: Dictionary to serialize
    
    Returns:
        JSON string
    """
    try:
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error formatting JSON response: {e}")
        logger.error(traceback.format_exc())
        return json.dumps({"error": str(e), "message": "Failed to format response"})


async def get_client() -> TickTickClient:
    """Get or create TickTick client instance."""
    global ticktick_client
    if ticktick_client is None:
        ticktick_client = TickTickClient()
    return ticktick_client


# Format a task object from TickTick for better display
def format_task(task: Dict) -> str:
    """Format a task into a human-readable string."""
    formatted = f"ID: {task.get('id', 'No ID')}\n"
    formatted += f"Title: {task.get('title', 'No title')}\n"
    
    # Add project ID
    formatted += f"Project ID: {task.get('projectId', 'None')}\n"
    
    # Add dates if available
    if task.get('startDate'):
        formatted += f"Start Date: {task.get('startDate')}\n"
    if task.get('dueDate'):
        formatted += f"Due Date: {task.get('dueDate')}\n"
    
    # Add priority if available
    priority_map = {0: "None", 1: "Low", 3: "Medium", 5: "High"}
    priority = task.get('priority', 0)
    formatted += f"Priority: {priority_map.get(priority, str(priority))}\n"
    
    # Add status if available
    status = "Completed" if task.get('status') == 2 else "Active"
    formatted += f"Status: {status}\n"
    
    # Add content if available
    if task.get('content'):
        formatted += f"\nContent:\n{task.get('content')}\n"
    
    # Add subtasks if available
    items = task.get('items', [])
    if items:
        formatted += f"\nSubtasks ({len(items)}):\n"
        for i, item in enumerate(items, 1):
            status = "✓" if item.get('status') == 1 else "□"
            formatted += f"{i}. [{status}] {item.get('title', 'No title')}\n"
    
    return formatted


# Format a project object from TickTick for better display
def format_project(project: Dict) -> str:
    """Format a project into a human-readable string."""
    formatted = f"Name: {project.get('name', 'No name')}\n"
    formatted += f"ID: {project.get('id', 'No ID')}\n"
    
    # Add color if available
    if project.get('color'):
        formatted += f"Color: {project.get('color')}\n"
    
    # Add view mode if available
    if project.get('viewMode'):
        formatted += f"View Mode: {project.get('viewMode')}\n"
    
    # Add closed status if available
    if 'closed' in project:
        formatted += f"Closed: {'Yes' if project.get('closed') else 'No'}\n"
    
    # Add kind if available
    if project.get('kind'):
        formatted += f"Kind: {project.get('kind')}\n"
    
    return formatted


# Helper Functions
PRIORITY_MAP = {0: "None", 1: "Low", 3: "Medium", 5: "High"}


def _is_task_due_today(task: Dict[str, Any]) -> bool:
    """Check if a task is due today."""
    due_date = task.get('dueDate')
    if not due_date:
        return False
    
    try:
        task_due_date = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%S.%f%z").date()
        today_date = datetime.now(timezone.utc).date()
        return task_due_date == today_date
    except (ValueError, TypeError):
        return False


def _is_task_overdue(task: Dict[str, Any]) -> bool:
    """Check if a task is overdue."""
    due_date = task.get('dueDate')
    if not due_date:
        return False
    
    try:
        task_due = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%S.%f%z")
        return task_due < datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return False


def _is_task_due_in_days(task: Dict[str, Any], days: int) -> bool:
    """Check if a task is due in exactly X days."""
    due_date = task.get('dueDate')
    if not due_date:
        return False
    
    try:
        task_due_date = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%S.%f%z").date()
        target_date = (datetime.now(timezone.utc) + timedelta(days=days)).date()
        return task_due_date == target_date
    except (ValueError, TypeError):
        return False


def _task_matches_search(task: Dict[str, Any], search_term: str) -> bool:
    """Check if a task matches the search term (case-insensitive)."""
    search_term = search_term.lower()
    
    # Search in title
    title = task.get('title', '').lower()
    if search_term in title:
        return True
    
    # Search in content
    content = task.get('content', '').lower()
    if search_term in content:
        return True
    
    # Search in subtasks
    items = task.get('items', [])
    for item in items:
        item_title = item.get('title', '').lower()
        if search_term in item_title:
            return True
    
    return False


def _validate_task_data(task_data: Dict[str, Any], task_index: int) -> Optional[str]:
    """
    Validate a single task's data for batch creation.
    
    Returns:
        None if valid, error message string if invalid
    """
    # Check required fields
    if 'title' not in task_data or not task_data['title']:
        return f"Task {task_index + 1}: 'title' is required and cannot be empty"
    
    if 'project_id' not in task_data or not task_data['project_id']:
        return f"Task {task_index + 1}: 'project_id' is required and cannot be empty"
    
    # Validate priority if provided
    priority = task_data.get('priority')
    if priority is not None and priority not in [0, 1, 3, 5]:
        return f"Task {task_index + 1}: Invalid priority {priority}. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)"
    
    # Validate dates if provided
    for date_field in ['start_date', 'due_date']:
        date_str = task_data.get(date_field)
        if date_str:
            try:
                # Try to parse the date to validate it
                if date_str.endswith('Z'):
                    datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                elif '+' in date_str or date_str.endswith(('00', '30')):
                    datetime.fromisoformat(date_str)
                else:
                    datetime.fromisoformat(date_str)
            except ValueError:
                return f"Task {task_index + 1}: Invalid {date_field} format '{date_str}'. Use ISO format: YYYY-MM-DDTHH:mm:ss or with timezone"
    
    return None


async def _get_project_tasks_by_filter(ticktick: TickTickClient, projects: List[Dict], filter_func, filter_name: str) -> str:
    """
    Helper function to filter tasks across all projects.
    
    Args:
        ticktick: TickTick client instance
        projects: List of project dictionaries
        filter_func: Function that takes a task and returns True if it matches the filter
        filter_name: Name of the filter for output formatting
    
    Returns:
        Formatted string of filtered tasks
    """
    if not projects:
        return "No projects found."
    
    result = f"Found {len(projects)} projects:\n\n"
    
    for i, project in enumerate(projects, 1):
        if project.get('closed'):
            continue
            
        project_id = project.get('id', 'No ID')
        project_data = await ticktick.get_project_with_data(project_id)
        if isinstance(project_data, dict) and 'error' in project_data:
            continue
            
        tasks = project_data.get('tasks', []) if isinstance(project_data, dict) else []
        
        if not tasks:
            result += f"Project {i}:\n{format_project(project)}"
            result += f"With 0 tasks that are to be '{filter_name}' in this project :\n\n\n"
            continue
        
        # Filter tasks using the provided function
        filtered_tasks = [(t, task) for t, task in enumerate(tasks, 1) if filter_func(task)]
        
        result += f"Project {i}:\n{format_project(project)}"
        result += f"With {len(filtered_tasks)} tasks that are to be '{filter_name}' in this project :\n"
        
        for t, task in filtered_tasks:
            result += f"Task {t}:\n{format_task(task)}\n"
        
        result += "\n\n"
    
    return result


# ==================== MCP TOOLS ====================

@mcp.tool()
async def get_projects() -> str:
    """Get all projects from TickTick."""
    try:
        ticktick = await get_client()
        projects = await ticktick.get_projects()
        
        if isinstance(projects, dict) and 'error' in projects:
            return format_json_response({"error": projects['error']})
        
        if not projects:
            return format_json_response({"message": "No projects found.", "results": []})
        
        result = f"Found {len(projects)} projects:\n\n"
        for i, project in enumerate(projects, 1):
            result += f"Project {i}:\n{format_project(project)}\n"
        
        return format_json_response({"count": len(projects), "results": projects, "formatted": result})
    except Exception as e:
        logger.error(f"Error in get_projects: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to retrieve projects"})


@mcp.tool()
async def get_project(project_id: str) -> str:
    """
    Get details about a specific project.
    
    Args:
        project_id: ID of the project
    """
    try:
        ticktick = await get_client()
        project = await ticktick.get_project(project_id)
        
        if isinstance(project, dict) and 'error' in project:
            return format_json_response({"error": project['error']})
        
        return format_json_response({"result": project, "formatted": format_project(project)})
    except Exception as e:
        logger.error(f"Error in get_project: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to retrieve project"})


@mcp.tool()
async def get_project_tasks(project_id: str) -> str:
    """
    Get all tasks in a specific project.
    
    Args:
        project_id: ID of the project
    """
    try:
        ticktick = await get_client()
        project_data = await ticktick.get_project_with_data(project_id)
        
        if isinstance(project_data, dict) and 'error' in project_data:
            return format_json_response({"error": project_data['error']})
        
        tasks = project_data.get('tasks', []) if isinstance(project_data, dict) else []
        project_name = project_data.get('project', {}).get('name', project_id) if isinstance(project_data, dict) else project_id
        
        if not tasks:
            return format_json_response({
                "message": f"No tasks found in project '{project_name}'.",
                "project_id": project_id,
                "results": []
            })
        
        result = f"Found {len(tasks)} tasks in project '{project_name}':\n\n"
        for i, task in enumerate(tasks, 1):
            result += f"Task {i}:\n{format_task(task)}\n"
        
        return format_json_response({"count": len(tasks), "results": tasks, "formatted": result})
    except Exception as e:
        logger.error(f"Error in get_project_tasks: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to retrieve project tasks"})


@mcp.tool()
async def get_task(project_id: str, task_id: str) -> str:
    """
    Get details about a specific task.
    
    Args:
        project_id: ID of the project
        task_id: ID of the task
    """
    try:
        ticktick = await get_client()
        task = await ticktick.get_task(project_id, task_id)
        
        if isinstance(task, dict) and 'error' in task:
            return format_json_response({"error": task['error']})
        
        return format_json_response({"result": task, "formatted": format_task(task)})
    except Exception as e:
        logger.error(f"Error in get_task: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to retrieve task"})


@mcp.tool()
async def create_task(
    title: str,
    project_id: str,
    content: Optional[str] = None,
    start_date: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: int = 0
) -> str:
    """
    Create a new task in TickTick.
    
    Args:
        title: Task title
        project_id: ID of the project to add the task to
        content: Task description/content (optional)
        start_date: Start date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
        due_date: Due date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
        priority: Priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
    """
    # Validate priority
    if priority not in [0, 1, 3, 5]:
        return format_json_response({"error": "Invalid priority. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)."})
    
    try:
        # Validate dates if provided
        for date_str, date_name in [(start_date, "start_date"), (due_date, "due_date")]:
            if date_str:
                try:
                    datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    return format_json_response({"error": f"Invalid {date_name} format. Use ISO format: YYYY-MM-DDThh:mm:ss+0000"})
        
        ticktick = await get_client()
        task = await ticktick.create_task(
            title=title,
            project_id=project_id,
            content=content,
            start_date=start_date,
            due_date=due_date,
            priority=priority
        )
        
        if isinstance(task, dict) and 'error' in task:
            return format_json_response({"error": task['error']})
        
        return format_json_response({
            "success": True,
            "message": "Task created successfully",
            "result": task,
            "formatted": format_task(task)
        })
    except Exception as e:
        logger.error(f"Error in create_task: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to create task"})


@mcp.tool()
async def update_task(
    task_id: str,
    project_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    start_date: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[int] = None
) -> str:
    """
    Update an existing task in TickTick.
    
    Args:
        task_id: ID of the task to update
        project_id: ID of the project the task belongs to
        title: New task title (optional)
        content: New task description/content (optional)
        start_date: New start date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
        due_date: New due date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
        priority: New priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
    """
    # Validate priority if provided
    if priority is not None and priority not in [0, 1, 3, 5]:
        return format_json_response({"error": "Invalid priority. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)."})
    
    try:
        # Validate dates if provided
        for date_str, date_name in [(start_date, "start_date"), (due_date, "due_date")]:
            if date_str:
                try:
                    datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    return format_json_response({"error": f"Invalid {date_name} format. Use ISO format: YYYY-MM-DDThh:mm:ss+0000"})
        
        ticktick = await get_client()
        task = await ticktick.update_task(
            task_id=task_id,
            project_id=project_id,
            title=title,
            content=content,
            start_date=start_date,
            due_date=due_date,
            priority=priority
        )
        
        if isinstance(task, dict) and 'error' in task:
            return format_json_response({"error": task['error']})
        
        return format_json_response({
            "success": True,
            "message": "Task updated successfully",
            "result": task,
            "formatted": format_task(task)
        })
    except Exception as e:
        logger.error(f"Error in update_task: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to update task"})


@mcp.tool()
async def complete_task(project_id: str, task_id: str) -> str:
    """
    Mark a task as complete.
    
    Args:
        project_id: ID of the project
        task_id: ID of the task
    """
    try:
        ticktick = await get_client()
        result = await ticktick.complete_task(project_id, task_id)
        
        if isinstance(result, dict) and 'error' in result:
            return format_json_response({"error": result['error']})
        
        return format_json_response({"success": True, "message": f"Task {task_id} marked as complete."})
    except Exception as e:
        logger.error(f"Error in complete_task: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to complete task"})


@mcp.tool()
async def delete_task(project_id: str, task_id: str) -> str:
    """
    Delete a task.
    
    Args:
        project_id: ID of the project
        task_id: ID of the task
    """
    try:
        ticktick = await get_client()
        result = await ticktick.delete_task(project_id, task_id)
        
        if isinstance(result, dict) and 'error' in result:
            return format_json_response({"error": result['error']})
        
        return format_json_response({"success": True, "message": f"Task {task_id} deleted successfully."})
    except Exception as e:
        logger.error(f"Error in delete_task: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to delete task"})


@mcp.tool()
async def create_project(
    name: str,
    color: str = "#F18181",
    view_mode: str = "list"
) -> str:
    """
    Create a new project in TickTick.
    
    Args:
        name: Project name
        color: Color code (hex format) (optional)
        view_mode: View mode - one of list, kanban, or timeline (optional)
    """
    # Validate view_mode
    if view_mode not in ["list", "kanban", "timeline"]:
        return format_json_response({"error": "Invalid view_mode. Must be one of: list, kanban, timeline."})
    
    try:
        ticktick = await get_client()
        project = await ticktick.create_project(
            name=name,
            color=color,
            view_mode=view_mode
        )
        
        if isinstance(project, dict) and 'error' in project:
            return format_json_response({"error": project['error']})
        
        return format_json_response({
            "success": True,
            "message": "Project created successfully",
            "result": project,
            "formatted": format_project(project)
        })
    except Exception as e:
        logger.error(f"Error in create_project: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to create project"})


@mcp.tool()
async def delete_project(project_id: str) -> str:
    """
    Delete a project.
    
    Args:
        project_id: ID of the project
    """
    try:
        ticktick = await get_client()
        result = await ticktick.delete_project(project_id)
        
        if isinstance(result, dict) and 'error' in result:
            return format_json_response({"error": result['error']})
        
        return format_json_response({"success": True, "message": f"Project {project_id} deleted successfully."})
    except Exception as e:
        logger.error(f"Error in delete_project: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to delete project"})


@mcp.tool()
async def get_all_tasks() -> str:
    """Get all tasks from TickTick. Ignores closed projects."""
    try:
        ticktick = await get_client()
        projects = await ticktick.get_projects()
        
        if isinstance(projects, dict) and 'error' in projects:
            return format_json_response({"error": projects['error']})
        
        def all_tasks_filter(task: Dict[str, Any]) -> bool:
            return True  # Include all tasks
        
        result = await _get_project_tasks_by_filter(ticktick, projects, all_tasks_filter, "included")
        return format_json_response({"formatted": result})
    except Exception as e:
        logger.error(f"Error in get_all_tasks: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to retrieve tasks"})


@mcp.tool()
async def get_tasks_by_priority(priority_id: int) -> str:
    """
    Get all tasks from TickTick by priority. Ignores closed projects.

    Args:
        priority_id: Priority of tasks to retrieve {0: "None", 1: "Low", 3: "Medium", 5: "High"}
    """
    if priority_id not in PRIORITY_MAP:
        return format_json_response({"error": f"Invalid priority_id. Valid values: {list(PRIORITY_MAP.keys())}"})
    
    try:
        ticktick = await get_client()
        projects = await ticktick.get_projects()
        
        if isinstance(projects, dict) and 'error' in projects:
            return format_json_response({"error": projects['error']})
        
        def priority_filter(task: Dict[str, Any]) -> bool:
            return task.get('priority', 0) == priority_id
        
        priority_name = f"{PRIORITY_MAP[priority_id]} ({priority_id})"
        result = await _get_project_tasks_by_filter(ticktick, projects, priority_filter, f"priority '{priority_name}'")
        return format_json_response({"formatted": result})
    except Exception as e:
        logger.error(f"Error in get_tasks_by_priority: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to retrieve tasks"})


@mcp.tool()
async def get_tasks_due_today() -> str:
    """Get all tasks from TickTick that are due today. Ignores closed projects."""
    try:
        ticktick = await get_client()
        projects = await ticktick.get_projects()
        
        if isinstance(projects, dict) and 'error' in projects:
            return format_json_response({"error": projects['error']})
        
        def today_filter(task: Dict[str, Any]) -> bool:
            return _is_task_due_today(task)
        
        result = await _get_project_tasks_by_filter(ticktick, projects, today_filter, "due today")
        return format_json_response({"formatted": result})
    except Exception as e:
        logger.error(f"Error in get_tasks_due_today: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to retrieve tasks"})


@mcp.tool()
async def get_overdue_tasks() -> str:
    """Get all overdue tasks from TickTick. Ignores closed projects."""
    try:
        ticktick = await get_client()
        projects = await ticktick.get_projects()
        
        if isinstance(projects, dict) and 'error' in projects:
            return format_json_response({"error": projects['error']})
        
        def overdue_filter(task: Dict[str, Any]) -> bool:
            return _is_task_overdue(task)
        
        result = await _get_project_tasks_by_filter(ticktick, projects, overdue_filter, "overdue")
        return format_json_response({"formatted": result})
    except Exception as e:
        logger.error(f"Error in get_overdue_tasks: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to retrieve tasks"})


@mcp.tool()
async def get_tasks_due_tomorrow() -> str:
    """Get all tasks from TickTick that are due tomorrow. Ignores closed projects."""
    try:
        ticktick = await get_client()
        projects = await ticktick.get_projects()
        
        if isinstance(projects, dict) and 'error' in projects:
            return format_json_response({"error": projects['error']})
        
        def tomorrow_filter(task: Dict[str, Any]) -> bool:
            return _is_task_due_in_days(task, 1)
        
        result = await _get_project_tasks_by_filter(ticktick, projects, tomorrow_filter, "due tomorrow")
        return format_json_response({"formatted": result})
    except Exception as e:
        logger.error(f"Error in get_tasks_due_tomorrow: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to retrieve tasks"})


@mcp.tool()
async def get_tasks_due_in_days(days: int) -> str:
    """
    Get all tasks from TickTick that are due in exactly X days. Ignores closed projects.
    
    Args:
        days: Number of days from today (0 = today, 1 = tomorrow, etc.)
    """
    if days < 0:
        return format_json_response({"error": "Days must be a non-negative integer."})
    
    try:
        ticktick = await get_client()
        projects = await ticktick.get_projects()
        
        if isinstance(projects, dict) and 'error' in projects:
            return format_json_response({"error": projects['error']})
        
        def days_filter(task: Dict[str, Any]) -> bool:
            return _is_task_due_in_days(task, days)
        
        day_description = "today" if days == 0 else f"in {days} day{'s' if days != 1 else ''}"
        result = await _get_project_tasks_by_filter(ticktick, projects, days_filter, f"due {day_description}")
        return format_json_response({"formatted": result})
    except Exception as e:
        logger.error(f"Error in get_tasks_due_in_days: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to retrieve tasks"})


@mcp.tool()
async def get_tasks_due_this_week() -> str:
    """Get all tasks from TickTick that are due within the next 7 days. Ignores closed projects."""
    try:
        ticktick = await get_client()
        projects = await ticktick.get_projects()
        
        if isinstance(projects, dict) and 'error' in projects:
            return format_json_response({"error": projects['error']})
        
        def week_filter(task: Dict[str, Any]) -> bool:
            due_date = task.get('dueDate')
            if not due_date:
                return False
            
            try:
                task_due_date = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%S.%f%z").date()
                today = datetime.now(timezone.utc).date()
                week_from_today = today + timedelta(days=7)
                return today <= task_due_date <= week_from_today
            except (ValueError, TypeError):
                return False
        
        result = await _get_project_tasks_by_filter(ticktick, projects, week_filter, "due this week")
        return format_json_response({"formatted": result})
    except Exception as e:
        logger.error(f"Error in get_tasks_due_this_week: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to retrieve tasks"})


@mcp.tool()
async def search_tasks(search_term: str) -> str:
    """
    Search for tasks in TickTick by title, content, or subtask titles. Ignores closed projects.
    
    Args:
        search_term: Text to search for (case-insensitive)
    """
    if not search_term.strip():
        return format_json_response({"error": "Search term cannot be empty."})
    
    try:
        ticktick = await get_client()
        projects = await ticktick.get_projects()
        
        if isinstance(projects, dict) and 'error' in projects:
            return format_json_response({"error": projects['error']})
        
        def search_filter(task: Dict[str, Any]) -> bool:
            return _task_matches_search(task, search_term)
        
        result = await _get_project_tasks_by_filter(ticktick, projects, search_filter, f"matching '{search_term}'")
        return format_json_response({"formatted": result})
    except Exception as e:
        logger.error(f"Error in search_tasks: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to search tasks"})


@mcp.tool()
async def batch_create_tasks(tasks: List[Dict[str, Any]]) -> str:
    """
    Create multiple tasks in TickTick at once
    
    Args:
        tasks: List of task dictionaries. Each task must contain:
            - title (required): Task Name
            - project_id (required): ID of the project for the task
            - content (optional): Task description
            - start_date (optional): Start date in user timezone (YYYY-MM-DDTHH:mm:ss or with timezone)
            - due_date (optional): Due date in user timezone (YYYY-MM-DDTHH:mm:ss or with timezone)  
            - priority (optional): Priority level {0: "None", 1: "Low", 3: "Medium", 5: "High"}
    
    Example:
        tasks = [
            {"title": "Example A", "project_id": "1234ABC", "priority": 5},
            {"title": "Example B", "project_id": "1234XYZ", "content": "Description", "start_date": "2025-07-18T10:00:00", "due_date": "2025-07-19T10:00:00"}
        ]
    """
    if not tasks:
        return format_json_response({"error": "No tasks provided. Please provide a list of tasks to create."})
    
    if not isinstance(tasks, list):
        return format_json_response({"error": "Tasks must be provided as a list of dictionaries."})
    
    # Validate all tasks before creating any
    validation_errors = []
    for i, task_data in enumerate(tasks):
        if not isinstance(task_data, dict):
            validation_errors.append(f"Task {i + 1}: Must be a dictionary")
            continue
        
        error = _validate_task_data(task_data, i)
        if error:
            validation_errors.append(error)
    
    if validation_errors:
        return format_json_response({"error": "Validation errors found", "errors": validation_errors})
    
    # Create tasks one by one and collect results
    created_tasks = []
    failed_tasks = []
    
    try:
        ticktick = await get_client()
        for i, task_data in enumerate(tasks):
            try:
                # Extract task parameters with defaults
                title = task_data['title']
                project_id = task_data['project_id']
                content = task_data.get('content')
                start_date = task_data.get('start_date')
                due_date = task_data.get('due_date')
                priority = task_data.get('priority', 0)
                
                # Create the task
                result = await ticktick.create_task(
                    title=title,
                    project_id=project_id,
                    content=content,
                    start_date=start_date,
                    due_date=due_date,
                    priority=priority
                )
                
                if isinstance(result, dict) and 'error' in result:
                    failed_tasks.append(f"Task {i + 1} ('{title}'): {result['error']}")
                else:
                    created_tasks.append((i + 1, title, result))
                    
            except Exception as e:
                failed_tasks.append(f"Task {i + 1} ('{task_data.get('title', 'Unknown')}'): {str(e)}")
        
        # Format the results
        result_message = f"Batch task creation completed.\n\n"
        result_message += f"Successfully created: {len(created_tasks)} tasks\n"
        result_message += f"Failed: {len(failed_tasks)} tasks\n\n"
        
        if created_tasks:
            result_message += "Successfully Created Tasks:\n"
            for task_num, title, task_obj in created_tasks:
                result_message += f"{task_num}. {title} (ID: {task_obj.get('id', 'Unknown') if isinstance(task_obj, dict) else 'Unknown'})\n"
            result_message += "\n"
        
        if failed_tasks:
            result_message += "Failed Tasks:\n"
            for error in failed_tasks:
                result_message += f"{error}\n"
        
        return format_json_response({
            "success": len(failed_tasks) == 0,
            "created_count": len(created_tasks),
            "failed_count": len(failed_tasks),
            "formatted": result_message,
            "created": created_tasks,
            "failed": failed_tasks
        })
        
    except Exception as e:
        logger.error(f"Error in batch_create_tasks: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed during batch task creation"})


@mcp.tool()
async def get_engaged_tasks() -> str:
    """
    Get all tasks from TickTick that are "Engaged".
    This includes tasks marked as high priority (5), due today or overdue.
    """
    try:
        ticktick = await get_client()
        projects = await ticktick.get_projects()
        
        if isinstance(projects, dict) and 'error' in projects:
            return format_json_response({"error": projects['error']})
        
        def engaged_filter(task: Dict[str, Any]) -> bool:
            is_high_priority = task.get('priority', 0) == 5
            is_overdue = _is_task_overdue(task)
            is_today = _is_task_due_today(task)
            return is_high_priority or is_overdue or is_today
        
        result = await _get_project_tasks_by_filter(ticktick, projects, engaged_filter, "engaged")
        return format_json_response({"formatted": result})
    except Exception as e:
        logger.error(f"Error in get_engaged_tasks: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to retrieve tasks"})


@mcp.tool()
async def get_next_tasks() -> str:
    """
    Get all tasks from TickTick that are "Next".
    This includes tasks marked as medium priority (3) or due tomorrow.
    """
    try:
        ticktick = await get_client()
        projects = await ticktick.get_projects()
        
        if isinstance(projects, dict) and 'error' in projects:
            return format_json_response({"error": projects['error']})
        
        def next_filter(task: Dict[str, Any]) -> bool:
            is_medium_priority = task.get('priority', 0) == 3
            is_due_tomorrow = _is_task_due_in_days(task, 1)
            return is_medium_priority or is_due_tomorrow
        
        result = await _get_project_tasks_by_filter(ticktick, projects, next_filter, "next")
        return format_json_response({"formatted": result})
    except Exception as e:
        logger.error(f"Error in get_next_tasks: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to retrieve tasks"})


@mcp.tool()
async def create_subtask(
    subtask_title: str,
    parent_task_id: str,
    project_id: str,
    content: Optional[str] = None,
    priority: int = 0
) -> str:
    """
    Create a subtask for a parent task within the same project.
    
    Args:
        subtask_title: Title of the subtask
        parent_task_id: ID of the parent task
        project_id: ID of the project (must be same for both parent and subtask)
        content: Optional content/description for the subtask
        priority: Priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
    """
    # Validate priority
    if priority not in [0, 1, 3, 5]:
        return format_json_response({"error": "Invalid priority. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)."})
    
    try:
        ticktick = await get_client()
        subtask = await ticktick.create_subtask(
            subtask_title=subtask_title,
            parent_task_id=parent_task_id,
            project_id=project_id,
            content=content,
            priority=priority
        )
        
        if isinstance(subtask, dict) and 'error' in subtask:
            return format_json_response({"error": subtask['error']})
        
        return format_json_response({
            "success": True,
            "message": "Subtask created successfully",
            "result": subtask,
            "formatted": format_task(subtask)
        })
    except Exception as e:
        logger.error(f"Error in create_subtask: {e}")
        logger.error(traceback.format_exc())
        return format_json_response({"error": str(e), "message": "Failed to create subtask"})


# ==================== Server Entry Point ====================

def create_app():
    """Create the ASGI app with authentication wrapper"""
    from starlette.applications import Starlette
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
    from starlette.responses import JSONResponse
    from starlette.routing import Route, Mount

    async def health_check(request):
        return JSONResponse({
            "status": "healthy",
            "service": "ticktick-mcp-remote",
            "version": "1.0.0",
            "authentication": "enabled" if MCP_API_KEY else "disabled"
        })

    async def root_endpoint(request):
        """Root endpoint for Claude AI discovery"""
        return JSONResponse({
            "service": "ticktick-mcp-remote",
            "version": "1.0.0",
            "mcp_endpoint": "/mcp",
            "health": "/health"
        })

    async def oauth_protected_resource(request):
        """OAuth protected resource discovery endpoint"""
        return JSONResponse({
            "resource": "ticktick-mcp-remote",
            "scopes_supported": []
        })

    async def oauth_authorization_server(request):
        """OAuth authorization server discovery endpoint"""
        return JSONResponse({
            "issuer": "https://remote-ticktick-mcp.onrender.com",
            "authorization_endpoint": None,
            "token_endpoint": None,
            "scopes_supported": []
        })

    async def register_endpoint(request):
        """Registration endpoint for Claude AI"""
        return JSONResponse({
            "status": "ok",
            "message": "TickTick MCP server is ready",
            "mcp_endpoint": "/mcp"
        })

    async def auth_middleware(request, call_next):
        # Skip auth for health check, root path, and OAuth discovery endpoints
        # Claude AI may probe these paths during connection
        skip_paths = [
            "/health",
            "/",
            "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-authorization-server",
            "/register"
        ]
        
        if request.url.path in skip_paths:
            return await call_next(request)

        # Check API key if configured
        if MCP_API_KEY:
            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                logger.warning(f"Unauthenticated request to {request.url.path} - missing Authorization header")
                return JSONResponse(
                    {"error": "Missing or invalid Authorization header"},
                    status_code=401
                )

            token = auth_header.replace("Bearer ", "")
            if token != MCP_API_KEY:
                logger.warning(f"Unauthenticated request to {request.url.path} - invalid API key")
                return JSONResponse(
                    {"error": "Invalid API key"},
                    status_code=401
                )

        return await call_next(request)

    # Get the FastMCP ASGI app
    mcp_app = mcp.http_app()

    # Create wrapper app with auth and CORS
    # IMPORTANT: FastMCP's http_app() expects to handle requests at its root
    # So we mount it at / and it will handle /mcp endpoint internally
    # We add specific routes BEFORE mounting FastMCP so they take precedence
    app = Starlette(
        routes=[
            Route("/health", health_check, methods=["GET", "HEAD"]),
            Route("/", root_endpoint, methods=["GET", "HEAD"]),
            Route("/.well-known/oauth-protected-resource", oauth_protected_resource, methods=["GET", "HEAD"]),
            Route("/.well-known/oauth-authorization-server", oauth_authorization_server, methods=["GET", "HEAD"]),
            Route("/register", register_endpoint, methods=["GET", "POST", "HEAD"]),
            Mount("/", mcp_app)  # FastMCP handles /mcp internally - must be last
        ],
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=["https://claude.ai", "https://claude.com", "https://*.anthropic.com"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ],
        lifespan=mcp_app.lifespan
    )

    # Add auth middleware
    @app.middleware("http")
    async def add_auth(request, call_next):
        return await auth_middleware(request, call_next)

    return app


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting Remote TickTick MCP server on {host}:{port}")
    logger.info(f"Authentication: {'Enabled' if MCP_API_KEY else 'Disabled (WARNING: Not secure for production)'}")
    
    # Create the app first
    app = create_app()
    
    # Log registered tools for debugging (after app creation)
    try:
        if hasattr(mcp, '_tools'):
            tool_names = [name for name in mcp._tools.keys()]
            logger.info(f"Registered {len(tool_names)} tools: {', '.join(sorted(tool_names))}")
        elif hasattr(mcp, 'tools'):
            tool_names = [name for name in mcp.tools.keys()]
            logger.info(f"Registered {len(tool_names)} tools: {', '.join(sorted(tool_names))}")
        else:
            logger.info("Tool registration verified")
    except Exception as e:
        logger.warning(f"Could not list registered tools: {e}")

    # Run with optimized settings for production
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

