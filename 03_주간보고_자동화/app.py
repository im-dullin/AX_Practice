#!/usr/bin/env python3
"""
주간보고 자동 생성 웹앱

http://localhost:5000 → Notion 페이지 URL 입력 → HTML 주간 보고서

흐름:
  Notion 페이지 fetch → 일별 토글/H2 추출 → 이번 주만 필터
  → claude -p로 BEFORE/PROGRESS/NEXT/RISK 구조화 → HTML 렌더링
"""
import json
import os
import re
import subprocess
import sys
import webbrowser
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request

# Windows 콘솔 한글·이모지 깨짐 방지
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Windows에서는 claude가 claude.cmd로 등록 → subprocess 호출에 shell=True 필요
_USE_SHELL = sys.platform.startswith("win")

load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
DATE_RE = re.compile(r"^\s*(\d{4})[-./](\d{1,2})[-./](\d{1,2})")
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
PROMPT_TEMPLATE = (ROOT / "prompts" / "structure.md").read_text(encoding="utf-8")

app = Flask(__name__)


# ───────── Notion API ─────────

def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def extract_page_id(url: str) -> str:
    """URL 끝에서 32자 hex 페이지 ID 추출, dash 형식으로 포맷."""
    raw = re.sub(r"[^0-9a-f]", "", url.lower().split("?")[0])
    m = re.search(r"([0-9a-f]{32})", raw)
    if not m:
        raise ValueError(f"페이지 ID를 URL에서 추출할 수 없습니다: {url}")
    h = m.group(1)
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def fetch_blocks(block_id: str) -> list:
    """블록의 모든 자식 블록을 페이지네이션으로 수집."""
    results = []
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        resp = requests.get(
            f"{NOTION_API}/blocks/{block_id}/children",
            headers=notion_headers(),
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return results


def block_text(block: dict) -> str:
    btype = block.get("type")
    if not btype:
        return ""
    rich = block.get(btype, {}).get("rich_text", [])
    return "".join(r.get("plain_text", "") for r in rich)


# ───────── 메모 추출 ─────────

def parse_date(text: str):
    m = DATE_RE.match(text)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def week_range(ref: date):
    monday = ref - timedelta(days=ref.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def collect_block_lines(block: dict, indent: int = 0, max_depth: int = 4) -> list:
    """블록 하나에서 텍스트 라인들을 들여쓰기 포함 재귀 수집.

    paragraph 안의 paragraph, 토글 안의 토글, 표(table → table_row), 리스트, 체크박스,
    quote, callout 등 노션의 블록 트리를 깊이 우선으로 평탄화한다.
    """
    lines = []
    btype = block.get("type")
    pad = "  " * indent

    if btype == "table":
        if block.get("has_children"):
            for row in fetch_blocks(block["id"]):
                cells = row.get("table_row", {}).get("cells", []) or []
                row_text = " | ".join(
                    "".join(rt.get("plain_text", "") for rt in cell).strip()
                    for cell in cells
                )
                if row_text.strip(" |"):
                    lines.append(f"{pad}| {row_text} |")
        return lines

    if btype in ("divider", "image", "file", "video", "audio", "embed", "bookmark"):
        return lines

    if btype == "child_page":
        title = block.get("child_page", {}).get("title", "")
        if title:
            lines.append(f"{pad}📄 {title}")
        return lines

    text = block_text(block).strip()

    prefix = ""
    if btype == "bulleted_list_item":
        prefix = "- "
    elif btype == "numbered_list_item":
        prefix = "1. "
    elif btype == "to_do":
        checked = block.get("to_do", {}).get("checked", False)
        prefix = "[x] " if checked else "[ ] "
    elif btype == "quote":
        prefix = "> "
    elif btype == "callout":
        emoji = (block.get("callout", {}).get("icon") or {}).get("emoji", "💡")
        prefix = f"{emoji} "
    elif btype == "heading_1":
        prefix = "# "
    elif btype == "heading_2":
        prefix = "## "
    elif btype == "heading_3":
        prefix = "### "
    elif btype == "toggle":
        prefix = "▸ "

    if text:
        lines.append(f"{pad}{prefix}{text}")

    if max_depth > 0 and block.get("has_children"):
        for c in fetch_blocks(block["id"]):
            lines.extend(collect_block_lines(c, indent + 1, max_depth - 1))

    return lines


def collect_week_memos(page_id: str, ref: date):
    monday, sunday = week_range(ref)
    top_blocks = fetch_blocks(page_id)
    memos = []
    other_weeks = []  # 매칭은 됐지만 이번 주 아닌 날짜들 (UX 안내용)
    for blk in top_blocks:
        btype = blk.get("type")
        if btype not in ("toggle", "heading_2"):
            continue
        text = block_text(blk).strip()
        if "주간 요약 아카이브" in text or text.startswith("📚") or text.startswith("📊"):
            continue
        d = parse_date(text)
        if not d:
            continue
        if not (monday <= d <= sunday):
            other_weeks.append(d)
            continue
        child_lines = []
        if blk.get("has_children"):
            for c in fetch_blocks(blk["id"]):
                child_lines.extend(collect_block_lines(c, indent=0, max_depth=4))
        memos.append({
            "date": d.isoformat(),
            "weekday": WEEKDAYS[d.weekday()],
            "header": text,
            "body": "\n".join(child_lines),
        })
    memos.sort(key=lambda m: m["date"])
    return memos, monday, sunday, other_weeks


# ───────── 구조화 (claude -p) ─────────

def structure_with_claude(memos: list, monday: date, sunday: date) -> dict:
    week_num = monday.isocalendar().week
    memo_text = "\n\n".join(
        f"### {m['date']} ({m['weekday']}) - {m['header']}\n{m['body']}"
        for m in memos
    )
    prompt = PROMPT_TEMPLATE.format(
        week_num=week_num,
        monday=monday.isoformat(),
        sunday=sunday.isoformat(),
        memos=memo_text,
    )
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=180,
        shell=_USE_SHELL,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude -p 실패: {result.stderr or result.stdout}")
    content = result.stdout
    # ```json ... ``` 또는 첫 JSON 객체 추출
    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content)
    if fenced:
        return json.loads(fenced.group(1))
    bare = re.search(r"\{[\s\S]*\}", content)
    if not bare:
        raise RuntimeError(f"Claude 응답에서 JSON을 찾을 수 없음:\n{content[:500]}")
    return json.loads(bare.group(0))


# ───────── 라우팅 ─────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    url = request.form.get("url", "").strip()
    ref_str = request.form.get("ref_date", "").strip()
    if not url:
        return render_template("index.html", error="URL을 입력해주세요"), 400
    try:
        ref = date.fromisoformat(ref_str) if ref_str else date.today()
        page_id = extract_page_id(url)
        memos, monday, sunday, other_weeks = collect_week_memos(page_id, ref)
    except requests.HTTPError as e:
        status = e.response.status_code if e.response else "?"
        hint = "페이지를 Notion Integration Connection에 추가했는지 확인하세요" if status in (401, 403, 404) else ""
        return render_template("index.html", error=f"Notion API {status} 오류. {hint}", url=url), 400
    except Exception as e:
        return render_template("index.html", error=f"실패: {e}", url=url), 400

    if not memos:
        hint = ""
        if other_weeks:
            latest = max(other_weeks)
            lm = latest - timedelta(days=latest.weekday())
            ls = lm + timedelta(days=6)
            hint = (f" 발견된 가장 최근 데이터: {latest} (W{lm.isocalendar().week}, {lm}~{ls}). "
                    f"기준일을 이 주의 날짜로 잡고 다시 시도해 보세요.")
        return render_template(
            "index.html",
            error=f"이번 주({monday} ~ {sunday}) 메모가 없어요.{hint}",
            url=url,
        ), 400

    try:
        report = structure_with_claude(memos, monday, sunday)
    except Exception as e:
        return render_template("index.html", error=f"Claude 구조화 실패: {e}", url=url), 500

    week_num = monday.isocalendar().week
    html_out = render_template(
        "report.html",
        report=report,
        week_num=week_num,
        monday=monday.isoformat(),
        sunday=sunday.isoformat(),
        memos=memos,
        page_url=url,
        generated_at=date.today().isoformat(),
    )
    fname = f"W{week_num:02d}_{monday.isoformat()}.html"
    (OUTPUT_DIR / fname).write_text(html_out, encoding="utf-8")
    return html_out


# ───────── 진입점 ─────────

def check_claude_cli() -> bool:
    try:
        r = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=10,
            shell=_USE_SHELL,
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


if __name__ == "__main__":
    if not NOTION_TOKEN:
        print("❌ NOTION_TOKEN이 .env에 없습니다. .env.example을 복사해서 .env로 만들고 토큰을 넣어주세요.", file=sys.stderr)
        sys.exit(1)
    if not check_claude_cli():
        print("❌ claude CLI를 찾을 수 없습니다. Claude Code가 설치돼 있는지 확인해주세요.", file=sys.stderr)
        sys.exit(1)

    port = int(os.environ.get("PORT", 5000))
    url = f"http://localhost:{port}"
    print(f"🌐 주간보고 웹앱 시작: {url}")
    webbrowser.open(url)
    app.run(host="127.0.0.1", port=port, debug=False)
