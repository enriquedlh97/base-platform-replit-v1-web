import logging
import os
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq

from app.agent.core.prompts import build_system_prompt
from app.agent.tools.scheduling_tool import schedule_appointment_with_cua
from app.core.config import settings

logger = logging.getLogger(__name__)


async def stream_agent_reply(
    *,
    workspace_knowledge_base_text: str,
    conversation_history: list[dict[str, str]],
    calendly_url: str | None = None,
    request_id: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Streaming agent with tool support.

    Emits dict events:
    - {"type": "delta", "text_chunk": str}
    - {"type": "tool_call", "id": str, "tool": str, "args": dict}
    - {"type": "tool_result", "id": str, "status": str, "data": str, "error": str | None}
    """
    # Configure model from central settings (.env via app/core/config.py)
    if not settings.GROQ_API_KEY:
        # Let the route emit an error event with a clear message
        raise RuntimeError("Missing GROQ_API_KEY in backend environment")
    # Ensure downstream SDK sees the key via env (ChatGroq reads env var)
    os.environ.setdefault("GROQ_API_KEY", settings.GROQ_API_KEY)

    # Create tools list
    tools = [schedule_appointment_with_cua]

    model = ChatGroq(
        model=settings.TEXT_MODEL_NAME,
        temperature=settings.MODEL_TEMPERATURE,
        stop_sequences=None,
    ).bind_tools(tools)

    # Build system prompt with Calendly URL if available
    system_prompt_text = build_system_prompt(workspace_knowledge_base_text)
    if calendly_url:
        system_prompt_text += (
            f"\n\nIMPORTANT - Appointment Scheduling:\n"
            f"When a user wants to book an appointment, you should:\n"
            f"1. Collect their name, email, preferred date, and time\n"
            f"2. Once you have all the information, acknowledge that you'll schedule it (e.g., 'Of course, let me schedule that for you')\n"
            f"3. Then use the schedule_appointment_with_cua tool to actually schedule it\n"
            f"4. The Calendly link to use is: {calendly_url}\n"
            f"5. After the tool completes, confirm the appointment details with the user (e.g., 'Great! I've successfully scheduled your appointment...')\n"
            f"6. CRITICAL: Only schedule when the user explicitly requests it. Do NOT schedule when the user is just thanking you, "
            f"acknowledging, or having a general conversation. If an appointment was already successfully scheduled in this conversation, "
            f"do NOT call the scheduling tool again unless the user explicitly requests a NEW appointment "
            f"(e.g., 'schedule another one', 'book a different time', 'I need another appointment', etc.). "
            f"If the user says 'thanks', 'great', 'ok', 'perfect', etc. after a successful scheduling, "
            f"just acknowledge their message - do NOT schedule again."
        )

    # Convert conversation history to LangChain messages
    messages: list[Any] = [SystemMessage(content=system_prompt_text)]
    for item in conversation_history:
        role = item.get("role", "user")
        content = item.get("content", "")
        if not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    # Avoid unused variable warning while keeping signature stable for idempotency in future
    _ = request_id

    # LangChain message format expected: list of dict(role, content)
    accumulated: list[str] = []
    max_iterations = 10  # Prevent infinite loops
    iteration = 0
    just_executed_tool = False  # Track if we just executed a tool

    try:
        while iteration < max_iterations:
            iteration += 1
            has_tool_calls = False

            # Stream response from model
            response_content = ""
            tool_calls = []

            # Stream response and collect tool calls
            async for chunk in model.astream(messages):
                # Stream text content as it comes - this includes any acknowledgment text
                text_chunk = getattr(chunk, "content", None) or getattr(
                    chunk, "delta", None
                )
                if text_chunk:
                    response_content += text_chunk
                    accumulated.append(text_chunk)
                    yield {"type": "delta", "text_chunk": text_chunk}

                # Track tool calls
                if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    tool_calls = chunk.tool_calls
                    has_tool_calls = True

            # After streaming all text, emit tool call events if any
            # This ensures text is displayed before tool status appears
            if has_tool_calls and tool_calls:
                # If we have accumulated text (pre-message), emit message_end to save it separately
                # This prevents the pre-message from being merged with the post-tool message
                if accumulated:
                    pre_message_text = "".join(accumulated)
                    yield {
                        "type": "message_end",
                        "message_id": None,  # Will be set by route
                        "full_text": pre_message_text,
                    }
                    # Clear accumulated for the post-tool message
                    accumulated = []

                for tool_call in tool_calls:
                    yield {
                        "type": "tool_call",
                        "id": tool_call.get("id", ""),
                        "tool": tool_call.get("name", ""),
                        "args": tool_call.get("args", {}),
                    }

            # If no tool calls, check if we need to continue or break
            if not has_tool_calls:
                # If we have text content in this iteration, we're done
                if response_content:
                    just_executed_tool = False  # Reset flag
                    break
                # If no text and no tool calls, check if we just executed a tool
                # We check if we just executed a tool OR if the last message is a ToolMessage
                if just_executed_tool or (
                    messages and isinstance(messages[-1], ToolMessage)
                ):
                    # We just executed a tool but got no response - force one
                    logger.info(
                        "Tool executed but no response generated, forcing final response"
                    )
                    # Log the last few messages for debugging
                    for i, msg in enumerate(messages[-3:], start=len(messages) - 2):
                        msg_type = type(msg).__name__
                        msg_content = (
                            getattr(msg, "content", "")[:100]
                            if hasattr(msg, "content")
                            else str(msg)[:100]
                        )
                        logger.info(f"Message {i}: {msg_type} - {msg_content}...")

                    try:
                        # Add a human message to prompt the model to respond to the tool result
                        # This makes it clearer that we expect a response
                        tool_result_msg = None
                        for msg in reversed(messages):
                            if isinstance(msg, ToolMessage):
                                tool_result_msg = msg.content
                                break

                        if tool_result_msg:
                            # Create a new message list with an explicit prompt to respond
                            messages_with_prompt = messages + [
                                HumanMessage(
                                    content=f"Please respond to the user about the scheduling result: {tool_result_msg}"
                                )
                            ]
                        else:
                            messages_with_prompt = messages + [
                                HumanMessage(
                                    content="Please provide a response to the user based on the tool result above."
                                )
                            ]

                        response = await model.ainvoke(messages_with_prompt)
                        # Try multiple ways to get the text content
                        text = None
                        if hasattr(response, "content"):
                            text = response.content
                        elif hasattr(response, "text"):
                            text = response.text
                        elif isinstance(response, str):
                            text = response

                        # Check if response has tool_calls (model wants to call tools again)
                        if hasattr(response, "tool_calls") and response.tool_calls:
                            logger.warning(
                                f"Model wants to call tools again instead of responding: {response.tool_calls}"
                            )
                            # Don't allow tool calls - we want a text response
                            # Try invoking again with a stronger prompt
                            messages_with_stronger_prompt = messages_with_prompt + [
                                SystemMessage(
                                    content="You must provide a text response to the user. Do not call any tools. Just explain the result in natural language."
                                )
                            ]
                            response = await model.ainvoke(
                                messages_with_stronger_prompt
                            )
                            text = getattr(response, "content", None) or getattr(
                                response, "text", None
                            )

                        if text and text.strip():
                            logger.info(f"Generated final response: {text[:100]}...")
                            # Stream the response
                            for char in text:
                                accumulated.append(char)
                                yield {"type": "delta", "text_chunk": char}
                            just_executed_tool = False  # Reset flag
                            break
                        else:
                            logger.warning(
                                "Model returned empty response after tool execution"
                            )
                            # Try to get more info about the response
                            logger.warning(f"Response object: {response}")
                            logger.warning(f"Response type: {type(response)}")
                            if hasattr(response, "response_metadata"):
                                logger.warning(
                                    f"Response metadata: {response.response_metadata}"
                                )
                            if hasattr(response, "tool_calls"):
                                logger.warning(
                                    f"Response tool_calls: {response.tool_calls}"
                                )
                    except Exception as e:
                        logger.exception(f"Error forcing final response: {e}")
                # Otherwise, we're done
                just_executed_tool = False  # Reset flag
                break

            # Execute tool calls
            for tool_call in tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id", "")

                # Always inject Calendly URL from DB (user doesn't provide it)
                # The Calendly URL comes from the workspace's SchedulingConnector in the database
                if tool_name == "schedule_appointment_with_cua":
                    if calendly_url:
                        # Always use the Calendly URL from the database
                        tool_args["calendly_url"] = calendly_url
                    else:
                        # If no Calendly URL in DB, this is an error
                        logger.warning("No Calendly URL found in workspace settings")

                try:
                    # Call the tool
                    if tool_name == "schedule_appointment_with_cua":
                        result = await schedule_appointment_with_cua.ainvoke(tool_args)
                        result_str = str(result)

                        # Determine success/failure by checking the result string
                        # If it starts with "FAILED:", it's a failure
                        # Otherwise, if it contains "Successfully" or similar, it's success
                        if result_str.startswith("FAILED:"):
                            tool_status = "error"
                            # Extract the error message (remove "FAILED: " prefix)
                            error_msg = result_str.replace("FAILED: ", "", 1)
                        elif (
                            "Successfully" in result_str
                            or "successfully" in result_str.lower()
                        ):
                            # Success message detected
                            tool_status = "success"
                            error_msg = None
                        else:
                            # Default to success if we can't determine (most cases are success)
                            tool_status = "success"
                            error_msg = None
                    else:
                        result = f"Unknown tool: {tool_name}"
                        tool_status = "success"
                        error_msg = None

                    # Add tool result to messages
                    messages.append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tool_id,
                        )
                    )

                    # Emit tool result event with correct status
                    # For frontend: use user-friendly error message
                    yield {
                        "type": "tool_result",
                        "id": tool_id,
                        "status": tool_status,
                        "data": str(result) if tool_status == "success" else None,
                        "error": "Failed to schedule appointment"
                        if tool_status == "error"
                        else None,
                    }

                except Exception as e:
                    error_msg = str(e)
                    messages.append(
                        ToolMessage(
                            content=f"Error: {error_msg}",
                            tool_call_id=tool_id,
                        )
                    )
                    yield {
                        "type": "tool_result",
                        "id": tool_id,
                        "status": "error",
                        "data": None,
                        "error": error_msg,
                    }

            # Add the assistant's response with tool calls to messages
            if has_tool_calls:
                messages.append(
                    AIMessage(content=response_content, tool_calls=tool_calls)
                )
                # After tool execution, we need to continue the loop to get the agent's final response
                # The model will generate a response based on the tool results
                # Clear accumulated text since we'll get new text in the next iteration
                accumulated = []
                # Mark that we just executed a tool so we can force a response if needed
                just_executed_tool = True
                # Continue loop to get agent's response after tool execution
                # The next iteration will call the model again with tool results in messages
                # Don't break here - continue to next iteration to get final response
                continue

    except Exception as e:
        # Log error but don't break the stream
        # Use the module-level logger, don't redefine it
        error_msg = str(e)
        logger.exception(f"Error in stream_agent_reply: {e}")

        # If it's a rate limit error and we have a ToolMessage, provide a fallback response
        if (
            "rate_limit" in error_msg.lower()
            or "429" in error_msg
            or "Rate limit" in error_msg
        ):
            logger.warning("Rate limit error detected, checking for fallback response")
            if messages:
                # Look for the last ToolMessage to extract the error message
                for msg in reversed(messages):
                    if isinstance(msg, ToolMessage):
                        tool_content = msg.content
                        # If it's a failure message, provide a user-friendly fallback
                        if "FAILED:" in tool_content:
                            error_explanation = tool_content.replace("FAILED: ", "")
                            fallback_msg = f"I apologize, but I encountered an issue while trying to schedule your appointment. {error_explanation}"
                            logger.info(
                                f"Providing fallback response: {fallback_msg[:100]}..."
                            )
                            accumulated.append(fallback_msg)
                            yield {"type": "delta", "text_chunk": fallback_msg}
                        break

    # Safety net: If we have messages but no accumulated text (e.g., after tool execution),
    # force the model to generate a response
    if not accumulated and messages:
        try:
            # Check if we just executed a tool (flag is set) or if there's a ToolMessage
            # After tool execution, messages will be: [...ToolMessage, AIMessage with tool_calls]
            # So we check if the last message is an AIMessage with tool_calls, or if there's a ToolMessage
            needs_final_response = False
            if just_executed_tool:
                needs_final_response = True
                logger.info(
                    "Safety net: just_executed_tool flag is set, forcing final response"
                )
            elif messages and isinstance(messages[-1], ToolMessage):
                needs_final_response = True
                logger.info(
                    "Safety net: last message is ToolMessage, forcing final response"
                )
            elif len(messages) >= 2 and isinstance(messages[-2], ToolMessage):
                # ToolMessage is second-to-last (after AIMessage with tool_calls)
                needs_final_response = True
                logger.info(
                    "Safety net: ToolMessage found in recent messages, forcing final response"
                )

            if needs_final_response:
                # Get final response from model
                logger.info(
                    f"Safety net: Invoking model with {len(messages)} messages to get final response"
                )
                # Log the last few messages for debugging
                for i, msg in enumerate(messages[-3:], start=len(messages) - 2):
                    msg_type = type(msg).__name__
                    msg_content = (
                        getattr(msg, "content", "")[:100]
                        if hasattr(msg, "content")
                        else str(msg)[:100]
                    )
                    logger.info(
                        f"Safety net: Message {i}: {msg_type} - {msg_content}..."
                    )

                # Add a human message to prompt the model to respond to the tool result
                tool_result_msg = None
                for msg in reversed(messages):
                    if isinstance(msg, ToolMessage):
                        tool_result_msg = msg.content
                        break

                if tool_result_msg:
                    # Create a new message list with an explicit prompt to respond
                    messages_with_prompt = messages + [
                        HumanMessage(
                            content=f"Please respond to the user about the scheduling result: {tool_result_msg}"
                        )
                    ]
                else:
                    messages_with_prompt = messages + [
                        HumanMessage(
                            content="Please provide a response to the user based on the tool result above."
                        )
                    ]

                response = await model.ainvoke(messages_with_prompt)
                # Try multiple ways to get the text content
                text = None
                if hasattr(response, "content"):
                    text = response.content
                elif hasattr(response, "text"):
                    text = response.text
                elif isinstance(response, str):
                    text = response

                # Check if response has tool_calls (model wants to call tools again)
                if hasattr(response, "tool_calls") and response.tool_calls:
                    logger.warning(
                        f"Safety net: Model wants to call tools again instead of responding: {response.tool_calls}"
                    )
                    # Don't allow tool calls - we want a text response
                    # Try invoking again with a stronger prompt
                    messages_with_stronger_prompt = messages_with_prompt + [
                        SystemMessage(
                            content="You must provide a text response to the user. Do not call any tools. Just explain the result in natural language."
                        )
                    ]
                    response = await model.ainvoke(messages_with_stronger_prompt)
                    text = getattr(response, "content", None) or getattr(
                        response, "text", None
                    )

                if text and text.strip():
                    logger.info(
                        f"Safety net: Generated final response: {text[:100]}..."
                    )
                    # Stream the response in chunks (not char by char)
                    accumulated.append(text)
                    yield {"type": "delta", "text_chunk": text}
                else:
                    logger.warning("Safety net: Model returned empty response")
                    # Try to get more info about the response
                    logger.warning(f"Safety net: Response object: {response}")
                    logger.warning(f"Safety net: Response type: {type(response)}")
                    if hasattr(response, "response_metadata"):
                        logger.warning(
                            f"Safety net: Response metadata: {response.response_metadata}"
                        )
                    if hasattr(response, "tool_calls"):
                        logger.warning(
                            f"Safety net: Response tool_calls: {response.tool_calls}"
                        )
        except Exception as e:
            # Log the error but don't break
            # Use the module-level logger, don't redefine it
            error_msg = str(e)
            logger.exception(f"Error in safety net response generation: {e}")

            # If it's a rate limit error, provide a fallback response based on ToolMessage
            if (
                "rate_limit" in error_msg.lower()
                or "429" in error_msg
                or "Rate limit" in error_msg
            ):
                logger.warning(
                    "Rate limit error in safety net, providing fallback response"
                )
                if messages:
                    # Look for the last ToolMessage to extract the error message
                    for msg in reversed(messages):
                        if isinstance(msg, ToolMessage):
                            tool_content = msg.content
                            # If it's a failure message, provide a user-friendly fallback
                            if "FAILED:" in tool_content:
                                error_explanation = tool_content.replace("FAILED: ", "")
                                fallback_msg = f"I apologize, but I encountered an issue while trying to schedule your appointment. {error_explanation}"
                                logger.info(
                                    f"Safety net fallback response: {fallback_msg[:100]}..."
                                )
                                accumulated.append(fallback_msg)
                                yield {"type": "delta", "text_chunk": fallback_msg}
                            break
            pass
