# 주간보고 자동화 ③ — Claude Code 재현 프롬프트 · macOS / Linux

> **윈도우 사용자는 `PROMPT_WINDOWS.md`를 사용하세요.**
>
> **사용법**: 빈 폴더에서 `claude` 실행 → 아래 `---` 사이 전체를 복사·붙여넣기 → Enter.
> Claude Code가 폴더 구조·파일·의존성·검증까지 한 번에 끝냅니다.
>
> **사전 준비 (1회)**
> - Python 3.10+ — `brew install python@3.12`
> - Claude Code — `npm i -g @anthropic-ai/claude-code` 또는 brew (Claude Code CLI에서 `claude` 명령이 떠야 함)
> - Notion 계정 + 주간보고용 페이지 1개
> - Notion Internal Integration Token — https://www.notion.so/profile/integrations → "신규 연결" → "액세스 토큰" → 생성 → `Show` → 토큰 복사 (`ntn_…` 또는 `secret_…`)
> - 주간보고 페이지 우상단 `···` → 연결 → 위 Integration 추가 (페이지 접근 권한 부여)

---

당신은 시니어 풀스택 엔지니어입니다. 다음 사양대로 **주간보고 자동화 시스템**을 처음부터 끝까지 구축하고 동작까지 검증해 주세요. 진행 도중 의문이 생기면 사양을 우선하고, 사양이 모호한 부분만 보고하세요.

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
| LLM 호출 | Claude Code CLI | `subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, timeout=180)` |
| 환경변수 | `python-dotenv` | `.env`에서 `NOTION_TOKEN` 로딩 |
| HTML 렌더 | Jinja2 (Flask 내장) | `render_template()` |
| 슬래시 커맨드 | `.claude/commands/주간보고.md` | Notion MCP 도구 호출 (Claude Code 인증 그대로 사용) |

## 디렉토리 구조

```
주간보고_자동화/
├── app.py                          ← Flask 웹앱 (모드 B)
├── prompts/
│   └── structure.md                ← claude -p에 줄 구조화 프롬프트
├── templates/
│   ├── index.html                  ← 입력 폼
│   └── report.html                 ← HTML 보고서
├── samples/
│   └── 노션페이지_예시.md          ← 사용자가 적을 형식 예시 (참고용 텍스트)
├── output/                         ← 생성된 HTML 누적 (.gitkeep)
├── .claude/commands/주간보고.md    ← 모드 A 슬래시 커맨드
├── .env.example                    ← NOTION_TOKEN 템플릿
├── .gitignore                      ← .env, .venv, output/*.html 제외
├── requirements.txt
└── README.md
```

## prompts/structure.md — Claude 구조화 프롬프트

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
    # URL에서 32자 hex 추출 → 8-4-4-4-12 dash 형식으로 포맷

def fetch_blocks(block_id: str) -> list: ...
    # GET /v1/blocks/{id}/children, 페이지네이션 처리 (has_more / next_cursor)

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
    # subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, timeout=180)
    # stdout에서 ```json ... ``` 또는 첫 {...} 정규식 추출 → json.loads
```

라우트:
- `GET /` → `render_template("index.html")`
- `POST /generate` → 위 함수들 체이닝 → `render_template("report.html", ...)` + `output/W{n}_{monday}.html` 저장

진입점:
```python
if __name__ == "__main__":
    if not NOTION_TOKEN: 종료
    if not check_claude_cli(): 종료
    webbrowser.open(f"http://localhost:{port}")
    app.run(host="127.0.0.1", port=port)
