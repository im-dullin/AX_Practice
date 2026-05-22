# 세팅 가이드 · Windows

> Windows 11 기준 · 약 30~45분 · 단계별로 따라가면 3가지 프로젝트(회의비서 · 카드뉴스 · 주간보고) 모두 실행 가능합니다.
>
> 각 단계는 **작업 → 명령어 → 예상 결과 → 흔한 오류 / 대처 → 검증** 순서.

---

## 1. Windows Terminal 설치

**작업** — Windows 기본 cmd / PowerShell 5.1은 한글·이모지가 깨집니다. UTF-8 지원하는 **Windows Terminal** 먼저 설치.

**명령어** — GUI 작업:
1. 시작 메뉴 → "Microsoft Store" 검색 → 실행
2. Store 검색창에 "Windows Terminal" 입력
3. *Microsoft Corporation* 게시자 결과 → **설치**

**예상 결과**: 시작 메뉴에 "Windows Terminal" 등록됨.

**흔한 오류 / 대처**:
- Windows 10 구버전이라 Store에서 안 보임
  → <https://github.com/microsoft/terminal/releases> 에서 `.msixbundle` 파일 직접 다운로드 후 더블 클릭 설치

**검증**:
시작 → "Windows Terminal" 검색 → 실행 → 창이 뜨면 OK

---

## 2. PowerShell 7 설치

**작업** — Windows에 기본 깔린 PowerShell 5.1은 한글 인코딩 문제. **PowerShell 7**을 추가 설치.

**명령어** — Windows Terminal에서 (관리자 권한 추천: 시작 → "Terminal" 우클릭 → "관리자 권한으로 실행"):

```powershell
winget install Microsoft.PowerShell
```

**예상 결과**:
```
Successfully installed
```

**흔한 오류 / 대처**:
- `winget 명령을 찾을 수 없습니다`
  → Microsoft Store → "App Installer" 검색 → 설치 → Windows Terminal 재시작
- `0x80070005` (권한 거부)
  → Windows Terminal을 *관리자 권한*으로 다시 실행

**검증**:
Windows Terminal 완전히 닫고 새로 실행 → 상단 탭 옆 **∨** 클릭 → **PowerShell** (← 7 버전. *Windows PowerShell*은 5.1이라 선택 X) 선택 → 다음 명령:

```powershell
$PSVersionTable.PSVersion
```

→ `Major: 7, Minor: x` 가 떠야 OK

---

## 3. 콘솔 UTF-8 영구 설정

**작업** — PowerShell이 새 창에서도 한글·이모지를 정상 표시하게 영구 설정.

**명령어** — PowerShell 7에서:

```powershell
notepad $PROFILE
```

> *"파일이 없습니다. 만들겠습니까?"* 가 뜨면 **예** 클릭.

메모장이 열리면 파일 끝에 아래 **3줄을 추가** → `Ctrl + S` 저장 → 메모장 닫기:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
chcp 65001 > $null
```

**예상 결과**: 파일이 저장되고 메모장이 닫힘.

**흔한 오류 / 대처**:
- `이 시스템에서 스크립트를 실행할 수 없으므로...`
  → PowerShell에서 한 번 실행:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```
  → `Y` 입력 후 Enter

**검증**:
Windows Terminal **닫고 새로 열기** → PowerShell 7 탭 → 다음 명령:

```powershell
[Console]::OutputEncoding.WebName
```

→ `utf-8` 출력되면 OK

```powershell
Write-Host "한글 ✅ 이모지"
```

→ `한글 ✅ 이모지` 깨지지 않고 정상 표시되면 OK

---

## 4. Python 3.12 설치

**작업** — 모든 시연의 본체 언어 설치.

**명령어**:
```powershell
winget install Python.Python.3.12
```

**예상 결과**:
```
Successfully installed
```

**흔한 오류 / 대처**:
- `1603 에러` (Windows Installer 실패)
  → PowerShell을 *관리자 권한*으로 다시 열고 명령 재실행
- `winget` 인식 안 됨 → 2단계 흔한 오류 항목 참고

**검증** — 설치 후 반드시 **새 PowerShell 창** 열고:

```powershell
python --version
```

→ `Python 3.12.x` 출력

```powershell
where.exe python
```

→ `C:\Users\...\AppData\Local\Programs\Python\Python312\python.exe` 가 첫 줄에 보여야 OK

> 만약 첫 줄이 `...\WindowsApps\python.exe` (Microsoft Store stub)이면 → 설정 → 앱 → 고급 앱 설정 → 앱 실행 별칭에서 `python.exe`, `python3.exe` 두 토글 OFF → 새 PowerShell 창

---

## 5. Node.js LTS 설치

