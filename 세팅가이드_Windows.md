# 세팅 가이드 · Windows

## 개요

| 항목 | 값 |
|---|---|
| 대상 OS | Windows 11 (또는 Windows 10 21H2 이상) |
| 소요 시간 | 30 ~ 45분 |
| 필요 권한 | 관리자 계정 |
| 디스크 여유 | 최소 5GB |
| 셸 | PowerShell 7+ (★ cmd 및 PowerShell 5.1 사용 금지) |
| 대상 프로젝트 | 시그니처 시연 ①~⑤ 전체 + 미니프로젝트 (단일 Python 환경 공유) |

## 설치 항목 요약

| # | 항목 | 용도 | 크기 |
|---|---|---|---|
| 1 | Windows Terminal | UTF-8 지원 콘솔 (한글·이모지 정상 표시) | ~30MB |
| 2 | PowerShell 7 | 최신 셸 (cmd·PS 5.1은 cp949 인코딩 한계) | ~120MB |
| 3 | Python 3.12 | 시연 본체 언어 | ~80MB |
| 4 | Node.js LTS | Firecrawl MCP의 `npx` 런타임 | ~70MB |
| 5 | FFmpeg | 회의비서 오디오 처리 | ~80MB |
| 6 | Claude Code | AI CLI · MCP 호스트 | ~150MB |
| 7 | Python 패키지 (pip) | sounddevice · faster-whisper · playwright · flask 등 | ~500MB |
| 8 | Chromium (Playwright) | 헤드리스 브라우저 (카드뉴스 PNG 생성) | ~150MB |
| 9 | Whisper `small` 모델 | 한국어 음성 인식 모델 캐시 | ~470MB |

---

## 1. Windows Terminal + PowerShell 7 설치

**목적**: cmd · PowerShell 5.1은 cp949 기본 인코딩이라 한글·이모지가 깨짐. UTF-8 지원 콘솔 환경 확보.
**소요**: 5분

### 절차
1. **시작** 메뉴 → "Microsoft Store" 검색 → 열기
2. Store에서 **"Windows Terminal"** 검색 → *설치*
3. 시작 메뉴에서 *Windows Terminal* 실행 (없으면 검색)
4. Windows Terminal 안에서 *PowerShell* 탭 → 다음 명령:
   ```powershell
   winget install Microsoft.PowerShell
   ```
5. 설치 완료 후 Windows Terminal **완전 종료 후 재실행**
6. 상단 탭 옆 **∨** 드롭다운 → *PowerShell* (← 7 버전, *Windows PowerShell*은 5.1이므로 선택 금지)

### 검증
```powershell
$PSVersionTable.PSVersion
```
**예상 출력**: `Major: 7, Minor: x, Build: x`

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| Microsoft Store에서 *Windows Terminal*을 찾을 수 없음 | Windows 10 구 버전 | <https://github.com/microsoft/terminal/releases> 에서 `.msixbundle` 직접 설치 |
| `winget` 명령이 인식되지 않음 | App Installer 누락 | Microsoft Store → "App Installer" 검색 후 설치 → PowerShell 재시작 |
| 드롭다운에 PowerShell 7이 안 보임 | Windows Terminal 재시작 안 함 | 모든 Windows Terminal 창 닫고 재실행 |

---

## 2. 콘솔 인코딩 영구 설정

**목적**: PowerShell이 새 창에서도 UTF-8을 기본으로 사용하게 함 (한글·이모지 깨짐 영구 해소).
**소요**: 2분

### 절차
PowerShell 7 창에서:
```powershell
notepad $PROFILE
```
> *"파일이 없습니다. 만들겠습니까?"* 다이얼로그 → *예*.

