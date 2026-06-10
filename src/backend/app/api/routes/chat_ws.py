"""
WebSocket 聊天路由 — 支持流式 AI 问答与多轮对话上下文。

功能：
  1. 流式推送：LLM 逐 token 输出实时推送到 WebSocket 客户端
  2. 多轮对话：自动累积历史消息作为上下文
  3. 任务状态推送：PDF 解析进度实时通知

协议：
  客户端 → 服务端：JSON 文本帧
    {"type": "question", "paper_id": "...", "content": "你的问题"}
    {"type": "clear"}      // 清除当前对话历史

  服务端 → 客户端：JSON 文本帧（流式）
    {"type": "token",  "content": "部分", "index": 0}
    {"type": "token",  "content": "回答", "index": 1}
    {"type": "done",   "content": "完整回答", "sources": [...]}
    {"type": "error",  "content": "错误信息"}
    {"type": "status", "content": "task_progress", "data": {"progress": 50}}
"""

import json
import logging
import asyncio
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.prompts import QA_SYSTEM_PROMPT, build_qa_user_prompt
from db.session import get_db
from db.crud_note import get_notes_by_paper
from middleware.jwt_middleware import JWT_SECRET, JWT_ALGORITHM

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """WebSocket 连接管理器，支持多用户多会话。"""

    def __init__(self):
        # {user_id: {paper_id: WebSocket}}
        self._connections: dict[str, dict[str, WebSocket]] = {}
        # {user_id: {paper_id: [messages]}} 多轮对话历史
        self._contexts: dict[str, dict[str, list[dict]]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, paper_id: str):
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = {}
            self._contexts[user_id] = {}
        self._connections[user_id][paper_id] = websocket
        if paper_id not in self._contexts[user_id]:
            self._contexts[user_id][paper_id] = []
        logger.info("WebSocket connected: user=%s paper=%s", user_id, paper_id)

    def disconnect(self, user_id: str, paper_id: str):
        if user_id in self._connections:
            self._connections[user_id].pop(paper_id, None)
            if not self._connections[user_id]:
                self._connections.pop(user_id, None)
                self._contexts.pop(user_id, None)
        logger.info("WebSocket disconnected: user=%s paper=%s", user_id, paper_id)

    async def send_json(self, user_id: str, paper_id: str, data: dict):
        ws = self._connections.get(user_id, {}).get(paper_id)
        if ws:
            await ws.send_text(json.dumps(data, ensure_ascii=False))

    def get_context(self, user_id: str, paper_id: str) -> list:
        return self._contexts.get(user_id, {}).get(paper_id, [])

    def clear_context(self, user_id: str, paper_id: str):
        if user_id in self._contexts and paper_id in self._contexts[user_id]:
            self._contexts[user_id][paper_id] = []

    def add_to_context(self, user_id: str, paper_id: str, role: str, content: str):
        if user_id in self._contexts and paper_id in self._contexts[user_id]:
            self._contexts[user_id][paper_id].append({
                "role": role, "content": content
            })
            # 限制历史长度，防止 token 超限
            max_history = 20
            if len(self._contexts[user_id][paper_id]) > max_history:
                self._contexts[user_id][paper_id] = \
                    self._contexts[user_id][paper_id][-max_history:]


manager = ConnectionManager()


async def _verify_ws_token(websocket: WebSocket) -> Optional[dict]:
    """从 WebSocket 查询参数验证 JWT token。"""
    import jwt
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return None
        return {"id": user_id, "email": payload.get("email", "")}
    except jwt.ExpiredSignatureError:
        await websocket.close(code=4001, reason="Token expired")
        return None
    except jwt.InvalidTokenError:
        await websocket.close(code=4001, reason="Invalid token")
        return None


