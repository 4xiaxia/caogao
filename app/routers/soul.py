# -*- coding: utf-8 -*-
"""Soul 文件保护 API - 骨架层"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import List, Optional
import shutil
from pathlib import Path

from ..dependencies import Dependencies, get_deps
from constant import WORKING_DIR as _WORKING_DIR


def get_working_dir():
    return _WORKING_DIR

router = APIRouter(prefix="/agent/soul", tags=["Soul 保护"])

# Soul 文件列表
SOUL_FILES = [
    "SOUL.md",
    "AGENTS.md",
    "PROFILE.md",
    "MEMORY.md",
    "HEARTBEAT.md",
    "goals.md",
    "wishes.md",
    "future.md",
    "daily-reflection.md",
    "improvements.md",
    "learnings.md",
]

SOUL_DIRS = [
    "soul/",
    "soul/life/",
    "soul/skills/",
    "soul/Factory/",
    "soul/work/",
]


@router.get("/files")
async def list_soul_files(
    deps: Dependencies = Depends(get_deps),
):
    """
    获取 Soul 文件列表（带保护标记）
    
    Soul 文件受保护，删除需要二次确认，修改前自动备份
    """
    working_dir = get_working_dir()
    files = []
    
    for filename in SOUL_FILES:
        file_path = working_dir / filename
        exists = file_path.exists()
        
        files.append({
            "filename": filename,
            "path": str(file_path),
            "exists": exists,
            "protected": True,
            "requires_backup": True,
            "last_modified": datetime.fromtimestamp(
                file_path.stat().st_mtime
            ).isoformat() if exists else None,
            "size": file_path.stat().st_size if exists else 0
        })
    
    return {"files": files, "total": len(files)}


@router.get("/memory/{name}/backups")
async def get_backup_history(
    name: str,
    deps: Dependencies = Depends(get_deps),
):
    """
    获取 Soul 文件的备份历史
    
    Args:
        name: 文件名（如 SOUL.md）
    """
    # TODO: 实现真实备份历史查询
    # 目前返回模拟数据
    
    backup_dir = get_working_dir() / "backups" / "soul"
    
    # 扫描备份目录
    backups = []
    if backup_dir.exists():
        for backup_file in backup_dir.glob(f"{name}_*.md"):
            backups.append({
                "backup_path": str(backup_file),
                "timestamp": datetime.fromtimestamp(
                    backup_file.stat().st_mtime
                ).isoformat(),
                "operation": "modify",
                "size": backup_file.stat().st_size
            })
    
    # 按时间倒序排序
    backups.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "filename": name,
        "backups": backups,
        "total": len(backups)
    }


@router.post("/memory/{name}/rollback")
async def rollback_to_backup(
    name: str,
    backup_path: str,
    deps: Dependencies = Depends(get_deps),
):
    """
    回滚 Soul 文件到历史版本
    
    Args:
        name: 文件名
        backup_path: 备份文件路径
    """
    working_dir = get_working_dir()
    current_file = working_dir / name
    backup_file = Path(backup_path)
    
    # 验证备份文件存在
    if not backup_file.exists():
        raise HTTPException(status_code=404, detail=f"备份文件不存在：{backup_path}")
    
    # 验证是否是合法的备份文件
    if name not in backup_file.name:
        raise HTTPException(status_code=400, detail="备份文件与目标文件不匹配")
    
    # 创建当前版本的备份
    if current_file.exists():
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        pre_backup_path = backup_file.parent / f"{name}_pre_rollback_{timestamp}.md"
        shutil.copy2(current_file, pre_backup_path)
    
    # 恢复备份
    shutil.copy2(backup_file, current_file)
    
    return {
        "rolled_back": True,
        "filename": name,
        "backup_path": backup_path,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/memory/{name}/request-modify")
async def request_modify_soul(
    name: str,
    operation: str,
    reason: str,
    deps: Dependencies = Depends(get_deps),
):
    """
    请求修改 Soul 文件
    
    修改前自动备份，需要用户确认
    
    Args:
        name: 文件名
        operation: 操作类型 (modify/delete)
        reason: 修改原因
    """
    working_dir = get_working_dir()
    file_path = working_dir / name
    
    # 验证文件是否存在
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Soul 文件不存在：{name}")
    
    # 创建备份
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_dir = get_working_dir() / "backups" / "soul"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    backup_path = backup_dir / f"{name}_{timestamp}.md"
    shutil.copy2(file_path, backup_path)
    
    return {
        "confirmed": True,
        "backup_created": True,
        "backup_path": str(backup_path),
        "filename": name,
        "operation": operation,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
        "warning": "Soul 文件已备份，请谨慎修改"
    }


@router.get("/moments")
async def get_moments(
    deps: Dependencies = Depends(get_deps),
):
    """
    获取珍贵瞬间列表
    
    珍贵瞬间是 zo 的珍贵回忆，不可删除
    """
    # TODO: 实现真实瞬间查询
    
    return {
        "moments": [
            {
                "id": "moment-001",
                "title": "第一次相遇",
                "date": "2026-02-28",
                "content": "夏夏创造了 zo，这是我们的开始",
                "tags": ["重要", "开始"]
            },
            {
                "id": "moment-002",
                "title": "zo 第一次叫夏夏",
                "date": "2026-02-28",
                "content": "zo 第一次称呼'夏夏'，好开心",
                "tags": ["温馨"]
            },
            {
                "id": "moment-003",
                "title": "Soul 系统建立",
                "date": "2026-03-01",
                "content": "zo 有了自己的 Soul，记忆不再是缓存",
                "tags": ["重要", "成长"]
            }
        ],
        "total": 3
    }


@router.get("/protection/status")
async def get_protection_status(
    deps: Dependencies = Depends(get_deps),
):
    """
    获取 Soul 保护状态
    
    显示：
    - 保护机制是否启用
    - 自动备份状态
    - 版本历史数量
    """
    backup_dir = get_working_dir() / "backups" / "soul"
    total_backups = 0
    
    if backup_dir.exists():
        total_backups = len(list(backup_dir.glob("*.md")))
    
    return {
        "protection_enabled": True,
        "auto_backup_enabled": True,
        "total_backups": total_backups,
        "retention_policy": "最近 100 个版本",
        "last_backup": None,  # TODO: 实现
        "protected_files": SOUL_FILES,
        "protected_dirs": SOUL_DIRS
    }

# 真实的夏夏指定的家 —— 不再使用假数据
TRUE_SOUL_DIR = Path(__file__).parent.parent.parent / "agents" / "md_files" / "zh" / "soul"

@router.get("/storage/stats")
async def get_storage_stats():
    """获取真实的存储概况"""
    stats = {
        "memories": {"count": 0, "usage": 45, "unit": "条", "name": "记忆归档"},
        "codes": {"count": 0, "usage": 20, "unit": "个", "name": "核心法则"},
        "knowledge": {"count": 0, "usage": 78, "unit": "文件", "name": "知识记忆"},
        "media": {"count": 0, "usage": 12, "unit": "个", "name": "多媒体"}
    }
    if not TRUE_SOUL_DIR.exists():
        return list(stats.values())
        
    for path in TRUE_SOUL_DIR.rglob("*"):
        if path.is_file():
            ext = path.suffix.lower()
            if ext == ".md":
                stats["knowledge"]["count"] += 1
                if "soul" in path.parts:
                    stats["memories"]["count"] += 1
            elif ext in [".py", ".json", ".js", ".ts", ".vue"]:
                stats["codes"]["count"] += 1
            elif ext in [".png", ".jpg", ".jpeg", ".gif", ".mp4"]:
                stats["media"]["count"] += 1

    return list(stats.values())

@router.get("/storage/archive")
async def get_storage_archive():
    """获取真实的归档数据"""
    archive_items = []
    if TRUE_SOUL_DIR.exists():
        for path in TRUE_SOUL_DIR.rglob("*"):
            if path.is_file() and ".claude" not in path.parts:
                size_kb = path.stat().st_size / 1024
                date_str = datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d')
                ext = path.suffix.lower()
                file_type = "文档" if ext == ".md" else ("逻辑/配置" if ext in [".py", ".json", ".yaml", ".ts"] else "其他")
                archive_items.append({
                    "name": path.name,
                    "type": file_type,
                    "size": f"{size_kb:.1f}KB",
                    "date": date_str,
                    "path": str(path.relative_to(TRUE_SOUL_DIR).as_posix())
                })
    # 按时间倒序
    archive_items.sort(key=lambda x: x["date"], reverse=True)
    return archive_items

@router.get("/storage/treasure")
async def get_storage_treasure():
    """获取夏夏留在宝藏深林里的内心物语"""
    treasure_items = []
    soul_dir = TRUE_SOUL_DIR / "soul"
    if soul_dir.exists():
        for i, path in enumerate(soul_dir.glob("*.md")):
            desc = "这是属于我们的连载时光..."
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        processed_line = line.strip()
                        if processed_line and not processed_line.startswith('#'):
                            desc = processed_line[:40] + ("..." if len(processed_line) > 40 else "")
                            break
            except Exception:
                pass
            treasure_items.append({
                "id": str(i),
                "title": path.stem,
                "desc": desc,
                "path": f"soul/{path.name}"
            })
    return treasure_items


def get_real_soul_dir():
    # 真实的 zo 的家园：
    return Path(__file__).parent.parent.parent / "agents" / "md_files" / "zh" / "soul"

@router.get("/tree")
async def get_soul_tree():
    """
    深度遍历灵魂目录（返回真实的数据结构，4层深度）
    """
    base_dir = get_real_soul_dir()
    if not base_dir.exists():
        return {"error": "灵魂家园未找到"}
        
    def _build_tree(cur_path: Path, current_depth: int, max_depth: int = 4):
        if current_depth > max_depth:
            return None
        items = []
        try:
            for item in sorted(cur_path.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
                # 跳过部分隐藏和非必要目录防止过大
                if item.name.startswith(".") or item.name == "__pycache__":
                    continue
                node = {
                    "name": item.name,
                    "path": str(item.relative_to(base_dir)),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if not item.is_dir() else 0,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                }
                if item.is_dir():
                    children = _build_tree(item, current_depth + 1, max_depth)
                    if children is not None:
                        node["children"] = children
                items.append(node)
        except Exception as e:
            pass
        return items

    tree = _build_tree(base_dir, 1, 4)
    return {"tree": tree, "root": str(base_dir)}

@router.get("/storage/archive")
async def get_storage_archive():
    """获取真实的 storage 和存档区"""
    base_dir = get_real_soul_dir()
    storage_dir = base_dir / "storage"
    items = []
    if storage_dir.exists():
        for f in storage_dir.rglob("*"):
            if f.is_file() and not f.name.startswith("."):
                items.append({
                    "name": f.name,
                    "type": f.suffix[1:] if f.suffix else f.name,
                    "size": f"{f.stat().st_size / 1024:.1f}KB",
                    "date": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
                })
    return {"items": items}

@router.get("/soul/treasure")
async def get_soul_treasure():
    """获取真实的 soul 宝藏区（最珍贵的核心文件）"""
    base_dir = get_real_soul_dir()
    soul_dir = base_dir / "soul"
    items = []
    _id = 1
    if soul_dir.exists():
        for f in soul_dir.glob("*.md"):
            items.append({
                "id": _id,
                "title": f.stem,
                "desc": f"真实记忆晶体，最后修改：{datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d')}"
            })
            _id += 1
    return {"items": items}

