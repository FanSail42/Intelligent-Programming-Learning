"""Generate per-paper summary files and download guide from 文献清单.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "out_data" / "论文" / "参考文献"
META = ROOT / "文献清单.json"
SUMMARY_DIR = ROOT / "摘要"
LINK_HTML = ROOT / "知网链接清单.html"
README = ROOT / "下载说明.md"


def safe_name(title: str, idx: int) -> str:
    t = re.sub(r'[<>:"/\\\\|?*]', "_", title).strip()
    return f"{idx:02d}_{t[:50]}"


def main() -> None:
    papers = json.loads(META.read_text(encoding="utf-8"))
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    html = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        "<title>慧编学伴开题报告 — 知网文献链接</title>",
        "<style>body{font-family:sans-serif;max-width:960px;margin:24px auto;line-height:1.6}",
        "a{color:#0066cc} li{margin:8px 0}</style></head><body>",
        "<h1>知网文献链接清单（28篇）</h1>",
        "<p>请在校内网/VPN登录知网后，逐条打开链接，点击「PDF下载」保存到 <code>PDF/</code> 目录。</p><ol>",
    ]

    for p in papers:
        idx = p["ref_no"]
        fname = safe_name(p["title"], idx)
        body = [
            f"# [{idx}] {p['title']}",
            "",
            f"**引用格式**：{p['citation_gb7714']}",
            "",
            f"**作者**：{p.get('authors','')}",
            f"**来源**：{p.get('source','')} | **日期**：{p.get('date','')}",
            f"**检索主题**：{p.get('search_query','')}",
            "",
            f"**知网链接**：{p.get('href','')}",
            "",
        ]
        if p.get("abstract"):
            body += ["## 摘要", "", p["abstract"], ""]
        else:
            body += ["## 摘要", "", "（请在知网详情页查看完整摘要）", ""]
        (SUMMARY_DIR / f"{fname}.md").write_text("\n".join(body), encoding="utf-8")
        html.append(
            f"<li><strong>[{idx}]</strong> {p['title']} — "
            f"<a href='{p['href']}' target='_blank'>打开知网</a></li>"
        )

    html += ["</ol></body></html>"]
    LINK_HTML.write_text("\n".join(html), encoding="utf-8")

    pdf_count = len(list((ROOT / "PDF").glob("*.pdf"))) if (ROOT / "PDF").exists() else 0
    readme = f"""# 知网参考文献 — 下载说明

## 已完成内容

| 项目 | 说明 |
|------|------|
| 文献数量 | **28 篇**（GB/T 7714 格式见 `参考文献_GB7714.txt`） |
| 元数据 | `文献清单.json` + `文献导读.md` |
| 摘要笔记 | `摘要/` 目录下 28 个 `.md` 文件 |
| 知网链接 | 打开 `知网链接清单.html` 可逐篇跳转 |
| 已下载 PDF | **{pdf_count}** 篇（见 `PDF/` 目录） |

## 检索主题（中国知网 https://www.cnki.net/）

1. 大语言模型 编程教学
2. 检索增强生成 教育
3. 生成式AI 编程教育
4. 补充：`计算机教育` 期刊相关论文

## 如何批量下载剩余 PDF

知网全文下载需**机构订阅**（当前浏览器已识别机构：阿坝师范学院）或个人付费。

**推荐步骤：**

1. 连接学校 VPN 或在校内网环境；
2. 用浏览器打开本目录下的 **`知网链接清单.html`**；
3. 逐篇点击「PDF下载」，保存到 **`PDF/`** 文件夹（建议按 `[序号]_论文标题.pdf` 命名）；
4. 或使用 [知网研学（E-Study）](https://estudy.cnki.net/)：导入 `参考文献_GB7714.txt` 中的题录，批量下载。

## 文献与论题对应关系（撰写提示）

- **研究背景（政策/痛点）**：可引用 [2][3][7][16][17] 等关于编程教学困境、师资不足、通用 AI 脱离课程语境的论述；
- **LLM 编程教学**： [2][3][5][6][11][12][16][17][18][19][20][21][22][23][24][25][26][27][28]；
- **RAG / 知识库**： [1][8][9][10][13][14]；
- **智能助教 / 学情**： [4][7][15]；
- **在线判题**： [15]。

## 注意事项

- 参考文献**仅标注**于开题报告的「研究背景」和「国内外研究动态」（见撰写说明）；
- 知网 PDF 仅供个人学术研究，请勿传播。
"""
    README.write_text(readme, encoding="utf-8")
    print(f"Generated summaries + guide. PDF count={pdf_count}")


if __name__ == "__main__":
    main()
