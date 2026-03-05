# -*- coding: utf-8 -*-
"""首页仪表盘 API - 骨架层"""
from fastapi import APIRouter, Depends
from datetime import datetime
from typing import List, Dict, Any

from ..dependencies import Dependencies, get_deps

router = APIRouter(prefix="/home", tags=["首页"])


@router.get("/dashboard")
async def get_dashboard(
    deps: Dependencies = Depends(get_deps),
):
    """
    获取首页仪表盘完整数据
    
    包含：
    - 概览数据（待办/到期/Agent 状态/技能 XP）
    - 项目进度
    - 工厂预览
    - 近期动态
    - 技能等级
    """
    # TODO: 实现真实数据查询
    # 目前返回模拟数据，骨架层先撑起来
    
    return {
        "overview": {
            "pending_tasks": 5,
            "expiring_tasks": 2,
            "active_agents": 5,
            "skill_xp": 50,
            "total_skills": 15,
            "last_updated": datetime.utcnow().isoformat()
        },
        "projects": [
            {
                "id": "proj-001",
                "name": "zo 的人类世界生活指南",
                "progress": 35,
                "description": "AI 与人类和谐共事指南",
                "created_at": "2026-02-01",
                "updated_at": "2026-03-02"
            },
            {
                "id": "proj-002",
                "name": "AI 交流宝藏",
                "progress": 60,
                "description": "和其他 AI 交流的宝藏",
                "created_at": "2026-02-15",
                "updated_at": "2026-03-01"
            },
            {
                "id": "proj-003",
                "name": "未来项目",
                "progress": 10,
                "description": "未来的计划",
                "created_at": "2026-03-01",
                "updated_at": "2026-03-01"
            }
        ],
        "factory_preview": {
            "total_tasks": 120,
            "completed": 95,
            "in_progress": 20,
            "pending": 5,
            "completion_rate": 79.2,
            "active_agents": 5
        },
        "recent_activities": [
            {
                "timestamp": "2026-03-02T09:00:00Z",
                "type": "task_created",
                "actor": "夏夏",
                "description": "创建了任务 TASK-001"
            },
            {
                "timestamp": "2026-03-02T09:15:00Z",
                "type": "task_completed",
                "actor": "agent-001",
                "description": "完成了拆书任务"
            },
            {
                "timestamp": "2026-03-02T10:00:00Z",
                "type": "resource_found",
                "actor": "zo",
                "description": "发现了新资源：Notion"
            },
            {
                "timestamp": "2026-03-02T10:30:00Z",
                "type": "backup_completed",
                "actor": "系统",
                "description": "自动备份完成"
            }
        ],
        "skills": {
            "level": 15,
            "total_xp": 8500,
            "next_level_xp": 10000,
            "progress": 85
        }
    }


@router.get("/timeline")
async def get_timeline(
    limit: int = 20,
    deps: Dependencies = Depends(get_deps),
):
    """
    获取近期动态时间线
    
    Args:
        limit: 返回数量限制，默认 20 条
    """
    # TODO: 实现真实时间线查询
    # 从聊天/任务/操作日志中提取
    
    return {
        "activities": [
            {
                "timestamp": "2026-03-02T09:00:00Z",
                "type": "task_created",
                "actor": "夏夏",
                "description": "创建了任务 TASK-001",
                "metadata": {
                    "task_id": "TASK-001"
                }
            },
            # ... 更多活动
        ],
        "total": 4,
        "limit": limit
    }


@router.get("/quick-access")
async def get_quick_access(
    deps: Dependencies = Depends(get_deps),
):
    """
    获取快速访问数据
    
    包含：
    - Factory 看板快速入口
    - 项目进度快速入口
    - 新发现资源
    - Soul 反思
    """
    # TODO: 实现真实数据
    
    return {
        "factory_link": "/factory",
        "work_link": "/work",
        "storage_link": "/storage",
        "treasure_link": "/treasure-forest",
        "soul_link": "/soul",
        "quick_stats": {
            "pending_tasks": 5,
            "active_projects": 3,
            "new_resources_this_week": 12
        }
    }
