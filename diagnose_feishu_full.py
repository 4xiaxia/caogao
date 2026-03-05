# -*- coding: utf-8 -*-
"""飞书渠道完整诊断工具"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import load_config

def diagnose_feishu_full():
    print("=" * 70)
    print("CoPaw 飞书渠道完整诊断")
    print("=" * 70)
    print()
    
    # 1. 配置检查
    print("[1] 配置检查")
    config = load_config()
    feishu = config.channels.feishu
    print(f"    启用：{feishu.enabled}")
    print(f"    App ID: {feishu.app_id[:20] + '...' if feishu.app_id else '❌'}")
    print(f"    App Secret: {'✅' if feishu.app_secret else '❌'}")
    print(f"    Bot Prefix: '{feishu.bot_prefix}'")
    print()
    
    # 2. SDK 检查
    print("[2] lark_oapi SDK 检查")
    try:
        import lark_oapi as lark
        print(f"    ✅ SDK 已安装")
        print(f"    ✅ Client: {hasattr(lark, 'Client')}")
        print(f"    ✅ ws.Client: {hasattr(lark, 'ws')}")
    except ImportError as e:
        print(f"    ❌ SDK 未安装：{e}")
    print()
    
    # 3. 渠道类检查
    print("[3] 渠道类检查")
    try:
        from app.channels.feishu import FeishuChannel, FEISHU_AVAILABLE
        print(f"    ✅ FeishuChannel 导入成功")
        print(f"    ✅ FEISHU_AVAILABLE: {FEISHU_AVAILABLE}")
    except Exception as e:
        print(f"    ❌ 导入失败：{e}")
    print()
    
    # 4. 客户端初始化测试
    print("[4] 客户端初始化测试")
    try:
        from app.channels.feishu import FeishuChannel
        
        def dummy_process(request):
            pass
        
        channel = FeishuChannel.from_config(
            process=dummy_process,
            config=feishu,
            show_tool_details=True,
        )
        print(f"    ✅ 渠道实例创建成功")
        print(f"    客户端状态：{'❌ 未创建 (正常，start() 后才会创建)' if not channel._client else '✅ 已创建'}")
        print(f"    WebSocket 客户端：{'❌ 未创建' if not channel._ws_client else '✅ 已创建'}")
    except Exception as e:
        print(f"    ❌ 初始化失败：{e}")
        import traceback
        traceback.print_exc()
    print()
    
    # 5. Access Token 获取测试
    print("[5] Access Token 获取测试")
    try:
        import requests
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": feishu.app_id,
            "app_secret": feishu.app_secret
        }
        
        response = requests.post(url=url, headers=headers, json=data, timeout=5)
        res = response.json()
        
        if res.get("code") == 0:
            token = res.get("tenant_access_token")
            print(f"    ✅ Token 获取成功：{token[:20]}...")
        else:
            print(f"    ❌ Token 获取失败：code={res.get('code')}, msg={res.get('msg')}")
    except Exception as e:
        print(f"    ❌ 测试失败：{e}")
    print()
    
    # 6. 消息发送测试（模拟）
    print("[6] 消息发送逻辑检查")
    try:
        from app.channels.feishu import FeishuChannel
        
        def dummy_process(request):
            pass
        
        channel = FeishuChannel.from_config(
            process=dummy_process,
            config=feishu,
            show_tool_details=True,
        )
        
        # 检查发送方法是否存在
        print(f"    ✅ _send_message_sync: {hasattr(channel, '_send_message_sync')}")
        print(f"    ✅ _send_text: {hasattr(channel, '_send_text')}")
        print(f"    ✅ send_content_parts: {hasattr(channel, 'send_content_parts')}")
        print(f"    ✅ send: {hasattr(channel, 'send')}")
        
        # 检查 SDK 客户端方法
        if channel._client:
            print(f"    ✅ SDK 客户端可用")
        else:
            print(f"    ⚠️  SDK 客户端未创建（需要调用 start()）")
    except Exception as e:
        print(f"    ❌ 检查失败：{e}")
    print()
    
    print("=" * 70)
    print("诊断完成！")
    print("=" * 70)
    print()
    print("💡 提示：")
    print("1. 如果客户端未创建，请确保调用了 channel.start()")
    print("2. 如果 Token 获取失败，请检查 App ID 和 App Secret")
    print("3. 如果消息发送失败，请查看后端控制台的详细错误日志")

if __name__ == "__main__":
    diagnose_feishu_full()
