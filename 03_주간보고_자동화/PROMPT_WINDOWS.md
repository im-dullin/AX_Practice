# 주간보고 자동화 ③ — Claude Code 재현 프롬프트 · Windows

> **macOS / Linux 사용자는 `PROMPT.md`를 사용하세요.**
>
> **사용법**: PowerShell 7+ (또는 Windows Terminal)에서 빈 폴더로 이동 → `claude` 실행 → 아래 `---` 사이 전체를 복사·붙여넣기 → Enter.
> Claude Code가 폴더 구조·파일·의존성·검증까지 한 번에 끝냅니다.
>
> **사전 준비 (1회)**
> - Python 3.10+ — `winget install Python.Python.3.12`
> - Claude Code — `winget install Anthropic.Claude` 또는 `npm i -g @anthropic-ai/claude-code` (`claude --version`으로 확인)
> - Notion 계정 + 주간보고용 페이지 1개
> - Notion Internal Integration Token — https://www.notion.so/profile/integrations → "신규 연결" → "액세스 토큰" → 생성 → `Show` → 토큰 복사 (`ntn_…` 또는 `secret_…`)
> - 주간보고 페이지 우상단 `···` → 연결 → 위 Integration 추가 (페이지 접근 권한 부여)
> - 콘솔 한글 깨짐 방지 — PowerShell에서 한 번 실행:
>   ```powershell
>   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
>   $env:PYTHONIOENCODING = "utf-8"
>   ```

---

당신은 시니어 풀스택 엔지니어입니다. 다음 사양대로 **주간보고 자동화 시스템**을 처음부터 끝까지 구축하고 동작까지 검증해 주세요. 실행 환경은 **Windows 11 + PowerShell 7+ + Python 3.10+** 입니다. 진행 도중 의문이 생기면 사양을 우선하고, 사양이 모호한 부분만 보고하세요.

## 목표

사용자가 Notion 한 페이지에 **일별로 토글을 만들어 그날 업무를 적기만 하면**, 한 주가 끝날 때 그 메모들을 자동으로 모아 `BEFORE / PROGRESS / NEXT / RISK` 4섹션의 주간 보고서로 정리하는 시스템. 두 모드 동시 지원:

- **모드 A — Claude Code 슬래시 커맨드**: `/주간보고 <URL>` → Notion에 자식 페이지로 보고서 생성 + 부모 페이지 맨 위 아카이브 토글에 링크 누적
- **모드 B — 웹앱**: 브라우저 폼에 URL 붙여넣기 → HTML 보고서 자동 오픈 + `output/` 저장

LLM 호출은 외부 API 키 없이 **Claude Code CLI(`claude -p`)** 서브프로세스로만 수행 (Anthropic SDK 사용 금지).

## 입력 페이지 구조 (사용자가 Notion에 적는 형식)

부모 페이지에 일별 메모를 다음 두 형식 중 하나로 누적 입력. 둘 다 인식.

**형식 A — 토글 (실사용 다수)**:
```
▶ 2026-05-21 목
   - 파트너사 미팅: 토스 계약 6/15 발효
▶ 2026-05-20 수
   - 스프린트 22 회고
```

**형식 B — H2 헤더**:
```
## 2026-05-21 목
- 파트너사 미팅: ...
```

날짜 인식: 블록 텍스트 시작이 `YYYY-MM-DD` 또는 `YYYY.MM.DD`. 요일·이모지·괄호는 무시.

## 기술 스택

| 영역 | 도구 | 핵심 설정 |
|---|---|---|
| 웹 서버 | Flask 3.x | `app.run(host="127.0.0.1", port=5000)`, 자동 브라우저 오픈 |
| Notion API | `requests` | `Authorization: Bearer ntn_…`, `Notion-Version: 2022-06-28` |
| LLM 호출 | Claude Code CLI | `subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, timeout=180, shell=True, encoding="utf-8")` |
| 환경변수 | `python-dotenv` | `.env`에서 `NOTION_TOKEN` 로딩 |
| HTML 렌더 | Jinja2 (Flask 내장) | `render_template()` |
| 슬래시 커맨드 | `.claude/commands/주간보고.md` | Notion MCP 도구 호출 (Claude Code 인증 그대로 사용) |

설치 명령:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 디렉토리 구조

