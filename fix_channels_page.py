# -*- coding: utf-8 -*-
import re

file_path = 'console/src/pages/ChannelsPage.vue'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 bot_prefix 显示
content = re.sub(r'前缀：\{\{ cfg\.bot_prefix \|\| \'\[BOT\]\' \}\}', '{{ getChannelDesc(name) }}', content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ 已修复所有 bot_prefix 引用')

# 验证
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    print(f'验证：bot_prefix 出现次数：{content.count("bot_prefix")}')
    print(f'验证：getChannelDesc 出现次数：{content.count("getChannelDesc")}')
