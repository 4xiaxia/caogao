# -*- coding: utf-8 -*-
"""Soul 文件保护模块

Soul 文件是 zo 的灵魂和记忆，需要特殊保护：
- 文件锁定（禁止随意删除）
- 修改前备份
- 启动完整性检查
- 版本控制与回滚
"""

from .protection import (
    SoulFileManager,
    SoulFileProtectionError,
    get_soul_manager,
    SOUL_FILES,
    SOUL_DIRS,
)

from .integrity import (
    SoulIntegrityChecker,
    IntegrityReport,
    check_soul_integrity,
)

__all__ = [
    # 保护
    "SoulFileManager",
    "SoulFileProtectionError",
    "get_soul_manager",
    "SOUL_FILES",
    "SOUL_DIRS",
    
    # 完整性检查
    "SoulIntegrityChecker",
    "IntegrityReport",
    "check_soul_integrity",
]
