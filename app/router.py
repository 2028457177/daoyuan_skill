import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from app.schemas import WsAction, WsMessageType, WsRole, CounselorInfo
from counselor_style import CounselorStyle
from llm_client import LLMClient

logger = logging.getLogger("ai_counselor")
router = APIRouter()


@router.get("/")
async def root():
    return FileResponse("frontend/dist/index.html")


@router.get("/api/health")
async def health():
    return {"status": "ok", "service": "ai-counselor", "version": "2.0.0"}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket 客户端已连接")

    try:
        llm = LLMClient()
    except ValueError as e:
        await _send_error(websocket, str(e))
        await websocket.close()
        return

    connection = llm.check_connection()
    if connection["status"] == "error":
        await _send_error(websocket, connection["message"])
        await websocket.close()
        return

    info = CounselorInfo()
    await _send(websocket, WsMessageType.INFO, content=f"连接成功 | 模型: {llm.model}", counselor_name=info.name, counselor_avatar=info.avatar)
    await _send(websocket, WsMessageType.STATUS, content="initiating")

    first_msg = llm.counselor_initiate()
    if first_msg.startswith("调用大模型出错"):
        await _send_error(websocket, first_msg)
        await websocket.close()
        return

    await _send(websocket, WsMessageType.MESSAGE, role=WsRole.COUNSELOR, content=first_msg)

    while True:
        try:
            raw = await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("WebSocket 客户端断开")
            break

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        action = data.get("action", "")

        if action == WsAction.CHAT:
            await _handle_chat(websocket, llm, data.get("content", "").strip())
        elif action == WsAction.CLEAR:
            await _handle_clear(websocket, llm)
        elif action == WsAction.RELOAD:
            await _handle_reload(websocket)

    try:
        await websocket.close()
    except Exception:
        pass


async def _handle_chat(websocket: WebSocket, llm: LLMClient, user_input: str):
    if not user_input:
        return

    is_offense, _ = CounselorStyle.detect_student_offense(user_input)
    await _send(websocket, WsMessageType.MESSAGE, role=WsRole.STUDENT, content=user_input)

    if is_offense:
        await _send(websocket, WsMessageType.STERN_MODE)

    try:
        for chunk in llm.chat_stream(user_input):
            if chunk:
                await _send(websocket, WsMessageType.CHUNK, content=chunk)
                await asyncio.sleep(0.015)
    except Exception as e:
        await _send_error(websocket, f"生成回复出错: {str(e)}")

    await _send(websocket, WsMessageType.DONE)


async def _handle_clear(websocket: WebSocket, llm: LLMClient):
    llm.clear_history()
    await _send(websocket, WsMessageType.STATUS, content="clearing")
    first_msg = llm.counselor_initiate()
    if not first_msg.startswith("调用大模型出错"):
        await _send(websocket, WsMessageType.MESSAGE, role=WsRole.COUNSELOR, content=first_msg)


async def _handle_reload(websocket: WebSocket):
    examples = CounselorStyle.reload_examples()
    msg = f"聊天记录已重载 ({len(examples)} 字符)" if examples else "聊天记录为空"
    await _send(websocket, WsMessageType.INFO, content=msg)


async def _send(
    websocket: WebSocket,
    msg_type: WsMessageType,
    *,
    content: str = "",
    role: WsRole | None = None,
    counselor_name: str | None = None,
    counselor_avatar: str | None = None,
):
    payload: dict = {"type": msg_type.value, "content": content}
    if role is not None:
        payload["role"] = role.value
    if counselor_name is not None:
        payload["counselor_name"] = counselor_name
    if counselor_avatar is not None:
        payload["counselor_avatar"] = counselor_avatar
    await websocket.send_json(payload)


async def _send_error(websocket: WebSocket, msg: str):
    await _send(websocket, WsMessageType.ERROR, content=msg)
