# 카드뉴스 자동 제작 ② — Claude Code 재현 프롬프트 · Windows

> **macOS / Linux 사용자는 `PROMPT.md`를 사용하세요.**
>
> **사용법**: PowerShell 7+ (또는 Windows Terminal)에서 빈 폴더로 이동 → `claude` 실행 → 아래 `---` 사이 전체를 복사·붙여넣기 → Enter.
>
> **사전 준비 (1회)**
> - Python 3.10+ — `winget install Python.Python.3.12`
> - Node.js (Firecrawl MCP의 npx 실행용) — `winget install OpenJS.NodeJS.LTS`
> - Claude Code — `winget install Anthropic.Claude` 또는 npm
> - 콘솔 한글 깨짐 방지: `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"`
> - (URL 모드) Firecrawl 가입 + MCP 등록 — *PowerShell(claude 세션 바깥)에서*. **name(`firecrawl`)을 `-e` 앞에 두는 게 핵심**:
>   ```powershell
>   claude mcp add firecrawl -e FIRECRAWL_API_KEY=fc-xxxxxxxxxxxx -- npx -y firecrawl-mcp
>   claude mcp list   # firecrawl ✓ Connected 확인
>   ```

---

당신은 시니어 풀스택 엔지니어입니다. 다음 사양대로 **카드뉴스 자동 제작 미니프로젝트**를 처음부터 끝까지 구축하고 동작까지 검증해 주세요. 실행 환경은 **Windows 11 + PowerShell 7+ + Python 3.10+** 입니다.

## 목표

사용자가 **URL 한 줄** 또는 **마크다운 파일 경로**를 입력하면, 본문의 핫이슈를 분석해 **인스타용 1080×1080 카드 5장 PNG**를 자동 생성하고, **로컬 웹 UI에서 ZIP으로 한 번에 다운로드**할 수 있는 도구.

## 입력 방식 — 3가지 모두 지원

| 명령 | 동작 |
|---|---|
| `python run.py` *(인자 없음)* | **Flask 웹 UI** 자동 오픈 (`http://localhost:8765`) |
| `python run.py https://example.com/news` | CLI · URL 모드 (Firecrawl MCP) |
| `python run.py samples\sample_markdown.md` | CLI · 오프라인 모드 |

## 기술 스택 (정확히 이 조합)

| 단계 | 도구 | 핵심 설정 |
|---|---|---|
| 웹 UI | Flask | `127.0.0.1:8765`, `debug=False, use_reloader=False` |
| 크롤링 | Firecrawl MCP | `claude.cmd -p ... --allowedTools mcp__firecrawl__firecrawl_scrape` subprocess (`shell=True`) |
| 분석 | Claude Code CLI | `claude -p <prompt> --output-format json` |
| 렌더 | Playwright + Chromium 헤드리스 | viewport 1080×1080, `device_scale_factor=2` |
| ZIP | Python 표준 `zipfile` | `ZIP_DEFLATED`, `arcname=png.name` |
| 디자인 | 정적 HTML/CSS | Pretendard 웹폰트 + Paperlogy 톤 |

설치:
```powershell
python -m pip install playwright flask
python -m playwright install chromium
```

## 디렉토리 구조

```
카드뉴스\
├── run.py
├── prompts\
│   └── cards.md
├── templates\
│   ├── card.html
│   ├── index.html
│   ├── form.html
│   └── result.html
├── samples\
│   └── sample_markdown.md
├── output\
└── README.md
```

## prompts/cards.md — 카드 추출 프롬프트

JSON 블록 하나만, 한국어, 정확히 5장:

```json
{
  "topic": "8-15자",
  "source_url": "<source>",
  "cards": [
    {"kind":"cover", "label":"", "headline":"후킹 20-28자", "text":"왜 봐야 하는지 1-2줄"},
    {"kind":"body",  "label":"이슈 #1", "headline":"쟁점 15-25자", "text":"설명 2-3줄"},
    {"kind":"body",  "label":"이슈 #2", "headline":"...", "text":"..."},
    {"kind":"body",  "label":"이슈 #3", "headline":"...", "text":"..."},
    {"kind":"outro", "label":"", "headline":"TL;DR 한 줄", "text":"다음 행동"}
  ]
}
```

진부한 표현 금지 · 사실·숫자·인용 우선 · word-break:keep-all 가정.

## templates/card.html — 1080×1080

- `<body class="{kind}">` cover/body/outro 분기
- 컬러: paper #F5F1E8 / ink #1A1A1A / accent #7A2E2E / 골드 #C9A86E (outro)
- 폰트: `'Pretendard', 'Malgun Gothic', -apple-system, sans-serif` + Pretendard CDN link
- 레이아웃 (공통): 상단 topic + 브랜드 / 중앙 label + accent-line + headline + text / 하단 큰 카운터 + brand + source URL
- `body.cover` headline 80px / `body.outro` 다크 인버스 + 골드
- `word-break: keep-all`
- **★ `str.format()` 호환 위해 *CSS 중괄호 전부 `{{` `}}` 이스케이프***
- placeholder: `{kind}` `{topic}` `{label_html}` `{headline}` `{text}` `{n_str}` `{total}` `{source}`

## templates/index.html — CLI 정적 시트

