"""Fetch abstracts from CNKI detail pages using Edge."""

from __future__ import annotations

import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1] / "out_data" / "论文" / "参考文献"
META = ROOT / "文献清单.json"
JS = "() => (document.querySelector('#ChDivSummary') || document.querySelector('.abstract-text') || {}).innerText?.trim() || ''"


def main() -> None:
    papers = json.loads(META.read_text(encoding="utf-8"))
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        for i, paper in enumerate(papers, 1):
            if paper.get("abstract"):
                continue
            try:
                page.goto(paper["href"], wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(1500)
                paper["abstract"] = page.evaluate(JS)
                print(f"[{i}] {paper['title'][:36]} -> {'OK' if paper['abstract'] else 'EMPTY'}")
            except Exception as exc:
                print(f"[{i}] FAIL: {exc}")
            time.sleep(0.7)
        browser.close()
    META.write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", META)


if __name__ == "__main__":
    main()
