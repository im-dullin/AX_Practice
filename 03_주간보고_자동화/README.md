# 주간보고 자동화 — 시그니처 시연 ③

Notion에 일별 메모만 적어두면, **두 가지 방식**으로 주간 보고서를 자동 생성.

## 두 모드

| 모드 | 입력 | 출력 | 누구에게 좋은가 |
|---|---|---|---|
| **A. Claude Code 슬래시 커맨드** | `/주간보고 <Notion URL>` | Notion 자식 페이지 + 부모 페이지 아카이브 토글 | 개발자·파워유저, 반복·자동화·팀 공유 |
| **B. 웹앱** | 브라우저에서 URL 붙여넣기 | HTML 보고서 (인쇄·PDF 가능) | 비개발자, 1회성·즉시 결과 |

둘 다 같은 Notion 페이지 구조를 입력으로 받는다.

---

## Notion 페이지 구조 (공통)

Notion에 페이지 1개를 만들고, **일별 메모를 토글 또는 H2 헤더**로 누적 입력.

```
📅 주간보고 (페이지 제목)

▶ 2026-05-21 목         ← 토글 라벨이 YYYY-MM-DD로 시작
   - 파트너사 미팅: 토스 계약 6/15 발효
   - 법무 검토 의뢰 5/22

▶ 2026-05-20 수
   - 스프린트 22 회고: 14중 11완료
   - 긴급 장애 73분
```

날짜 인식 패턴: `YYYY-MM-DD` 또는 `YYYY.MM.DD`로 시작. 요일·이모지는 무시.

---

## 모드 A — Claude Code 슬래시 커맨드

부모 페이지 본문은 깨끗하게 유지하면서, 매주 요약은 자식 페이지로 분리하고 부모 페이지 맨 위 `📚 주간 요약 아카이브` 토글에 링크만 누적한다.

### 1회 셋업
1. Claude Code에 Notion MCP 인증 (`/mcp` → "claude.ai Notion" 선택)
2. Notion 페이지 `···` → Connections에 Claude 추가

### 실행
이 디렉토리에서 Claude Code 진입 후:
```
/주간보고 https://www.notion.so/your-page-url
```

기준일 지정 (지난 주 보고서 늦게 만들 때):
```
/주간보고 https://www.notion.so/your-page-url 2026-05-17
```

### 결과
- 부모 페이지 맨 위에 `📚 주간 요약 아카이브` 토글이 생기고 (또는 기존 재사용), 안에 `📊 W21 주간 요약 (2026-05-18~24) — 헤드라인` 링크가 추가됨
- 자식 페이지에 BEFORE / PROGRESS / NEXT / RISK 본문이 생성됨
- 일별 메모 영역은 손대지 않음

---

## 모드 B — 웹앱

### 1회 셋업

```bash
# 1. 가상환경 + 의존성
cd "08_시그니처시연/03_주간보고_자동화"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Notion Integration Token 발급
#    https://www.notion.so/profile/integrations → New integration → Internal
#    → 토큰 복사 (secret_로 시작)

# 3. .env 만들기
cp .env.example .env
# .env 파일 열어서 NOTION_TOKEN=secret_xxx 채워넣기

# 4. Notion 주간보고 페이지 ··· → Connections에 위 Integration 추가
```

### 실행
```bash
python app.py
```

- 자동으로 브라우저가 열림 (http://localhost:5000)
- 폼에 Notion 페이지 URL 붙여넣고 "주간보고 생성" 클릭
- HTML 보고서가 화면에 표시됨 (인쇄·PDF 저장 버튼 제공)
- 동시에 `output/W21_2026-05-18.html` 로 파일 저장

### 흐름
```
브라우저 폼 → app.py
  → Notion API로 페이지 fetch (requests)
  → 일별 토글 children 추가 fetch (lazy load)
  → 이번 주 메모만 필터
  → claude -p로 BEFORE/PROGRESS/NEXT/RISK JSON 구조화
  → Jinja2로 HTML 렌더링
```

### 의존성
- **flask** — 웹 서버
- **requests** — Notion API 호출
- **python-dotenv** — 토큰 로딩
- **claude CLI** — 구조화 (별도 설치, Claude Code 인증 그대로 사용)

API 키 없이 동작: Claude API 키 대신 `claude -p` 서브프로세스 사용 → Claude Code 인증을 그대로 재활용.

---

## 파일 구조

```
03_주간보고_자동화/
├── README.md                      # 이 파일
├── .claude/commands/주간보고.md   # 모드 A 슬래시 커맨드
├── app.py                         # 모드 B 웹앱 (Flask)
├── prompts/structure.md           # 구조화용 Claude 프롬프트
├── templates/
│   ├── index.html                 # 입력 폼
│   └── report.html                # 결과 HTML 보고서
├── samples/
│   └── 노션페이지_예시.md         # 사용자가 적을 형식 예시
├── output/                        # 생성된 HTML 보고서 누적
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 자주 막히는 곳

| 증상 | 원인 / 해결 |
|---|---|
| `Notion API 403` | 페이지를 Integration Connection에 추가하지 않음. 페이지 `···` → Connections에서 명시 추가 |
| `이번 주 메모가 없어요` | 토글 라벨이 `YYYY-MM-DD`로 시작하지 않거나, 모든 토글이 이번 주 범위 밖 |
| `claude CLI를 찾을 수 없습니다` | Claude Code 설치 또는 `PATH` 확인 |
| (모드 A) Notion 툴 호출 안 됨 | Claude Code 세션 재시작. `claude mcp list`로 Connected 확인 |
| 같은 주차 재실행 | 모드 A는 자식 페이지 본문 덮어쓰기 (1회 확인). 모드 B는 항상 새 HTML 생성 |

---

## 확장 아이디어

- **자동 실행**: 매주 일요일 21시에 cron으로 모드 B 실행 → 생성된 HTML을 본인에게 Slack/Gmail로 발송
- **출력 템플릿 변경**: 회사 보고서 양식(KPI/이슈/요청사항 등)에 맞추려면 `prompts/structure.md`와 `templates/report.html` 두 파일만 수정
- **다른 페이지 재사용**: 팀 회고, 클라이언트 미팅 노트, 학습 일지 등 동일 패턴