- 5장 grid, placeholder `{topic}` `{source}` `{cells}` `{generated_at}`

## templates/form.html — 웹 UI 입력 폼 (Jinja2)

- 중앙 정렬 카드형 박스, Paperlogy 톤
- `<form method="POST" action="/generate">` + `<input name="source" required autofocus>` + `<button>5장 생성 시작</button>`
- 제출 시 JS로 로딩 박스 + 버튼 disabled

## templates/result.html — 웹 UI 결과 (Jinja2)

- 상단 큰 버튼:
  ```html
  <a class="btn-primary" href="/output/{{ stamp }}_cards.zip" download>📥 5장 한 번에 다운로드 (ZIP)</a>
  <a class="btn-ghost" href="/">← 새 카드뉴스 만들기</a>
  ```
- 5장 grid · 각 figure에 img + figcaption + 개별 다운로드

## run.py — 함수 시그니처

```python
import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # 콘솔 깨짐 방지

def crawl_url(url) -> str:
    # subprocess.run([...], shell=True, encoding="utf-8")
    # claude.cmd가 윈도우에 등록되므로 shell=True 필수

def extract_cards(markdown, source) -> dict: ...
def render_card_html(card, n, total, topic, source) -> str: ...

async def screenshot_cards(html_list, stamp) -> list[Path]:
    # playwright viewport 1080x1080 + device_scale_factor=2
    # page.set_content → document.fonts.ready 대기 → screenshot(clip 1080x1080)

def build_zip(pngs, stamp) -> Path:
    # zipfile.ZipFile(path, "w", ZIP_DEFLATED)

def build_index_sheet(cards, pngs, topic, source, stamp) -> Path: ...
def process(src, log=print) -> dict: ...   # CLI/웹 공통

def serve_web(port=8765):
    # Flask app, debug=False, use_reloader=False
    # 라우트: / · /generate · /result/<stamp> · /output/<filename>
    # send_from_directory(OUTDIR, filename, as_attachment=filename.endswith(".zip"))

def open_in_browser(path_or_url):
    import os
    if str(path_or_url).startswith("http"):
        import webbrowser; webbrowser.open(str(path_or_url))
    else:
        os.startfile(str(Path(path_or_url).resolve()))

def main():
    if len(sys.argv) < 2: serve_web()
    else: process(sys.argv[1]) → build_index_sheet → open_in_browser
```

## samples/sample_markdown.md

한국어 기사 1,500자. 사실·숫자·인용·담당자명 명시.

## Windows 특화 안전장치

- **subprocess `claude` 호출**: `shell=True` + `encoding="utf-8"` 필수. `[WinError 2]` 발생하면 거의 항상 `shell=True` 누락
- **콘솔 인코딩**: 스크립트 최상단 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` + PowerShell `chcp 65001`
- **PowerShell 7+** 또는 **Windows Terminal** 강제. cmd / PS 5.1은 cp949 → 이모지·한글 깨짐
- **Playwright Chromium 경로**: `%USERPROFILE%\AppData\Local\ms-playwright\` (≈150MB)
- **브라우저 자동 오픈**: `os.startfile(str(path.resolve()))` — 한글 경로 안전
- **Flask `host="127.0.0.1"`** 명시 — Windows Defender 방화벽 알림 최소화

## 검증 — 아래 2개 모두 통과해야 완료

1. **CLI 오프라인**
   ```powershell
   python run.py samples\sample_markdown.md
   ```
   → 약 15초 안에 `output\<TS>_01~05.png` + `<TS>_cards.zip` + `<TS>_index.html`

2. **웹 UI**
   ```powershell
   python run.py
   ```
   → `http://localhost:8765` 자동 오픈 → 입력 폼에 `samples\sample_markdown.md` 입력 → 결과 페이지 → ZIP 다운로드 클릭 → 5개 PNG 확인

## 흔히 빠지는 함정 (Windows 한정 포함)

- `[WinError 2]` `claude` 못 찾음 → `subprocess.run([...], shell=True)`
- 콘솔에서 이모지·한글 깨짐 → PowerShell 7+ + `chcp 65001` + `sys.stdout.reconfigure(encoding="utf-8")`
- Playwright 첫 실행 시 chromium 미설치 → `python -m playwright install chromium`
- CSS 중괄호 이스케이프 누락 → `str.format` `KeyError`
- Pretendard 웹폰트 로드 전 스크린샷 → `document.fonts.ready` 대기
- 한글 어절 줄바꿈 깨짐 → `word-break: keep-all`
- Firecrawl MCP 등록 명령 옵션 순서 (`add <name> -e KEY -- <cmd>`)
- Flask debug + reloader → 두 번 실행 → `debug=False, use_reloader=False`
- ZIP 다운로드가 인라인 열림 → `send_from_directory(..., as_attachment=True)` 분기
- 방화벽 알림 → `host="127.0.0.1"`만 바인딩

## 마지막 한 줄

완료 후 검증 #2(웹 UI) 결과 — 폼 + 결과 페이지 화면 캡처 + ZIP 안의 5개 PNG 파일명을 첨부해 보고해 주세요.

---

> Day 1 시그니처 시연 ②의 Windows 재현 사양입니다.