메모장이 열리면 파일 끝에 다음 **3줄을 추가** 후 저장 (`Ctrl + S`) 후 메모장 종료:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
chcp 65001 > $null
```

설정 적용: Windows Terminal 닫고 새 창 열기.

### 검증
```powershell
[Console]::OutputEncoding.WebName
```
**예상 출력**: `utf-8`

이모지 표시 테스트:
```powershell
Write-Host "한글 ✅ 이모지"
```
**예상 출력**: 깨지지 않고 정상 표시.

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `이 시스템에서 스크립트를 실행할 수 없으므로` | 실행 정책 제한 | 관리자 PowerShell에서 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `$PROFILE` 위치를 모르겠음 | 표시 명령 | `echo $PROFILE` 로 경로 확인 후 직접 메모장 실행 |
| 새 창에서도 여전히 깨짐 | $PROFILE 저장 안 됨 / Windows PowerShell 5.1 창 사용 | 메모장 저장 재확인 + 드롭다운에서 *PowerShell* (7) 선택 |

---

## 3. winget 동작 확인

**목적**: Windows 11 기본 탑재된 패키지 매니저 작동 확인.
**소요**: 1분

### 절차
PowerShell 7에서:
```powershell
winget --version
```

### 검증
**예상 출력**: `v1.x.x`

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `winget이라는 cmdlet ... 인식되지 않습니다` | App Installer 누락 (구버전 Windows 10) | Microsoft Store → "App Installer" 설치 후 PowerShell 재시작 |
| `0x80073D02` 에러 | Windows 업데이트 필요 | 설정 → Windows Update → 최신 업데이트 적용 |

---

## 4. 핵심 도구 4종 설치 (Python · Node · FFmpeg · Claude Code)

**목적**: 모든 시연이 의존하는 런타임·CLI 한 번에 설치.
**소요**: 10 ~ 15분

### 절차
PowerShell 7에서 각 줄을 *순차적으로* 실행:
```powershell
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
winget install Gyan.FFmpeg
winget install Anthropic.Claude
```

각 명령마다 라이선스 동의 프롬프트가 뜨면 `Y` 입력 후 Enter.

설치 완료 후 **새 PowerShell 7 창**을 열어야 PATH가 반영됨 (Windows Terminal에서 `Ctrl + Shift + T` 또는 새 탭).

### 검증
새 창에서:
```powershell
python --version
node --version
ffmpeg -version | Select-Object -First 1
claude --version
```
**예상 출력** (4줄):
```
Python 3.12.x
v22.x.x      (또는 v20.x.x+)
ffmpeg version 7.x  또는 8.x
1.x.x        (Claude Code 버전)
```

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `python.exe is not recognized` | PATH 미반영 | 새 PowerShell 창 또는 PC 재시작 |
| `claude를 인식할 수 없습니다` | PATH 미반영 또는 설치 실패 | `where.exe claude` 로 위치 확인. 안 보이면 winget 재실행 |
| `winget install` 후 `0x80070005` | 관리자 권한 필요 | Windows Terminal *관리자 권한*으로 재실행 |
| `python` 명령이 Microsoft Store를 열려고 함 | Windows 기본 stub | 설정 → 앱 → 고급 앱 설정 → 앱 실행 별칭 → `python.exe` / `python3.exe` 끄기 |
| Node.js 설치 후에도 `node` 명령 없음 | PATH 미반영 | 새 창. 그래도 안 되면 `winget install OpenJS.NodeJS.LTS` 재실행 |

---

## 5. Claude Code 로그인

**목적**: Anthropic 계정 인증. 이후 모든 `claude` 명령 사용 가능.
**소요**: 1 ~ 3분

### 절차
```powershell
claude login
```
브라우저 자동 오픈 → Anthropic 계정 로그인 → 권한 승인 → 터미널 복귀.

### 검증
```powershell
claude -p "안녕하세요"
```
**예상 출력**: 한국어 짧은 응답.

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| 브라우저가 열리지 않음 | 기본 브라우저 미설정 | 표시되는 URL을 수동으로 복사해 브라우저에 붙여넣기 |
| `Authentication failed` | 결제 정보 미등록 | <https://claude.ai/settings/billing> 확인 |
| `Rate limit exceeded` | 무료/구독 한도 소진 | 한도 회복 대기 또는 상위 플랜 |

---

## 6. 시연 자료 폴더 이동

**목적**: 작업 디렉토리를 시연 자료 위치로 변경.
**소요**: 1분 미만

### 절차
다운로드 받은 자료 경로에 따라 다름. 예시:
```powershell
cd $HOME\Downloads\20260528_프리미엄01
ls
```

### 검증
**예상 출력**: `08_시그니처시연` 폴더가 목록에 보임.

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `Cannot find path '...'` | 자료 위치가 다름 | 파일 탐색기에서 폴더 우클릭 → *경로로 복사* 후 `cd "붙여넣기"` |
| `cd: 인수 ...에 위치할 수 없습니다` | 공백 포함 경로 | 경로를 따옴표로 감싸기 |

---

## 7. Python 패키지 설치

**목적**: 시연 도구가 의존하는 Python 라이브러리 일괄 설치.
**소요**: 3 ~ 5분

### 절차
```powershell
python -m pip install --upgrade pip
python -m pip install sounddevice soundfile numpy faster-whisper playwright flask
python -m playwright install chromium
```

### 검증
```powershell
python -c "import sounddevice, soundfile, numpy, faster_whisper, playwright, flask; print('OK')"
```
**예상 출력**: `OK`

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `ERROR: Could not install packages due to an OSError` | 권한 부족 | Windows Terminal *관리자 권한* 재실행, 또는 `python -m pip install --user <패키지>` |
| `Microsoft Visual C++ 14.0 or greater is required` | 일부 패키지 빌드용 컴파일러 부족 | <https://aka.ms/vs/17/release/vs_BuildTools.exe> 설치, *C++ 빌드 도구* 선택 |
| Chromium 다운로드 실패 | 네트워크 / 회사 프록시 | 프록시 환경변수 설정: `$env:HTTPS_PROXY="http://proxy:port"` |
| `pip` 자체가 인식 안 됨 | python -m pip 형태로 호출해야 함 | 명령을 `python -m pip install ...` 로 통일 |

---

## 8. Whisper `small` 모델 사전 다운로드

**목적**: 회의비서 첫 실행 시 모델 다운로드(약 470MB) 지연 방지.
**소요**: 3 ~ 5분

### 절차
```powershell
python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"
```

### 검증
```powershell
ls $HOME\.cache\huggingface\hub\
```
**예상 출력**: `models--Systran--faster-whisper-small` 디렉토리 존재.

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `Warning: You are sending unauthenticated requests` | 정상 경고 | 무시 |
| 다운로드 멈춤 | 네트워크 불안정 | 재실행. 부분 다운로드는 자동 재개 |
| `Permission denied` | 캐시 디렉토리 쓰기 권한 | `%USERPROFILE%\.cache\huggingface` 폴더 권한 확인 |

---

## 9. 마이크 권한 부여

**목적**: 회의비서 `--record` 모드의 PortAudio 접근 허용.
**소요**: 2분

### 절차
1. **설정** (Windows + I) → **개인 정보 및 보안** → **마이크**
2. 다음 두 토글을 **모두 켜기**:
   - *앱에서 마이크에 액세스하도록 허용*
   - ★ ***데스크톱 앱이 마이크에 액세스하도록 허용*** ← `python.exe` 가 데스크톱 앱으로 분류됨
3. (선택) 아래 *최근에 액세스한 데스크톱 앱* 목록에 Python 관련 항목 표시 확인

### 검증
```powershell
python -c "import sounddevice as sd; print(sd.query_devices(kind='input'))"
```
**예상 출력**: 기본 입력 장치 정보.

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `PortAudioError: Error opening InputStream` | *데스크톱 앱* 토글 꺼짐 | 위 두 번째 토글 확인 |
| `OSError: PortAudio library not found` | sounddevice 빌드 누락 | `python -m pip install --force-reinstall sounddevice` |

---

## 10. Firecrawl MCP 등록 (선택 — 카드뉴스 URL 모드 사용 시)

**목적**: 카드뉴스 ②의 URL 모드(웹 크롤링) 활성화.
**소요**: 3분

### 사전 작업
1. <https://firecrawl.dev> 회원가입
2. 대시보드 → **API Keys** → **Create API Key**
3. 키 복사 (형식: `fc-` 로 시작하는 32자 문자열)

### 절차
PowerShell 7 (★ Claude Code 인터랙티브 세션 *바깥*) 에서:
```powershell
claude mcp add firecrawl -e FIRECRAWL_API_KEY=fc-여기에키 -- npx -y firecrawl-mcp
```
> 옵션 순서 주의: `<name>`(`firecrawl`)이 반드시 `-e` *앞에* 와야 함. `-e`는 variadic 옵션이라 뒤로 가면 name까지 환경변수로 해석됨.

### 검증
```powershell
claude mcp list
```
**예상 출력**: `firecrawl: npx -y firecrawl-mcp - ✓ Connected`

추가 스모크 테스트:
```powershell
claude -p "https://example.com 을 firecrawl_scrape로 가져와 markdown만 출력" --allowedTools mcp__firecrawl__firecrawl_scrape
```

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `Invalid environment variable format: firecrawl` | `<name>`이 `-e` 뒤에 위치 | 명령 순서 수정: `add firecrawl -e KEY=value -- npx ...` |
| `firecrawl: ... ✗ Failed to connect` | API 키 오타 또는 만료 | 키 재확인 또는 새 키 발급 후 재등록 |
| `npx: command not found` | Node.js 미설치 또는 PATH 미반영 | Step 4 확인 |
| `Quota exceeded` | 무료 500/월 한도 소진 | 한도 회복 대기 또는 유료 플랜 |

---

## 11. 회의비서 동작 검증

**목적**: 시연 ① 풀 파이프라인 검증.
**소요**: 2분

### 절차
```powershell
cd 08_시그니처시연\01_회의비서
python run.py samples\sample_transcript.txt
```

### 검증
- 약 5초 후 기본 브라우저가 자동으로 열림
- HTML 리포트 표시: 제목 · 핵심 요약 · 액션 아이템 · 결정 사항 · 리스크 · 회의 전문 토글

마이크 모드 검증:
```powershell
python run.py --record
```
"🔴 녹음 시작" 표시 → 5~10초 발화 → Enter → 전사·요약·HTML 자동 오픈.

첫 실행 시 Windows Defender 방화벽 알림 가능 — *개인 네트워크* 허용.

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `ModuleNotFoundError: No module named '<X>'` | 패키지 미설치 | Step 7 재실행 |
| `PortAudioError` | 마이크 권한 (★ 데스크톱 앱 토글) | Step 9 재확인 |
| `[WinError 2] 지정된 파일을 찾을 수 없습니다` (subprocess) | `claude.cmd` 호출 시 `shell=True` 누락 | `run.py` 의 subprocess 호출에 `shell=True` 추가됐는지 확인 |
| 한국어가 일본어로 전사됨 | `language="ko"` 미지정 | `run.py` 코드 확인 |
| 콘솔에서 이모지·한글 깨짐 | PowerShell 5.1 사용 또는 인코딩 미설정 | Step 1·2 재확인 |

---

## 12. 카드뉴스 동작 검증

**목적**: 시연 ② 풀 파이프라인 + 웹 UI 검증.
**소요**: 3분

### 절차
```powershell
cd ..\02_카드뉴스
python run.py
```
브라우저가 `http://localhost:8765` 자동 오픈.

