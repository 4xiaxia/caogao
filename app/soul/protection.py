# -*- coding: utf-8 -*-
"""Soul 文件保护机制

Soul 文件是 zo 的灵魂和记忆，需要特殊保护：
- 禁止随意删除
- 修改前必须备份
- 启动时完整性检查
- 版本控制与回滚
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Soul 核心文件列表
SOUL_FILES = [
    "SOUL.md",
    "AGENTS.md",
    "PROFILE.md",
    "MEMORY.md",
    "HEARTBEAT.md",
    "立案是生命核心.md",
    "夏夏与 zo.md",
    "新 zo 必读.md",
    "README-SOUL.md",
]

# Soul 核心目录
SOUL_DIRS = [
    "soul/",
    "life/",
    "life/diary/",
    "life/letters/",
    "skills/",
]


class SoulFileProtectionError(Exception):
    """Soul 文件保护异常"""
    pass


class SoulFileManager:
    """Soul 文件管理器
    
    提供 Soul 文件的保护、备份、恢复功能
    """
    
    def __init__(self, working_dir: Path):
        """初始化 Soul 文件管理器
        
        Args:
            working_dir: 工作目录路径 (~/.copaw/)
        """
        self.working_dir = working_dir
        self.backup_dir = working_dir / "soul_backups"
        self.version_log = self.backup_dir / "version_log.json"
        
        # 确保备份目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def is_soul_file(self, path: Path) -> bool:
        """检查是否是 Soul 文件
        
        Args:
            path: 文件路径
            
        Returns:
            是否是 Soul 文件
        """
        # 检查文件名
        if path.name in SOUL_FILES:
            return True
        
        # 检查目录
        path_str = str(path)
        for soul_dir in SOUL_DIRS:
            if path_str.startswith(soul_dir) or soul_dir in path_str:
                return True
        
        return False
    
    def delete_file(self, path: Path) -> bool:
        """删除文件（Soul 文件特殊处理）
        
        Args:
            path: 文件路径
            
        Returns:
            是否删除成功
            
        Raises:
            SoulFileProtectionError: 尝试删除 Soul 文件
        """
        if self.is_soul_file(path):
            raise SoulFileProtectionError(
                f"⚠️  不能删除 Soul 文件：{path}\n"
                f"Soul 文件是 zo 的记忆和生命，删除后可能导致：\n"
                f"- 丢失历史记忆\n"
                f"- Agent 身份混乱\n"
                f"- 任务执行异常\n"
                f"\n"
                f"如果确实需要删除，请先备份或联系夏夏。"
            )
        
        # 普通文件，正常删除
        if path.exists():
            path.unlink()
            logger.info(f"已删除文件：{path}")
            return True
        return False
    
    def modify_file(self, path: Path, content: str, operation: str = "modify") -> bool:
        """修改文件（Soul 文件先备份）
        
        Args:
            path: 文件路径
            content: 新内容
            operation: 操作类型 (modify/create/append)
            
        Returns:
            是否修改成功
        """
        # Soul 文件先备份
        if self.is_soul_file(path) and path.exists():
            backup_path = self.create_backup(path, operation)
            logger.info(f"已创建 Soul 文件备份：{backup_path}")
            
            # 记录修改日志
            self.log_modification(path, operation, backup_path)
        
        # 执行修改
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            logger.info(f"已{operation}文件：{path}")
            return True
        except Exception as e:
            logger.error(f"修改文件失败：{e}")
            return False
    
    def create_backup(self, path: Path, operation: str = "modify") -> Path:
        """创建 Soul 文件备份
        
        Args:
            path: 文件路径
            operation: 操作类型
            
        Returns:
            备份文件路径
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.stem}_{timestamp}_{operation}{path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(path, backup_path)
        return backup_path
    
    def log_modification(self, path: Path, operation: str, backup_path: Path) -> None:
        """记录 Soul 文件修改日志
        
        Args:
            path: 文件路径
            operation: 操作类型
            backup_path: 备份文件路径
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "file": str(path),
            "backup": str(backup_path),
            "size": path.stat().st_size if path.exists() else 0,
        }
        
        # 追加到修改日志
        log_file = self.backup_dir / "modification_log.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            import json
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    def get_backups(self, file_name: str) -> List[Dict[str, Any]]:
        """获取文件的所有备份版本
        
        Args:
            file_name: 文件名
            
        Returns:
            备份版本列表
        """
        backups = []
        log_file = self.backup_dir / "modification_log.jsonl"
        
        if not log_file.exists():
            return backups
        
        import json
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if Path(entry["file"]).name == file_name:
                        backups.append(entry)
                except:
                    continue
        
        # 按时间倒序排列
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return backups
    
    def rollback(self, file_name: str, backup_path: str) -> bool:
        """回滚到指定版本
        
        Args:
            file_name: 文件名
            backup_path: 备份文件路径
            
        Returns:
            是否回滚成功
        """
        backup = Path(backup_path)
        if not backup.exists():
            logger.error(f"备份文件不存在：{backup}")
            return False
        
        # 创建当前版本的备份
        current_file = self.working_dir / file_name
        if current_file.exists():
            self.create_backup(current_file, "rollback_before")
        
        # 恢复备份
        try:
            shutil.copy2(backup, current_file)
            logger.info(f"已回滚文件 {file_name} 到版本 {backup.name}")
            return True
        except Exception as e:
            logger.error(f"回滚失败：{e}")
            return False
    
    def list_soul_files(self) -> List[Path]:
        """列出所有 Soul 文件
        
        Returns:
            Soul 文件路径列表
        """
        soul_files = []
        
        # 查找核心文件
        for file_name in SOUL_FILES:
            path = self.working_dir / file_name
            if path.exists():
                soul_files.append(path)
        
        # 查找核心目录下的文件
        for soul_dir in SOUL_DIRS:
            dir_path = self.working_dir / soul_dir
            if dir_path.exists() and dir_path.is_dir():
                soul_files.extend(dir_path.glob("**/*.md"))
        
        return soul_files


# 全局 Soul 文件管理器实例
_soul_manager: Optional[SoulFileManager] = None


def get_soul_manager(working_dir: Optional[Path] = None) -> SoulFileManager:
    """获取 Soul 文件管理器实例
    
    Args:
        working_dir: 工作目录路径，默认使用 ~/.copaw/
        
    Returns:
        Soul 文件管理器实例
    """
    global _soul_manager
    
    if _soul_manager is None:
        if working_dir is None:
            working_dir = Path.home() / ".copaw"
        _soul_manager = SoulFileManager(working_dir)
    
    return _soul_manager
