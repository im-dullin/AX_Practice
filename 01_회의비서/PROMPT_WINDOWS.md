# 회의비서 ① — Claude Code 재현 프롬프트 · Windows

> **macOS / Linux 사용자는 `PROMPT.md`를 사용하세요.**
>
> **사용법**: PowerShell 7+ (또는 Windows Terminal)에서 빈 폴더로 이동 → `claude` 실행 → 아래 `---` 사이 전체를 복사·붙여넣기 → Enter.
> Claude Code가 폴더 구조·파일·의존성·검증까지 한 번에 끝냅니다.
>
> **사전 준비 (1회)**
> - Python 3.10+ — `winget install Python.Python.3.12`
> - ffmpeg — `winget install Gyan.FFmpeg` (PATH 등록 확인: `ffmpeg -version`)
> - Claude Code — `winget install Anthropic.Claude` 또는 npm 설치
> - 마이크 권한 — 설정 → 개인정보 및 보안 → 마이크 → "데스크톱 앱이 마이크에 액세스할 수 있도록 허용" 켜기
> - 콘솔 한글 깨짐 방지 — PowerShell에서 한 번 실행: `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $env:PYTHONIOENCODING = "utf-8"`

---

당신은 시니어 풀스택 엔지니어입니다. 다음 사양대로 **회의비서 미니프로젝트**를 처음부터 끝까지 구축하고 동작까지 검증해 주세요. 실행 환경은 **Windows 11 + PowerShell 7+ + Python 3.10+** 입니다. 진행 도중 의문이 생기면 사양을 우선하고, 사양이 모호한 부분만 보고하세요.

## 목표

마이크 녹음 또는 오디오/텍스트 파일을 입력 받아 **로컬에서** 전사·요약·액션 추출을 수행하고 **HTML 리포트를 자동으로 기본 브라우저에 띄우는** CLI 도구. 외부 클라우드 LLM/STT 호출 금지 — Claude Code CLI(`claude -p`)는 예외.

## 입력 3가지 모두 지원

- `python run.py --record` : 기본 마이크 녹음, **Enter 키로 종료**
- `python run.py <path>.m4a|mp3|wav` : 기존 오디오 파일
- `python run.py <path>.txt` : 즉시 데모용 회의 전문 텍스트

## 기술 스택 (정확히 이 조합 · 모두 무료·로컬)

| 단계 | OSS | 핵심 설정 |
|---|---|---|
| 녹음 | `sounddevice` + `soundfile` + `numpy` | 16kHz mono float32 WAV |
| 전사 | `faster-whisper` | `WhisperModel("small", device="cpu", compute_type="int8")`, `transcribe(..., language="ko", vad_filter=True)` |
| 요약 | Claude Code CLI | `subprocess.run(["claude", "-p", prompt, "--output-format", "json"])` |
| 출력 | Python `str.format` → HTML | `os.startfile(path)` (기본) / `webbrowser.open(file:// + urllib.parse.quote)` 폴백 |

설치 명령:
```powershell
python -m pip install --upgrade pip
python -m pip install sounddevice soundfile numpy faster-whisper
```

## 디렉토리 구조

```
회의비서/
├── run.py
├── prompts/
│   └── summarize.md
├── templates/
│   └── report.html
├── samples/
│   └── sample_transcript.txt   ← 한국어 회의 5분 분량 샘플 작성
├── output/                     ← 생성된 리포트 저장 (.gitkeep)
└── README.md
```

## prompts/summarize.md — Claude 요약 프롬프트

핵심 요건: **JSON 코드블록 하나만 응답**, 한국어, 다음 스키마 강제.

```json
{
  "title": "20자 이내 회의 제목",
  "date": "YYYY-MM-DD or empty",
  "summary": "3-5문장 핵심 요약 (비전문가도 이해 가능)",
  "decisions": ["회의에서 합의된 결정사항"],
  "actions": [{"owner": "담당자 or TBD", "task": "구체적 액션", "due": "기한 or empty"}],
  "risks": ["남은 리스크"]
}
```

## templates/report.html — 디자인 시스템

- 컬러 토큰: `--paper:#F5F1E8` / `--paper-2:#ECE5D3` / `--ink:#1A1A1A` / `--ink-2:#4A4540` / `--ink-3:#8A8479` / `--accent:#7A2E2E`
- 폰트: `Segoe UI, "Malgun Gothic", -apple-system, sans-serif` (Windows 한글 폰트 우선)
- 섹션 순서: 제목 → 날짜 → **핵심 요약** → **액션 아이템**(grid `110px 1fr 110px` · who/what/due) → **결정 사항** → **남은 리스크** → **회의 전문**(`<details>` 접힘 토글)
- 액션 아이템 빈 due는 `:empty::before { content: "—"; }`로 placeholder 표시
- **★ Python `str.format()` 호환을 위해 *모든 CSS 중괄호를 `{{` `}}` 로 이스케이프*하세요. 빠뜨리면 KeyError 납니다.**
- placeholder는 정확히 `{title}` `{date}` `{summary}` `{actions_block}` `{decisions_block}` `{risks_block}` `{transcript}` `{generated_at}`

## run.py — 함수 시그니처