```
주간보고_자동화\
├── app.py                          ← Flask 웹앱 (모드 B)
├── prompts\
│   └── structure.md                ← claude -p에 줄 구조화 프롬프트
├── templates\
│   ├── index.html                  ← 입력 폼
│   └── report.html                 ← HTML 보고서
├── samples\
│   └── 노션페이지_예시.md          ← 사용자가 적을 형식 예시 (참고용 텍스트)
├── output\                         ← 생성된 HTML 누적 (.gitkeep)
├── .claude\commands\주간보고.md    ← 모드 A 슬래시 커맨드
├── .env.example                    ← NOTION_TOKEN 템플릿
├── .gitignore                      ← .env, .venv, output\*.html 제외
├── requirements.txt
└── README.md
```

## prompts\structure.md — Claude 구조화 프롬프트

핵심 요건: **```json 코드블록 하나만 응답**, 한국어, 다음 스키마 강제.

```json
{
  "headline": "한 줄로 그 주를 요약 (50자 이내)",
  "before": ["지난 주에서 이어진 작업/열린 이슈", "..."],
  "progress": ["완료된 결정/산출물/합의 (핵심 수치 포함)", "..."],
  "next": ["다음 7일 이내 deadline 액션 (담당자·날짜 명시)", "..."],
  "risk": ["장애/블로커/이탈 신호/외부 의존성", "..."]
}
```

**가드레일 (반드시 프롬프트에 명시)**:
- 원문에 없는 사실을 절대 만들지 마세요
- 모호하면 끝에 `(확인 필요)` 라벨을 답니다
- 각 섹션 2~4개 불릿
- 핵심 수치·날짜·담당자는 누락 금지

템플릿 placeholder: `{week_num}` `{monday}` `{sunday}` `{memos}` — Python `.format()`으로 치환.

## app.py — 함수 시그니처

```python
def extract_page_id(url: str) -> str: ...
    # URL에서 32자 hex 추출 → 8-4-4-4-12 dash 형식

def fetch_blocks(block_id: str) -> list: ...
    # GET /v1/blocks/{id}/children, 페이지네이션 처리

def block_text(block: dict) -> str: ...
    # rich_text 배열에서 plain_text 추출

def parse_date(text: str) -> date | None: ...
    # ^\s*(\d{4})[-./](\d{1,2})[-./](\d{1,2}) 정규식

def week_range(ref: date) -> tuple[date, date]: ...
    # ref가 속한 ISO 주의 월요일~일요일

def collect_week_memos(page_id: str, ref: date) -> tuple[list, date, date]: ...
    # 1) 최상위 블록 fetch
    # 2) toggle/heading_2 중 날짜로 시작하는 것 매칭
    # 3) "주간 요약 아카이브" 또는 📚 📊 시작 토글은 제외
    # 4) 매칭된 토글의 children 별도 fetch (lazy load)
    # 5) 이번 주 범위 안의 것만 반환

def structure_with_claude(memos: list, monday: date, sunday: date) -> dict: ...
    # prompts/structure.md 로딩 → .format() 치환
    # subprocess.run(["claude", "-p", prompt], capture_output=True, text=True,
    #                timeout=180, shell=True, encoding="utf-8")
    # stdout에서 ```json ... ``` 또는 첫 {...} 정규식 추출 → json.loads
```

라우트:
- `GET /` → `render_template("index.html")`
- `POST /generate` → 위 함수들 체이닝 → `render_template("report.html", ...)` + `output\W{n}_{monday}.html` 저장

진입점:
```python
import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
...
if __name__ == "__main__":
    if not NOTION_TOKEN: 종료
    if not check_claude_cli(): 종료
    webbrowser.open(f"http://localhost:{port}")
    app.run(host="127.0.0.1", port=port)
