"""CUA-based scheduling tool implementation."""

import logging
import os
from typing import Any
from uuid import UUID

from app.agent.core.context import get_conversation_id, get_workspace_id
from app.services.cua_client import CUAClientError, send_task_to_cua

logger = logging.getLogger(__name__)


class CUASchedulingTool:
    """Scheduling tool that uses CUA (Computer Use Agent) to schedule appointments via Calendly."""

    def __init__(
        self,
        cua_ws_url: str | None = None,
        default_model_id: str = "Qwen/Qwen3-VL-30B-A3B-Instruct",
    ):
        """Initialize the CUA scheduling tool.

        Args:
            cua_ws_url: WebSocket URL for CUA backend. Defaults to ws://localhost:7860/ws
            default_model_id: Default model ID to use for CUA tasks
        """
        self.cua_ws_url = cua_ws_url or os.getenv(
            "CUA_WS_URL", "ws://localhost:7860/ws"
        )
        self.default_model_id = default_model_id

    async def create_booking(self, *, args: dict[str, Any]) -> dict[str, Any]:
        """Create a booking by sending a task to CUA.

        Expected args:
            - name: str - Customer name
            - email: str - Customer email
            - date: str - Appointment date (e.g., "November 24, 2025")
            - time: str - Appointment time with timezone (e.g., "10:00 AM EST")
            - calendly_url: str - Calendly scheduling link

        Returns:
            Dictionary with status and result:
            {
                "status": "success" | "failed",
                "message": str,
                "error": dict | None
            }
        """
        try:
            # Extract required fields
            name = args.get("name", "").strip()
            email = args.get("email", "").strip()
            date = args.get("date", "").strip()
            time = args.get("time", "").strip()
            calendly_url = args.get("calendly_url", "").strip()

            # Validate required fields
            if not name:
                return {
                    "status": "failed",
                    "error": {
                        "code": "missing_field",
                        "message": "Name is required for scheduling",
                    },
                }

            if not email:
                return {
                    "status": "failed",
                    "error": {
                        "code": "missing_field",
                        "message": "Email is required for scheduling",
                    },
                }

            if not date:
                return {
                    "status": "failed",
                    "error": {
                        "code": "missing_field",
                        "message": "Date is required for scheduling",
                    },
                }

            if not time:
                return {
                    "status": "failed",
                    "error": {
                        "code": "missing_field",
                        "message": "Time is required for scheduling",
                    },
                }

            if not calendly_url:
                return {
                    "status": "failed",
                    "error": {
                        "code": "missing_field",
                        "message": "Calendly URL is required for scheduling",
                    },
                }

            # Format the instruction for CUA
            # This matches the format you tested successfully
            instruction = (
                f"Hi I'm {name}, I want to schedule an appointment for {date} at {time}, "
                f"my email is {email}: {calendly_url} "
                f"make sure eastern time is selected since it usually defaults to UTC or something like that. "
                f"You can click the place to select the time and there is an input box where you can write 'eastern', "
                f"and that should show the correct one and then you can just click. also, if the specific day and time is "
                f"not available, then just stop the task say that saying so, it will be marked as failed. no need for you search for other ways to book or anything. "
                f"for example if the requested time is 1pm and in the options you see 12:30pm, 1:30pm, then it means the time slot is not available and you should stop the task immediately saying that the time isnt avalbale."
            )

            # Log all the details being sent to CUA
            logger.info("=" * 80)
            logger.info("CUA SCHEDULING REQUEST - DETAILS:")
            logger.info(f"  Name: {name}")
            logger.info(f"  Email: {email}")
            logger.info(f"  Date: {date}")
            logger.info(f"  Time: {time}")
            logger.info(f"  Calendly URL: {calendly_url}")
            logger.info("-" * 80)
            logger.info("FULL INSTRUCTION BEING SENT TO CUA:")
            logger.info(instruction)
            logger.info("=" * 80)

            # Get workspace and conversation IDs from context for task persistence
            workspace_id: UUID | None = get_workspace_id()
            conversation_id: UUID | None = get_conversation_id()

            logger.info(
                f"Workspace ID from context: {workspace_id}, Conversation ID: {conversation_id}"
            )

            # Send task to CUA and wait for completion
            # Ensure cua_ws_url is not None
            ws_url = self.cua_ws_url or "ws://localhost:7860/ws"
            result = await send_task_to_cua(
                instruction=instruction,
                model_id=self.default_model_id,
                cua_ws_url=ws_url,
                timeout_seconds=300,  # 5 minutes timeout
                workspace_id=workspace_id,
                conversation_id=conversation_id,
            )

            # Log the agent's final answer
            agent_final_answer = result.get("agent_final_answer")
            logger.info("=" * 80)
            logger.info("CUA TASK RESULT:")
            logger.info(f"  Status: {result.get('status')}")
            logger.info(f"  Final State: {result.get('final_state')}")
            if agent_final_answer:
                logger.info(f"  Agent Final Answer: {agent_final_answer}")
            logger.info("=" * 80)

            if result["status"] == "success":
                return {
                    "status": "success",
                    "message": (
                        f"Successfully scheduled appointment for {name} ({email}) "
                        f"on {date} at {time}. Confirmation email has been sent."
                    ),
                    "error": None,
                }
            else:
                # Use agent's final answer if available, otherwise use error/message
                # The agent's final answer contains the specific reason (e.g., "time not available")
                error_msg = (
                    agent_final_answer
                    or result.get("error")
                    or result.get("message", "Unknown error")
                )

                # If we have the agent's final answer, use it directly as the message
                # This gives the chat agent the full context (e.g., "The requested time of 11:30 AM on November 25th, 2025, is not available. The task is marked as failed.")
                if agent_final_answer:
                    return {
                        "status": "failed",
                        "message": agent_final_answer,  # Use agent's explanation directly
                        "error": {
                            "code": "cua_task_failed",
                            "message": agent_final_answer,
                        },
                    }
                else:
                    # Fallback if no agent final answer
                    return {
                        "status": "failed",
                        "message": f"Failed to schedule appointment: {error_msg}",
                        "error": {
                            "code": "cua_task_failed",
                            "message": error_msg,
                        },
                    }

        except CUAClientError as e:
            logger.error(f"CUA client error: {e}")
            return {
                "status": "failed",
                "message": f"Failed to connect to scheduling service: {str(e)}",
                "error": {
                    "code": "connection_error",
                    "message": str(e),
                },
            }
        except Exception as e:
            logger.exception(f"Unexpected error in create_booking: {e}")
            return {
                "status": "failed",
                "message": f"An unexpected error occurred: {str(e)}",
                "error": {
                    "code": "internal_error",
                    "message": str(e),
                },
            }
