"""CUA (Computer Use Agent) WebSocket client for scheduling appointments."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)


class CUAClientError(Exception):
    """Error raised when CUA client operations fail."""

    pass


class CuaTaskPersistence:
    """Handles persistence of CUA task data to the database."""

    def __init__(self, workspace_id: UUID, conversation_id: UUID | None = None):
        self.workspace_id = workspace_id
        self.conversation_id = conversation_id
        self.task_id: UUID | None = None

    async def create_task(
        self,
        trace_id: str,
        instruction: str,
        model_id: str,
    ) -> UUID:
        """Create a new CuaTask record in the database."""
        from app.api.deps import get_db
        from app.models import CuaTask, CuaTaskStatus

        def _create_task() -> UUID:
            db = next(get_db())
            try:
                task = CuaTask(
                    workspace_id=self.workspace_id,
                    conversation_id=self.conversation_id,
                    trace_id=trace_id,
                    instruction=instruction,
                    model_id=model_id,
                    status=CuaTaskStatus.RUNNING,
                    steps=[],
                    task_metadata={
                        "input_tokens_used": 0,
                        "output_tokens_used": 0,
                        "duration": 0.0,
                        "number_of_steps": 0,
                        "max_steps": 30,
                    },
                    started_at=datetime.now(timezone.utc),
                )
                db.add(task)
                db.commit()
                db.refresh(task)
                if not task.id:
                    raise ValueError("Task ID not generated")
                return task.id
            finally:
                db.close()

        self.task_id = await asyncio.to_thread(_create_task)
        logger.info(f"Created CUA task record: {self.task_id}")
        return self.task_id

    async def add_step(
        self, step_data: dict[str, Any], metadata: dict[str, Any]
    ) -> None:
        """Add a step to the CuaTask record."""
        if not self.task_id:
            return

        from app.api.deps import get_db
        from app.models import CuaTask

        def _add_step() -> None:
            db = next(get_db())
            try:
                task = db.get(CuaTask, self.task_id)
                if task:
                    # Append step to steps array
                    steps = list(task.steps) if task.steps else []
                    steps.append(step_data)
                    task.steps = steps

                    # Update task_metadata
                    task.task_metadata = {
                        "input_tokens_used": metadata.get("inputTokensUsed", 0),
                        "output_tokens_used": metadata.get("outputTokensUsed", 0),
                        "duration": metadata.get("duration", 0.0),
                        "number_of_steps": metadata.get("numberOfSteps", 0),
                        "max_steps": metadata.get("maxSteps", 30),
                    }
                    task.updated_at = datetime.now(timezone.utc)
                    db.add(task)
                    db.commit()
            finally:
                db.close()

        await asyncio.to_thread(_add_step)
        logger.debug(f"Added step to CUA task: {self.task_id}")

    async def complete_task(
        self,
        final_state: str,
        error_message: str | None = None,
    ) -> None:
        """Mark the CuaTask as completed."""
        if not self.task_id:
            return

        from app.api.deps import get_db
        from app.models import CuaTask, CuaTaskStatus

        def _complete_task() -> None:
            db = next(get_db())
            try:
                task = db.get(CuaTask, self.task_id)
                if task:
                    # Map CUA final_state to our status
                    status_map = {
                        "success": CuaTaskStatus.COMPLETED,
                        "error": CuaTaskStatus.FAILED,
                        "stopped": CuaTaskStatus.STOPPED,
                        "max_steps_reached": CuaTaskStatus.COMPLETED,
                        "sandbox_timeout": CuaTaskStatus.TIMEOUT,
                    }
                    task.status = status_map.get(final_state, CuaTaskStatus.FAILED)
                    task.final_state = final_state
                    task.error_message = error_message
                    task.completed_at = datetime.now(timezone.utc)
                    task.updated_at = datetime.now(timezone.utc)
                    db.add(task)
                    db.commit()
            finally:
                db.close()

        await asyncio.to_thread(_complete_task)
        logger.info(f"Completed CUA task: {self.task_id} with state: {final_state}")

    async def mark_timeout(self) -> None:
        """Mark the task as timed out."""
        await self.complete_task("timeout", "Task timed out")

    async def mark_error(self, error_message: str) -> None:
        """Mark the task as errored."""
        await self.complete_task("error", error_message)


async def send_task_to_cua(
    instruction: str,
    model_id: str = "Qwen/Qwen3-VL-30B-A3B-Instruct",
    cua_ws_url: str = "ws://localhost:7860/ws",
    timeout_seconds: int = 300,
    workspace_id: UUID | None = None,
    conversation_id: UUID | None = None,
) -> dict[str, Any]:
    """Send a task to CUA via WebSocket and wait for completion.

    Args:
        instruction: The task instruction to send to CUA (e.g., "schedule appointment...")
        model_id: The model ID to use for the task
        cua_ws_url: The WebSocket URL for CUA backend
        timeout_seconds: Maximum time to wait for task completion
        workspace_id: Optional workspace ID to persist task in database
        conversation_id: Optional conversation ID to link task to a conversation

    Returns:
        Dictionary with status and result information:
        {
            "status": "success" | "error" | "timeout",
            "final_state": "success" | "error" | ...,
            "trace_id": str,
            "task_id": str (if workspace_id provided),
            "message": str,
            "error": str (if status is "error")
        }

    Raises:
        CUAClientError: If connection or communication fails
    """
    task_start_time = datetime.now(timezone.utc)

    # Initialize persistence layer if workspace_id is provided
    persistence: CuaTaskPersistence | None = None
    if workspace_id:
        persistence = CuaTaskPersistence(workspace_id, conversation_id)

    try:
        async with websockets.connect(cua_ws_url) as websocket:
            logger.info("Connected to CUA WebSocket")

            # Wait for initial heartbeat to get UUID - this is REQUIRED
            # CUA creates the UUID and expects us to use it as trace_id
            trace_id: str | None = None
            try:
                heartbeat_message = await asyncio.wait_for(
                    websocket.recv(), timeout=5.0
                )
                heartbeat_data = json.loads(heartbeat_message)
                if heartbeat_data.get("type") == "heartbeat":
                    trace_id = heartbeat_data.get("uuid")
                    if not trace_id:
                        raise CUAClientError("Heartbeat message missing UUID")
                    logger.info(f"Received heartbeat, UUID: {trace_id}")
                else:
                    raise CUAClientError(
                        f"Expected heartbeat, got: {heartbeat_data.get('type')}"
                    )
            except asyncio.TimeoutError:
                raise CUAClientError("Timeout waiting for heartbeat from CUA")

            if not trace_id:
                raise CUAClientError("Failed to get trace_id from CUA heartbeat")

            # At this point, trace_id is guaranteed to be a string
            assert trace_id is not None, "trace_id should not be None after validation"

            # Create AgentTrace message
            trace_message = {
                "type": "user_task",
                "trace": {
                    "id": trace_id,
                    "timestamp": task_start_time.isoformat(),
                    "instruction": instruction,
                    "modelId": model_id,
                    "isRunning": True,
                    "steps": [],
                    "traceMetadata": {
                        "traceId": trace_id,
                        "inputTokensUsed": 0,
                        "outputTokensUsed": 0,
                        "duration": 0.0,
                        "numberOfSteps": 0,
                        "maxSteps": 30,
                        "completed": False,
                        "final_state": None,
                        "user_evaluation": "not_evaluated",
                    },
                },
            }

            # Log the exact message being sent to CUA
            logger.info("=" * 80)
            logger.info("EXACT MESSAGE BEING SENT TO CUA WEBSOCKET:")
            logger.info(f"Trace ID: {trace_id}")
            logger.info(f"Model ID: {model_id}")
            logger.info(f"Instruction: {instruction}")
            logger.info("-" * 80)
            logger.info("FULL JSON MESSAGE:")
            logger.info(json.dumps(trace_message, indent=2))
            logger.info("=" * 80)

            # Send the task
            await websocket.send(json.dumps(trace_message))
            logger.info("Message sent to CUA WebSocket successfully")

            # Create persistent task record if workspace_id was provided
            task_id: UUID | None = None
            if persistence:
                task_id = await persistence.create_task(trace_id, instruction, model_id)

            # Wait for completion events
            final_state = None
            final_message = None
            error_message = None
            steps: list[
                dict[str, Any]
            ] = []  # Collect all steps to extract final answer
            agent_final_answer: str | None = None  # The agent's final answer message

            def extract_final_answer_from_steps(
                steps_list: list[dict[str, Any]],
            ) -> str | None:
                """Extract the final answer from steps, looking for final_answer action."""
                if not steps_list:
                    return None

                # Iterate backwards through steps to find the most recent final_answer
                for step in reversed(steps_list):
                    actions = step.get("actions", [])
                    if not isinstance(actions, list):
                        continue

                    for action in actions:
                        if action.get("function_name") == "final_answer":
                            # Try to get answer from parameters
                            params = action.get("parameters", {})
                            if isinstance(params, dict):
                                answer = params.get("answer") or params.get("arg_0")
                                if answer:
                                    return str(answer)

                    # Fallback: use the last thought if no final_answer found
                    thought = step.get("thought")
                    if thought:
                        return str(thought)

                return None

            try:
                # Use wait_for for timeout (compatible with Python 3.11+)
                async def wait_for_completion() -> None:
                    nonlocal \
                        final_state, \
                        final_message, \
                        error_message, \
                        steps, \
                        agent_final_answer
                    while True:
                        message = await websocket.recv()
                        event_data = json.loads(message)

                        event_type = event_data.get("type")

                        if event_type == "agent_start":
                            logger.info("Agent started processing task")
                        elif event_type == "agent_progress":
                            # Collect steps from progress events
                            # The step might be in "agentStep" or "step" field
                            agent_step = event_data.get("agentStep") or event_data.get(
                                "step"
                            )
                            trace_metadata = event_data.get("traceMetadata", {})
                            if agent_step:
                                steps.append(agent_step)
                                # Persist step if persistence is enabled
                                if persistence:
                                    await persistence.add_step(
                                        agent_step, trace_metadata
                                    )
                                # Log if we found a final_answer in this step
                                if isinstance(agent_step, dict):
                                    actions = agent_step.get("actions", [])
                                    if isinstance(actions, list):
                                        for action in actions:
                                            if (
                                                action.get("function_name")
                                                == "final_answer"
                                            ):
                                                params = action.get("parameters", {})
                                                if isinstance(params, dict):
                                                    answer = params.get(
                                                        "answer"
                                                    ) or params.get("arg_0")
                                                    if answer:
                                                        logger.info(
                                                            f"Found final_answer in step: {answer[:200]}..."
                                                        )
                            logger.debug("Agent progress update received")
                        elif event_type == "agent_complete":
                            final_state = event_data.get("final_state")
                            trace_metadata = event_data.get("traceMetadata", {})
                            completed = trace_metadata.get("completed", False)

                            # Extract final answer from collected steps
                            agent_final_answer = extract_final_answer_from_steps(steps)

                            # Log the final answer
                            logger.info("=" * 80)
                            logger.info("CUA AGENT FINAL ANSWER:")
                            if agent_final_answer:
                                logger.info(f"Final Answer: {agent_final_answer}")
                            else:
                                logger.warning("No final answer found in steps")
                            logger.info(f"Final State: {final_state}")
                            logger.info(f"Completed: {completed}")
                            logger.info("=" * 80)

                            if final_state == "success" and completed:
                                final_message = "Task completed successfully"
                                logger.info(f"Task completed successfully: {trace_id}")
                            else:
                                final_message = (
                                    f"Task completed with state: {final_state}"
                                )
                                logger.warning(
                                    f"Task completed with non-success state: {final_state}"
                                )
                            return
                        elif event_type == "agent_error":
                            error_message = event_data.get("error", "Unknown error")
                            logger.error(f"Agent error: {error_message}")
                            return
                        elif event_type == "heartbeat":
                            # Ignore heartbeat messages
                            continue

                await asyncio.wait_for(wait_for_completion(), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                logger.error(f"Task timeout after {timeout_seconds} seconds")
                if persistence:
                    await persistence.mark_timeout()
                return {
                    "status": "timeout",
                    "final_state": None,
                    "trace_id": trace_id,
                    "task_id": str(task_id) if task_id else None,
                    "message": f"Task timed out after {timeout_seconds} seconds",
                    "error": "timeout",
                }

            if error_message:
                if persistence:
                    await persistence.mark_error(error_message)
                return {
                    "status": "error",
                    "final_state": "error",
                    "trace_id": trace_id,
                    "task_id": str(task_id) if task_id else None,
                    "message": f"Task failed: {error_message}",
                    "error": error_message,
                    "agent_final_answer": agent_final_answer,
                }

            # Check if the agent's final answer indicates failure
            # Even if final_state is "success", the agent might say it failed
            is_actually_success = True
            if agent_final_answer:
                final_answer_lower = agent_final_answer.lower()
                # Check for failure indicators in the final answer
                failure_indicators = [
                    "not available",
                    "unavailable",
                    "failed",
                    "could not",
                    "unable to",
                    "marked as failed",
                    "task is marked as failed",
                ]
                if any(
                    indicator in final_answer_lower for indicator in failure_indicators
                ):
                    is_actually_success = False
                    logger.warning(
                        f"Agent final answer indicates failure despite final_state={final_state}: {agent_final_answer}"
                    )

            if final_state == "success" and is_actually_success:
                if persistence:
                    await persistence.complete_task("success")
                return {
                    "status": "success",
                    "final_state": final_state,
                    "trace_id": trace_id,
                    "task_id": str(task_id) if task_id else None,
                    "message": final_message or "Task completed successfully",
                    "error": None,
                    "agent_final_answer": agent_final_answer,
                }
            else:
                # Task failed - use agent's final answer if available, otherwise use generic message
                failure_message = (
                    agent_final_answer
                    or final_message
                    or "Task did not complete successfully"
                )
                if persistence:
                    await persistence.complete_task(
                        final_state or "error", failure_message
                    )
                return {
                    "status": "failed",
                    "final_state": final_state or "unknown",
                    "trace_id": trace_id,
                    "task_id": str(task_id) if task_id else None,
                    "message": failure_message,
                    "error": agent_final_answer or final_state or "unknown_error",
                    "agent_final_answer": agent_final_answer,
                }

    except ConnectionClosed as e:
        error_msg = f"WebSocket connection closed: {e}"
        logger.error(error_msg)
        if persistence:
            await persistence.mark_error(error_msg)
        raise CUAClientError(error_msg) from e
    except WebSocketException as e:
        error_msg = f"WebSocket error: {e}"
        logger.error(error_msg)
        if persistence:
            await persistence.mark_error(error_msg)
        raise CUAClientError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error communicating with CUA: {e}"
        logger.exception(error_msg)
        if persistence:
            await persistence.mark_error(error_msg)
        raise CUAClientError(error_msg) from e
