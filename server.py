import asyncio
import json
import sys

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import OPENAI_MODEL, OPENAI_BASE_URL
from counselor_style import CounselorStyle
from llm_client import LLMClient

app = FastAPI(title="AI Counselor", version="1.0")

app.mount("/static", StaticFiles(directory="."), name="static")

COUNSELOR_NAME = "blingbling"
COUNSELOR_AVATAR = "/static/导员头像.jpg"


@app.get("/")
async def root():
    return FileResponse("index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        llm = LLMClient()
    except ValueError as e:
        await websocket.send_json({"type": "error", "content": str(e)})
        await websocket.close()
        return

    connection = llm.check_connection()
    if connection["status"] == "error":
        await websocket.send_json({"type": "error", "content": connection["message"]})
        await websocket.close()
        return

    await websocket.send_json({
        "type": "info",
        "content": f"连接成功 | 模型: {llm.model}",
        "counselor_name": COUNSELOR_NAME,
        "counselor_avatar": COUNSELOR_AVATAR,
    })

    await websocket.send_json({"type": "status", "content": "initiating"})

    first_msg = llm.counselor_initiate()
    if first_msg.startswith("调用大模型出错"):
        await websocket.send_json({"type": "error", "content": first_msg})
        await websocket.close()
        return

    await websocket.send_json({
        "type": "message",
        "role": "counselor",
        "content": first_msg,
    })

    while True:
        try:
            raw = await websocket.receive_text()
        except WebSocketDisconnect:
            break

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        action = data.get("action", "")

        if action == "chat":
            user_input = data.get("content", "").strip()
            if not user_input:
                continue

            is_offense, _ = CounselorStyle.detect_student_offense(user_input)

            await websocket.send_json({
                "type": "message",
                "role": "student",
                "content": user_input,
            })

            if is_offense:
                await websocket.send_json({"type": "stern_mode"})

            try:
                for chunk in llm.chat_stream(user_input):
                    if chunk:
                        await websocket.send_json({
                            "type": "chunk",
                            "content": chunk,
                        })
                        await asyncio.sleep(0.015)
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": f"生成回复出错: {str(e)}",
                })

            await websocket.send_json({"type": "done"})

        elif action == "clear":
            llm.clear_history()
            await websocket.send_json({"type": "status", "content": "clearing"})

            first_msg = llm.counselor_initiate()
            if first_msg.startswith("调用大模型出错"):
                await websocket.send_json({"type": "error", "content": first_msg})
                continue

            await websocket.send_json({
                "type": "message",
                "role": "counselor",
                "content": first_msg,
            })

        elif action == "reload":
            examples = CounselorStyle.reload_examples()
            await websocket.send_json({
                "type": "info",
                "content": f"聊天记录已重载 ({len(examples)} 字符)" if examples else "聊天记录为空",
            })

    try:
        await websocket.close()
    except Exception:
        pass


if __name__ == "__main__":
    import uvicorn
    print("🚀 辅导员助手 Web 服务启动中...")
    print(f"   打开浏览器访问: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
