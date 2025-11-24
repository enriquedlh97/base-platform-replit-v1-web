"""LangChain tool for scheduling appointments via CUA."""

import logging

from langchain_core.tools import tool

from app.agent.modules.tools import get_scheduling_tool

logger = logging.getLogger(__name__)


@tool
async def schedule_appointment_with_cua(
    name: str,
    email: str,
    date: str,
    time: str,
    calendly_url: str = "",
) -> str:
    """Schedule an appointment using the Calendly link.

    Use this tool ONLY when a user explicitly requests to schedule/book an appointment.

    CRITICAL - Do NOT use this tool if:
    - The user is just thanking you or acknowledging a previous message (e.g., 'thanks', 'great', 'ok', 'perfect')
    - An appointment was already successfully scheduled in this conversation (unless the user explicitly requests a NEW appointment)
    - The user is having a general conversation without explicitly requesting scheduling

    Only use this tool if the user explicitly requests scheduling, such as:
    - "I want to schedule an appointment"
    - "Can you book me for..."
    - "Schedule another appointment" (if they want a second one)
    - "Book a different time" (if they want to reschedule or add another)

    You must have all the required information:
    - name: The customer's full name
    - email: The customer's email address
    - date: The appointment date (e.g., "November 24, 2025" or "Nov 24, 2025")
    - time: The appointment time with timezone (e.g., "10:00 AM EST" or "2:00 PM Eastern Time")
    - calendly_url: The Calendly scheduling link (optional - will be provided automatically if not specified)

    IMPORTANT: You do NOT need to ask the user for the Calendly link. It is automatically provided from the workspace settings.
    You only need to collect: name, email, date, and time from the user.

    Once you have all this information from the conversation AND the user is explicitly requesting scheduling,
    call this tool to schedule the appointment. The tool will handle the actual scheduling process and return a success or error message.

    Args:
        name: Customer's full name
        email: Customer's email address
        date: Appointment date (e.g., "November 24, 2025")
        time: Appointment time with timezone (e.g., "10:00 AM EST")
        calendly_url: The Calendly scheduling link URL (optional - auto-provided)

    Returns:
        A message indicating success or failure of the scheduling operation
    """
    scheduling_tool = get_scheduling_tool()

    result = await scheduling_tool.create_booking(
        args={
            "name": name,
            "email": email,
            "date": date,
            "time": time,
            "calendly_url": calendly_url,
        }
    )

    # Return a string that indicates success or failure
    # The graph will parse this to determine status
    if result["status"] == "success":
        # Success message - the agent will use this to confirm to the user
        return result["message"]
    else:
        # Failure - return the message directly (it already contains the agent's explanation)
        # The message from cua_scheduling_tool already contains the agent's final answer
        # (e.g., "The requested time of 11:30 AM on November 25th, 2025, is not available. The task is marked as failed.")
        error_info = result.get("error", {})
        error_msg = error_info.get(
            "message", result.get("message", "Unknown error occurred")
        )
        # Return a message that starts with "FAILED:" so the graph can detect it
        # The error_msg already contains the full explanation from CUA agent
        return f"FAILED: {error_msg}"