**작업** — Firecrawl MCP 서버를 `npx`로 실행하기 위해 필요.

**명령어**:
```powershell
winget install OpenJS.NodeJS.LTS
```

**예상 결과**: `Successfully installed`

**흔한 오류 / 대처**:
- `1603` → 관리자 권한 PowerShell로 재시도
- 설치는 됐는데 `node` 명령이 안 됨 → PowerShell 창 닫고 새로 열기 (PATH 반영)

**검증** — 새 PowerShell 창에서:
```powershell
node --version
```

→ `v20.x.x` 또는 `v22.x.x` 출력

---

## 6. FFmpeg 설치

**작업** — 회의비서가 오디오 변환할 때 내부적으로 사용.

**명령어**:
```powershell
winget install Gyan.FFmpeg
```

**예상 결과**: `Successfully installed`

**흔한 오류 / 대처**:
- 설치는 됐는데 `ffmpeg` 명령이 안 됨 → 새 PowerShell 창

**검증** — 새 PowerShell 창에서:
```powershell
ffmpeg -version
```

→ `ffmpeg version 7.x` 또는 `8.x` 출력

---

## 7. Claude Code 설치

**작업** — 시연의 두뇌. AI CLI.

**명령어**:
```powershell
winget install Anthropic.Claude
```

**예상 결과**: `Successfully installed`

**흔한 오류 / 대처**:
- 인식 안 됨 → 새 PowerShell 창

**검증** — 새 PowerShell 창에서:
```powershell
claude --version
```

→ `1.x.x` 출력

---

## 8. Claude Code 로그인

**작업** — Anthropic 계정 인증. 이후 모든 `claude` 명령 사용 가능.

**명령어**:
```powershell
claude login
```

**예상 결과**: 브라우저가 자동으로 열리고 Anthropic 로그인 화면 표시 → 로그인 후 권한 승인 → 터미널로 돌아오면 끝.

**흔한 오류 / 대처**:
- 브라우저가 안 열림
  → 터미널에 표시된 URL을 *수동으로 복사*해서 브라우저에 붙여넣기
- 로그인 후에도 `Authentication failed`
  → <https://claude.ai/settings/billing> 에서 결제 정보 확인

**검증**:
```powershell
claude -p "안녕"
```

→ 한국어 짧은 응답이 와야 OK

---

## 9. AX_Practice 자료 받기

**작업** — 부트캠프 실습 자료 다운로드.

**명령어**:
```powershell
cd $HOME\Downloads
git clone https://github.com/im-dullin/AX_Practice.git
cd AX_Practice
```

**예상 결과**:
```
Cloning into 'AX_Practice'...
remote: ...
Receiving objects: 100% ...
```

폴더 안에 `01_회의비서`, `02_카드뉴스`, `03_주간보고_자동화` 가 보여야 OK.

**흔한 오류 / 대처**:
- `git 명령을 찾을 수 없습니다`
  → ```powershell
  winget install Git.Git
  ```
  → 새 PowerShell 창

**검증**:
```powershell
ls
```

→ 디렉토리 목록에 `01_회의비서`, `02_카드뉴스`, `03_주간보고_자동화`, `세팅가이드_Windows.md` 등이 보이면 OK

---

## 10. Python 라이브러리 설치

**작업** — 3개 프로젝트가 사용하는 Python 패키지 한 번에 설치.

**명령어**:
```powershell
python -m pip install --upgrade pip
```
```powershell
python -m pip install sounddevice soundfile numpy faster-whisper playwright flask requests python-dotenv
```

**예상 결과**:
```
Successfully installed sounddevice-... soundfile-... numpy-... faster-whisper-... playwright-... flask-... requests-... python-dotenv-...
```

**흔한 오류 / 대처**:
- `Microsoft Visual C++ 14.0 or greater is required`
  → <https://aka.ms/vs/17/release/vs_BuildTools.exe> 다운로드 → 설치 시 *"C++ 빌드 도구"* 선택 → 재시도
- `ERROR: Could not install packages due to an OSError`
  → 관리자 권한 PowerShell로 재시도
- `SSL DECRYPTION_FAILED_OR_BAD_RECORD_MAC`
  → 같은 명령 재실행 (pip 캐시 사용해 끊긴 부분부터 재개)

**검증**:
```powershell
python -c "import sounddevice, soundfile, faster_whisper, playwright, flask, requests, dotenv; print('OK')"
```

→ `OK` 한 단어가 출력되면 OK

---

## 11. Playwright Chromium 캐시

**작업** — 카드뉴스가 PNG 5장 찍을 때 사용하는 헤드리스 브라우저 (약 150MB).

**명령어**:
```powershell
python -m playwright install chromium
```