```

## .claude/commands/주간보고.md — 슬래시 커맨드

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

## templates/ — 디자인 시스템

**미니멀 · 우아함 · Stripe Press/Linear 톤**.

- 폰트: Pretendard Variable CDN (`https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/...`) + 시스템 폴백 (`-apple-system, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif`)
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
- 도움말은 `<details>`로 접힘, 매우 옅은 톤

### report.html — 보고서
- 좁은 컬럼 (max-width 680px)
- 헤더: eyebrow(`Week 21 · 2026-05-18 — 2026-05-24`) → 작은 라벨 "주간 보고서" → **큰 헤드라인 (큰따옴표로 감싸진 typography, 인용박스 X)**
- 4섹션: 각 섹션은 `01/02/03/04` 번호 + UPPERCASE 라벨 + soft 부제. 컨텐츠는 ul/li
- 불릿: `•` 점 아니라 **얇은 dash 라인** (`li::before { content: ""; width: 0.4rem; height: 1px; background: var(--fg-soft); }`)
- 액션 버튼: outline pill, "인쇄·PDF" / "새로 만들기"
- 원문 메모: `<details>` 토글, dashed divider로 분리
- `@media print` 지원 (인쇄 시 button/details 숨김)

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

## samples/노션페이지_예시.md

사용자가 Notion에 적을 형식 예시 (텍스트). 한 주치(5~6일) 합성 메모를 한국어로 직접 작성. 일별 4~5개 불릿. 회의·인터뷰·미팅·장애·액션 등이 자연스럽게 등장하여 4섹션 구조화가 의미 있게 나오도록.

## macOS 특화 안전장치

- 모든 파일 I/O에 `encoding="utf-8"` 명시
- 가상환경 권장: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- `claude -p` 응답은 ```` ```json ... ``` ```` 코드블록으로 감싸 나옴 → `re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw)` 1차 시도, 실패 시 `re.search(r"\{[\s\S]*\}", raw)` 폴백
- Notion API는 페이지마다 Integration Connection이 명시적으로 추가돼야 접근 가능 → 404가 나오면 사용자에게 "페이지 ··· → 연결 추가" 안내 (워크스페이스 권한과 별개)
- Notion 토글의 children은 lazy load → `has_children: true`면 `GET /v1/blocks/{toggle_id}/children` 추가 호출 필수
- `webbrowser.open(f"http://localhost:{port}")`로 자동 오픈

## 검증 — 아래 3개 모두 통과해야 완료

### 검증 1 — 토큰 sanity check

`.env`에 `NOTION_TOKEN`을 채운 뒤:
```bash
python3 -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
r = requests.get('https://api.notion.com/v1/users/me',
    headers={'Authorization': f'Bearer {os.environ[\"NOTION_TOKEN\"]}', 'Notion-Version': '2022-06-28'})
print(r.status_code, r.json().get('name'))
"
```
→ `200 <Integration 이름>` 이어야 통과.

### 검증 2 — 웹앱 엔드투엔드 (모드 B)

```bash
source .venv/bin/activate
python app.py
```
→ 브라우저 자동 오픈 → 폼에 본인 Notion 페이지 URL 붙여넣고 "보고서 생성" 클릭 → 약 10~30초 후 HTML 보고서 화면 표시 + `output/W{n}_{YYYY-MM-DD}.html` 파일 생성.

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

## 흔히 빠지는 함정

- **Notion 404**: 토큰 권한 있어도 페이지에 Connection 추가 안 하면 페이지별로 404. Notion 메시지 그대로 사용자에게 전달
- **토글 children 누락**: 페이지 fetch만 하고 토글 children fetch 안 하면 일별 메모가 비어 보임
- **JSON 추출 실패**: claude 응답에서 ```` ``` ```` 코드블록을 못 잡으면 `json.JSONDecodeError`. 폴백 정규식 필수
- **자식 페이지 중복 생성**: 같은 주차에 슬래시 커맨드를 두 번 실행했을 때 자식 페이지가 둘 생기면 오버라이트 로직 누락. 부모 페이지의 자식들을 fetch해서 제목 일치 검사 후 본문 덮어쓰기
- **아카이브 토글 본문 손상**: 다른 주차 링크를 삭제하거나 정렬 잘못하면 사용자 신뢰 무너짐. 이번 주 항목만 add, 기존은 read-only
- **모드 A 세션 인증 타이밍**: Notion MCP는 인증 후 새 세션에서만 도구 레지스트리에 로드됨. 인증 직후 같은 세션에서 호출하면 InputValidationError. 사용자에게 세션 재시작 안내

## 마지막 한 줄

완료 후 검증 #2(웹앱) 실행 결과(브라우저 화면 캡처 또는 생성된 HTML의 헤드라인·4섹션 첫 줄)를 첨부해 보고해 주세요.

---

> 위 프롬프트는 **Day 1 시그니처 시연 ③**의 정식 재현 사양입니다. 부트캠프 후 자기 회사 환경(Slack 발송, 다른 출력 양식, 자동 cron 실행 등)으로 확장하는 것이 **30일 로드맵 Week 2**의 핵심 미션입니다.
