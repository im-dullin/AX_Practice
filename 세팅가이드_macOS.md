# 세팅 가이드 · macOS

## 개요

| 항목 | 값 |
|---|---|
| 대상 OS | macOS 13 Ventura 이상 (Apple Silicon 또는 Intel) |
| 소요 시간 | 30 ~ 45분 |
| 필요 권한 | 관리자 계정 (sudo 가능) |
| 디스크 여유 | 최소 5GB |
| 네트워크 | 안정적인 인터넷 |
| 대상 프로젝트 | 시그니처 시연 ①~⑤ 전체 + 미니프로젝트 (단일 Python 환경 공유) |

## 설치 항목 요약

| # | 항목 | 용도 | 크기 |
|---|---|---|---|
| 1 | Xcode Command Line Tools | macOS 빌드 도구 (Homebrew 의존성) | ~1GB |
| 2 | Homebrew | macOS 패키지 매니저 | ~200MB |
| 3 | Python 3.12 | 시연 본체 언어 | ~80MB |
| 4 | Node.js LTS | Firecrawl MCP의 `npx` 런타임 | ~70MB |
| 5 | FFmpeg | 회의비서 오디오 처리 | ~50MB |
| 6 | Claude Code | AI CLI · MCP 호스트 | ~150MB |
| 7 | Python 패키지 (pip) | sounddevice · faster-whisper · playwright · flask 등 | ~500MB |
| 8 | Chromium (Playwright) | 헤드리스 브라우저 (카드뉴스 PNG 생성) | ~150MB |
| 9 | Whisper `small` 모델 | 한국어 음성 인식 모델 캐시 | ~470MB |

---

## 1. Xcode Command Line Tools 설치

**목적**: Homebrew 및 일부 Python 패키지가 의존하는 macOS 빌드 도구 설치.
**소요**: 5 ~ 10분

### 절차
```bash
xcode-select --install
```
GUI 다이얼로그가 뜨면 *설치* 클릭.

### 검증
```bash
xcode-select -p
```
**예상 출력**: `/Library/Developer/CommandLineTools` 또는 `/Applications/Xcode.app/Contents/Developer`

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `xcode-select: error: command line tools are already installed` | 이미 설치됨 | 정상. 다음 단계 진행. |
| 다이얼로그가 뜨지 않음 | 설치 진행 중 백그라운드 동작 | `softwareupdate --list` 로 진행 상태 확인 후 대기 |
| 설치 실패 / 멈춤 | macOS 업데이트 필요 | 시스템 설정 → 일반 → 소프트웨어 업데이트 후 재시도 |

---

## 2. Homebrew 설치

**목적**: macOS용 패키지 매니저. 이후 모든 도구를 단일 명령으로 설치·관리.
**소요**: 5 ~ 10분

### 절차
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
중간에 로그인 비밀번호 입력 (입력 시 화면에 표시되지 않음 — 정상). `Press RETURN to continue` 표시 시 Enter.