**예상 결과**:
```
Downloading Chromium ...
Chromium ... downloaded to C:\Users\...\AppData\Local\ms-playwright\chromium-...
```

**흔한 오류 / 대처**:
- 다운로드 멈춤 → 같은 명령 재실행 (이어받기)

**검증**:
```powershell
ls $env:USERPROFILE\AppData\Local\ms-playwright
```

→ `chromium-...` 디렉토리가 보이면 OK

---

## 12. Whisper 모델 사전 다운로드

**작업** — 회의비서의 한국어 음성 인식 모델 (약 470MB) 미리 받아 시연 시 지연 방지.

**명령어**:
```powershell
python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"
```

**예상 결과**:
```
config.json: ... 100%
model.bin: ... 100%
tokenizer.json: ... 100%
```

(노란색 `Warning` 메시지는 정상 — 무시)

**흔한 오류 / 대처**:
- 다운로드 멈춤 → 같은 명령 재실행
- `Permission denied` → `%USERPROFILE%\.cache\huggingface` 폴더 권한 확인

**검증**:
```powershell
ls $HOME\.cache\huggingface\hub
```

→ `models--Systran--faster-whisper-small` 디렉토리가 보이면 OK

---

## 13. 마이크 권한 부여

**작업** — 회의비서 마이크 녹음(`--record`)이 동작하려면 Windows 권한 필요.

**명령어** — GUI 작업:
1. **설정** 열기 (Windows + I)
2. 왼쪽 **개인 정보 및 보안** → **마이크**
3. 다음 **두 토글을 모두 ON**:
   - *"앱에서 마이크에 액세스하도록 허용"*
   - ★ ***"데스크톱 앱이 마이크에 액세스하도록 허용"*** ← 이게 더 중요

**예상 결과**: 두 토글 모두 *켜짐* 상태.

**흔한 오류 / 대처**:
- 첫 번째 토글만 켜면 `PortAudioError`
  → 반드시 두 번째 *"데스크톱 앱"* 토글도 ON (python.exe가 데스크톱 앱으로 분류됨)

**검증**:
```powershell
python -c "import sounddevice as sd; print(sd.query_devices(kind='input'))"
```

→ 기본 마이크 정보 출력 (이름·채널 수)

---

## 14. (선택) Firecrawl MCP 서버 등록

**작업** — 카드뉴스 ②의 URL 모드 사용 시 필요. 오프라인 데모만 할 거면 건너뛰기.

**명령어** — 사전 작업:
1. <https://firecrawl.dev> 가입
2. 대시보드 → **API Keys** → **Create API Key** → 키 복사 (예: `fc-abc123...`)

PowerShell에서 (Claude Code 인터랙티브 세션 *바깥*):

```powershell
claude mcp add firecrawl -e FIRECRAWL_API_KEY=fc-여기에키 -- npx -y firecrawl-mcp
```

> ★ `firecrawl` 이름을 `-e` *앞에* 두는 게 핵심. 뒤에 두면 환경변수로 오인됨.

**예상 결과**:
```
Added stdio MCP server: firecrawl
```

**흔한 오류 / 대처**:
- `Invalid environment variable format: firecrawl`
  → name을 `-e` 뒤에 둠. 위 명령 그대로 복사해서 키 부분만 교체
- `Quota exceeded` (한도 초과)
  → 다음 달 회복 대기 또는 유료 플랜

**검증**:
```powershell
claude mcp list
```

→ `firecrawl: npx -y firecrawl-mcp - ✓ Connected` 가 보이면 OK

---

## 15. (선택) Notion Integration Token 발급

**작업** — 주간보고 ③에서 사용. Notion 안 쓰면 건너뛰기.

**명령어** — 사전 작업:
1. <https://www.notion.so/profile/integrations> 접속
2. **+ New integration** 클릭
3. Type: **Internal** 선택, 이름 자유
4. 생성 후 **"Show"** 클릭 → 토큰 복사 (`ntn_` 또는 `secret_` 로 시작)

PowerShell에서:
```powershell
cd 03_주간보고_자동화
Copy-Item .env.example .env
notepad .env
```

메모장이 열리면 `NOTION_TOKEN=` 뒤를 *실제 토큰*으로 교체 → 저장.

마지막으로 Notion 페이지에 Integration 연결:
1. 주간보고용 Notion 페이지 우상단 `···` → **Connections** → 위에서 만든 Integration 추가

**예상 결과**: `.env` 파일에 진짜 토큰이 저장됨.

**흔한 오류 / 대처**:
- 토큰을 코드에 박지 마세요. *반드시* `.env` 파일에만.
- 채팅·캡처에 노출되었다면 → Notion에서 *Reset* 버튼으로 새 토큰 발급

