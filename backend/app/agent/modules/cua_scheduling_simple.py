"""
Simplified CUA Scheduling Integration

This module provides lightweight scheduling detection and handling
without circular import issues.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def detect_scheduling_intent(message: str) -> bool:
    """
    Detect if a message contains scheduling intent

    Args:
        message: The user's message

    Returns:
        True if scheduling intent is detected, False otherwise
    """
    scheduling_keywords = [
        r"\bbook\b",
        r"\bschedule\b",
        r"\bappointment\b",
        r"\bmeeting\b",
        r"\bavailable\b",
        r"\bcalendar\b",
        r"\bslot\b",
        r"\bset up\b.*\b(call|meeting|appointment)\b",
        r"\b(can|could|would)\b.*\b(meet|talk|chat|discuss)\b",
    ]

    message_lower = message.lower()

    for pattern in scheduling_keywords:
        if re.search(pattern, message_lower):
            return True

    return False


def extract_scheduling_details(message: str) -> dict[str, Any]:
    """
    Extract scheduling details from a message

    Args:
        message: The user's message

    Returns:
        Dictionary containing extracted scheduling details
    """
    details = {}

    # Extract date patterns
    date_patterns = [
        (r"tomorrow", "tomorrow"),
        (r"today", "today"),
        (r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", None),
        (r"\d{1,2}/\d{1,2}/\d{4}", None),
        (r"\d{4}-\d{2}-\d{2}", None),
    ]

    # Extract time patterns
    time_patterns = [
        (r"\d{1,2}:\d{2}\s*(am|pm|AM|PM)?", None),
        (r"\d{1,2}\s*(am|pm|AM|PM)", None),
        (r"(morning|afternoon|evening)", None),
    ]

    # Extract duration patterns
    duration_patterns = [
        (r"\d+\s*(hour|hr|minute|min)s?", None),
    ]

    message_lower = message.lower()

    # Extract dates
    for pattern, value in date_patterns:
        match = re.search(pattern, message_lower)
        if match:
            details["date"] = value or match.group(0)
            break

    # Extract times
    for pattern, value in time_patterns:
        match = re.search(pattern, message_lower)
        if match:
            details["time"] = value or match.group(0)
            break

    # Extract duration
    for pattern, value in duration_patterns:
        match = re.search(pattern, message_lower)
        if match:
            details["duration"] = value or match.group(0)
            break

    # Extract meeting type if mentioned
    if "call" in message_lower:
        details["meeting_type"] = "Phone Call"
    elif "video" in message_lower:
        details["meeting_type"] = "Video Meeting"
    elif "in-person" in message_lower or "in person" in message_lower:
        details["meeting_type"] = "In-Person Meeting"

    return details


async def trigger_cua_scheduling(
    workspace_id: str,
    conversation_id: str | None,  # noqa: ARG001
    scheduling_details: dict[str, Any],
) -> dict[str, Any]:
    """
    Trigger CUA scheduling automation

    Fetches the Calendly URL from the workspace's scheduling connector
    and triggers the CUA browser automation.

    Args:
        workspace_id: The workspace ID
        conversation_id: The conversation ID
        scheduling_details: Extracted scheduling details

    Returns:
        Result of the scheduling attempt
    """
    from app.core.config import settings

    if not settings.CUA_ENABLED:
        return {
            "status": "disabled",
            "message": "Automated scheduling is not enabled. Please use the manual scheduling link.",
        }

    try:
        # Import here to avoid circular dependency
        import asyncio
        from uuid import UUID

        from sqlmodel import select

        from app.api.deps import get_db
        from app.models import SchedulingConnector
        from app.services.cua_service import cua_service

        # Get database session (synchronous, but we're in async context)
        # Use asyncio.to_thread to run sync DB operations in thread pool
        workspace_uuid = UUID(workspace_id)

        def get_scheduling_connector():
            """Synchronous function to get scheduling connector from DB"""
            db = next(get_db())
            try:
                # Query for active scheduling connector
                connector = db.exec(
                    select(SchedulingConnector)
                    .where(SchedulingConnector.workspace_id == workspace_uuid)
                    .where(SchedulingConnector.is_active)
                    .where(SchedulingConnector.type == "calendly")
                ).first()
                return connector
            finally:
                db.close()

        # Run DB query in thread pool to avoid blocking
        connector = await asyncio.to_thread(get_scheduling_connector)

        # Check if connector exists and has config with link
        if not connector:
            logger.warning(
                f"No active Calendly connector found for workspace {workspace_id}"
            )
            return {
                "status": "error",
                "message": "No Calendly connector configured. Please add your Calendly link in the Knowledge Base settings.",
            }

        logger.info(
            f"Found Calendly connector for workspace {workspace_id}: {connector.id}"
        )

        if not connector.config or not connector.config.get("link"):
            logger.warning(
                f"Calendly connector {connector.id} exists but has no link in config: {connector.config}"
            )
            return {
                "status": "error",
                "message": "No Calendly link configured. Please add your Calendly URL in the Knowledge Base settings.",
            }

        calendly_url = connector.config["link"]
        logger.info(f"Using Calendly URL: {calendly_url}")

        # Build natural language instruction for CUA agent
        instruction_parts = [
            f"Navigate to {calendly_url}",
            "Wait for the Calendly page to fully load",
        ]

        if scheduling_details.get("date"):
            instruction_parts.append(
                f"Select a date for {scheduling_details.get('date')}"
            )

        if scheduling_details.get("time"):
            instruction_parts.append(
                f"Select a time slot at {scheduling_details.get('time')}"
            )
        else:
            instruction_parts.append("Select the first available time slot")

        # Extract user info from conversation or use defaults
        user_name = "Guest User"  # TODO: Extract from conversation/user profile
        user_email = "guest@example.com"  # TODO: Extract from conversation/user profile

        instruction_parts.extend(
            [
                f"Fill in the name field with '{user_name}'",
                f"Fill in the email field with '{user_email}'",
            ]
        )

        if scheduling_details.get("notes"):
            instruction_parts.append(
                f"Add the following notes: {scheduling_details.get('notes')}"
            )

        instruction_parts.extend(
            [
                "Complete the booking by clicking the confirm or schedule button",
                "Wait for the confirmation page to fully load (you should see a confirmation message or success page)",
                "Verify the booking was successful by checking that you see a confirmation message, confirmation number, or success indicator on the page",
                "Extract and report the confirmation details from the page including: the exact scheduled date, the exact scheduled time, and any confirmation number or booking ID that is displayed",
                "In your final_answer, provide the confirmation details in this format: 'Booking confirmed for [DATE] at [TIME]. Confirmation number: [NUMBER]' or similar format with the actual details you see on the page",
            ]
        )

        instruction = ". ".join(instruction_parts) + "."

        logger.info(f"Sending instruction to CUA agent: {instruction}")

        # Call CUA agent with simple natural language instruction
        result = await cua_service.run_task(instruction)

        # Format the response
        if result.get("status") == "completed":
            # CUA agent returns a final_answer with the result
            final_answer = result.get("final_answer", "Task completed successfully")

            # Extract date/time from the answer or use original details
            scheduled_date = scheduling_details.get("date", "your preferred date")
            scheduled_time = scheduling_details.get("time", "your preferred time")

            # Build confirmation message
            confirmation_msg = f"✅ Great! I've scheduled your appointment for {scheduled_date} at {scheduled_time}."

            # Add details from CUA agent's final answer if available
            if final_answer and "confirmation" in final_answer.lower():
                confirmation_msg += f" {final_answer}"
            else:
                confirmation_msg += " You should receive a confirmation email shortly."

            logger.info(
                f"Scheduling completed successfully. CUA agent response: {final_answer}"
            )

            return {
                "status": "success",
                "message": confirmation_msg,
                "details": {
                    "scheduled_date": scheduled_date,
                    "scheduled_time": scheduled_time,
                    "cua_response": final_answer,
                },
            }
        else:
            # Failed or unknown status
            error_msg = (
                result.get("error_message")
                or result.get("final_answer")
                or "Unknown error"
            )
            logger.error(f"Scheduling failed: {error_msg}")
            return {
                "status": "error",
                "message": f"I encountered an issue while scheduling: {error_msg}. Please try again or use the manual scheduling link.",
                "details": scheduling_details,
            }

    except Exception as e:
        logger.error(f"Error in trigger_cua_scheduling: {str(e)}", exc_info=True)

        return {
            "status": "error",
            "message": f"I encountered an issue while scheduling: {str(e)}. You can use our scheduling link directly: [Schedule here]",
            "details": scheduling_details,
        }
