# 카드뉴스 자동 제작 ② — Claude Code 재현 프롬프트 · macOS / Linux

> **윈도우 사용자는 `PROMPT_WINDOWS.md`를 사용하세요.**
>
> **사용법**: 빈 폴더에서 `claude` 실행 → 아래 `---` 사이 전체를 복사·붙여넣기 → Enter.
> Claude Code가 폴더 구조·파일·의존성·검증까지 한 번에 끝냅니다.
>
> **사전 준비**
> - Python 3.10+ · `pip` 사용 가능
> - Claude Code 인증 완료 (`claude` CLI 동작)
> - (URL 모드 사용 시) Firecrawl 가입 + MCP 등록 — *터미널(claude 세션 바깥)에서*. **name(`firecrawl`)을 `-e` 앞에 두는 게 핵심** (`-e`가 variadic이라 뒤에 두면 name까지 env로 빨려들어감):
>   ```bash
>   claude mcp add firecrawl -e FIRECRAWL_API_KEY=fc-xxxxxxxxxxxx -- npx -y firecrawl-mcp
>   claude mcp list   # firecrawl ✓ Connected 확인
>   ```

---

당신은 시니어 풀스택 엔지니어입니다. 다음 사양대로 **카드뉴스 자동 제작 미니프로젝트**를 처음부터 끝까지 구축하고 동작까지 검증해 주세요. 진행 도중 사양이 모호하면 사양을 우선하고, 정말 모호한 부분만 보고하세요.

## 목표

사용자가 **URL 한 줄** 또는 **마크다운 파일 경로**를 입력하면, 본문의 핫이슈를 분석해 **인스타용 1080×1080 카드 5장 PNG**를 자동 생성하고, **로컬 웹 UI에서 ZIP으로 한 번에 다운로드**할 수 있는 도구. 외부 클라우드 LLM 호출 금지 — Claude Code CLI(`claude -p`) 및 Firecrawl MCP만 예외.

## 입력 방식 — 3가지 모두 지원

| 명령 | 동작 |
|---|---|
| `python3 run.py` *(인자 없음)* | **Flask 웹 UI** 자동 오픈 (`http://localhost:8765`) |
| `python3 run.py https://example.com/news` | CLI · URL 모드 (Firecrawl MCP) |
| `python3 run.py samples/sample_markdown.md` | CLI · 오프라인 모드 |

## 기술 스택 (정확히 이 조합)

| 단계 | 도구 | 핵심 설정 |
|---|---|---|
| 웹 UI | Flask | 로컬 전용 (`127.0.0.1:8765`), `debug=False, use_reloader=False` |
| 크롤링 | Firecrawl MCP | `claude -p ... --allowedTools mcp__firecrawl__firecrawl_scrape` subprocess |
| 분석 | Claude Code CLI | `claude -p <prompt> --output-format json` |
| 렌더 | Playwright + Chromium 헤드리스 | viewport 1080×1080, `device_scale_factor=2` |
| ZIP | Python 표준 `zipfile` | `ZIP_DEFLATED`, `arcname=png.name` |
| 디자인 | 정적 HTML/CSS | Pretendard 웹폰트 CDN + Paperlogy 톤 |

설치:
```bash
pip install playwright flask
playwright install chromium
```

## 디렉토리 구조

```
카드뉴스/
├── run.py
├── prompts/
│   └── cards.md              # Claude 카드 JSON 추출 프롬프트
├── templates/
│   ├── card.html             # 1장 1080×1080 (kind=cover/body/outro)
│   ├── index.html            # CLI 모드 정적 시트 (str.format)
│   ├── form.html             # 웹 UI · 입력 폼 (Jinja)
│   └── result.html           # 웹 UI · 결과 페이지 (5장 + ZIP)
├── samples/
│   └── sample_markdown.md    # 한국어 기사 1,500자 직접 작성
├── output/                   # PNG·ZIP·HTML·meta.json (.gitkeep)
└── README.md
```

## prompts/cards.md — 카드 추출 프롬프트

JSON 코드블록 하나만 응답, 한국어, 정확히 5장 (cover 1 + body 3 + outro 1):

