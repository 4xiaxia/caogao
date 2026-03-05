import re
from pathlib import Path

root = Path(__file__).parent / "说明文档"
out = root / "00A-项目文档核心信息提炼表.md"
keywords = {
    "项目目标": [r"目标", r"愿景", r"scope", r"目的", r"milestone"],
    "已实现功能": [r"已实现", r"完成", r"implemented", r"done", r"上线"],
    "待开发需求": [r"待开发", r"todo", r"backlog", r"未完成", r"下一步", r"计划"],
    "已知问题": [r"问题", r"bug", r"风险", r"缺陷", r"故障", r"瓶颈"],
    "版本依赖": [r"版本", r"依赖", r"requirements", r"package", r"python", r"node"],
    "核心API/路由": [r"api", r"路由", r"endpoint", r"/", r"fastapi", r"router"],
    "前端视觉优化": [r"前端", r"视觉", r"ui", r"ux", r"设计", r"主题", r"马卡龙"],
    "API对接要求": [r"对接", r"接口", r"联调", r"请求", r"返回"],
    "技术栈限制": [r"技术栈", r"限制", r"约束", r"必须", r"禁止"],
}

files = sorted([p for p in root.glob("*.md") if p.is_file()])
rows = []
ambiguous = []

for p in files:
    txt = p.read_text(encoding="utf-8", errors="ignore")
    lines = txt.splitlines()
    heads = [ln.strip() for ln in lines if ln.strip().startswith("#")][:12]
    hit = {k: 0 for k in keywords}
    for ln in lines:
        for k, pats in keywords.items():
            if any(re.search(pat, ln, flags=re.I) for pat in pats):
                hit[k] += 1
    rows.append((p.name, len(lines), heads, hit))

    if any(x in txt for x in ["TODO", "待补", "待确认", "待补充", "?", "待定", "后续确认"]):
        ambiguous.append(p.name)

rows_sorted = sorted(
    rows,
    key=lambda r: (
        r[3]["项目目标"] + r[3]["核心API/路由"] + r[3]["前端视觉优化"] + r[3]["待开发需求"],
        r[1],
    ),
    reverse=True,
)
selected = rows_sorted[:20]

md = []
md.append("# 项目文档核心信息提炼表\n")
md.append("## 范围与方法")
md.append("- 扫描范围：说明文档/*.md 全量文件")
md.append(f"- 文件总数：{len(files)}")
md.append("- 维度：项目目标 / 已实现功能 / 待开发需求 / 已知问题 / 版本依赖 / 核心API路由")

md.append("\n## 高优先级文档（按命中度排序）")
md.append("| 文档 | 行数 | 项目目标 | 已实现功能 | 待开发需求 | 已知问题 | 版本依赖 | 核心API/路由 | 前端视觉优化 | API对接要求 | 技术栈限制 |")
md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for name, n, heads, h in selected:
    md.append(
        f"| {name} | {n} | {h['项目目标']} | {h['已实现功能']} | {h['待开发需求']} | {h['已知问题']} | {h['版本依赖']} | {h['核心API/路由']} | {h['前端视觉优化']} | {h['API对接要求']} | {h['技术栈限制']} |"
    )

md.append("\n## 关键章节摘录（Top20 文档标题）")
for name, n, heads, h in selected:
    md.append(f"\n### {name}")
    if heads:
        for hd in heads[:8]:
            md.append(f"- {hd}")
    else:
        md.append("- （无标题，建议补充结构）")

md.append("\n## 疑问与模糊项（待代码扫描逆向验证）")
if ambiguous:
    for f in sorted(set(ambiguous)):
        md.append(f"- {f}")
else:
    md.append("- 暂未检出显式待确认词")

md.append("\n## 下一步执行建议")
md.append("1. 进入四层目录扫描，建立模块-功能-文件映射")
md.append("2. 对 /api/spots、配置、前端路由做三维映射")
md.append("3. 回填模糊项，形成可执行开发基线")

out.write_text("\n".join(md), encoding="utf-8")
print(out)
