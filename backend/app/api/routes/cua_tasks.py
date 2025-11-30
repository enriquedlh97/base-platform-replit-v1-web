"""CUA (Computer Use Agent) Task management routes."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import col, func, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    CuaTask,
    CuaTaskPublic,
    CuaTasksPublic,
    CuaTaskStatus,
    CuaTaskSummary,
    Workspace,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cua-tasks", tags=["cua-tasks"])


def get_user_workspace(session: SessionDep, current_user: CurrentUser) -> Workspace:
    """Get the current user's workspace."""
    statement: SelectOfScalar[Workspace] = select(Workspace).where(
        Workspace.owner_id == current_user.id
    )
    workspace = session.exec(statement).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


def get_task_or_404(
    task_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> CuaTask:
    """Verify task exists and user has access."""
    workspace = get_user_workspace(session, current_user)

    statement: SelectOfScalar[CuaTask] = select(CuaTask).where(
        CuaTask.id == task_id, CuaTask.workspace_id == workspace.id
    )
    task = session.exec(statement).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/", response_model=CuaTasksPublic)
def list_cua_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    status: str | None = Query(
        default=None,
        description="Filter by status (pending, running, completed, failed, stopped, timeout)",
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> Any:
    """
    List CUA tasks for the current user's workspace.

    Results are ordered by created_at descending (most recent first).
    """
    workspace = get_user_workspace(session, current_user)

    # Build query
    statement: SelectOfScalar[CuaTask] = (
        select(CuaTask)
        .where(CuaTask.workspace_id == workspace.id)
        .order_by(col(CuaTask.created_at).desc())
    )

    # Apply status filter if provided
    if status:
        valid_statuses = [
            CuaTaskStatus.PENDING,
            CuaTaskStatus.RUNNING,
            CuaTaskStatus.COMPLETED,
            CuaTaskStatus.FAILED,
            CuaTaskStatus.STOPPED,
            CuaTaskStatus.TIMEOUT,
        ]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )
        statement = statement.where(CuaTask.status == status)

    # Get total count
    count_statement = (
        select(func.count())
        .select_from(CuaTask)
        .where(CuaTask.workspace_id == workspace.id)
    )
    if status:
        count_statement = count_statement.where(CuaTask.status == status)
    total_count = session.exec(count_statement).one()

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    tasks = list(session.exec(statement).all())

    # Convert to summary format (without full step data)
    summaries = [
        CuaTaskSummary(
            id=task.id,
            workspace_id=task.workspace_id,
            conversation_id=task.conversation_id,
            trace_id=task.trace_id,
            instruction=task.instruction,
            status=task.status,
            model_id=task.model_id,
            final_state=task.final_state,
            error_message=task.error_message,
            step_count=len(task.steps) if task.steps else 0,
            task_metadata=task.task_metadata if task.task_metadata else {},
            started_at=task.started_at,
            completed_at=task.completed_at,
            created_at=task.created_at,
        )
        for task in tasks
    ]

    return CuaTasksPublic(data=summaries, count=total_count)


@router.get("/active", response_model=CuaTasksPublic)
def list_active_cua_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    List active (pending or running) CUA tasks for the current user's workspace.
    """
    workspace = get_user_workspace(session, current_user)

    # Query for active tasks
    statement: SelectOfScalar[CuaTask] = (
        select(CuaTask)
        .where(
            CuaTask.workspace_id == workspace.id,
            col(CuaTask.status).in_([CuaTaskStatus.PENDING, CuaTaskStatus.RUNNING]),
        )
        .order_by(col(CuaTask.created_at).desc())
    )

    tasks = list(session.exec(statement).all())
    total_count = len(tasks)

    # Convert to summary format
    summaries = [
        CuaTaskSummary(
            id=task.id,
            workspace_id=task.workspace_id,
            conversation_id=task.conversation_id,
            trace_id=task.trace_id,
            instruction=task.instruction,
            status=task.status,
            model_id=task.model_id,
            final_state=task.final_state,
            error_message=task.error_message,
            step_count=len(task.steps) if task.steps else 0,
            task_metadata=task.task_metadata if task.task_metadata else {},
            started_at=task.started_at,
            completed_at=task.completed_at,
            created_at=task.created_at,
        )
        for task in tasks
    ]

    return CuaTasksPublic(data=summaries, count=total_count)


@router.get("/{task_id}", response_model=CuaTaskPublic)
def get_cua_task(
    *,
    task_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get a single CUA task by ID, including all step data.
    """
    task = get_task_or_404(task_id, session, current_user)
    return CuaTaskPublic(
        id=task.id,
        workspace_id=task.workspace_id,
        conversation_id=task.conversation_id,
        trace_id=task.trace_id,
        instruction=task.instruction,
        status=task.status,
        model_id=task.model_id,
        final_state=task.final_state,
        error_message=task.error_message,
        steps=task.steps if task.steps else [],
        task_metadata=task.task_metadata if task.task_metadata else {},
        started_at=task.started_at,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.delete("/{task_id}")
async def stop_cua_task(
    *,
    task_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Stop a running CUA task.

    This will attempt to stop the task if it's currently running.
    Note: The actual stopping is best-effort and depends on the CUA backend.
    """
    task = get_task_or_404(task_id, session, current_user)

    if task.status not in [CuaTaskStatus.PENDING, CuaTaskStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot stop task with status '{task.status}'. Only pending or running tasks can be stopped.",
        )

    # Update task status to stopped
    task.status = CuaTaskStatus.STOPPED
    task.final_state = "stopped"
    task.completed_at = datetime.now(timezone.utc)
    task.updated_at = datetime.now(timezone.utc)
    session.add(task)
    session.commit()

    logger.info(f"Stopped CUA task: {task_id}")

    return {"message": "Task stopped successfully", "task_id": str(task_id)}


@router.delete("/{task_id}/permanently")
def delete_cua_task(
    *,
    task_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Permanently delete a CUA task.

    This removes the task and all its step data from the database.
    """
    task = get_task_or_404(task_id, session, current_user)

    if task.status in [CuaTaskStatus.PENDING, CuaTaskStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a running task. Stop it first.",
        )

    session.delete(task)
    session.commit()

    logger.info(f"Deleted CUA task: {task_id}")

    return {"message": "Task deleted successfully", "task_id": str(task_id)}
