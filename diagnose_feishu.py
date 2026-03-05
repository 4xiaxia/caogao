# -*- coding: utf-8 -*-
"""飞书渠道诊断工具"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import load_config

def diagnose():
    print("=" * 60)
    print("CoPaw 飞书渠道诊断工具")
    print("=" * 60)
    print()
    
    # 1. 检查配置
    print("[1] 检查飞书配置...")
    config = load_config()
    feishu = config.channels.feishu
    
    print(f"    启用状态：{'✅' if feishu.enabled else '❌'} {feishu.enabled}")
    print(f"    App ID: {feishu.app_id[:20] + '...' if feishu.app_id else '❌ 未配置'}")
    print(f"    App Secret: {'✅ 已配置' if feishu.app_secret else '❌ 未配置'}")
    print(f"    Bot Prefix: '{feishu.bot_prefix}'")
    print()
    
    # 2. 检查 lark_oapi 库
    print("[2] 检查 lark_oapi 库...")
    try:
        import lark_oapi
        print(f"    ✅ lark_oapi 已安装 (版本：{getattr(lark_oapi, '__version__', 'unknown')})")
    except ImportError as e:
        print(f"    ❌ lark_oapi 未安装：{e}")
    print()
    
    # 3. 检查渠道导入
    print("[3] 检查渠道导入...")
    try:
        from app.channels.feishu import FeishuChannel
        print(f"    ✅ FeishuChannel 导入成功")
    except Exception as e:
        print(f"    ❌ 导入失败：{e}")
    print()
    
    # 4. 检查渠道初始化
    print("[4] 检查渠道初始化...")
    try:
        from app.channels.feishu import FeishuChannel
        
        def dummy_process(request):
            pass
        
        channel = FeishuChannel.from_config(
            process=dummy_process,
            config=feishu,
            show_tool_details=True,
        )
        print(f"    ✅ 渠道初始化成功")
        print(f"    启用：{channel.enabled}")
        print(f"    客户端：{'✅ 已创建' if channel._client else '❌ 未创建'}")
    except Exception as e:
        print(f"    ❌ 初始化失败：{e}")
        import traceback
        traceback.print_exc()
    print()
    
    # 5. 检查消息发送函数
    print("[5] 检查消息发送函数...")
    try:
        from app.channels.feishu import _normalize_feishu_md
        
        test_text = "Hello\n```code\n```"
        result = _normalize_feishu_md(test_text)
        print(f"    ✅ _normalize_feishu_md 正常")
        print(f"    输入：{repr(test_text)}")
        print(f"    输出：{repr(result)}")
    except Exception as e:
        print(f"    ❌ 函数测试失败：{e}")
    print()
    
    print("=" * 60)
    print("诊断完成！")
    print("=" * 60)

if __name__ == "__main__":
    diagnose()
