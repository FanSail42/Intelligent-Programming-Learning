"""Merge CNKI search batches, pick top references, write bibliography files."""

from __future__ import annotations

import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "out_data" / "论文" / "参考文献"
RAW = Path(__file__).resolve().parent / "cnki_raw_batches.json"

# Priority keywords for thesis topic ranking
PRIORITY = [
    "大语言模型", "LLM", "生成式", "RAG", "检索增强", "编程", "程序设计",
    "助教", "智能体", "学习分析", "在线判题", "OJ", "代码", "Python",
    "教育", "课程", "实验", "知识库", "向量", "ChatGPT",
]

EXTRA_PAPERS = [
    {
        "title": "大模型时代计算机程序设计类课程教学模式探索",
        "authors": "王聪;万聪",
        "source": "计算机教育",
        "date": "2025-04-10",
        "search_query": "补充-计算机教育",
        "href": "https://jyjs.cbpt.cnki.net/portal/journal/portal/client/paper/1380e68db9623ee3297e25c0c9a14bf6",
        "abstract": "针对大语言模型给程序设计工作带来的巨大影响，分析大模型的程序设计能力及其给程序设计类课程带来的挑战，提出将大语言模型融入程序设计类课程的教学路径。",
    },
    {
        "title": "生成式AI赋能计算机编程教学的实践创新与效果评估",
        "authors": "兰丽娜;杨仕昌;刘瑞芳",
        "source": "计算机教育",
        "date": "2026-04-10",
        "search_query": "补充-计算机教育",
        "href": "https://jyjs.cbpt.cnki.net/portal/journal/portal/client/paper/7e5ecab89c1ac280be3995f1e2001e6d",
        "abstract": "提出融合生成式AI的智能编程训练系统AIOJ，通过对照实验说明其在编程能力、学习投入度与批判性思维方面的影响。",
    },
    {
        "title": "基于大语言模型的C语言程序设计课程教学改革",
        "authors": "杨晓贤;张凯淇;石林祥",
        "source": "计算机教育",
        "date": "2025-12-06",
        "search_query": "补充-计算机教育",
        "href": "https://jyjs.cbpt.cnki.net/portal/journal/portal/client/paper/424da398dd1ddba5b08d9368ee8fde7a",
        "abstract": "提出基于大语言模型辅助教学的“AI+教师”双轨制教学模式，依托AI助教实现智能生成、即时响应与个性化辅导。",
    },
    {
        "title": "基于检索增强生成的计算机实验指导平台设计与实践",
        "authors": "潘耀宗;刘凯;于柯远",
        "source": "实验技术与管理",
        "date": "2025-04-27",
        "search_query": "补充-实验平台",
        "href": "https://www.sciopen.com/local/article_pdf/10.16791/j.cnki.sjg.2025.04.027.pdf",
        "abstract": "结合大语言模型检索增强生成技术设计计算机实验指导平台，通过Prompt模板与知识检索提升实验效率与效果。",
        "pdf_url": "https://www.sciopen.com/local/article_pdf/10.16791/j.cnki.sjg.2025.04.027.pdf",
    },
]


def score(p: dict) -> int:
    text = f"{p.get('title','')} {p.get('source','')} {p.get('search_query','')}"
    s = 0
    for i, kw in enumerate(PRIORITY):
        if kw.lower() in text.lower():
            s += max(1, 20 - i)
    if p.get("source") in {"计算机教育", "电化教育研究", "中国电化教育", "实验室研究与探索", "实验技术与管理"}:
        s += 8
    if "医学" in text or "化学" in text or "民法" in text or "肿瘤" in text or "历史学科" in text:
        s -= 15
    return s


def format_gb7714(p: dict, idx: int) -> str:
    authors = p.get("authors", "").replace(";", "，").replace(",", "，")
    year = (p.get("date") or "")[:4] or "n.d."
    return f"[{idx}] {authors}. {p.get('title','')}[J]. {p.get('source','')}, {year}."


def main() -> None:
    batches = json.loads(RAW.read_text(encoding="utf-8"))
    merged: dict[str, dict] = {}
    for batch in batches:
        for p in batch:
            t = p["title"].strip()
            if t and t not in merged:
                merged[t] = p
    for p in EXTRA_PAPERS:
        merged[p["title"]] = p

    ranked = sorted(merged.values(), key=score, reverse=True)
    selected = ranked[:28]

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "PDF").mkdir(exist_ok=True)

    for i, p in enumerate(selected, 1):
        p["ref_no"] = i
        p["citation_gb7714"] = format_gb7714(p, i)
        p.setdefault("abstract", "")

    (OUT / "文献清单.json").write_text(
        json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "参考文献_GB7714.txt").write_text(
        "\n".join(p["citation_gb7714"] for p in selected) + "\n", encoding="utf-8"
    )

    md_lines = [
        "# 慧编学伴开题报告 — 知网参考文献清单",
        "",
        f"共 **{len(selected)}** 篇，检索主题涵盖：大语言模型编程教学、RAG教育应用、生成式AI编程教育等。",
        "",
        "## 文献目录",
        "",
    ]
    for p in selected:
        md_lines += [
            f"### [{p['ref_no']}] {p['title']}",
            "",
            f"- **作者**：{p.get('authors','')}",
            f"- **来源**：{p.get('source','')}（{p.get('date','')[:10]}）",
            f"- **检索式**：{p.get('search_query','')}",
            f"- **知网链接**：{p.get('href','')}",
        ]
        if p.get("abstract"):
            md_lines.append(f"- **摘要**：{p['abstract']}")
        md_lines.append("")

    (OUT / "文献导读.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {len(selected)} references to {OUT}")


if __name__ == "__main__":
    main()
