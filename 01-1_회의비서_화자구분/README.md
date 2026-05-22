# 회의비서 (화자 구분 버전) — 시그니처 시연 ①-1

기본 회의비서(`../01_회의비서/`) **+ pyannote.audio 화자 분리**. 회의 음성에서 *누가 무엇을 말했는지* 자동으로 라벨링하고, HTML 리포트에 화자별 색상으로 표시.

## 기본 버전과의 차이

| 항목 | 01_회의비서 (기본) | 01-1_회의비서_화자구분 (★) |
|---|---|---|
| 음성 → 텍스트 | faster-whisper만 | faster-whisper + **pyannote.audio** |
| 화자 라벨 | 없음 (한 줄로 평탄) | **SPEAKER_00, SPEAKER_01, ...** 자동 |
| HTML 표시 | 단일 색 | **화자별 색상 6종** |
| 첫 실행 모델 다운로드 | 470MB (Whisper) | 470MB + **1.5GB (pyannote)** |
| 추가 셋업 | 0 | HuggingFace 토큰 + 모델 라이선스 동의 |

## 동작 흐름

```
🎤 마이크 / 🎵 오디오 파일
        ↓
  ┌─────────────────────────────────┐
  │ faster-whisper (전사)            │
  │ pyannote.audio (화자 분리)        │  ← 두 모델 병렬 실행
  └──────────────┬──────────────────┘
                 ↓ (시간축 기반 병합)
  SPEAKER_00: 자, 시작하겠습니다.
  SPEAKER_01: 이번 주 신규 리드는 32건...
        ↓
🤖 Claude — 요약·결정·액션·리스크 JSON
        ↓
🎨 HTML 리포트 (화자별 색상)
```

## 사전 준비 (1회만)

### Windows (PowerShell 7) ★

1. 의존성 설치
```powershell
python -m pip install -r requirements.txt
```

2. HuggingFace 토큰 발급 + 모델 라이선스 동의 (한 번만, 약 3분):
   - <https://huggingface.co/settings/tokens> → *Create new token* → **Token type: Read**
   - <https://huggingface.co/pyannote/speaker-diarization-3.1> → *Agree and access*
   - <https://huggingface.co/pyannote/segmentation-3.0> → *Agree and access* (의존 모델)

3. `.env` 파일 만들고 토큰 저장
```powershell
Copy-Item .env.example .env
notepad .env
```
→ `HF_TOKEN=hf_xxx...` 의 `hf_xxx...` 자리에 실제 토큰을 붙여넣고 저장.

### macOS / Linux

```bash
pip install -r requirements.txt

cp .env.example .env
# .env 파일 열어서 HF_TOKEN=hf_xxx... 채워넣기
```

## 실행

### Windows
```powershell
python run.py --record                       # 마이크 녹음 (Enter로 종료)
python run.py samples\meeting.m4a            # 기존 오디오 파일
python run.py samples\sample_transcript.txt  # 텍스트 (이미 화자 표기 있으면 그대로)
```

### macOS / Linux
```bash
python3 run.py --record
python3 run.py samples/meeting.m4a
python3 run.py samples/sample_transcript.txt
```

## 실측 성능 (small + pyannote 3.1)

| 입력 | 길이 | 전사 | 화자 분리 | 요약 | 합계 |
|---|---|---|---|---|---|
| 텍스트 | 1,000자 | 0초 | 0초 | 5초 | **5초** |
| 합성 음성 | 10초 | 7초 | 8초 | 5초 | **약 20초** |
| 실제 회의 | 5분 | 120초 | 90초 | 10초 | **약 3분 40초** |

→ 화자 분리가 *전사와 비슷한 시간* 추가됨. 시연용으로 무겁지 않은 수준.

## 흔히 막히는 곳 (Windows 우선)

| 증상 | 원인 / 해결 |
|---|---|
| `HF_TOKEN 환경변수가 비어 있습니다` | `.env` 파일이 폴더 안에 있고 `HF_TOKEN=hf_xxx` 줄이 있어야 함. PowerShell 새 창에서 재실행 |
| `Model is not currently accessible` / `Repository ... gated` | pyannote 모델 페이지에서 *Agree and access* 클릭 안 함 (두 모델 다) |
| `Invalid token` / `401` | 토큰 권한 부족 또는 만료. **Read** 타입으로 재발급 |
| 첫 실행이 너무 오래 걸림 | pyannote 모델 ~1.5GB 다운로드 중. 두 번째 실행부터는 캐시 사용 |
| `PortAudioError` (마이크) | 설정 → 개인 정보 및 보안 → 마이크 → ★ *데스크톱 앱이 마이크에 액세스하도록 허용* 토글 ON |
| 한글 □ 깨짐 | PowerShell 7 + `chcp 65001` |

## 강의 시연 흐름 (5분)

1. **0:00–1:00** — 기본 회의비서 결과 먼저 보여주기 → *"화자 누군지 안 나오죠?"*
2. **1:00–4:00** — 같은 음성을 이 버전으로 처리 → 화자별 색상 HTML 워크스루
3. **4:00–5:00** — *"이게 Week 2 미션 후보 ① 입니다. 코드 60줄 추가."*

## Week 2 미션 후보 (수강생용)

- 화자 라벨(`SPEAKER_00`)을 **실명 매핑** UI 추가 — 본인 회사 회의에서 즉시 활용
- pyannote에 `num_speakers=3` *힌트* 옵션 추가 — 인원수 알 때 정확도 ↑
- 출력 단을 **Notion 페이지 자동 등재**로 갈아끼우기

## 파일 구조

```
01-1_회의비서_화자구분/
├── run.py                  # 전사 + 화자 분리 + 요약 통합
├── requirements.txt        # pyannote.audio 포함
├── .env.example            # HF_TOKEN 템플릿
├── prompts/summarize.md    # Claude 프롬프트
├── templates/report.html   # 화자 라인 스타일 추가됨
├── samples/sample_transcript.txt
├── output/                 # 생성된 리포트
└── README.md               # (이 파일)
```

## 라이선스

- **pyannote.audio** — MIT
- **pyannote/speaker-diarization-3.1** 모델 — 공개 라이선스 (가입·동의 필요, 비상업 사용 자유, 상업 사용은 pyannoteAI Premium 권장)
- **python-dotenv** — BSD-3

> 상업적 운영 환경에 배포 시 모델 라이선스 재확인 필요.
