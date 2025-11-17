"""Async TickTick API Client using httpx"""

import os
import json
import base64
import httpx
import asyncio
import logging
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

# Configuration from environment variables
RATE_LIMIT_DELAY = float(os.getenv("TICKTICK_RATE_LIMIT_DELAY", "0.2"))  # Default 0.2 seconds


class TickTickClient:
    """
    Async client for the TickTick API using OAuth2 authentication.
    """

    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv("TICKTICK_CLIENT_ID")
        self.client_secret = os.getenv("TICKTICK_CLIENT_SECRET")
        self.access_token = os.getenv("TICKTICK_ACCESS_TOKEN")
        self.refresh_token = os.getenv("TICKTICK_REFRESH_TOKEN")

        if not self.access_token:
            raise ValueError(
                "TICKTICK_ACCESS_TOKEN environment variable is not set. "
                "Please set up your TickTick credentials in environment variables."
            )

        self.base_url = os.getenv("TICKTICK_BASE_URL") or "https://api.ticktick.com/open/v1"
        self.token_url = os.getenv("TICKTICK_TOKEN_URL") or "https://ticktick.com/oauth/token"
        self.rate_limit_delay = RATE_LIMIT_DELAY

        # Create httpx client with timeout
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "User-Agent": "curl/8.7.1"
            }
        )

    async def _refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token.

        Returns:
            True if successful, False otherwise
        """
        if not self.refresh_token:
            logger.warning("No refresh token available. Cannot refresh access token.")
            return False

        if not self.client_id or not self.client_secret:
            logger.warning("Client ID or Client Secret missing. Cannot refresh access token.")
            return False

        # Prepare the token request
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }

        # Prepare Basic Auth credentials
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_str.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            # Send the token request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.token_url, data=token_data, headers=headers)
                response.raise_for_status()

                # Parse the response
                tokens = response.json()

                # Update the tokens
                self.access_token = tokens.get('access_token')
                if 'refresh_token' in tokens:
                    self.refresh_token = tokens.get('refresh_token')

                # Update the client headers
                self.client.headers["Authorization"] = f"Bearer {self.access_token}"

                logger.info("Access token refreshed successfully.")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Error refreshing access token: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            return False

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        max_retries: int = 3
    ) -> Dict:
        """
        Makes an async request to the TickTick API with automatic token refresh.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request data (for POST)
            max_retries: Maximum number of retries for rate limiting

        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}{endpoint}"

        retry_count = 0
        while retry_count <= max_retries:
            try:
                # Make the request
                if method == "GET":
                    response = await self.client.get(url)
                elif method == "POST":
                    response = await self.client.post(url, json=data)
                elif method == "DELETE":
                    response = await self.client.delete(url)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Check if the request was unauthorized (401)
                if response.status_code == 401:
                    logger.info("Access token expired. Attempting to refresh...")

                    # Try to refresh the access token
                    if await self._refresh_access_token():
                        # Retry the request with the new token
                        if method == "GET":
                            response = await self.client.get(url)
                        elif method == "POST":
                            response = await self.client.post(url, json=data)
                        elif method == "DELETE":
                            response = await self.client.delete(url)
                    else:
                        return {"error": "Failed to refresh access token. Please update your credentials."}

                # Handle rate limiting (429)
                if response.status_code == 429:
                    if retry_count < max_retries:
                        wait_time = (2 ** retry_count) * self.rate_limit_delay
                        logger.warning(f"Rate limit hit (429). Retrying in {wait_time:.2f}s (attempt {retry_count + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        retry_count += 1
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} retries")
                        return {"error": "Rate limit exceeded. Please try again later."}

                # Raise an exception for other 4xx/5xx status codes
                response.raise_for_status()

                # Return empty dict for 204 No Content
                if response.status_code == 204 or response.text == "":
                    return {}

                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Already handled above, but catch it here too
                    if retry_count < max_retries:
                        wait_time = (2 ** retry_count) * self.rate_limit_delay
                        await asyncio.sleep(wait_time)
                        retry_count += 1
                        continue
                logger.error(f"API request failed: {e.response.status_code} - {e.response.text}")
                return {"error": f"API error: {e.response.status_code} - {e.response.text}"}
            except Exception as e:
                logger.error(f"Request error: {str(e)}")
                return {"error": str(e)}

        return {"error": "Request failed after retries"}

    async def close(self):
        """Close the httpx client."""
        await self.client.aclose()

    # Project methods
    async def get_projects(self) -> List[Dict]:
        """Gets all projects for the user."""
        result = await self._make_request("GET", "/project")
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "error" in result:
            return result
        else:
            return result if isinstance(result, list) else []

    async def get_project(self, project_id: str) -> Dict:
        """Gets a specific project by ID."""
        return await self._make_request("GET", f"/project/{project_id}")

    async def get_project_with_data(self, project_id: str) -> Dict:
        """Gets project with tasks and columns."""
        return await self._make_request("GET", f"/project/{project_id}/data")

    async def create_project(
        self,
        name: str,
        color: str = "#F18181",
        view_mode: str = "list",
        kind: str = "TASK"
    ) -> Dict:
        """Creates a new project."""
        data = {
            "name": name,
            "color": color,
            "viewMode": view_mode,
            "kind": kind
        }
        return await self._make_request("POST", "/project", data)

    async def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        color: Optional[str] = None,
        view_mode: Optional[str] = None,
        kind: Optional[str] = None
    ) -> Dict:
        """Updates an existing project."""
        data = {}
        if name:
            data["name"] = name
        if color:
            data["color"] = color
        if view_mode:
            data["viewMode"] = view_mode
        if kind:
            data["kind"] = kind

        return await self._make_request("POST", f"/project/{project_id}", data)

    async def delete_project(self, project_id: str) -> Dict:
        """Deletes a project."""
        return await self._make_request("DELETE", f"/project/{project_id}")

    # Task methods
    async def get_task(self, project_id: str, task_id: str) -> Dict:
        """Gets a specific task by project ID and task ID."""
        return await self._make_request("GET", f"/project/{project_id}/task/{task_id}")

    async def create_task(
        self,
        title: str,
        project_id: str,
        content: Optional[str] = None,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: int = 0,
        is_all_day: bool = False
    ) -> Dict:
        """Creates a new task."""
        data = {
            "title": title,
            "projectId": project_id
        }

        if content:
            data["content"] = content
        if start_date:
            data["startDate"] = start_date
        if due_date:
            data["dueDate"] = due_date
        if priority is not None:
            data["priority"] = priority
        if is_all_day is not None:
            data["isAllDay"] = is_all_day

        return await self._make_request("POST", "/task", data)

    async def update_task(
        self,
        task_id: str,
        project_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        priority: Optional[int] = None,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> Dict:
        """Updates an existing task."""
        data = {
            "id": task_id,
            "projectId": project_id
        }

        if title:
            data["title"] = title
        if content:
            data["content"] = content
        if priority is not None:
            data["priority"] = priority
        if start_date:
            data["startDate"] = start_date
        if due_date:
            data["dueDate"] = due_date

        return await self._make_request("POST", f"/task/{task_id}", data)

    async def complete_task(self, project_id: str, task_id: str) -> Dict:
        """Marks a task as complete."""
        return await self._make_request("POST", f"/project/{project_id}/task/{task_id}/complete")

    async def delete_task(self, project_id: str, task_id: str) -> Dict:
        """Deletes a task."""
        return await self._make_request("DELETE", f"/project/{project_id}/task/{task_id}")

    async def create_subtask(
        self,
        subtask_title: str,
        parent_task_id: str,
        project_id: str,
        content: Optional[str] = None,
        priority: int = 0
    ) -> Dict:
        """
        Creates a subtask for a parent task within the same project.

        Args:
            subtask_title: Title of the subtask
            parent_task_id: ID of the parent task
            project_id: ID of the project (must be same for both parent and subtask)
            content: Optional content/description for the subtask
            priority: Priority level (0: None, 1: Low, 3: Medium, 5: High)

        Returns:
            API response as a dictionary containing the created subtask
        """
        data = {
            "title": subtask_title,
            "projectId": project_id,
            "parentId": parent_task_id
        }

        if content:
            data["content"] = content
        if priority is not None:
            data["priority"] = priority

        return await self._make_request("POST", "/task", data)