**검증** — 03_주간보고_자동화 폴더에서:
```powershell
type .env
```

→ `NOTION_TOKEN=ntn_xxx...` 가 표시되면 OK

---

## 16. 회의비서 동작 검증

**작업** — 시연 ① 동작 확인.

**명령어**:
```powershell
cd $HOME\Downloads\AX_Practice\01_회의비서
python run.py samples\sample_transcript.txt
```

**예상 결과**:
```
📥 입력: sample_transcript.txt
📄 텍스트 로드...
🤖 Claude 요약 + 액션 추출...
🎨 HTML 렌더링...
✅ 완료: ...
```

→ 약 5초 후 기본 브라우저가 자동으로 열리고 *회의 요약 리포트* 표시.

**흔한 오류 / 대처**:
- `ModuleNotFoundError` → 10단계(Python 라이브러리) 재실행
- 브라우저가 안 열림 → `output\` 폴더의 HTML 파일을 더블 클릭으로 직접 열기

**검증**: 브라우저에 *제목 + 핵심 요약 + 액션 아이템 + 결정 사항 + 리스크* 5섹션이 모두 보이면 OK

---

## 17. 카드뉴스 동작 검증

**작업** — 시연 ② 동작 확인.

**명령어**:
```powershell
cd ..\02_카드뉴스
python run.py
```

**예상 결과**:
```
🌐 카드뉴스 자동 제작 UI — http://localhost:8765
   브라우저가 자동으로 열립니다.
```

→ 브라우저가 자동으로 열림.

폼에 다음 입력:
```
samples\sample_markdown.md
```

→ *"5장 생성 시작"* 클릭 → 약 15~25초 대기 → 결과 페이지 → **📥 5장 한 번에 다운로드 (ZIP)** 클릭

**흔한 오류 / 대처**:
- Defender 방화벽 알림 → *"개인 네트워크"* 허용 (localhost만 바인딩되어 외부 접근 불가)
- 8765 포트 충돌
  → ```powershell
  Get-NetTCPConnection -LocalPort 8765
  ```
  → PID 확인 후 작업 관리자에서 해당 프로세스 종료

**검증**: ZIP 파일을 다운로드 폴더에서 압축 해제 → PNG 5장이 들어있으면 OK

종료: 터미널에서 `Ctrl + C`

---

## 18. 주간보고 동작 검증

**작업** — 시연 ③ 동작 확인 (Notion 토큰 + 페이지 연결이 끝나 있어야 함).

**명령어**:
```powershell
cd ..\03_주간보고_자동화
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

**예상 결과**:
```
 * Running on http://127.0.0.1:5000
```

→ 브라우저가 자동으로 열림 → 폼에 Notion 페이지 URL 붙여넣기 → *"주간보고 생성"* 클릭.

**흔한 오류 / 대처**:
- `Activate.ps1을 로드할 수 없습니다` (실행 정책)
  → ```powershell
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```
  → `Y` 후 재시도
- `Notion API 403` → Notion 페이지 `···` → Connections에 Integration이 추가됐는지 확인
- `이번 주 메모가 없어요` → 일별 토글 라벨이 `YYYY-MM-DD` (예: `2026-05-22 화`) 로 *시작*하는지 확인

**검증**: 브라우저에 *헤드라인 + 메트릭 + 7섹션 (BEFORE/PROGRESS/DECISIONS/LESSONS/NEXT/ASKS/RISKS)* HTML 보고서가 표시되면 OK

종료: 터미널 `Ctrl + C` + `deactivate`

---

## 끝났습니다

여기까지 통과하면 **회의비서 · 카드뉴스 · 주간보고 3개 프로젝트 모두 자기 PC에서 100% 동작**합니다.

막히는 단계가 있으면 그 단계의 **흔한 오류 / 대처** 항목 먼저 확인 → 그래도 안 풀리면 강사에게 *몇 번째 단계 · 어떤 오류 메시지* 한 줄로 요청.

---

## (선택) 화자 구분 회의비서 추가 설치

기본 회의비서(`01_회의비서`)에 **화자 자동 분리**를 더한 *심화 버전*. HuggingFace 가입 + 모델 3개 동의 + pyannote.audio 추가 설치가 필요합니다.

→ **[`01-1_회의비서_화자구분/세팅가이드_Windows.md`](01-1_회의비서_화자구분/세팅가이드_Windows.md)** 별도 가이드 참고 (약 20~30분 추가 소요).

> 이 단계는 *Week 2 미션 후보*이기도 합니다. 강의 시간엔 강사 PC 시연만 보고, *집에서 자기 손으로 추가하기*가 자연스러운 학습 흐름.