폼 입력: `samples\sample_markdown.md` → *5장 생성 시작* → 약 15~25초 대기 → 결과 페이지 → *📥 5장 한 번에 다운로드 (ZIP)* 클릭.

종료: PowerShell에서 `Ctrl + C`.

### 검증
- ZIP 파일이 다운로드 폴더에 생성됨 (~470KB)
- 압축 해제 시 5장 PNG (1080×1080 @2x = 2160×2160 실픽셀)

### 흔한 오류

| 증상 | 원인 | 대처 |
|---|---|---|
| `Address already in use` (8765 포트) | 다른 프로세스 점유 | `Get-NetTCPConnection -LocalPort 8765` → 작업 관리자에서 PID 종료 |
| Defender 방화벽 알림 (Flask 시작 시) | 첫 실행 시 정상 | *개인 네트워크* 허용. localhost만 바인딩되어 외부 접근 불가 |
| 결과 페이지 카드가 빈 헤드라인 | 입력 URL이 봇 차단 또는 글 목록 페이지 | 글 단건 URL로 재시도, 또는 `samples\sample_markdown.md` 폴백 |
| Playwright Chromium 미설치 | Step 7의 `python -m playwright install chromium` 누락 | 재실행 |
| 한글이 세로로 한 글자씩 깨짐 | `word-break: keep-all` 누락 | `templates/card.html` CSS 확인 |
| ZIP이 다운로드 대신 인라인 열림 | `as_attachment=True` 누락 | `run.py` 의 `send_from_directory` 분기 확인 |

---

## 검증 완료 체크리스트

- [ ] `$PSVersionTable.PSVersion` Major: 7 이상
- [ ] `[Console]::OutputEncoding.WebName` → `utf-8`
- [ ] `python --version` ≥ 3.10
- [ ] `node --version` ≥ 20
- [ ] `claude --version` 정상
- [ ] `python -c "import sounddevice, faster_whisper, playwright, flask; print('OK')"` → OK
- [ ] `claude mcp list` 에 `firecrawl ✓ Connected` (URL 모드 사용 시)
- [ ] 회의비서: `samples\sample_transcript.txt` 입력 → HTML 자동 오픈
- [ ] 회의비서: `--record` 모드 → 마이크 녹음 → HTML 자동 오픈
- [ ] 카드뉴스: 웹 UI → 폼 제출 → 5장 PNG + ZIP 다운로드

---

## 참고 자료

- 회의비서 재현용 프롬프트: `01_회의비서/PROMPT_WINDOWS.md`
- 카드뉴스 재현용 프롬프트: `02_카드뉴스/PROMPT_WINDOWS.md`
- 강사용 시연 매뉴얼: `강사매뉴얼.md`
