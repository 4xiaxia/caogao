# -*- coding: utf-8 -*-
"""Chat management API."""
from __future__ import annotations
import asyncio
import json

from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from agentscope.message import Msg
from agentscope.session import JSONSession
from agentscope.memory import InMemoryMemory
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from pydantic import BaseModel, Field

from .manager import ChatManager
from .models import (
    ChatSpec,
    ChatHistory,
)
from .session import SafeJSONSession
from .utils import agentscope_msg_to_message
from ..dependencies import get_chat_manager, get_runner, get_deps  # 新增：统一依赖注入

router = APIRouter(prefix="/chats", tags=["chats"])


def get_session() -> SafeJSONSession:
    """获取 SafeJSONSession（从 runner 实例中取）"""
    runner = get_deps().get_runner()
    return runner.session


class SendMessageRequest(BaseModel):
    """Request body for sending a chat message."""

    content: str = Field(..., description="Message text content")


@router.get("", response_model=list[ChatSpec])
async def list_chats(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    mgr: ChatManager = Depends(get_chat_manager),
):
    """List all chats with optional filters.

    Args:
        user_id: Optional user ID to filter chats
        channel: Optional channel name to filter chats
        mgr: Chat manager dependency
    """
    return await mgr.list_chats(user_id=user_id, channel=channel)


@router.post("", response_model=ChatSpec)
async def create_chat(
    request: ChatSpec,
    mgr: ChatManager = Depends(get_chat_manager),
):
    """Create a new chat.

    Server generates chat_id (UUID) automatically.

    Args:
        request: Chat creation request
        mgr: Chat manager dependency

    Returns:
        Created chat spec with UUID
    """
    chat_id = str(uuid4())
    spec = ChatSpec(
        id=chat_id,
        name=request.name,
        session_id=request.session_id,
        user_id=request.user_id,
        channel=request.channel,
        meta=request.meta,
    )
    return await mgr.create_chat(spec)


@router.post("/batch-delete", response_model=dict)
async def batch_delete_chats(
    chat_ids: list[str],
    mgr: ChatManager = Depends(get_chat_manager),
):
    """Delete chats by chat IDs.

    Args:
        chat_ids: List of chat IDs
        mgr: Chat manager dependency
    Returns:
        True if deleted, False if failed

    """
    deleted = await mgr.delete_chats(chat_ids=chat_ids)
    return {"deleted": deleted}


@router.get("/{chat_id}", response_model=ChatHistory)
async def get_chat(
    chat_id: str,
    mgr: ChatManager = Depends(get_chat_manager),
    session: JSONSession = Depends(get_session),
):
    """Get detailed information about a specific chat by UUID.

    Args:
        chat_id: Chat UUID
        mgr: Chat manager dependency
        session: JSONSession  dependency

    Returns:
        ChatHistory with messages

    Raises:
        HTTPException: If chat not found (404)
    """
    chat_spec = await mgr.get_chat(chat_id)
    if not chat_spec:
        raise HTTPException(
            status_code=404,
            detail=f"Chat not found: {chat_id}",
        )

    # pylint: disable=protected-access
    session_path = session._get_save_path(
        chat_spec.session_id,
        chat_spec.user_id,
    )

    try:
        with open(session_path, "r", encoding="utf-8") as file:
            state = json.load(file)
    except Exception:
        return ChatHistory(messages=[])
    memories = state.get("agent", {}).get("memory", [])
    memory = InMemoryMemory()
    memory.load_state_dict(memories)

    memories = await memory.get_memory()
    messages = agentscope_msg_to_message(memories)
    return ChatHistory(messages=messages)


@router.put("/{chat_id}", response_model=ChatSpec)
async def update_chat(
    chat_id: str,
    spec: ChatSpec,
    mgr: ChatManager = Depends(get_chat_manager),
):
    """Update an existing chat.

    Args:
        chat_id: Chat UUID
        spec: Updated chat specification
        mgr: Chat manager dependency

    Returns:
        Updated chat spec

    Raises:
        HTTPException: If chat_id mismatch (400) or not found (404)
    """
    if spec.id != chat_id:
        raise HTTPException(
            status_code=400,
            detail="chat_id mismatch",
        )

    # Check if exists
    existing = await mgr.get_chat(chat_id)
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"Chat not found: {chat_id}",
        )

    updated = await mgr.update_chat(spec)
    return updated


@router.delete("/{chat_id}", response_model=dict)
async def delete_chat(
    chat_id: str,
    mgr: ChatManager = Depends(get_chat_manager),
):
    """Delete a chat by UUID.

    Note: This only deletes the chat spec (UUID mapping).
    JSONSession state is NOT deleted.

    Args:
        chat_id: Chat UUID
        mgr: Chat manager dependency

    Returns:
        True if deleted, False if failed

    Raises:
        HTTPException: If chat not found (404)
    """
    deleted = await mgr.delete_chats(chat_ids=[chat_id])
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Chat not found: {chat_id}",
        )
    return {"deleted": True}


@router.post("/{chat_id}/stream")
async def stream_chat_message(
    chat_id: str,
    body: SendMessageRequest,
    mgr: ChatManager = Depends(get_chat_manager),
    runner=Depends(get_runner),
):
    """Send a user message and receive the Agent response via Server-Sent Events.

    The client should consume this endpoint with ``EventSource`` (browser) or
    an equivalent SSE client.  Each event carries a JSON payload:

    - Regular message tokens:
      ``data: {"role": "assistant", "content": "...", "last": false}``
    - Final message (Agent turn complete):
      ``data: {"role": "assistant", "content": "...", "last": true}``
    - Stream finished sentinel:
      ``data: [DONE]``
    - Error:
      ``data: {"error": "..."}``

    Args:
        chat_id: Target chat UUID
        body: Message body with ``content`` field
        mgr: Chat manager dependency
        runner: AgentRunner dependency

    Raises:
        HTTPException: If chat not found (404) or runner not ready (503)
    """
    chat_spec = await mgr.get_chat(chat_id)
    if not chat_spec:
        raise HTTPException(
            status_code=404,
            detail=f"Chat not found: {chat_id}",
        )

    # Build AgentRequest so query_handler has session/user/channel context
    agent_request = AgentRequest(
        input=body.content,
        session_id=chat_spec.session_id,
        user_id=chat_spec.user_id,
        channel=chat_spec.channel,
    )

    # Agentscope Msg object representing the user turn
    user_msg = Msg(name=chat_spec.user_id, content=body.content, role="user")

    async def event_generator():
        try:
            async for msg, last in runner.query_handler(
                [user_msg],
                request=agent_request,
            ):
                payload = json.dumps(
                    {
                        "role": getattr(msg, "role", "assistant"),
                        "content": msg.get_text_content()
                        if hasattr(msg, "get_text_content")
                        else str(msg.content),
                        "last": last,
                    },
                    ensure_ascii=False,
                )
                yield f"data: {payload}\n\n"
                # Yield control so other coroutines can run
                await asyncio.sleep(0)
        except Exception as exc:  # pylint: disable=broad-except
            error_payload = json.dumps({"error": str(exc)}, ensure_ascii=False)
            yield f"data: {error_payload}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
