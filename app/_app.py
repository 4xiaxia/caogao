# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name,unused-argument
"""CoPaw Backend Application."""
import os
import sys
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from agentscope_runtime.engine.app import AgentApp

from .runner import AgentRunner

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
from config import (  # pylint: disable=no-name-in-module
    load_config,
    update_last_dispatch,
    ConfigWatcher,
)
from config.utils import get_jobs_path, get_chats_path
from constant import DOCS_ENABLED, LOG_LEVEL_ENV
from __version__ import __version__
from utils.logging import setup_logger
from .channels import ChannelManager
from .channels.utils import make_process_from_runner
from .runner.repo.json_repo import JsonChatRepository
from .crons.repo.json_repo import JsonJobRepository
from .crons.manager import CronManager
from .runner.manager import ChatManager
from .routers import router as api_router
from .dependencies import Dependencies
from envs import load_envs_into_environ

# Setup logger
logger = setup_logger(os.environ.get(LOG_LEVEL_ENV, "info"))

# Load persisted env vars into os.environ at module import time
load_envs_into_environ()

runner = AgentRunner()

agent_app = AgentApp(
    app_name="Friday",
    app_description="A helpful assistant",
    runner=runner,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await runner.start()

    # --- channel connector init/start (from config.json) ---
    config = load_config()
    channel_manager = ChannelManager.from_config(
        process=make_process_from_runner(runner),
        config=config,
        on_last_dispatch=update_last_dispatch,
    )
    await channel_manager.start_all()

    # --- cron init/start ---
    repo = JsonJobRepository(get_jobs_path())
    cron_manager = CronManager(
        repo=repo,
        runner=runner,
        channel_manager=channel_manager,
        timezone="UTC",
    )
    await cron_manager.start()

    # --- chat manager init and connect to runner.session ---
    chat_repo = JsonChatRepository(get_chats_path())
    chat_manager = ChatManager(
        repo=chat_repo,
    )

    runner.set_chat_manager(chat_manager)

    # --- config file watcher (auto-reload channels on config.json change) ---
    config_watcher = ConfigWatcher(channel_manager=channel_manager)
    await config_watcher.start()

    # expose to endpoints
    app.state.runner = runner
    app.state.channel_manager = channel_manager
    app.state.cron_manager = cron_manager
    app.state.chat_manager = chat_manager
    app.state.config_watcher = config_watcher

    # 初始化统一依赖注入容器
    deps = Dependencies.initialize()
    deps.set_runner(runner)
    deps.set_channel_manager(channel_manager)
    deps.set_cron_manager(cron_manager)
    deps.set_chat_manager(chat_manager)

    try:
        yield
    finally:
        # stop order: watcher -> cron -> channels -> runner
        try:
            await config_watcher.stop()
        except Exception:
            pass
        try:
            await cron_manager.stop()
        finally:
            await channel_manager.stop_all()
            await runner.stop()


app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Console static dir
_CONSOLE_STATIC_ENV = "COPAW_CONSOLE_STATIC_DIR"


def _resolve_console_static_dir() -> str:
    if os.environ.get(_CONSOLE_STATIC_ENV):
        return os.environ[_CONSOLE_STATIC_ENV]
    root_dir = Path(__file__).resolve().parent.parent
    candidate_dist = root_dir / "console" / "dist"
    if candidate_dist.is_dir() and (candidate_dist / "index.html").exists():
        return str(candidate_dist)
    candidate = root_dir / "console"
    if candidate.is_dir() and (candidate / "index.html").exists():
        return str(candidate)
    return str(root_dir / "console")


_CONSOLE_STATIC_DIR = _resolve_console_static_dir()
_CONSOLE_INDEX = (
    Path(_CONSOLE_STATIC_DIR) / "index.html" if _CONSOLE_STATIC_DIR else None
)
logger.info(f"STATIC_DIR: {_CONSOLE_STATIC_DIR}")

# WebSocket 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: str):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)
        logger.info(f"WebSocket 连接：chat_id={chat_id}")

    def disconnect(self, websocket: WebSocket, chat_id: str):
        if chat_id in self.active_connections:
            self.active_connections[chat_id].remove(websocket)
            if len(self.active_connections[chat_id]) == 0:
                del self.active_connections[chat_id]
        logger.info(f"WebSocket 断开：chat_id={chat_id}")

    async def send_personal_message(self, message: dict, chat_id: str):
        if chat_id in self.active_connections:
            message_text = json.dumps(message, ensure_ascii=False)
            for websocket in self.active_connections[chat_id]:
                try:
                    await websocket.send_text(message_text)
                except Exception as e:
                    logger.error(f"发送消息失败：{e}")

manager = ConnectionManager()


@app.websocket("/ws/chats/{chat_id}")
async def websocket_chat(websocket: WebSocket, chat_id: str):
    await manager.connect(websocket, chat_id)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"收到 WebSocket 消息：{data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)
    except Exception as e:
        logger.error(f"WebSocket 错误：{e}")
        manager.disconnect(websocket, chat_id)


async def push_chat_message(chat_id: str, message: dict):
    await manager.send_personal_message(message, chat_id)


@app.get("/")
def read_root():
    if _CONSOLE_INDEX and _CONSOLE_INDEX.exists():
        return FileResponse(_CONSOLE_INDEX)
    return {"message": "Hello World"}


@app.get("/version")
def get_version():
    return {"version": __version__}


app.include_router(api_router)
app.mount("/agent", agent_app)

if os.path.isdir(_CONSOLE_STATIC_DIR):
    _console_path = Path(_CONSOLE_STATIC_DIR)

    @app.get("/logo.png")
    def _console_logo():
        f = _console_path / "logo.png"
        if f.is_file():
            return FileResponse(f, media_type="image/png")
        raise HTTPException(status_code=404, detail="Not Found")

    @app.get("/copaw-symbol.svg")
    def _console_icon():
        f = _console_path / "copaw-symbol.svg"
        if f.is_file():
            return FileResponse(f, media_type="image/svg+xml")
        raise HTTPException(status_code=404, detail="Not Found")

    _assets_dir = _console_path / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    def _console_spa(full_path: str):
        if _CONSOLE_INDEX and _CONSOLE_INDEX.exists():
            return FileResponse(_CONSOLE_INDEX)
        raise HTTPException(status_code=404, detail="Not Found")
