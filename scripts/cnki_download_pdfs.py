"""Download CNKI PDFs using authenticated session URL (Edge + Playwright)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

LOGIN_URL = (
    "https://www.cnki.net/?uid=WEEvREcwSlJHSldTTEYyT1g4YlhHdkRhcjNrVjlTQjVBUHQyOUV5NTk2ST0="
    "$9A4hF_YAuvQ5obgVAqNKPCYcEjKensW4IQMovwHtwkF4VYPoHbKxJw!!"
)
ROOT = Path(__file__).resolve().parents[1] / "out_data" / "论文" / "参考文献"
PDF_DIR = ROOT / "PDF"
META = ROOT / "文献清单.json"
LOG = ROOT / "下载日志.txt"


def safe_filename(idx: int, title: str) -> str:
    t = re.sub(r'[<>:"/\\\\|?*]', "_", title).strip()
    return f"{idx:02d}_{t[:55]}"


def already_have(idx: int, title: str) -> bool:
    prefix = f"{idx:02d}_"
    for p in PDF_DIR.glob("*.pdf"):
        if p.name.startswith(prefix) and p.stat().st_size > 8000:
            return True
    stem = safe_filename(idx, title)
    target = PDF_DIR / f"{stem}.pdf"
    return target.exists() and target.stat().st_size > 8000


def try_download(page, paper: dict) -> tuple[bool, str]:
    idx = paper["ref_no"]
    title = paper["title"]
    if already_have(idx, title):
        return True, "skipped (exists)"

    target = PDF_DIR / f"{safe_filename(idx, title)}.pdf"
    try:
        page.goto(paper["href"], wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        pdf = page.locator("a#pdfDown, li.btn-dlpdf a, a:has-text('PDF下载')").first
        if pdf.count() == 0:
            return False, "no PDF button"

        with page.expect_download(timeout=45000) as dl_info:
            pdf.click()
        download = dl_info.value
        download.save_as(str(target))

        if target.exists() and target.stat().st_size > 8000:
            return True, f"ok ({target.stat().st_size} bytes)"
        target.unlink(missing_ok=True)
        return False, "empty file"
    except PlaywrightTimeout:
        return False, "timeout"
    except Exception as exc:
        return False, str(exc)[:120]


def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    papers = json.loads(META.read_text(encoding="utf-8"))
    lines = [f"=== CNKI download run {time.strftime('%Y-%m-%d %H:%M:%S')} ==="]

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print("Opening login URL...")
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)

        ok = fail = skip = 0
        for paper in papers:
            idx = paper["ref_no"]
            if already_have(idx, paper["title"]):
                skip += 1
                msg = f"[{idx}] SKIP {paper['title'][:40]}"
                print(msg)
                lines.append(msg)
                continue

            success, detail = try_download(page, paper)
            if success:
                ok += 1
                status = "OK"
            else:
                fail += 1
                status = "FAIL"
            msg = f"[{idx}] {status} {paper['title'][:40]} -> {detail}"
            print(msg)
            lines.append(msg)
            time.sleep(1.5)

        browser.close()

    summary = f"Done: ok={ok}, skip={skip}, fail={fail}, total={len(papers)}"
    print(summary)
    lines.append(summary)
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