async def _stream_llm_answer(system_prompt: str, user_prompt: str):
    """
    模拟流式 LLM 输出。
    生产环境可替换为真实的 streaming API 调用。
    """
    from app.core.llm_client import _build_client, _active_model

    client = _build_client()
    model = _active_model()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            stream=True,
        )

        full_content = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                delta = chunk.choices[0].delta.content
                full_content += delta
                yield delta

        yield full_content  # 最后返回完整内容用于保存上下文
    except Exception as e:
        logger.error("Streaming LLM error: %s", e)
        raise


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket 聊天端点。

    连接方式：
      ws://localhost:8000/api/ws/chat?token=<JWT_TOKEN>&paper_id=<PAPER_ID>

    消息格式见模块文档。
    """
    # ── 1. 认证 ──
    user = await _verify_ws_token(websocket)
    if not user:
        return

    paper_id = websocket.query_params.get("paper_id", "")
    if not paper_id:
        await websocket.close(code=4002, reason="Missing paper_id")
        return

    await manager.connect(websocket, user["id"], paper_id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_json(user["id"], paper_id, {
                    "type": "error", "content": "无效的 JSON 格式"
                })
                continue

            msg_type = msg.get("type", "")

            # ── 清除历史 ──
            if msg_type == "clear":
                manager.clear_context(user["id"], paper_id)
                await manager.send_json(user["id"], paper_id, {
                    "type": "status", "content": "context_cleared"
                })
                continue

            # ── 提问 ──
            if msg_type == "question":
                question = msg.get("content", "").strip()
                if not question:
                    await manager.send_json(user["id"], paper_id, {
                        "type": "error", "content": "问题不能为空"
                    })
                    continue

                # 保存用户消息到上下文
                manager.add_to_context(user["id"], paper_id, "user", question)

                try:
                    # 获取论文和笔记数据
                    from db.session import get_session
                    from db.models import Paper

                    async with get_session() as session:
                        result = await session.execute(
                            select(Paper).where(
                                Paper.id == paper_id,
                                Paper.user_id == user["id"]
                            )
                        )
                        paper = result.scalar_one_or_none()

                        if not paper:
                            await manager.send_json(user["id"], paper_id, {
                                "type": "error",
                                "content": "论文不存在或无权访问"
                            })
                            continue

                        notes = await get_notes_by_paper(session, paper_id)

                        if not paper.full_text and not notes:
                            await manager.send_json(user["id"], paper_id, {
                                "type": "error",
                                "content": "论文尚未解析且无笔记，暂无内容可供回答"
                            })
                            continue

                    # 构建 prompt（含历史上下文）
                    history = manager.get_context(user["id"], paper_id)
                    history_text = ""
                    if len(history) > 1:  # 至少有一条历史
                        history_lines = []
                        for h in history[:-1]:  # 排除当前问题
                            role = "用户" if h["role"] == "user" else "AI"
                            history_lines.append(f"{role}: {h['content'][:200]}")
                        if history_lines:
                            history_text = "\n".join(history_lines[-6:]) + "\n"

                    user_prompt = build_qa_user_prompt(
                        title=paper.title,
                        authors=paper.authors,
                        full_text=paper.full_text,
                        notes=notes,
                        question=f"{history_text}当前问题：{question}",
                        max_chars=settings.QA_MAX_CHARS,
                    )

                    # 流式输出
                    full_answer = ""
                    index = 0
                    async for chunk in _stream_llm_answer_stream(
                        QA_SYSTEM_PROMPT, user_prompt
                    ):
                        if index == 0:
                            # 第一个 yield 是实际的 content
                            pass
                        await manager.send_json(user["id"], paper_id, {
                            "type": "token",
                            "content": chunk,
                            "index": index,
                        })
                        index += 1

                    # 构建来源
                    sources = []
                    if paper.full_text:
                        excerpt = paper.full_text[:300] + (
                            "…" if len(paper.full_text) > 300 else ""
                        )
                        sources.append({
                            "type": "full_text",
                            "excerpt": excerpt,
                            "page_number": None,
                        })
                    for note in notes:
                        note_excerpt = note.content[:200] + (
                            "…" if len(note.content) > 200 else ""
                        )
                        sources.append({
                            "type": "note",
                            "excerpt": note_excerpt,
                            "page_number": note.page_number,
                        })

                    # 发送完成信号
                    await manager.send_json(user["id"], paper_id, {
                        "type": "done",
                        "content": full_answer,
                        "sources": sources,
                    })

                    # 保存 AI 回答到上下文
                    manager.add_to_context(
                        user["id"], paper_id, "assistant", full_answer
                    )

                except Exception as e:
                    logger.error("WebSocket chat error: %s", e)
                    await manager.send_json(user["id"], paper_id, {
                        "type": "error",
                        "content": f"AI 服务暂时不可用: {str(e)}"
                    })
                continue

            # ── 未知类型 ──
            await manager.send_json(user["id"], paper_id, {
                "type": "error", "content": f"未知消息类型: {msg_type}"
            })

    except WebSocketDisconnect:
        manager.disconnect(user["id"], paper_id)
    except Exception as e:
        logger.error("WebSocket unexpected error: %s", e)
        manager.disconnect(user["id"], paper_id)


async def _stream_llm_answer_stream(system_prompt: str, user_prompt: str):
    """
    流式 LLM 输出生成器。
    使用真正的 streaming API。
    """
    from openai import OpenAI
    from app.core.llm_client import _build_client, _active_model

    client = _build_client()
    model = _active_model()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=settings.LLM_MAX_TOKENS,
        temperature=settings.LLM_TEMPERATURE,
        stream=True,
    )

    full_content = ""
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            delta = chunk.choices[0].delta.content
            full_content += delta
            yield delta

    # 用完整内容作为最后一个输出
    yield full_content
