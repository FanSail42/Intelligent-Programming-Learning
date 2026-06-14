"""Resolve and download remaining failed papers."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

LOGIN_URL = (
    "https://www.cnki.net/?uid=WEEvREcwSlJHSldTTEYyT1g4YlhHdkRhcjNrVjlTQjVBUHQyOUV5NTk2ST0="
    "$9A4hF_YAuvQ5obgVAqNKPCYcEjKensW4IQMovwHtwkF4VYPoHbKxJw!!"
)
ROOT = Path(__file__).resolve().parents[1] / "out_data" / "论文" / "参考文献"
PDF_DIR = ROOT / "PDF"
META = ROOT / "文献清单.json"
RETRY_NOS = [1, 10, 13, 25]

LINK_SEL = 'table.result-table-list tbody tr a[href*="kcms2"]'


def safe_filename(idx: int, title: str) -> str:
    t = re.sub(r'[<>:"/\\\\|?*]', "_", title).strip()
    return f"{idx:02d}_{t[:55]}"


def resolve_link(page, title: str) -> str:
    page.goto(
        f"https://kns.cnki.net/kns8s/defaultresult/index?kw={quote(title)}",
        wait_until="domcontentloaded",
        timeout=60000,
    )
    page.wait_for_selector(LINK_SEL, timeout=20000)
    return page.eval_on_selector(LINK_SEL, "el => el.href")


def download(page, href: str, target: Path) -> tuple[bool, str]:
    page.goto(href, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)
    for sel in ["a#pdfDown", "li.btn-dlpdf a", "a:has-text('PDF下载')", "a:has-text('CAJ下载')"]:
        loc = page.locator(sel).first
        if loc.count() == 0:
            continue
        try:
            with page.expect_download(timeout=50000) as dl_info:
                loc.click()
            dl_info.value.save_as(str(target))
            if target.exists() and target.stat().st_size > 8000:
                return True, sel
            target.unlink(missing_ok=True)
        except Exception:
            continue
    return False, "no button"


def main() -> None:
    papers = json.loads(META.read_text(encoding="utf-8"))
    by_no = {p["ref_no"]: p for p in papers}

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False)
        page = browser.new_page(accept_downloads=True)
        page.goto(LOGIN_URL, timeout=60000)
        page.wait_for_timeout(3500)

        for no in RETRY_NOS:
            paper = by_no[no]
            target = PDF_DIR / f"{safe_filename(no, paper['title'])}.pdf"
            if target.exists() and target.stat().st_size > 8000:
                print(f"[{no}] skip exists")
                continue

            href = paper.get("href", "")
            if "jyjs.cbpt.cnki.net" in href or not href.startswith("https://kns.cnki.net"):
                try:
                    href = resolve_link(page, paper["title"])
                    paper["href"] = href
                    print(f"[{no}] resolved link")
                except Exception as exc:
                    print(f"[{no}] resolve fail: {exc}")
                    continue

            ok, detail = download(page, href, target)
            print(f"[{no}] {'OK' if ok else 'FAIL'} via {detail}")
            time.sleep(1.2)

        browser.close()

    META.write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