설치 완료 후 출력되는 **`Next steps:`** 섹션의 3줄 명령을 그대로 복사·실행 (Apple Silicon 기준):
```bash
echo >> ~/.zprofile
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### 검증
```bash
brew --version
```
**예상 출력**: `Homebrew 4.x.x`

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `command not found: brew` | PATH 미반영 | 위 `eval "$(...)" `3줄 실행. 그래도 안 되면 터미널 재시작. |
| `Failed during: /usr/bin/sudo ...` | 관리자 권한 없음 | 시스템 설정 → 사용자 및 그룹에서 관리자 권한 확인 |
| `curl: (6) Could not resolve host` | DNS / 네트워크 문제 | 네트워크 재연결, VPN 비활성화 후 재시도 |
| `Error: Your CLT does not support macOS 14` | CLT 버전 오래됨 | Step 1 재실행 또는 `sudo rm -rf /Library/Developer/CommandLineTools` 후 재설치 |

---

## 3. 핵심 도구 4종 설치 (Python · Node · FFmpeg · Claude Code)

**목적**: 모든 시연이 의존하는 런타임·CLI 한 번에 설치.
**소요**: 5 ~ 10분

### 절차
```bash
brew install python@3.12 node ffmpeg
brew install --cask claude
```

### 검증
```bash
python3 --version
node --version
ffmpeg -version | head -1
claude --version
```
**예상 출력** (4줄):
```
Python 3.12.x
v22.x.x      (또는 v20.x.x+)
ffmpeg version 8.x
1.x.x        (Claude Code 버전)
```

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `command not found: claude` | PATH 미반영 | 터미널 완전 종료(⌘+Q) 후 재실행. 또는 `brew link --overwrite claude` |
| `Error: Cask 'claude' is unavailable` | Homebrew tap 부족 | `brew update` 실행 후 재시도 |
| `python3` 명령은 동작하지만 버전이 3.9.x | 시스템 기본 Python이 우선 | `brew link --overwrite python@3.12`, 또는 `/opt/homebrew/bin/python3 --version` 직접 호출 |
| `node: command not found` | PATH 미반영 | 터미널 재시작 |

---

## 4. Claude Code 로그인

**목적**: Anthropic 계정 인증. 이후 모든 `claude` 명령 사용 가능.
**소요**: 1 ~ 3분

### 절차
```bash
claude login
```
브라우저가 자동으로 열림 → Anthropic 계정 로그인 → 권한 승인 → 터미널 복귀.

### 검증
```bash
claude -p "안녕하세요"
```
**예상 출력**: 한국어 짧은 응답.

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| 브라우저가 열리지 않음 | 기본 브라우저 미설정 | 표시되는 URL을 수동으로 복사해 브라우저에 붙여넣기 |
| 응답이 오지 않음 / `Authentication failed` | 결제 정보 미등록 | <https://claude.ai/settings/billing> 확인 |
| `Rate limit exceeded` | 무료/구독 한도 소진 | 한도 회복 대기 또는 상위 플랜 |

---

## 5. 시연 자료 폴더 이동

**목적**: 작업 디렉토리를 시연 자료 위치로 변경.
**소요**: 1분 미만

### 절차
다운로드 받은 자료 경로에 따라 다름. 예시:
```bash
cd ~/Downloads/20260528_프리미엄01
ls
```

### 검증
**예상 출력**: `08_시그니처시연` 폴더가 목록에 보임.

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `cd: no such file or directory` | 자료 위치가 다름 | Finder에서 폴더 우클릭 → *경로 이름 복사* 후 `cd "붙여넣기"` |
| 한글 경로에서 깨짐 | macOS는 UTF-8 NFD, 일부 도구는 NFC | 영문 디렉토리(`~/work` 등)로 자료 이동 후 재시도 |

---

## 6. Python 패키지 설치

**목적**: 시연 도구가 의존하는 Python 라이브러리 일괄 설치.
**소요**: 3 ~ 5분

### 절차
```bash
pip3 install --upgrade pip
pip3 install sounddevice soundfile numpy faster-whisper playwright flask
playwright install chromium
```

### 검증
```bash
python3 -c "import sounddevice, soundfile, numpy, faster_whisper, playwright, flask; print('OK')"
```
**예상 출력**: `OK`

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `error: externally-managed-environment` | macOS 시스템 Python 보호 | `pip3 install --user <패키지>` 또는 가상환경(`python3 -m venv venv && source venv/bin/activate`) 사용 |
| `ERROR: Could not build wheels for sounddevice` | PortAudio 헤더 부족 | `brew install portaudio` 후 재시도 |
| `Permission denied` | 시스템 Python 사용 시 | `pip3 install --user` |
| Chromium 다운로드 실패 | 네트워크 차단 | VPN 또는 회사 프록시 설정 확인. 수동 재시도: `playwright install chromium` |

---

## 7. Whisper `small` 모델 사전 다운로드

**목적**: 회의비서 첫 실행 시 모델 다운로드(약 470MB) 지연 방지.
**소요**: 3 ~ 5분

### 절차
```bash
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"
```

### 검증
```bash
ls ~/.cache/huggingface/hub/ | grep -i whisper
```
**예상 출력**: `models--Systran--faster-whisper-small` 디렉토리 존재.

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `Warning: You are sending unauthenticated requests to the HF Hub` | 노란색 경고만 — 정상 | 무시 |
| 다운로드 멈춤 | 네트워크 불안정 | 재실행. 부분 다운로드는 자동 재개. |
| `OSError: Cannot load model` | 디스크 공간 부족 | `df -h ~/.cache/huggingface` 확인 |

---

## 8. 마이크 권한 부여

**목적**: 회의비서 `--record` 모드의 PortAudio 접근 허용.
**소요**: 1분

### 절차
1. 시스템 설정 → **개인정보 보호 및 보안** → **마이크**
2. 사용 중인 터미널 앱 (Terminal / iTerm2 / Cursor 등) **토글 켜기**
3. 터미널 완전 종료 (⌘+Q) 후 재실행

### 검증
```bash
python3 -c "import sounddevice as sd; print(sd.query_devices(kind='input'))"
```
**예상 출력**: 기본 입력 장치 정보 (이름·채널 수 등)

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `PortAudioError: Error opening InputStream` | 권한 미부여 또는 권한 변경 후 터미널 재시작 안 함 | 토글 재확인 + 터미널 ⌘+Q 후 재실행 |
| 목록에 터미널 앱이 없음 | 첫 권한 요청 전 | `--record` 한 번 실행하면 OS 권한 팝업이 뜸 → 허용 |

---

## 9. Firecrawl MCP 등록 (선택 — 카드뉴스 URL 모드 사용 시)

**목적**: 카드뉴스 ②의 URL 모드(웹 크롤링) 활성화.
**소요**: 3분

### 사전 작업
1. <https://firecrawl.dev> 회원가입
2. 대시보드 → **API Keys** → **Create API Key**
3. 키 복사 (형식: `fc-` 로 시작하는 32자 문자열)

### 절차
```bash
claude mcp add firecrawl -e FIRECRAWL_API_KEY=fc-여기에키 -- npx -y firecrawl-mcp
```
> 옵션 순서 주의: `<name>`(`firecrawl`)이 반드시 `-e` *앞에* 와야 함. `-e`는 variadic 옵션이라 뒤로 가면 name까지 환경변수로 해석됨.

### 검증
```bash
claude mcp list
```
**예상 출력**: `firecrawl: npx -y firecrawl-mcp - ✓ Connected`

추가 스모크 테스트:
```bash
claude -p "https://example.com 을 firecrawl_scrape로 가져와 markdown만 출력" --allowedTools mcp__firecrawl__firecrawl_scrape
```
**예상 출력**: `# Example Domain` 으로 시작하는 markdown.

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `Invalid environment variable format: firecrawl` | `<name>`이 `-e` 뒤에 위치 | 명령 순서 수정: `add firecrawl -e KEY=value -- npx ...` |
| `firecrawl: ... ✗ Failed to connect` | API 키 오타 또는 만료 | 키 재확인 또는 새 키 발급 후 재등록 |
| `npx: command not found` | Node.js 미설치 | Step 3 확인 |
| `Quota exceeded` | 무료 500/월 한도 소진 | 한도 회복 대기 또는 유료 플랜 |

