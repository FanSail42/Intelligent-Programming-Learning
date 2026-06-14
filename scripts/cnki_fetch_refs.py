"""Batch search CNKI and save reference metadata + attempt PDF download."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

OUT_DIR = Path(__file__).resolve().parents[1] / "out_data" / "论文" / "参考文献"
PDF_DIR = OUT_DIR / "PDF"
META_FILE = OUT_DIR / "文献清单.json"
BIB_FILE = OUT_DIR / "参考文献_GB7714.txt"
README_FILE = OUT_DIR / "下载说明.md"

SEARCH_QUERIES = [
    "大语言模型 编程教学",
    "检索增强生成 教育",
    "生成式AI 编程教育",
    "智能编程 助教",
    "学习分析 编程",
    "ChatGPT 程序设计",
    "在线判题 智能辅导",
    "教育大模型 个性化学习",
    "RAG 教学 知识库",
    "代码讲解 人工智能",
]

EXTRACT_JS = """
() => {
  const rows = Array.from(document.querySelectorAll('table.result-table-list tbody tr'));
  return rows.map(tr => {
    const a = tr.querySelector('a.fz14, a[href*="kcms2"]');
    if (!a) return null;
    const authors = tr.querySelector('.author')?.innerText?.trim() || '';
    const source = tr.querySelector('.source')?.innerText?.trim() || '';
    const date = tr.querySelector('.date')?.innerText?.trim() || '';
    return { title: a.innerText.trim(), href: a.href, authors, source, date };
  }).filter(Boolean);
}
"""

DETAIL_JS = """
() => {
  const abs = document.querySelector('#ChDivSummary, .abstract-text, .abstract')?.innerText?.trim() || '';
  const kw = document.querySelector('.keywords')?.innerText?.trim() || '';
  const doi = document.querySelector('a[href*="doi.org"]')?.innerText?.trim() || '';
  const cite = document.querySelector('.break, .wx-tit')?.innerText?.trim() || '';
  return { abstract: abs, keywords: kw, doi, cite };
}
"""


def safe_filename(title: str, max_len: int = 80) -> str:
    name = re.sub(r'[<>:"/\\\\|?*]', "_", title).strip()
    return name[:max_len] or "paper"


def search_cnki(page, query: str, max_pages: int = 2) -> list[dict]:
    url = f"https://kns.cnki.net/kns8s/defaultresult/index?korder=&kw={quote(query)}"
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)
    results: list[dict] = []
    for _ in range(max_pages):
        batch = page.evaluate(EXTRACT_JS)
        for item in batch:
            item["search_query"] = query
            results.append(item)
        next_btn = page.locator("a#PageNext, a:has-text('下一页')").first
        if next_btn.count() == 0 or not next_btn.is_visible():
            break
        cls = next_btn.get_attribute("class") or ""
        if "disabled" in cls:
            break
        next_btn.click()
        page.wait_for_timeout(2000)
    return results


def enrich_detail(page, paper: dict) -> dict:
    try:
        page.goto(paper["href"], wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(1500)
        detail = page.evaluate(DETAIL_JS)
        paper.update(detail)
    except PlaywrightTimeout:
        paper.setdefault("abstract", "")
    return paper


def try_download_pdf(page, paper: dict, pdf_dir: Path) -> str | None:
    fname = safe_filename(paper["title"]) + ".pdf"
    target = pdf_dir / fname
    if target.exists() and target.stat().st_size > 5000:
        return str(target.relative_to(OUT_DIR))
    try:
        page.goto(paper["href"], wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(1200)
        pdf_link = page.locator(
            "a#pdfDown, a:has-text('PDF下载'), a:has-text('PDF'), li.btn-dlpdf a"
        ).first
        if pdf_link.count() == 0:
            return None
        with page.expect_download(timeout=30000) as dl_info:
            pdf_link.click()
        download = dl_info.value
        download.save_as(str(target))
        if target.exists() and target.stat().st_size > 5000:
            return str(target.relative_to(OUT_DIR))
        target.unlink(missing_ok=True)
    except Exception:
        return None
    return None


def format_gb7714(p: dict, idx: int) -> str:
    authors = p.get("authors", "").replace(";", "，").replace(",", "，")
    source = p.get("source", "")
    date = p.get("date", "")
    year = date[:4] if date else "n.d."
    title = p.get("title", "")
    return f"[{idx}] {authors}. {title}[J]. {source}, {year}."


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    all_papers: dict[str, dict] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        for q in SEARCH_QUERIES:
            print(f"Searching: {q}")
            try:
                items = search_cnki(page, q, max_pages=2)
            except Exception as exc:
                print(f"  search failed: {exc}")
                continue
            for item in items:
                key = item["title"].strip()
                if key and key not in all_papers:
                    all_papers[key] = item
            print(f"  cumulative unique: {len(all_papers)}")
            if len(all_papers) >= 35:
                break
            time.sleep(1)

        selected = list(all_papers.values())[:30]
        print(f"Enriching {len(selected)} papers...")
        for i, paper in enumerate(selected, 1):
            enrich_detail(page, paper)
            print(f"  [{i}/{len(selected)}] {paper['title'][:40]}...")
            time.sleep(0.8)

        downloaded = 0
        print("Attempting PDF downloads...")
        for i, paper in enumerate(selected, 1):
            path = try_download_pdf(page, paper, PDF_DIR)
            if path:
                paper["pdf_path"] = path
                downloaded += 1
                print(f"  downloaded: {paper['title'][:35]}...")
            else:
                paper["pdf_path"] = None
            time.sleep(1.2)

        browser.close()

    for i, paper in enumerate(selected, 1):
        paper["ref_no"] = i
        paper["citation_gb7714"] = format_gb7714(paper, i)

    META_FILE.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")
    BIB_FILE.write_text("\n".join(p["citation_gb7714"] for p in selected) + "\n", encoding="utf-8")

    readme = f"""# 知网参考文献下载说明

- 检索时间：{time.strftime('%Y-%m-%d %H:%M')}
- 检索主题：慧编学伴开题报告（LLM/RAG/编程教学/学习分析等）
- 文献总数：**{len(selected)}** 篇
- PDF 成功下载：**{downloaded}** 篇（存放于 `PDF/` 子目录）

## 使用说明

1. `参考文献_GB7714.txt`：可直接粘贴到开题报告「研究背景」「国内外研究动态」的参考文献列表。
2. `文献清单.json`：含标题、作者、来源、摘要、知网链接等完整元数据。
3. 未下载 PDF 的条目请通过 `href` 链接，在校园网/VPN 登录知网后手动下载。

## 检索式

{chr(10).join(f'- {q}' for q in SEARCH_QUERIES)}

## 下载限制说明

知网全文下载通常需要**机构订阅**或**个人付费**。本脚本在可访问权限范围内自动尝试 PDF 下载；若无权限，仍会保留题录与摘要供撰写开题报告引用。
"""
    README_FILE.write_text(readme, encoding="utf-8")
    print(f"Done. papers={len(selected)} pdf={downloaded}")


if __name__ == "__main__":
    main()