```json
{
  "topic": "8-15자 시리즈 주제",
  "source_url": "<source>",
  "cards": [
    {"kind":"cover", "label":"", "headline":"후킹 20-28자", "text":"왜 봐야 하는지 1-2줄"},
    {"kind":"body",  "label":"이슈 #1", "headline":"쟁점 15-25자", "text":"설명 2-3줄 (숫자·인용)"},
    {"kind":"body",  "label":"이슈 #2", "headline":"...", "text":"..."},
    {"kind":"body",  "label":"이슈 #3", "headline":"...", "text":"..."},
    {"kind":"outro", "label":"", "headline":"TL;DR 한 줄", "text":"독자의 다음 행동"}
  ]
}
```

진부한 표현 절대 금지 (*"주목할 만한", "이슈가 되고 있다", "관심을 끌고 있다"*) · 사실·숫자·인용 우선 · word-break:keep-all 가정.

## templates/card.html — 1장 1080×1080

- `<body class="{kind}">` 로 cover/body/outro 분기
- 컬러: `--paper:#F5F1E8` / `--ink:#1A1A1A` / `--accent:#7A2E2E` / 골드 `#C9A86E` (outro)
- 폰트: `'Pretendard', -apple-system, "Apple SD Gothic Neo", sans-serif` + 상단 Pretendard CDN link
- 레이아웃: 상단 `topic` + 브랜드 / 중앙 `label` + accent-line(4px×80px) + `headline` + `text` / 하단 `NN / NN` 큰 카운터 + brand + truncated source URL
- `body.cover` headline 80px, `body.outro` 다크 인버스(#1A1A1A 배경) + 골드 accent
- `word-break: keep-all`
- **★ `str.format()` 호환을 위해 *CSS의 모든 중괄호를 `{{` `}}` 로 이스케이프*** — 빠뜨리면 `KeyError`
- placeholder는 정확히 `{kind}` `{topic}` `{label_html}` `{headline}` `{text}` `{n_str}` `{total}` `{source}`

## templates/index.html — CLI 모드 정적 시트

- 5장 grid (`repeat(auto-fit, minmax(280px, 1fr))`, gap 18px)
- placeholder: `{topic}` `{source}` `{cells}` `{generated_at}`
- CSS 중괄호 이스케이프 동일 (str.format 사용)

## templates/form.html — 웹 UI 입력 폼 (Jinja2)

- Paperlogy 톤 · 중앙 정렬 카드형 박스 (max-width 640px)
- 헤더: `Auto Card News` / `Poomda · Signature ②`
- `<h1>핫이슈 → 카드뉴스 5장.</h1>` + lead 설명
- 폼: `<form method="POST" action="/generate">` + `<input type="text" name="source" required autofocus>` + `<button id="go" type="submit">5장 생성 시작</button>`
- 제출 시 JS — 로딩 박스 표시 + 버튼 disabled + 문구 *"생성 중… (~20초)"*
- 로딩 박스: 스피너 + 진행 단계(🕸 🤖 📸) 안내 + "새로고침 금지" 경고

## templates/result.html — 웹 UI 결과 페이지 (Jinja2)

- 상단 `<h1>{{ topic }}</h1>` + source (http면 새창 링크)
- **★ 큰 액션 버튼 ★**:
  ```html
  <a class="btn-primary" href="/output/{{ stamp }}_cards.zip" download>
    📥 5장 한 번에 다운로드 (ZIP)
  </a>
  <a class="btn-ghost" href="/">← 새 카드뉴스 만들기</a>
  ```
- 5장 grid (form.html과 같은 grid 규칙)
- 각 figure: `<img src="/output/{{ stamp }}_{{ '%02d'|format(loop.index) }}.png" loading="lazy">` + figcaption(번호 + headline 42자 truncate) + 개별 다운로드 링크
- `{% for card in cards %}` Jinja loop

## run.py — 함수 시그니처

```python
def crawl_url(url) -> str: ...
    # subprocess.run(["claude","-p",prompt,"--output-format","json",
    #                 "--allowedTools","mcp__firecrawl__firecrawl_scrape"])
    # 실패 시 친절한 에러 + 등록 명령 가이드

def extract_cards(markdown, source) -> dict: ...
    # re.search(r"\{[\s\S]*\}", raw) 로 JSON 블록 추출

def render_card_html(card, n, total, topic, source) -> str: ...
    # html.escape + str.format
    # label 비어 있으면 label_html=""

async def screenshot_cards(html_list, stamp) -> list[Path]:
    # async_playwright + chromium.launch()
    # context viewport 1080×1080 + device_scale_factor=2
    # page.set_content(html, wait_until="load") → document.fonts.ready 대기 → screenshot(clip 1080×1080)

def build_zip(pngs, stamp) -> Path:
    # zipfile.ZipFile(path, "w", ZIP_DEFLATED) → arcname=png.name

def build_index_sheet(cards, pngs, topic, source, stamp) -> Path: ...  # CLI 모드만

def process(src, log=print) -> dict:
    # CLI/웹 공통 처리. URL/파일 → markdown → cards → screenshot → ZIP
    # output/<stamp>_meta.json 에 {stamp, topic, source, cards, png_count, zip} 저장
    # return meta dict

def serve_web(port=8765):
    # Flask app, template_folder=ROOT/"templates"
    # 라우트:
    #   GET /                  → render_template("form.html")
    #   POST /generate         → process(request.form["source"]) → redirect /result/<stamp>
    #   GET /result/<stamp>    → meta.json 로드 → render_template("result.html", ...)
    #   GET /output/<filename> → send_from_directory(OUTDIR, filename,
    #                              as_attachment=filename.endswith(".zip"))
    # 1.2초 후 webbrowser로 자동 오픈
    # app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)

def open_in_browser(path_or_url):
    # darwin: subprocess.run(["open", str(p)])
    # win32: os.startfile(str(p))
    # 그 외/url: webbrowser.open

def main():
    if len(sys.argv) < 2: serve_web()
    else: process(sys.argv[1]) → build_index_sheet → open_in_browser
```

## samples/sample_markdown.md

한국어 기사 1,500자 직접 작성. 사실·숫자·인용·담당자명 명시. 주제: 자유 (AI 자동화 도입 격차, 회의비서 효과, 비용 폭주 사례 등).

## 검증 — 아래 2개 모두 통과해야 완료

1. **CLI 오프라인**
   ```bash
   python3 run.py samples/sample_markdown.md
   ```
   → 약 15초 안에 `output/<TS>_01~05.png` + `<TS>_cards.zip` + `<TS>_index.html` 생성. 브라우저로 자동 오픈된 시트에 5장 정상 표시.

2. **웹 UI**
   ```bash
   python3 run.py
   ```
   → `http://localhost:8765` 자동 오픈 → 입력 폼에 `samples/sample_markdown.md` 입력 후 *"5장 생성 시작"* → 약 15-25초 후 결과 페이지 → *"📥 5장 한 번에 다운로드 (ZIP)"* 클릭 → ZIP 파일 다운로드 + 안에 5개 PNG 확인.

## 흔히 빠지는 함정

- CSS 중괄호 이스케이프 누락 → `str.format` `KeyError` (CLI 템플릿만 해당. Jinja 템플릿은 그대로)
- Pretendard 웹폰트 로드 전 스크린샷 → `document.fonts.ready.then(()=>true)` 대기 필수
- 한글 어절 줄바꿈 깨짐 → `.headline`, `.text` 에 `word-break: keep-all`
- Firecrawl MCP 등록 명령 옵션 순서 — `claude mcp add <name> -e KEY=val -- <cmd>` (name이 -e 앞)
- claude 응답에서 JSON만 추출 안 함 → `json.JSONDecodeError`
- Playwright `device_scale_factor` 미지정 → 1x 저해상도
- Flask `debug=True` + reloader 켜둠 → `serve_web()`이 두 번 실행되며 브라우저 두 번 열림. **`debug=False, use_reloader=False` 필수**
- `send_from_directory`에 `as_attachment=True` 누락 → 브라우저가 ZIP을 인라인 열기 시도 → `filename.endswith(".zip")`로 분기

## 마지막 한 줄

완료 후 검증 #2(웹 UI) 실행 결과를 첨부해 보고해 주세요 — 폼 화면 + 결과 페이지 화면 캡처 + 다운로드된 ZIP 안의 5개 PNG 파일명.

---

> Day 1 시그니처 시연 ②. 출력 단을 Notion DB 자동 등재 / Instagram Graph API 임시저장 등으로 갈아끼우는 것이 30일 로드맵 Week 1의 후보 미션입니다.