---

## 10. 회의비서 동작 검증

**목적**: 시연 ① 풀 파이프라인 검증.
**소요**: 2분

### 절차
```bash
cd 08_시그니처시연/01_회의비서
python3 run.py samples/sample_transcript.txt
```

### 검증
- 약 5초 후 기본 브라우저가 자동으로 열림
- HTML 리포트 표시: 제목 · 핵심 요약 · 액션 아이템 · 결정 사항 · 리스크 · 회의 전문 토글

마이크 모드 검증:
```bash
python3 run.py --record
```
"🔴 녹음 시작" 표시 → 5~10초 발화 → Enter → 전사·요약·HTML 자동 오픈.

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `ModuleNotFoundError: No module named '<X>'` | 패키지 미설치 | Step 6 재실행 |
| `PortAudioError` | 마이크 권한 | Step 8 확인 |
| 한국어가 일본어로 전사됨 | `language="ko"` 미지정 | `run.py` 코드 확인 |
| 브라우저 자동 오픈 실패 (-43) | 한글 경로 + `webbrowser.open` 사용 | `run.py`의 `open_in_browser()` 가 `subprocess.run(["open", ...])` 폴백 사용하는지 확인 |

---

## 11. 카드뉴스 동작 검증

**목적**: 시연 ② 풀 파이프라인 + 웹 UI 검증.
**소요**: 3분