```

## .claude\commands\주간보고.md — 슬래시 커맨드

frontmatter:
```yaml
---
description: Notion 주간보고 페이지의 일별 토글을 읽어 자식 페이지로 주간 요약 생성 + 부모 페이지 상단 아카이브 토글에 링크 누적
argument-hint: "<Notion 페이지 URL> [기준일=오늘]"
---
```

본문은 다음 6단계 절차를 명시한 자연어 지시문:
1. 페이지 fetch (Notion MCP)
2. 이번 주 토글/H2 추출 (토글이면 children 별도 fetch)
3. 헤드라인 + 4섹션 구조화
4. **자식 페이지 생성 또는 갱신** — 제목 `📊 W{n} 주간 요약 ({월}~{일})`, 같은 주차 자식이 있으면 본문 덮어쓰기 (1회 확인)
5. **부모 페이지 맨 위 `📚 주간 요약 아카이브` 토글에 자식 페이지 링크 추가** — 토글이 없으면 생성, 같은 주차 링크 중복 방지, 최신 위로 정렬
6. 결과 보고

**핵심 원칙 (가드레일)**: 부모 페이지 본문(일별 메모 토글)은 절대 수정·삭제하지 말 것. read-only.

## templates\ — 디자인 시스템

**미니멀 · 우아함 · Stripe Press/Linear 톤**.

- 폰트: Pretendard Variable CDN (`https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/...`) + 시스템 폴백 (`Segoe UI, "Malgun Gothic", "Apple SD Gothic Neo", sans-serif`)
- 컬러 토큰:
  - `--bg: #fbfaf7` (워-페이퍼)
  - `--surface: #ffffff`
  - `--fg: #0a0a0a`
  - `--fg-soft: #525252`
  - `--fg-muted: #a3a3a3`
  - `--line: #ececea`
  - `--line-strong: #d4d4d2`
  - `--ease: cubic-bezier(0.2, 0.8, 0.2, 1)`
- **컬러 액센트 0개 모노크롬** (BEFORE/PROGRESS/NEXT/RISK에 컬러 보더 사용 금지)
- 타이포 hierarchy:
  - eyebrow: 0.7rem, letter-spacing 0.18em, uppercase, muted
  - h1: clamp(2.4rem, 5vw, 3.2rem), weight 600, letter-spacing -0.02em
  - body: 1rem, line-height 1.65
- 섹션 구분은 박스가 아닌 `border-top: 1px solid var(--line)` hairline
- 입력 필드는 박스가 아닌 `border-bottom`만
- 버튼: pill shape (`border-radius: 999px`), 솔리드 검정 (또는 outline)

### index.html — 입력 폼
- 좁은 컬럼 (max-width 560px)
- 헤드라인: "한 주를<br>한 페이지로." (2줄, weight 600)
- 입력 필드 2개: URL · 기준일(선택)
- 도움말은 `<details>`로 접힘

### report.html — 보고서
- 좁은 컬럼 (max-width 680px)
- 헤더: eyebrow(`Week 21 · 2026-05-18 — 2026-05-24`) → 작은 라벨 "주간 보고서" → **큰 헤드라인 (큰따옴표로 감싸진 typography, 인용박스 X)**
- 4섹션: `01/02/03/04` 번호 + UPPERCASE 라벨 + soft 부제. ul/li
- 불릿: 점이 아닌 **얇은 dash 라인** (`li::before { width: 0.4rem; height: 1px; background: var(--fg-soft); }`)
- 액션 버튼: outline pill, "인쇄·PDF" / "새로 만들기"
- 원문 메모: `<details>` 토글, dashed divider로 분리
- `@media print` 지원

## requirements.txt

```
flask>=3.0
requests>=2.31
python-dotenv>=1.0
```

## .env.example

```
# Notion Internal Integration Token
# 발급: https://www.notion.so/profile/integrations → 신규 연결 → 액세스 토큰
NOTION_TOKEN=ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 선택: 포트 (기본 5000)
# PORT=5000
```

## .gitignore

```
.env
.venv/
__pycache__/
*.pyc
output/*.html
!output/.gitkeep
```

## samples\노션페이지_예시.md

사용자가 Notion에 적을 형식 예시. 한 주치(5~6일) 합성 메모를 한국어로 직접 작성. 일별 4~5개 불릿. 회의·인터뷰·미팅·장애·액션 등이 자연스럽게 등장하여 4섹션 구조화가 의미 있게 나오도록.

## Windows 특화 안전장치

- **인코딩**: 파일 I/O 전부 `encoding="utf-8"` 명시. app.py 최상단에 다음 한 줄 추가하여 콘솔 깨짐 방지:
  ```python
  import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
  ```
- **subprocess.run의 shell=True**: 윈도우에서 `claude` CLI는 `claude.cmd`로 설치되므로 반드시 `shell=True` + `encoding="utf-8"` 옵션 추가:
  ```python
  subprocess.run(["claude", "-p", prompt],
                 capture_output=True, text=True, timeout=180,
                 shell=True, encoding="utf-8")
  ```
