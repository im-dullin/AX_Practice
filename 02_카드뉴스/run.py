#!/usr/bin/env python3
"""
카드뉴스 자동 제작 — 웹 UI 또는 CLI로 URL/마크다운 → 카드 5장 PNG + ZIP

Usage:
  python3 run.py                                # 웹 UI (http://localhost:8765 자동 오픈)
  python3 run.py https://example.com/news       # CLI · URL 모드
  python3 run.py samples/sample_markdown.md     # CLI · 오프라인 모드
"""
import sys
import json
import re
import html as html_lib
import shutil
import asyncio
import subprocess
import threading
import webbrowser
import zipfile
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

ROOT = Path(__file__).parent
PROMPT_FILE = ROOT / "prompts" / "cards.md"
CARD_TPL = ROOT / "templates" / "card.html"
INDEX_TPL = ROOT / "templates" / "index.html"
OUTDIR = ROOT / "output"
OUTDIR.mkdir(exist_ok=True)


# ──────────────────────────────── Core ────────────────────────────────


def crawl_url(url: str) -> str:
    """Firecrawl MCP로 URL 스크랩 → markdown 본문 반환."""
    prompt = (
        f"다음 URL을 firecrawl_scrape 도구로 스크랩하고 *markdown 본문만* "
        f"코드블록·인사말·메타 설명 없이 그대로 출력하세요.\n\nURL: {url}"
    )
    proc = subprocess.run(
        [
            "claude", "-p", prompt,
            "--output-format", "json",
            "--allowedTools", "mcp__firecrawl__firecrawl_scrape",
        ],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "Firecrawl MCP 호출 실패. 다음을 확인하세요:\n"
            "  1. claude mcp list 에 firecrawl이 등록돼 있는가\n"
            "  2. 등록 명령 (터미널, claude 세션 바깥, name을 -e 앞에):\n"
            "     claude mcp add firecrawl -e FIRECRAWL_API_KEY=<key> -- npx -y firecrawl-mcp\n"
            f"\n--- stderr ---\n{proc.stderr}"
        )
    return json.loads(proc.stdout).get("result", "")