### 절차
```bash
cd ../02_카드뉴스
python3 run.py
```
브라우저가 `http://localhost:8765` 자동 오픈.

폼 입력: `samples/sample_markdown.md` → *5장 생성 시작* → 약 15~25초 대기 → 결과 페이지 → *📥 5장 한 번에 다운로드 (ZIP)* 클릭.

종료: 터미널에서 `Ctrl + C`.

### 검증
- ZIP 파일이 다운로드 폴더에 생성됨 (~470KB)
- ZIP 압축 해제 시 5장 PNG (1080×1080 @2x = 2160×2160 실픽셀)

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `Address already in use` (포트 8765) | 다른 프로세스 점유 | `lsof -i :8765` 로 PID 확인 후 종료 |
| 결과 페이지 카드가 빈 헤드라인 | 입력 URL이 봇 차단 또는 글 목록 페이지 | 글 단건 URL로 재시도, 또는 `samples/sample_markdown.md` 폴백 |
| `Playwright` Chromium 미설치 | Step 6의 `playwright install chromium` 누락 | 재실행 |
| 한글이 세로로 한 글자씩 깨짐 | `word-break: keep-all` 누락 | `templates/card.html` CSS 확인 |
| 폰트가 시스템 기본으로 표시 | Pretendard CDN 로드 전 스크린샷 | 정상 동작 — 임팩트만 약간 떨어짐 |

---

## 검증 완료 체크리스트

- [ ] `brew --version` 정상
- [ ] `python3 --version` ≥ 3.10
- [ ] `node --version` ≥ 20
- [ ] `claude --version` 정상
- [ ] `python3 -c "import sounddevice, faster_whisper, playwright, flask; print('OK')"` → OK
- [ ] `claude mcp list` 에 `firecrawl ✓ Connected` (URL 모드 사용 시)
- [ ] 회의비서: `samples/sample_transcript.txt` 입력 → HTML 자동 오픈
- [ ] 회의비서: `--record` 모드 → 마이크 녹음 → HTML 자동 오픈
- [ ] 카드뉴스: 웹 UI → 폼 제출 → 5장 PNG + ZIP 다운로드

---

## (선택) 화자 구분 회의비서 추가 설치

기본 회의비서(`01_회의비서`)에 **화자 자동 분리**를 더한 *심화 버전*. HuggingFace 가입 + 모델 3개 동의 + pyannote.audio 추가 설치가 필요합니다.

→ **[`01-1_회의비서_화자구분/세팅가이드_macOS.md`](01-1_회의비서_화자구분/세팅가이드_macOS.md)** 별도 가이드 참고 (약 20~30분 추가 소요).

> 이 단계는 *Week 2 미션 후보*이기도 합니다. 강의 시간엔 강사 PC 시연만 보고, *집에서 자기 손으로 추가하기*가 자연스러운 학습 흐름.

---

## 참고 자료

- 회의비서 재현용 프롬프트: `01_회의비서/PROMPT.md`
- 카드뉴스 재현용 프롬프트: `02_카드뉴스/PROMPT.md`
- 강사용 시연 매뉴얼: `강사매뉴얼.md`