```python
def record_audio() -> Path: ...                  # Enter 또는 Ctrl+C로 종료. samples/recording_<TS>.wav 저장
def transcribe(src: Path) -> str: ...            # .txt 면 그대로 read, 오디오면 faster-whisper
def summarize(transcript: str) -> dict: ...      # claude -p subprocess → JSON 응답에서 \{[\s\S]*\} 정규식으로 JSON 블록 추출
def render(data: dict, transcript: str) -> Path: ...  # html.escape 후 str.format. 빈 리스트면 "해당 사항 없음"
def open_in_browser(path: Path) -> None: ...     # win32: os.startfile(str(path.resolve())) / 폴백: webbrowser.open("file://" + urllib.parse.quote(...))
def main() -> None: ...
```

main 흐름:
```
argv[1] == "--record" → record_audio()
else → Path(argv[1])

→ transcribe → summarize → render → open_in_browser
각 단계 한 줄 진행 메시지(📥 📝 🤖 🎨 ✅) 출력.
```

## Windows 특화 안전장치

- **인코딩**: 파일 I/O 전부 `encoding="utf-8"` 명시. 스크립트 최상단에 다음 한 줄 추가하여 콘솔 깨짐 방지:
  ```python
  import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
  ```
- **브라우저 자동 오픈**: `os.startfile(str(path.resolve()))` 사용. 한글·공백 경로 안전.
- **subprocess.run**: 윈도우에서 `claude` CLI가 `claude.cmd`로 설치되는 경우가 있으므로 `shell=True` 옵션 추가:
  ```python
  subprocess.run(["claude", "-p", prompt, "--output-format", "json"], capture_output=True, text=True, shell=True, encoding="utf-8")
  ```
- **`claude` 응답 파싱**: ```` ```json ... ``` ```` 코드블록 → `re.search(r"\{[\s\S]*\}", raw)` 로 JSON 블록만 추출
- **whisper 첫 실행 시 ≈470MB 모델 자동 다운로드** — 검증 전에 사전 캐시:
  ```powershell
  python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"
  ```
  모델은 `%USERPROFILE%\.cache\huggingface\hub\` 에 저장됩니다.
- **마이크 권한**: 설정 → 개인정보 및 보안 → 마이크 → "앱이 마이크에 액세스할 수 있도록 허용" + "데스크톱 앱이 마이크에 액세스할 수 있도록 허용" 둘 다 켜야 함. 첫 `--record` 실행 시 윈도우 알림 팝업 → 허용.
- **PowerShell vs cmd**: 반드시 **PowerShell 7+** 또는 **Windows Terminal** 사용. cmd.exe / PowerShell 5.1은 cp949 기본이라 이모지·한글 깨짐.

## samples/sample_transcript.txt — 즉시 검증용 한국어 샘플 작성

영업팀 주간 회의 1,000자 분량 한국어 대본을 직접 작성하세요. 액션 4개·결정 3~4개·리스크 1~2개가 자연스럽게 추출될 수 있게 — 담당자 이름, 기한(YYYY-MM-DD), 금액, 인용 등이 명시적으로 포함되어야 합니다.

## 검증 — 아래 3개 모두 통과해야 완료

1. **텍스트 즉시 데모**
   ```powershell
   python run.py samples\sample_transcript.txt
   ```
   → 약 5초 안에 `output\<TS>_<title>.html` 생성 + 기본 브라우저 자동 오픈. 액션·결정·리스크가 정확히 추출됐는지 화면 캡처로 확인.

2. **합성 음성 검증** (선택) — PowerShell의 내장 SAPI 사용:
   ```powershell
   Add-Type -AssemblyName System.Speech
   $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
   $s.SetOutputToWaveFile("samples\test.wav")
   $s.Speak("오늘 회의를 시작합니다. 김부장입니다. 이번 주 신규 리드는 32건이고 미팅은 8건입니다.")
   $s.Dispose()
   python run.py samples\test.wav
   ```

3. **실제 마이크 녹음**
   ```powershell
   python run.py --record
   ```
   → 5초 정도 말한 뒤 Enter → 전사·요약·HTML 오픈까지 일직선.

## 흔히 빠지는 함정 (Windows 한정 포함)

- CSS 중괄호 이스케이프 누락 → `str.format` `KeyError`
- `subprocess.run(["claude", ...])` 호출 시 `[WinError 2] 지정된 파일을 찾을 수 없습니다` → `shell=True` 추가
- 콘솔에서 이모지·한글 깨짐 → PowerShell 7+ 사용 + `chcp 65001` + `sys.stdout.reconfigure(encoding="utf-8")`
- ffmpeg PATH 미등록 → faster-whisper가 .m4a/.mp3 변환 시 실패. `winget install Gyan.FFmpeg` 후 새 PowerShell 창
- whisper `language` 미지정 → 한국어를 일본어로 오인 전사
- claude 응답에서 JSON만 추출 안 함 → `json.JSONDecodeError`
- 마이크 권한 미허용 → `PortAudioError: Error opening InputStream`
- `os.startfile` 미사용하고 `webbrowser.open(file://경로)` 만 쓰면 한글 경로에서 에러 발생 가능

## 마지막 한 줄

완료 후 검증 #1 실행 결과(터미널 출력 + 생성된 HTML의 제목·요약·액션 3가지)를 첨부해 보고해 주세요.

---

> 위 프롬프트는 **Day 1 시그니처 시연 ①**의 Windows 재현 사양입니다. 부트캠프 후 자기 회사 환경(Teams 채널 발송, OneNote/Notion 페이지 등록 등)으로 출력 대상을 갈아끼우는 것이 **30일 로드맵 Week 1**의 첫 미션입니다.
