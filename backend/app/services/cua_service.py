"""
CUA (Computer Use Agent) Service Client

This service handles communication with the CUA browser automation service
for scheduling appointments and other web-based automation tasks.
"""

import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from app.core.config import settings

logger = logging.getLogger(__name__)


class CUAServiceError(Exception):
    """Base exception for CUA service errors"""

    pass


class CUAConnectionError(CUAServiceError):
    """Raised when unable to connect to CUA service"""

    pass


class CUAAutomationError(CUAServiceError):
    """Raised when automation fails"""

    pass


class CUAService:
    """
    Service client for interacting with the Computer Use Agent (CUA).

    The CUA service provides browser automation capabilities for tasks like
    scheduling appointments on various platforms.
    """

    def __init__(self):
        self.base_url = settings.CUA_SERVICE_URL
        self.enabled = settings.CUA_ENABLED
        self.timeout = ClientTimeout(total=settings.AUTOMATION_TIMEOUT_SECONDS)
        self._session: ClientSession | None = None
        self._ws_connection = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self):
        """Initialize HTTP session for CUA communication"""
        if not self._session:
            self._session = ClientSession(timeout=self.timeout)

    async def disconnect(self):
        """Close HTTP session and cleanup"""
        if self._session:
            await self._session.close()
            self._session = None
        if self._ws_connection:
            await self._ws_connection.close()
            self._ws_connection = None

    def is_enabled(self) -> bool:
        """Check if CUA integration is enabled"""
        return self.enabled and bool(settings.HF_TOKEN) and bool(settings.E2B_API_KEY)

    async def health_check(self) -> bool:
        """Check if CUA service is healthy and responding"""
        if not self.is_enabled():
            return False

        try:
            if not self._session:
                await self.connect()

            async with self._session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except aiohttp.ClientError as e:
            logger.error(f"CUA health check failed: {e}")
            return False

    async def create_automation_session(
        self,
        workspace_id: UUID,
        conversation_id: UUID,
        automation_type: str = "scheduling",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Create a new automation session with CUA

        Args:
            workspace_id: ID of the workspace
            conversation_id: ID of the conversation
            automation_type: Type of automation (e.g., 'scheduling')
            metadata: Additional metadata for the session

        Returns:
            Session ID for the automation
        """
        if not self.is_enabled():
            raise CUAServiceError("CUA service is not enabled or configured")

        if not self._session:
            await self.connect()

        # Create session via CUA API
        session_data = {
            "workspace_id": str(workspace_id),
            "conversation_id": str(conversation_id),
            "automation_type": automation_type,
            "metadata": metadata or {},
        }

        try:
            async with self._session.post(
                f"{self.base_url}/api/scheduling/create_session",
                json=session_data,
                headers={"Authorization": f"Bearer {settings.HF_TOKEN}"},
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise CUAServiceError(f"Failed to create session: {error_text}")

                result = await response.json()
                session_id = result.get("session_id")
                logger.info(f"Created CUA automation session: {session_id}")
                return session_id

        except aiohttp.ClientError as e:
            logger.error(f"Failed to create CUA session: {e}")
            raise CUAConnectionError(f"Failed to connect to CUA service: {e}")

    async def run_task(self, instruction: str) -> dict[str, Any]:
        """
        Run a task using the CUA agent with a natural language instruction.

        This is the simple interface - just pass an instruction and the agent handles it.

        Args:
            instruction: Natural language instruction for the CUA agent

        Returns:
            Dict containing task result
        """
        if not self.is_enabled():
            raise CUAServiceError("CUA service is not enabled or configured")

        if not self._session:
            await self.connect()

        try:
            async with self._session.post(
                f"{self.base_url}/api/scheduling/run_task",
                json={"instruction": instruction},
                headers={
                    "Authorization": f"Bearer {settings.HF_TOKEN}",
                    "X-E2B-API-Key": settings.E2B_API_KEY,
                },
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise CUAAutomationError(f"Task failed: {error_text}")

                result = await response.json()
                logger.info(f"CUA task completed: {result.get('status')}")
                return result

        except aiohttp.ClientError as e:
            logger.error(f"Failed to communicate with CUA service: {e}")
            raise CUAConnectionError(f"Failed to connect to CUA service: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during task execution: {e}")
            raise CUAAutomationError(f"Task failed unexpectedly: {e}")

    async def schedule_appointment(
        self,
        session_id: str,
        calendly_url: str,
        user_name: str,
        user_email: str,
        preferred_date: str | None = None,
        preferred_time: str | None = None,
        meeting_type: str | None = None,
        additional_info: str | None = None,
    ) -> dict[str, Any]:
        """
        Automate appointment scheduling using browser automation

        Args:
            session_id: Automation session ID
            calendly_url: URL of the Calendly scheduling page
            user_name: Name of the person scheduling
            user_email: Email of the person scheduling
            preferred_date: Preferred date for the appointment
            preferred_time: Preferred time for the appointment
            meeting_type: Type of meeting if multiple options
            additional_info: Any additional information

        Returns:
            Dict containing confirmation details
        """
        if not self.is_enabled():
            raise CUAServiceError("CUA service is not enabled or configured")

        if not self._session:
            await self.connect()

        # Prepare the automation request
        automation_request = {
            "session_id": session_id,
            "calendly_url": calendly_url,
            "user_name": user_name,
            "user_email": user_email,
            "preferred_date": preferred_date,
            "preferred_time": preferred_time,
            "meeting_type": meeting_type,
            "additional_info": additional_info,
        }

        try:
            # Send automation request to CUA
            async with self._session.post(
                f"{self.base_url}/api/scheduling/schedule_appointment",
                json=automation_request,
                headers={
                    "Authorization": f"Bearer {settings.HF_TOKEN}",
                    "X-E2B-API-Key": settings.E2B_API_KEY,
                },
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise CUAAutomationError(f"Automation failed: {error_text}")

                result = await response.json()
                logger.info(
                    f"CUA service response for session {session_id}: status={result.get('status')}, error_message={result.get('error_message')}"
                )

                # Check if automation actually succeeded
                if result.get("status") != "completed":
                    error_msg = result.get("error_message", "Automation failed")
                    logger.error(
                        f"Automation failed for session {session_id}: {error_msg}"
                    )
                    raise CUAAutomationError(f"Automation failed: {error_msg}")

                # Extract confirmation details
                confirmation = {
                    "status": "completed",
                    "session_id": session_id,
                    "confirmation_number": result.get("confirmation_number"),
                    "scheduled_date": result.get("scheduled_date"),
                    "scheduled_time": result.get("scheduled_time"),
                    "meeting_link": result.get("meeting_link"),
                    "calendar_event": result.get("calendar_event"),
                    "completed_at": datetime.utcnow().isoformat(),
                }

                logger.info(
                    f"Successfully scheduled appointment for session {session_id}"
                )
                return confirmation

        except aiohttp.ClientError as e:
            logger.error(f"Failed to communicate with CUA service: {e}")
            raise CUAConnectionError(f"Failed to connect to CUA service: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during automation: {e}")
            raise CUAAutomationError(f"Automation failed unexpectedly: {e}")

    async def get_automation_status(self, session_id: str) -> dict[str, Any]:
        """
        Get the current status of an automation session

        Args:
            session_id: The automation session ID

        Returns:
            Dict containing session status and details
        """
        if not self._session:
            await self.connect()

        try:
            async with self._session.get(
                f"{self.base_url}/api/scheduling/session/{session_id}/status",
                headers={"Authorization": f"Bearer {settings.HF_TOKEN}"},
            ) as response:
                if response.status == 404:
                    return {"status": "not_found", "session_id": session_id}
                elif response.status != 200:
                    return {"status": "error", "session_id": session_id}

                return await response.json()

        except aiohttp.ClientError as e:
            logger.error(f"Failed to get automation status: {e}")
            return {"status": "error", "session_id": session_id, "error": str(e)}

    async def cancel_automation(self, session_id: str) -> bool:
        """
        Cancel an ongoing automation session

        Args:
            session_id: The automation session ID to cancel

        Returns:
            True if cancelled successfully, False otherwise
        """
        if not self._session:
            await self.connect()

        try:
            async with self._session.delete(
                f"{self.base_url}/api/scheduling/session/{session_id}",
                headers={"Authorization": f"Bearer {settings.HF_TOKEN}"},
            ) as response:
                return response.status in [200, 204]

        except aiohttp.ClientError as e:
            logger.error(f"Failed to cancel automation: {e}")
            return False

    async def connect_websocket(self, session_id: str):
        """
        Connect to CUA WebSocket for real-time automation updates

        Args:
            session_id: The automation session ID to monitor

        Returns:
            WebSocket connection for receiving updates
        """
        if not self.is_enabled():
            raise CUAServiceError("CUA service is not enabled")

        ws_url = f"{self.base_url.replace('http', 'ws')}/ws/{session_id}"

        if not self._session:
            await self.connect()

        try:
            self._ws_connection = await self._session.ws_connect(
                ws_url, headers={"Authorization": f"Bearer {settings.HF_TOKEN}"}
            )
            logger.info(f"Connected to CUA WebSocket for session {session_id}")
            return self._ws_connection

        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to CUA WebSocket: {e}")
            raise CUAConnectionError(f"WebSocket connection failed: {e}")

    async def stream_automation_updates(self, session_id: str):
        """
        Stream real-time updates from an automation session

        Args:
            session_id: The automation session ID to monitor

        Yields:
            Dict containing automation update messages
        """
        ws = await self.connect_websocket(session_id)

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    yield data
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.info("WebSocket connection closed")
                    break
        finally:
            if not ws.closed:
                await ws.close()


# Singleton instance
cua_service = CUAService()
