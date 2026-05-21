# AX_Practice

> AX 부트캠프 · Day 2 실습 자료. **시그니처 시연 ① ② ③** 세 프로젝트를 직접 만들고, *MCP 서버*와 *REST API 직접 호출*을 비교 학습합니다.

---

## 학습 흐름

| 회차 | 프로젝트 | 외부 의존 | 학습 포인트 |
|---|---|---|---|
| ① | **회의비서** (`01_회의비서/`) | 없음 (완전 로컬) | 음성 → 텍스트 · JSON 강제 · HTML 템플릿 · subprocess |
| ② | **카드뉴스** (`02_카드뉴스/`) | **Firecrawl MCP 서버** | ★ MCP 서버 첫 경험 · 헤드리스 브라우저 · 웹 UI · 비동기 |
| ③ | **주간보고** (`03_주간보고_자동화/`) | Notion REST API 직접 | ★ MCP vs REST 비교 · 인증 토큰 · 재귀 · Jinja2 · AI 가드레일 |

*외부 의존이 점진적으로 늘어나는* 학습 곡선을 의도적으로 설계했습니다.

---

## 시작하기

### Step 1. 환경 세팅 (1회)

자기 OS 가이드 한 번만 통과:
- macOS — [`세팅가이드_macOS.md`](세팅가이드_macOS.md)
- Windows — [`세팅가이드_Windows.md`](세팅가이드_Windows.md)

### Step 2. 저장소 클론

```bash
git clone https://github.com/im-dullin/AX_Practice.git
cd AX_Practice
```

> 한글 폴더명이라 셸에서 cd 할 때 `Tab` 자동완성 사용 권장.

### Step 3. 각 프로젝트 폴더 진입 → 개념 자료 먼저

각 프로젝트마다 학습 순서:

1. **`concept.md`** 읽기 (5분) — *이게 뭐예요·왜 만들어요·어떻게 동작해요*
2. **`concept.html`** 열어보기 — 강사 PT 슬라이드 (브라우저로 열기)
3. **`PROMPT.md`** (또는 `PROMPT_WINDOWS.md`) 를 Claude Code에 붙여넣기
4. Claude Code가 시키는 대로 따라가며 *바이브 코딩*
5. 막히면 *완성본 코드 (`run.py`, `app.py` 등)*와 비교 학습
6. **`README.md`** 의 검증 절차로 동작 확인

---

## 디렉토리 구조

```
AX_Practice/
├── README.md                      ← (지금 보고 있는 파일)
├── .gitignore
│
├── 세팅가이드_macOS.md            ← 환경 세팅 (Mac)
├── 세팅가이드_Windows.md          ← 환경 세팅 (Windows)
│
├── 01_회의비서/                    ← Project ① 회의비서
│   ├── concept.md / concept.html  ★ 개념 자료
│   ├── PROMPT.md / PROMPT_WINDOWS.md
│   ├── README.md
│   ├── run.py
│   ├── prompts/ · templates/ · samples/ · output/
│
├── 02_카드뉴스/                    ← Project ② 카드뉴스
│   ├── concept.md / concept.html  ★ MCP 서버 첫 경험
│   ├── PROMPT.md / PROMPT_WINDOWS.md
│   ├── README.md
│   ├── run.py
│   ├── prompts/ · templates/ · samples/ · output/
│
├── 03_주간보고_자동화/             ← Project ③ 주간보고
│   ├── concept.md / concept.html  ★ MCP vs REST 비교
│   ├── PROMPT.md / PROMPT_WINDOWS.md
│   ├── README.md / INSTRUCTOR.md
│   ├── app.py
│   ├── .env.example
│   ├── prompts/ · templates/ · samples/ · output/
│
└── docs/
    ├── mcp_guide.md               ★ MCP 끝판왕 요약집
    └── mcp_guide.html             ★ HTML 슬라이드
```

---

## 실습 모드 — 3단계 자유도

수업 회차별로 *자유도를 늘리는* 방식 권장:

| 회차 | 진행 방식 |
|---|---|
| **1회차** (회의비서) | PROMPT.md를 *Claude Code에 그대로* 붙여넣기 + 완성본 비교. *환경 세팅 검증*이 목적. |
| **2회차** (카드뉴스) | PROMPT.md를 *부분적으로 참고* + 자기 손으로 더 많이. MCP 서버 첫 경험. |
| **3회차** (주간보고) | PROMPT.md 없이 *개념 자료만* 보고 자기 손으로 — 진짜 바이브 코딩. |

수강생 수준 차이가 크면 *느린 분은 PROMPT.md 풀활용, 빠른 분은 PROMPT 안 보고 도전* 으로 분기.

---

## MCP 끝판왕 요약집

세 프로젝트의 *비교 학습 뼈대*. 카드뉴스 시작 전에 한 번, 주간보고 시작 전에 한 번 더 보세요.

- [`docs/mcp_guide.md`](docs/mcp_guide.md) — 8섹션 정리
- [`docs/mcp_guide.html`](docs/mcp_guide.html) — 8장 슬라이드 (강의 PT용)

---

## 흔히 빠지는 함정

| 증상 | 가장 흔한 원인 | 1순위 대처 |
|---|---|---|
| `claude` 명령이 안 됨 | PATH 미반영 | macOS: ⌘+Q 후 새 터미널 / Win: 새 PowerShell 7 창 |
| 한글·이모지가 □ 로 표시 | Win cmd / PS 5.1 사용 | PowerShell 7 + `chcp 65001` |
| `python.exe is not recognized` (Win) | 앱 실행 별칭 stub | 설정 → 앱 실행 별칭에서 python.exe 토글 OFF |
| `PortAudioError` (회의비서) | 마이크 권한 | macOS: 시스템 설정 / Win: *데스크톱 앱* 토글 필수 |
| `Firecrawl MCP 호출 실패` | MCP 미등록 | `claude mcp add firecrawl -e ... -- npx -y firecrawl-mcp` |
| `SSL DECRYPTION_FAILED` | 네트워크 불안정 | 같은 명령 재실행 (캐시 사용) / 또는 핫스팟 |
| 1603 (winget 설치 실패) | 관리자 권한 부족 | 관리자 권한 PowerShell로 재실행 |

자세한 OS별 트러블슈팅은 `00_setup/setup_<OS>.md` 의 *흔한 오류* 표 참고.

---

## 라이선스 안전 체크

본 자료의 모든 OSS는 *상업적 사용 OK*:

| 도구 | 라이선스 |
|---|---|
| Python, Flask | PSF / BSD-3 |
| faster-whisper · OpenAI Whisper 모델 | MIT / Apache 2.0 |
| sounddevice · soundfile · PortAudio | MIT |
| Playwright · Chromium 헤드리스 | Apache 2.0 |
| Pretendard 폰트 | SIL OFL |
| Firecrawl 무료 티어 | 500 페이지/월 — 시연용 충분 |
| Notion API | 무료 (Internal Integration) |
| Claude Code CLI | 사용자 본인 인증으로 사용 |

---

## 다음 단계 — 30일 로드맵

부트캠프 끝나고 *집에서* 할 일:

**Week 1** — 세 프로젝트를 *자기 회사 환경*에 맞춰 출력 단 갈아끼우기
- 회의비서 → 슬랙 채널 자동 발송
- 카드뉴스 → Notion DB 자동 등재
- 주간보고 → 상사 메일 초안 자동

**Week 2** — *사내 MCP 서버* 1개 직접 만들기 (Day 2 Block I 학습 적용)

**Week 3** — 팀에 `.claude/` 폴더 PR로 공유

**Week 4** — 팀 라이트닝 발표 (한 달 결과)

---

## 강사 정보

**김동엽 · 품다 (Poomda) 대표**
- yeopiya@gmail.com
- GitHub: [@im-dullin](https://github.com/im-dullin)