- **PowerShell vs cmd**: 반드시 **PowerShell 7+** 또는 **Windows Terminal** 사용. cmd.exe / PowerShell 5.1은 cp949 기본이라 한글·이모지 깨짐
- **claude 응답 파싱**: ```` ```json ... ``` ```` 코드블록 1차 추출 → 실패 시 `re.search(r"\{[\s\S]*\}", raw)` 폴백
- **Notion API 404**: 토큰 권한 있어도 페이지에 Connection 추가 안 하면 페이지별로 404. Notion 메시지 그대로 사용자에게 전달
- **토글 children 누락**: 페이지 fetch만 하고 토글 children fetch 안 하면 일별 메모가 비어 보임. `has_children: true`면 추가 호출 필수
- **`webbrowser.open` 한글 경로**: 로컬 파일 열 때 한글 경로 이슈 가능 — 웹앱은 `http://localhost:{port}`로만 오픈하므로 영향 없음
- **방화벽 첫 실행**: Flask 처음 실행 시 Windows Defender 방화벽 경고 → "액세스 허용"

## 검증 — 아래 3개 모두 통과해야 완료

### 검증 1 — 토큰 sanity check

`.env`에 `NOTION_TOKEN`을 채운 뒤 PowerShell에서:
```powershell
.venv\Scripts\Activate.ps1
python -c "import os, requests; from dotenv import load_dotenv; load_dotenv(); r = requests.get('https://api.notion.com/v1/users/me', headers={'Authorization': f'Bearer ' + os.environ['NOTION_TOKEN'], 'Notion-Version': '2022-06-28'}); print(r.status_code, r.json().get('name'))"
```
→ `200 <Integration 이름>` 이어야 통과.

### 검증 2 — 웹앱 엔드투엔드 (모드 B)

```powershell
.venv\Scripts\Activate.ps1
python app.py
```
→ 브라우저 자동 오픈 → 폼에 본인 Notion 페이지 URL 붙여넣고 "보고서 생성" 클릭 → 약 10~30초 후 HTML 보고서 화면 표시 + `output\W{n}_{YYYY-MM-DD}.html` 파일 생성.

### 검증 3 — 슬래시 커맨드 (모드 A)

이 디렉토리에서 `claude` 재진입 (Notion MCP가 도구 레지스트리에 로드되도록):
```
/주간보고 https://www.notion.so/your-page-url
```
→ Notion 페이지에서:
- 부모 페이지 맨 위에 `📚 주간 요약 아카이브` 토글 생성됨 (또는 기존 재사용)
- 토글 안에 자식 페이지 링크 추가됨
- 자식 페이지에 BEFORE/PROGRESS/NEXT/RISK 본문 작성됨
- **부모 페이지의 일별 토글들은 변경 없음** (가장 중요한 검증 포인트)

## 흔히 빠지는 함정 (Windows 한정 포함)

- **`[WinError 2] 지정된 파일을 찾을 수 없습니다`** → `subprocess.run`에 `shell=True` 누락
- **콘솔에서 이모지·한글 깨짐** → PowerShell 7+ 사용 + `$env:PYTHONIOENCODING="utf-8"` + `sys.stdout.reconfigure(encoding="utf-8")`
- **`.venv\Scripts\Activate.ps1` 실행 차단** → PowerShell 관리자로 한 번: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
- **Notion 404**: 토큰 권한 있어도 페이지에 Connection 추가 안 하면 페이지별로 404
- **토글 children 누락**: 페이지 fetch만 하고 토글 children fetch 안 하면 일별 메모가 비어 보임
- **JSON 추출 실패**: claude 응답에서 ```` ``` ```` 코드블록을 못 잡으면 `json.JSONDecodeError`. 폴백 정규식 필수
- **자식 페이지 중복 생성**: 같은 주차에 슬래시 커맨드를 두 번 실행했을 때 자식 페이지가 둘 생기면 오버라이트 로직 누락
- **아카이브 토글 본문 손상**: 다른 주차 링크를 삭제하면 사용자 신뢰 무너짐. 이번 주 항목만 add, 기존 read-only
- **모드 A 세션 인증 타이밍**: Notion MCP는 인증 후 새 세션에서만 도구 레지스트리에 로드됨. 사용자에게 세션 재시작 안내

## 마지막 한 줄

완료 후 검증 #2(웹앱) 실행 결과(브라우저 화면 캡처 또는 생성된 HTML의 헤드라인·4섹션 첫 줄)를 첨부해 보고해 주세요.

---

> 위 프롬프트는 **Day 1 시그니처 시연 ③**의 Windows 재현 사양입니다. 부트캠프 후 자기 회사 환경(Teams 채널 발송, 다른 출력 양식, 작업 스케줄러 자동 실행 등)으로 확장하는 것이 **30일 로드맵 Week 2**의 핵심 미션입니다.