def extract_cards(markdown: str, source: str) -> dict:
    """본문 markdown → 카드 5장 JSON."""
    base = PROMPT_FILE.read_text(encoding="utf-8")
    full = f"{base}\n\n[출처] {source}\n[본문 markdown]\n{markdown}"
    proc = subprocess.run(
        ["claude", "-p", full, "--output-format", "json"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude 카드 추출 실패:\n{proc.stderr}")
    raw = json.loads(proc.stdout).get("result", "")
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise RuntimeError(f"JSON 블록 추출 실패:\n{raw[:400]}")
    return json.loads(m.group(0))


def truncate_source(s: str, n: int = 60) -> str:
    return s if len(s) <= n else s[:n] + "…"


def render_card_html(card: dict, n: int, total: int, topic: str, source: str) -> str:
    tpl = CARD_TPL.read_text(encoding="utf-8")
    label = (card.get("label") or "").strip()
    label_html = f'<div class="label">{html_lib.escape(label)}</div>' if label else ""
    return tpl.format(
        kind=card.get("kind", "body"),
        topic=html_lib.escape(topic),
        label_html=label_html,
        headline=html_lib.escape(card.get("headline", "")),
        text=html_lib.escape(card.get("text", "")).replace("\n", "<br>"),
        n_str=f"{n:02d}",
        total=f"{total:02d}",
        source=html_lib.escape(truncate_source(source)),
    )


async def screenshot_cards(html_list: list, stamp: str) -> list:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError("playwright 미설치. pip install playwright && playwright install chromium")

    pngs = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": 1080, "height": 1080},
            device_scale_factor=2,
        )
        for i, html in enumerate(html_list, 1):
            page = await ctx.new_page()
            await page.set_content(html, wait_until="load")
            try:
                await page.wait_for_function(
                    "document.fonts.ready.then(() => true)", timeout=4000
                )
            except Exception:
                pass
            png = OUTDIR / f"{stamp}_{i:02d}.png"
            await page.screenshot(
                path=str(png),
                clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
            )
            await page.close()
            pngs.append(png)
        await browser.close()
    return pngs


def build_zip(pngs: list, stamp: str) -> Path:
    """5장 PNG → ZIP 한 묶음."""
    zip_path = OUTDIR / f"{stamp}_cards.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for png in pngs:
            z.write(png, arcname=png.name)
    return zip_path


def build_index_sheet(cards: list, pngs: list, topic: str, source: str, stamp: str) -> Path:
    """CLI 모드용 정적 미리보기 시트 (웹 UI 안 쓸 때)."""
    tpl = INDEX_TPL.read_text(encoding="utf-8")
    cells = "".join(
        f'<figure>'
        f'<img src="{png.name}" alt="card {i+1}">'
        f'<figcaption>{i+1:02d} · {html_lib.escape((c.get("headline") or "")[:36])}</figcaption>'
        f'</figure>'
        for i, (c, png) in enumerate(zip(cards, pngs))
    )
    out = OUTDIR / f"{stamp}_index.html"
    out.write_text(
        tpl.format(
            topic=html_lib.escape(topic),
            source=html_lib.escape(source),
            cells=cells,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        ),
        encoding="utf-8",
    )
    return out


def process(src: str, log=print) -> dict:
    """URL 또는 파일 경로 → 카드 5장 PNG + ZIP. CLI/웹 양쪽 공용."""
    if src.startswith(("http://", "https://")):
        log(f"🕸  크롤링 (Firecrawl MCP): {src}")
        markdown = crawl_url(src)
        source = src
    else:
        p = Path(src)
        if not p.exists():
            raise FileNotFoundError(f"파일 없음: {p}")
        log(f"📄 마크다운 로드: {p.name}")
        markdown = p.read_text(encoding="utf-8")
        source = p.name
    log(f"   ↳ {len(markdown):,}자")

    log("🤖 핫이슈 분석 + 카드 5장 콘텐츠 생성...")
    data = extract_cards(markdown, source)
    cards = data.get("cards") or []
    topic = data.get("topic") or "Auto Card News"

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log("🎨 카드 HTML 렌더링...")
    html_list = [render_card_html(c, i + 1, len(cards), topic, source) for i, c in enumerate(cards)]

    log("📸 Playwright 스크린샷 (1080×1080 @2x)...")
    pngs = asyncio.run(screenshot_cards(html_list, stamp))

    log("🗜  ZIP 묶음 생성...")
    zip_path = build_zip(pngs, stamp)

    meta = {
        "stamp": stamp,
        "topic": topic,
        "source": source,
        "cards": cards,
        "png_count": len(pngs),
        "zip": zip_path.name,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    (OUTDIR / f"{stamp}_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"✅ 완료: PNG {len(pngs)}장 · ZIP {zip_path.name}")
    return meta


def open_in_browser(path_or_url) -> None:
    target = str(path_or_url)
    if target.startswith("http"):
        webbrowser.open(target)
        return
    p = Path(target).resolve()
    if sys.platform == "darwin" and shutil.which("open"):
        subprocess.run(["open", str(p)], check=False)
        return
    if sys.platform.startswith("win"):
        import os
        os.startfile(str(p))  # type: ignore[attr-defined]
        return
    webbrowser.open("file://" + quote(str(p)))


# ──────────────────────────────── Web UI ────────────────────────────────


def serve_web(port: int = 8765) -> None:
    """Flask 웹 UI — 폼 입력 + 결과 페이지 + ZIP 다운로드."""
    try:
        from flask import Flask, render_template, request, redirect, url_for, send_from_directory
    except ImportError:
        sys.exit("❌ flask 미설치. pip install flask")

    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=None,
    )

    @app.route("/")
    def index():
        return render_template("form.html")

    @app.route("/generate", methods=["POST"])
    def generate():
        src = (request.form.get("source") or "").strip()
        if not src:
            return redirect(url_for("index"))
        try:
            meta = process(src)
        except Exception as e:
            return render_template(
                "form.html",
            ) + f"\n<!-- error: {e} -->", 500
        return redirect(url_for("result", stamp=meta["stamp"]))

    @app.route("/result/<stamp>")
    def result(stamp):
        meta_file = OUTDIR / f"{stamp}_meta.json"
        if not meta_file.exists():
            return "결과 없음", 404
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        return render_template(
            "result.html",
            stamp=stamp,
            topic=meta.get("topic", ""),
            source=meta.get("source", ""),
            cards=meta.get("cards", []),
        )

    @app.route("/output/<path:filename>")
    def output_file(filename):
        return send_from_directory(OUTDIR, filename, as_attachment=filename.endswith(".zip"))

    url = f"http://localhost:{port}"
    print()
    print(f"🌐 카드뉴스 자동 제작 UI — {url}")
    print(f"   브라우저가 자동으로 열립니다. 종료: Ctrl+C")
    print()
    threading.Timer(1.2, lambda: open_in_browser(url)).start()
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


# ──────────────────────────────── Entry ────────────────────────────────


def main() -> None:
    if len(sys.argv) < 2:
        # 웹 UI 모드
        serve_web()
        return

    # CLI 모드
    src = sys.argv[1]
    try:
        meta = process(src)
    except Exception as e:
        sys.exit(f"❌ {e}")

    # CLI 모드에서는 정적 미리보기 시트도 만들어 브라우저로 띄움
    pngs = [OUTDIR / f"{meta['stamp']}_{i+1:02d}.png" for i in range(meta["png_count"])]
    idx = build_index_sheet(meta["cards"], pngs, meta["topic"], meta["source"], meta["stamp"])
    print(f"📋 미리보기 시트: {idx.name}")
    open_in_browser(idx)


if __name__ == "__main__":
    main()
