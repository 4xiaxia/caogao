# -*- coding: utf-8 -*-
"""Factory 小工厂 API - 骨架层"""
from fastapi import APIRouter, Depends
from datetime import datetime
from typing import List, Dict, Any

from ..dependencies import Dependencies, get_deps

router = APIRouter(prefix="/factory", tags=["Factory"])


@router.get("/dashboard")
async def get_factory_dashboard(
    deps: Dependencies = Depends(get_deps),
):
    """
    获取 Factory 完整仪表盘
    
    包含：
    - 生产进度统计
    - Agent 状态
    - 任务看板预览
    """
    # TODO: 实现真实数据查询
    
    return {
        "stats": {
            "total_tasks": 120,
            "completed": 95,
            "in_progress": 20,
            "pending": 5,
            "completion_rate": 79.2,
            "last_updated": datetime.utcnow().isoformat()
        },
        "agents": [
            {
                "id": "agent-001",
                "name": "拆书专员 - 小说类",
                "status": "active",  # active/idle
                "specialty": "小说类书籍拆解",
                "current_task": "TASK-002",
                "completed_tasks": 15,
                "quality_score": 4.8,
                "last_active": datetime.utcnow().isoformat()
            },
            {
                "id": "agent-002",
                "name": "总结生成器",
                "status": "idle",
                "specialty": "文章/书籍总结",
                "current_task": None,
                "completed_tasks": 23,
                "quality_score": 4.6,
                "last_active": "2026-03-02T10:00:00Z"
            },
            {
                "id": "agent-003",
                "name": "质量检查员",
                "status": "active",
                "specialty": "质量审核",
                "current_task": "TASK-005",
                "completed_tasks": 18,
                "quality_score": 4.9,
                "last_active": datetime.utcnow().isoformat()
            }
        ],
        "kanban_preview": {
            "pending": 5,
            "in_progress": 20,
            "review": 3,
            "completed_today": 8
        }
    }


@router.get("/stats")
async def get_factory_stats(
    deps: Dependencies = Depends(get_deps),
):
    """
    获取 Factory 详细统计
    
    包含：
    - 任务统计
    - 完成率
    - 趋势数据
    """
    # TODO: 实现真实统计
    
    return {
        "total_tasks": 120,
        "completed": 95,
        "in_progress": 20,
        "pending": 5,
        "completion_rate": 79.2,
        "avg_completion_time_hours": 4.5,
        "quality_avg": 4.7,
        "trend": {
            "tasks_completed_today": 8,
            "tasks_completed_this_week": 35,
            "tasks_completed_this_month": 95
        }
    }


@router.get("/agents")
async def get_agents(
    status: str = None,
    deps: Dependencies = Depends(get_deps),
):
    """
    获取 Agent 列表
    
    Args:
        status: 筛选状态 (active/idle)
    """
    # TODO: 实现真实 Agent 列表
    
    agents = [
        {
            "id": "agent-001",
            "name": "拆书专员 - 小说类",
            "status": "active",
            "specialty": "小说类书籍拆解",
            "current_task": "TASK-002",
            "performance": 4.8
        },
        {
            "id": "agent-002",
            "name": "总结生成器",
            "status": "idle",
            "specialty": "文章/书籍总结",
            "current_task": None,
            "performance": 4.6
        }
    ]
    
    if status:
        agents = [a for a in agents if a["status"] == status]
    
    return {"agents": agents, "total": len(agents)}


@router.get("/kanban")
async def get_kanban(
    deps: Dependencies = Depends(get_deps),
):
    """
    获取任务看板（按状态分组）
    """
    # TODO: 实现真实任务查询
    
    return {
        "pending": [
            {"id": "TASK-006", "name": "拆书 - 章节 5", "priority": "high"},
            {"id": "TASK-007", "name": "总结 - 文章 A", "priority": "medium"}
        ],
        "in_progress": [
            {"id": "TASK-002", "name": "拆书 - 章节 2", "priority": "high", "agent": "agent-001"},
            {"id": "TASK-003", "name": "校对 - 章节 1", "priority": "medium", "agent": "agent-003"}
        ],
        "review": [
            {"id": "TASK-004", "name": "质检 - 章节 1", "priority": "low"}
        ],
        "completed": [
            {"id": "TASK-001", "name": "拆书 - 章节 1", "completed_at": "2026-03-02T09:15:00Z"}
        ]
    }


@router.get("/alerts")
async def get_alerts(
    deps: Dependencies = Depends(get_deps),
):
    """
    获取告警通知
    
    包含：
    - 逾期任务
    - 质量问题
    - 系统告警
    """
    # TODO: 实现真实告警
    
    return {
        "alerts": [
            {
                "id": "alert-001",
                "type": "overdue",
                "task_id": "TASK-005",
                "message": "逾期 1 天",
                "level": "warning",
                "timestamp": "2026-03-02T08:00:00Z"
            },
            {
                "id": "alert-002",
                "type": "quality_issue",
                "agent_id": "agent-003",
                "message": "质量评分下降到 4.5",
                "level": "info",
                "timestamp": "2026-03-02T07:30:00Z"
            }
        ],
        "total": 2,
        "unread": 1
    }


@router.get("/book-splitter/status")
async def get_book_splitter_status(
    deps: Dependencies = Depends(get_deps),
):
    """
    获取拆书流水线状态
    """
    # TODO: 实现真实流水线状态
    
    return {
        "queue_length": 3,
        "processing": [
            {
                "task_id": "TASK-002",
                "book": "书籍 A",
                "chapter": 2,
                "progress": 60
            }
        ],
        "completed_today": 5,
        "status": "running"
    }
