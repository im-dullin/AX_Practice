# 카드뉴스 자동 제작 — 시그니처 시연 ②

URL 또는 마크다운 한 줄 → **인스타용 카드 5장 PNG 자동 생성** + 미리보기 시트 자동 오픈. 전부 로컬·MIT 계열 OSS.

## 동작 흐름

```
🌐 URL ────┐  Firecrawl MCP        Claude              HTML+Playwright
           ├─→ scrape →─ markdown ──→ 핫이슈 분석 ──→ 1080×1080 ×5 ──→ output/*.png + index.html
📄 .md ───┘                            (5장 JSON)         (@2x 해상도)        브라우저 자동 오픈
```

| 단계 | OSS / 도구 | 라이선스 |
|---|---|---|
| 크롤링 | Firecrawl MCP (외부 서비스) | 무료 500/월 — 가입 필요 |
| 분석 | Claude Code CLI (`claude -p`) | 기존 인증 그대로 |
| 렌더 | Playwright + Chromium (헤드리스) | Apache 2.0 |
| 디자인 | Pretendard 웹폰트 + Paperlogy 톤 | OFL / — |
| 웹 UI | Flask (로컬 전용) | BSD-3 |
| ZIP | Python `zipfile` 표준 라이브러리 | — |

## 설치 (1회)

```bash
pip install playwright flask
playwright install chromium

# Firecrawl MCP 등록 (URL 모드 사용 시)
# 1) https://firecrawl.dev 가입 → 대시보드 → API Keys → 키 복사
# 2) 터미널(claude 인터랙티브 세션 바깥)에서 — *name을 -e 앞에 두는 게 핵심*:
claude mcp add firecrawl -e FIRECRAWL_API_KEY=fc-xxxxxxxxxxxx -- npx -y firecrawl-mcp
# 3) 등록 확인
claude mcp list   # firecrawl: ... ✓ Connected 가 떠야 OK
```

오프라인 데모만 할 거면 Firecrawl 가입은 생략 가능.

## 실행 — 3가지 모드

### ★ 웹 UI (Recommended · 비개발자 친화)

```bash
python3 run.py
```

→ 자동으로 브라우저에 `http://localhost:8765` 가 열립니다.

1. **URL 입력 폼** — *URL 또는 마크다운 파일 경로* 한 줄을 넣고 *"5장 생성 시작"* 클릭
2. 약 15-20초 진행 표시 후 자동으로 결과 페이지 이동
3. **결과 페이지** — 5장 카드 썸네일 + 상단의 *📥 5장 한 번에 다운로드 (ZIP)* 큰 버튼 + 각 카드 *↓ 개별 다운로드*
4. 새 카드 만들려면 *← 새 카드뉴스 만들기* 클릭

종료는 터미널에서 `Ctrl+C`.

### CLI · URL 모드 (시연 1줄용)

```bash
python3 run.py https://www.example.com/news/article-id
```

### CLI · 오프라인 모드 (Firecrawl 없이 데모)

```bash
python3 run.py samples/sample_markdown.md
```

## 출력 파일

모든 모드에서 `output/` 폴더에 다음이 생성됩니다:
- `<TS>_01.png ~ _05.png` — 카드 5장 (1080×1080 @2x · 2160×2160 실픽셀)
- `<TS>_cards.zip` — **★ 5장 한 묶음** (인스타 한 번에 업로드용)
- `<TS>_meta.json` — 메타데이터 (topic·source·cards)
- `<TS>_index.html` — CLI 모드에서만 (정적 미리보기 시트)

## 실측 성능 (M-시리즈 Mac)

| 입력 | 크롤링 | 분석 | 렌더+스크린샷 | 합계 |
|---|---|---|---|---|
| 마크다운 (오프라인) | 0초 | ~10초 | ~5초 | **~15초** |
| URL (Firecrawl) | ~5초 | ~10초 | ~5초 | **~20초** |

## 디자인 시스템

- 1080×1080 정사각형 · @2x 해상도 (인스타 권장)
- 컬러: `--paper:#F5F1E8 / --ink:#1A1A1A / --accent:#7A2E2E / 골드:#C9A86E (outro)`
- 폰트: Pretendard (웹폰트 CDN) + Apple SD Gothic Neo / Malgun Gothic fallback
- 5장 구성: **cover** (밝은 톤, 큰 헤드라인) + **body × 3** (이슈 라벨 + 헤드라인 + 본문) + **outro** (다크 인버스, TL;DR + CTA)

## 강의용 데모 흐름 (Block D · Demo 2)

1. **준비** — 시연 직전 sample 마크다운 1개 + Firecrawl MCP 등록 + Playwright 캐시 확보
2. **시연 (6분)**
   - 0:00~0:30 — 입력 URL 또는 마크다운 보여주기
   - 0:30~1:00 — `python3 run.py <input>` 실행
   - 1:00~1:30 — 진행 로그 5단계(🕸 📄 🤖 🎨 📸 📋) 흘러가는 동안 해설
   - 1:30~5:00 — 브라우저 자동 오픈된 5장 시트 워크스루
   - 5:00~6:00 — *"Day 2 매크로 #2 후보 — 폰 탭 한 번에 신상 콘텐츠 5장"* 메시지

## 파일 구조

```
02_카드뉴스/
├── run.py                  # 메인 — 웹 UI / CLI 두 모드
├── prompts/
│   └── cards.md           # Claude 카드 JSON 추출 프롬프트
├── templates/
│   ├── card.html          # 1장 1080×1080 (kind=cover/body/outro 분기)
│   ├── index.html         # CLI 모드 정적 미리보기 시트
│   ├── form.html          # 웹 UI · 입력 폼
│   └── result.html        # 웹 UI · 결과 페이지 (5장 + ZIP 다운로드)
├── samples/
│   └── sample_markdown.md # 오프라인 검증용 한국어 기사
├── output/                # PNG·ZIP·HTML·meta 생성 결과
├── PROMPT.md              # 수강생 재현 프롬프트 (macOS/Linux)
├── PROMPT_WINDOWS.md      # 수강생 재현 프롬프트 (Windows)
└── README.md
```

## 라이선스 안전 체크

- **Firecrawl 무료 티어** — 월 500 페이지. 강의 시연용 충분. 상업적 사용 시 유료 플랜 검토.
- **Pretendard** — SIL OFL · 상업적 사용 OK
- **Playwright** — Apache 2.0 · 상업적 사용 OK
- 출력 PNG는 **저작권 안전**: 자기 작성 콘텐츠 또는 사실 인용 기반. 원문 URL 카드 5에 명시.

## 30일 로드맵 Week 1 미션

이 카드뉴스 프로젝트의 출력 단을 갈아끼우는 게 첫 주 미션:
- **HTML 시트** → **Notion DB에 자동 등재** (`Notion MCP`)
- **PNG 5장** → **Instagram Graph API**로 자동 임시저장 (사람 검수 후 발행)
- **카드 헤드라인** → **자기 회사 톤 LoRA**로 fine-tune
