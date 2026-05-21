# 회의 비서 — 시그니처 시연 ①

마이크 녹음 → 전사 → 요약·액션 추출 → **HTML 리포트 자동 오픈**. 전부 로컬·MIT 계열 OSS.

## 동작 흐름

```
🎤 마이크 (sounddevice)  ─┐
🎵 .m4a/.mp3/.wav 파일 ─┼─→ faster-whisper 전사 ─→ claude -p (요약+액션) ─→ HTML 자동 오픈
📄 .txt 파일 ───────────┘
```

| 단계 | OSS | 라이선스 |
|---|---|---|
| 녹음 | sounddevice + soundfile + numpy | MIT / BSD |
| 전사 | faster-whisper (small, int8 CPU) | MIT (모델 Apache 2.0) |
| 요약 | Claude Code CLI (`claude -p`) | 기존 인증 그대로 |
| 출력 | Python str.format → HTML | — |

## 설치 (1회)

### Windows (PowerShell 7) ★

```powershell
python -m pip install sounddevice soundfile numpy faster-whisper
```

> Claude Code는 별도 설치돼 있어야 합니다 (`claude --version` 확인).
> 첫 마이크 녹음 시 **설정 → 개인 정보 및 보안 → 마이크 → "데스크톱 앱이 마이크에 액세스하도록 허용"** 토글 ON 필수.

### macOS / Linux

```bash
pip install sounddevice soundfile numpy faster-whisper
```

> macOS는 시스템 설정 → 개인정보 보호 → 마이크에서 터미널 앱 허용 후 ⌘+Q.

## 실행

### Windows (PowerShell) ★

```powershell
# ★ 회의 시작 — 마이크 녹음 (Enter로 종료)
python run.py --record

# 기존 녹음 파일 (m4a/mp3/wav)
python run.py samples\meeting.m4a

# 즉시 데모용 텍스트
python run.py samples\sample_transcript.txt
```

### macOS / Linux

```bash
python3 run.py --record
python3 run.py samples/meeting.m4a
python3 run.py samples/sample_transcript.txt
```

녹음본은 `samples/recording_YYYYMMDD_HHMMSS.wav`로 자동 저장, 리포트는 `output/`에 저장되고 기본 브라우저로 자동 오픈.

## 실측 성능 (small 모델 · CPU)

| 입력 | 길이 | 전사 시간 | 요약 시간 | 합계 |
|---|---|---|---|---|
| 텍스트 | 1,000자 | 0초 | 5초 | **5초** |
| 합성 음성 (.wav) | 10초 | 7초 | 5초 | **12초** |
| 실제 회의 (.m4a) | 5분 | 약 120초 | 약 10초 | **약 130초** |

## 모델 선택 (한국어 정확도 기준)

`run.py`의 `WhisperModel("small", ...)` 한 줄로 교체.

| 모델 | 용량 | 5분 회의 | 한국어 정확도 | 권장 |
|---|---|---|---|---|
| `base` | 150MB | ~60초 | 보통 | 시연 임팩트 최우선 시 |
| `small` | 470MB | ~120초 | 좋음 | **★ 기본값** |
| `medium` | 1.5GB | ~300초 | 매우 좋음 | 정확도 최우선 시 |
| `large-v3` | 3GB | ~600초 | 최고 | 공식 회의록용 |

**시연 직전 사전 다운로드** — 첫 실행 시 모델을 자동 다운로드하므로, 강의 직전 한 번 미리 실행해서 캐시해두세요:

**Windows**:
```powershell
python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"
```

**macOS / Linux**:
```bash
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"
```

## 강의용 데모 흐름 (Block D · Demo 1)

1. **전(前) 강의 준비** — `samples/`에 `sample_transcript.txt` 미리 배치
2. **시연 (6분)**
   - 0:00~1:00 — 입력 파일 보여주기 (회의 전문 / 또는 5분짜리 m4a)
   - 1:00~2:30 — `python run.py samples\sample_transcript.txt` (Windows) 실행
   - 2:30~5:00 — 브라우저 자동 오픈된 리포트 화면 워크스루
     - 핵심 요약 · 액션 아이템 · 결정사항 · 리스크
   - 5:00~6:00 — *"이걸 Day 2 매크로 #6 후보로 등록할 수 있습니다"* 메시지

## 출력 예시

`output/20260518_100432_영업팀_주간_회의.html` — 종이 톤 + 와인 액센트 디자인 시스템 그대로.

## 슬랙 안 쓰는 이유

학원생들은 사내 슬랙이 없는 경우가 많아서 시연 자체가 막힙니다. 로컬 HTML은:
- 설치/인증 0
- 결과물이 즉시 시각화됨
- "30일 로드맵" Week 1에서 *Notion/Gmail로 출력 대상만 바꾸기* 미션과 자연 연결

## 파일 구조

```
01_회의비서/
├── run.py                  # 메인 스크립트
├── prompts/
│   └── summarize.md        # Claude 프롬프트 (JSON 강제)
├── templates/
│   └── report.html         # 출력 템플릿 (Paperlogy 톤)
├── samples/
│   └── sample_transcript.txt
├── output/                 # 생성된 리포트
└── README.md
```

## 흔히 막히는 곳 (Windows 우선)

| 증상 | 해결 |
|---|---|
| `python` 명령이 인식 안 됨 | 새 PowerShell 창 / 설정 → 앱 실행 별칭에서 `python.exe`, `python3.exe` OFF |
| `PortAudioError` — 마이크 못 잡음 | 설정 → 개인 정보 → 마이크 → ★ ***데스크톱 앱*** 토글 ON 후 PowerShell 재시작 |
| 한글이 □ 로 표시 | PowerShell 7 사용 (cmd / PS 5.1 X) + `chcp 65001` |
| `claude` 명령 안 됨 | `claude.cmd` 가 PATH에 있는지 확인. 새 PowerShell 창 |
| `[WinError 2]` 에러 | 거의 항상 새 PowerShell 창 한 번 열면 해결 |
